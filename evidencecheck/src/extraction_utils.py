"""
Deterministic extraction utilities for study design and participant count.

These functions parse abstracts and return structured extractions with evidence spans.
No ML or Jev calls; pure pattern matching and heuristics.
"""

import re
import hashlib
from typing import Optional, Tuple
from datetime import datetime
from extraction_schema import (
    StudyDesignEnum,
    ParticipantCountStatus,
    EvidenceSpan,
    StudyDesignExtraction,
    ParticipantCountExtraction,
    AbstractExtraction,
)


def compute_abstract_hash(text: str) -> str:
    """Compute SHA256 hash of abstract text for deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()


def find_study_design(abstract_text: str) -> StudyDesignExtraction:
    """
    Identify study design from abstract text.
    Looks for explicit design keywords in methods section.
    Returns the extracted design with evidence span, or not_reported if unclear.
    """
    text = abstract_text.lower()

    # Pattern matching: Look for explicit design keywords
    patterns = [
        (StudyDesignEnum.RANDOMIZED_TRIAL, [
            r"random(?:ized|ly).*(?:trial|study|assignment)",
            r"randomized\s+(?:controlled\s+)?trial",
            r"rct\b",
            r"parallel.*randomized",
        ]),
        (StudyDesignEnum.OTHER_INTERVENTIONAL, [
            r"(?<!random)(?:quasi-)?experimental",
            r"intervention.*study",
            r"(?<!random)assigned.*(?:group|condition)",
            r"pre-post.*design",
        ]),
        (StudyDesignEnum.OBSERVATIONAL, [
            r"cross-sectional",
            r"cohort.*study",
            r"prospective\s+cohort",
            r"longitudinal.*study",
            r"observational",
            r"case-control",
            r"survey",
        ]),
        (StudyDesignEnum.REVIEW, [
            r"systematic\s+review",
            r"meta-analysis",
            r"literature\s+review",
            r"narrative\s+review",
            r"scoping\s+review",
        ]),
        (StudyDesignEnum.PROTOCOL, [
            r"protocol\s+(?:for|describes)",
            r"study\s+protocol",
            r"aims\s+to\s+(?:examine|test|evaluate).*(?:conducted|planned)",
        ]),
    ]

    # Try to find a match in methods-like sections
    for design, design_patterns in patterns:
        for pattern in design_patterns:
            match = re.search(pattern, text)
            if match:
                # Extract the original case text around the match
                original_text = abstract_text
                start = max(0, match.start())
                end = min(len(original_text), match.end() + 50)

                # Find the actual span in original text
                matched_text = abstract_text[start:end].split('.')[0]
                if matched_text.strip():
                    span = EvidenceSpan(
                        text=matched_text.strip(),
                        start_char=start,
                        end_char=start + len(matched_text.strip())
                    )
                    return StudyDesignExtraction(
                        design=design,
                        evidence_span=span,
                        confidence=1.0
                    )

    # No match found
    return StudyDesignExtraction(
        design=StudyDesignEnum.NOT_REPORTED,
        evidence_span=None,
        confidence=1.0
    )


def find_participant_count(abstract_text: str) -> ParticipantCountExtraction:
    """
    Extract participant count from abstract.
    Looks for explicit numbers associated with study participants.
    Returns count with status (reported, not_reported, ambiguous).

    Rules:
    - Use only explicit reported total for completed primary study
    - Do NOT substitute: screened, per-arm, planned, analyzed, animal, review-level counts
    - Mark ambiguous if multiple numbers without clear labels
    """

    # Pattern: explicit total numbers with participant indicators
    # Examples: "n=150", "120 adults", "240 participants"
    participant_patterns = [
        r"\bn\s*=\s*(\d+)\s*(?:adult|participant|subject|patient|person)",
        r"\bN\s*=\s*(\d+)\s*(?:adult|participant|subject|patient|person)",
        r"(\d+)\s+(?:adult|participant|subject|patient|person|individual)s?\s+(?:completed|included|enrolled)",
        r"(?:completed|included|enrolled|studied)\s+(\d+)\s+(?:adult|participant|subject|patient)s?",
    ]

    matches = []
    for pattern in participant_patterns:
        for match in re.finditer(pattern, abstract_text, re.IGNORECASE):
            count = int(match.group(1))
            span = EvidenceSpan(
                text=match.group(0),
                start_char=match.start(),
                end_char=match.end()
            )
            matches.append((count, span, match.group(0)))

    if not matches:
        # No participant count found
        return ParticipantCountExtraction(
            count=None,
            status=ParticipantCountStatus.NOT_REPORTED,
            evidence_span=None,
            confidence=1.0
        )

    if len(matches) == 1:
        # Single clear match
        count, span, text = matches[0]

        # Check for common exclusions (per-arm, planned, screened, etc.)
        lower_text = text.lower()
        if any(x in lower_text for x in ["per-arm", "per arm", "per group", "planned", "intended", "screened", "eligible"]):
            return ParticipantCountExtraction(
                count=None,
                status=ParticipantCountStatus.AMBIGUOUS,
                evidence_span=span,
                notes=f"Text mentions participant count but unclear if total: '{text}'",
                confidence=0.5
            )

        return ParticipantCountExtraction(
            count=count,
            status=ParticipantCountStatus.REPORTED,
            evidence_span=span,
            confidence=1.0
        )

    # Multiple numbers found: ambiguous
    if len(matches) <= 3:
        # Likely enrollment vs. completion; mark as ambiguous
        all_counts = [m[0] for m in matches]
        primary_span = matches[-1][1]  # Use the last (typically "completed")

        return ParticipantCountExtraction(
            count=None,
            status=ParticipantCountStatus.AMBIGUOUS,
            evidence_span=primary_span,
            notes=f"Multiple participant counts found: {', '.join(map(str, all_counts))}. Unclear which is primary.",
            confidence=0.4
        )

    # Many numbers: too ambiguous
    return ParticipantCountExtraction(
        count=None,
        status=ParticipantCountStatus.AMBIGUOUS,
        evidence_span=None,
        notes="Multiple participant counts mentioned; unable to determine primary total",
        confidence=0.2
    )


def extract_abstract(pmid: str, title: str, abstract_text: str) -> AbstractExtraction:
    """
    Perform complete deterministic extraction from an abstract.
    """
    abstract_hash = compute_abstract_hash(abstract_text)
    study_design = find_study_design(abstract_text)
    participant_count = find_participant_count(abstract_text)

    return AbstractExtraction(
        pmid=pmid,
        abstract_text=abstract_text,
        abstract_hash=abstract_hash,
        study_design=study_design,
        participant_count=participant_count,
        extraction_method="model",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


def validate_extraction_spans(extraction: AbstractExtraction) -> list[str]:
    """
    Validate that all evidence spans actually exist in the abstract.
    Returns list of errors, or empty list if all valid.
    """
    errors = []

    # Check study design span
    if extraction.study_design.evidence_span is not None:
        if not extraction.study_design.evidence_span.verify_in_text(extraction.abstract_text):
            errors.append(f"Study design span does not exist in abstract: '{extraction.study_design.evidence_span.text}'")

    # Check participant count span
    if extraction.participant_count.evidence_span is not None:
        if not extraction.participant_count.evidence_span.verify_in_text(extraction.abstract_text):
            errors.append(f"Participant count span does not exist in abstract: '{extraction.participant_count.evidence_span.text}'")

    return errors

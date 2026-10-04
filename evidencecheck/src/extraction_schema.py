"""
Extraction schema for medical study abstracts.

Pydantic models define what we extract and validate it structure.
Every extracted value must cite an exact evidence span from the abstract.
Missing and ambiguous cases remain explicit.
"""

from enum import Enum
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator


class StudyDesignEnum(str, Enum):
    """Controlled vocabulary for study design types."""
    RANDOMIZED_TRIAL = "randomized_trial"
    OTHER_INTERVENTIONAL = "other_interventional"
    OBSERVATIONAL = "observational"
    REVIEW = "review"
    PROTOCOL = "protocol"
    OTHER = "other"
    NOT_REPORTED = "not_reported"


class ParticipantCountStatus(str, Enum):
    """Status of participant count extraction."""
    REPORTED = "reported"
    NOT_REPORTED = "not_reported"
    AMBIGUOUS = "ambiguous"
    NOT_APPLICABLE = "not_applicable"


class EvidenceSpan(BaseModel):
    """An exact text span from the abstract supporting an extraction."""

    text: str = Field(..., description="Exact quoted text from the abstract")
    start_char: int = Field(..., description="Starting character position in abstract")
    end_char: int = Field(..., description="Ending character position (exclusive)")

    @validator("end_char")
    def end_after_start(cls, v, values):
        if "start_char" in values and v <= values["start_char"]:
            raise ValueError("end_char must be greater than start_char")
        return v

    def verify_in_text(self, abstract_text: str) -> bool:
        """Check that this span actually exists in the abstract."""
        return abstract_text[self.start_char : self.end_char] == self.text


class StudyDesignExtraction(BaseModel):
    """Extracted study design with evidence."""

    design: StudyDesignEnum = Field(
        ...,
        description="Study design category"
    )
    evidence_span: Optional[EvidenceSpan] = Field(
        None,
        description="Text span supporting the design category. None if not_reported."
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Model confidence (0.0-1.0). Always 1.0 for deterministic extraction."
    )

    def is_valid(self, abstract_text: str) -> bool:
        """Validate that evidence span exists if reported."""
        if self.design == StudyDesignEnum.NOT_REPORTED:
            return self.evidence_span is None
        if self.evidence_span is None:
            return False
        return self.evidence_span.verify_in_text(abstract_text)


class ParticipantCountExtraction(BaseModel):
    """Extracted participant count with evidence and status.

    Rules:
    - Use only explicitly reported total for completed primary human study
    - Do NOT silently substitute: screened, per-arm, planned, analyzed, animal, review-level counts
    - Ambiguity remains visible; never filled silently
    """

    count: Optional[int] = Field(
        None,
        ge=0,
        description="Total human participants in completed study, or None if not reported/ambiguous"
    )
    status: ParticipantCountStatus = Field(
        ...,
        description="Whether count was explicitly reported, ambiguous, not reported, or not applicable"
    )
    evidence_span: Optional[EvidenceSpan] = Field(
        None,
        description="Text span supporting the count. Required if status is 'reported'."
    )
    notes: Optional[str] = Field(
        None,
        description="Explanation for ambiguous/not_applicable status"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Model confidence (0.0-1.0)"
    )

    @validator("evidence_span")
    def evidence_required_if_reported(cls, v, values):
        if "status" in values and values["status"] == ParticipantCountStatus.REPORTED:
            if v is None:
                raise ValueError("evidence_span required when status is 'reported'")
        return v

    @validator("count")
    def count_required_if_reported(cls, v, values):
        if "status" in values and values["status"] == ParticipantCountStatus.REPORTED:
            if v is None:
                raise ValueError("count must be set when status is 'reported'")
        return v

    def is_valid(self, abstract_text: str) -> bool:
        """Validate extraction consistency."""
        if self.status == ParticipantCountStatus.REPORTED:
            if self.count is None or self.evidence_span is None:
                return False
            return self.evidence_span.verify_in_text(abstract_text)
        else:
            if self.status == ParticipantCountStatus.NOT_APPLICABLE:
                return self.count is None and self.evidence_span is None
            return True


class AbstractExtraction(BaseModel):
    """Complete extraction from an abstract."""

    pmid: str = Field(..., description="PubMed ID")
    abstract_text: str = Field(..., description="Full abstract text")
    abstract_hash: str = Field(..., description="SHA256 hash of abstract for deduplication")

    study_design: StudyDesignExtraction
    participant_count: ParticipantCountExtraction

    extraction_method: Literal["human", "model", "synthetic"] = Field(
        default="model",
        description="Source of extraction: human annotation, model prediction, or synthetic fixture"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp of extraction")

    def validate_all(self) -> list[str]:
        """Return list of validation errors, or empty if valid."""
        errors = []

        if not self.study_design.is_valid(self.abstract_text):
            errors.append("study_design: invalid evidence span or missing required span")

        if not self.participant_count.is_valid(self.abstract_text):
            errors.append("participant_count: invalid evidence span, missing count/status, or inconsistency")

        return errors


class ExtractionComparison(BaseModel):
    """Compare the same extraction under different review gates."""

    pmid: str
    abstract_text: str

    # Extraction before any review
    initial_extraction: AbstractExtraction

    # Human reference labels (for evaluation)
    human_study_design: Optional[StudyDesignEnum] = None
    human_participant_count: Optional[int] = None
    human_notes: Optional[str] = None
    human_annotator: Optional[str] = None
    human_annotation_timestamp: Optional[str] = None

    # Review gate outcomes
    gate_no_review: dict = Field(
        default_factory=dict,
        description="Extraction with no review (baseline)"
    )
    gate_deterministic: dict = Field(
        default_factory=dict,
        description="Extraction after deterministic checks"
    )
    gate_jev: dict = Field(
        default_factory=dict,
        description="Extraction after Jev review (if applicable)"
    )

    def design_accuracy(self, gate: Literal["no_review", "deterministic", "jev"]) -> Optional[bool]:
        """Check if extracted design matches human label."""
        if self.human_study_design is None:
            return None
        gate_data = getattr(self, f"gate_{gate}", {})
        extracted = gate_data.get("study_design", {}).get("design")
        return extracted == self.human_study_design.value if extracted else None

    def count_accuracy(self, gate: Literal["no_review", "deterministic", "jev"]) -> Optional[bool]:
        """Check if extracted count matches human label."""
        if self.human_participant_count is None:
            return None
        gate_data = getattr(self, f"gate_{gate}", {})
        extracted = gate_data.get("participant_count", {}).get("count")
        return extracted == self.human_participant_count if extracted else None

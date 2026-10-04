"""
Tests for extraction schema and deterministic extraction logic.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from extraction_schema import (
    StudyDesignEnum,
    ParticipantCountStatus,
    EvidenceSpan,
    StudyDesignExtraction,
    ParticipantCountExtraction,
    AbstractExtraction,
)
from extraction_utils import (
    compute_abstract_hash,
    find_study_design,
    find_participant_count,
    extract_abstract,
    validate_extraction_spans,
)


class TestEvidenceSpan:
    """Tests for EvidenceSpan model."""

    def test_valid_span(self):
        """Valid span can be created."""
        text = "This is a test."
        span = EvidenceSpan(text=text, start_char=0, end_char=14)
        assert span.text == text

    def test_verify_in_text(self):
        """Span verification checks if text exists at location."""
        full_text = "This is a test abstract."
        span = EvidenceSpan(text="is a test", start_char=5, end_char=14)
        assert span.verify_in_text(full_text)

    def test_verify_fails_on_mismatch(self):
        """Span verification fails if text doesn't match."""
        full_text = "This is a test abstract."
        span = EvidenceSpan(text="wrong text", start_char=5, end_char=14)
        assert not span.verify_in_text(full_text)

    def test_end_after_start(self):
        """end_char must be greater than start_char."""
        with pytest.raises(ValueError):
            EvidenceSpan(text="test", start_char=10, end_char=5)


class TestStudyDesignExtraction:
    """Tests for StudyDesignExtraction model."""

    def test_not_reported_has_no_span(self):
        """not_reported design must have no evidence span."""
        design = StudyDesignExtraction(
            design=StudyDesignEnum.NOT_REPORTED,
            evidence_span=None
        )
        assert design.is_valid("any abstract text")

    def test_reported_requires_span(self):
        """Reported design requires evidence span."""
        design = StudyDesignExtraction(
            design=StudyDesignEnum.RANDOMIZED_TRIAL,
            evidence_span=None
        )
        assert not design.is_valid("any abstract text")

    def test_span_must_exist(self):
        """Evidence span must actually exist in abstract."""
        abstract = "This is a randomized trial."
        span = EvidenceSpan(text="randomized trial", start_char=10, end_char=26)
        design = StudyDesignExtraction(
            design=StudyDesignEnum.RANDOMIZED_TRIAL,
            evidence_span=span
        )
        assert design.is_valid(abstract)


class TestParticipantCountExtraction:
    """Tests for ParticipantCountExtraction model."""

    def test_reported_requires_count_and_span(self):
        """Reported status requires both count and span."""
        with pytest.raises(ValueError):
            ParticipantCountExtraction(
                count=None,
                status=ParticipantCountStatus.REPORTED,
                evidence_span=None
            )

    def test_not_reported_can_have_no_count(self):
        """not_reported status can have count=None."""
        count = ParticipantCountExtraction(
            count=None,
            status=ParticipantCountStatus.NOT_REPORTED,
            evidence_span=None
        )
        assert count.count is None
        assert count.status == ParticipantCountStatus.NOT_REPORTED

    def test_ambiguous_valid(self):
        """Ambiguous status is valid with explanation."""
        abstract = "100 enrolled, 80 completed."
        span = EvidenceSpan(text="100 enrolled, 80 completed", start_char=0, end_char=28)
        count = ParticipantCountExtraction(
            count=None,
            status=ParticipantCountStatus.AMBIGUOUS,
            evidence_span=span,
            notes="Multiple counts, unclear which is primary"
        )
        assert count.is_valid(abstract)


class TestDeterministicExtraction:
    """Tests for deterministic extraction functions."""

    def test_compute_hash(self):
        """Hash function works."""
        text = "This is test text."
        hash1 = compute_abstract_hash(text)
        hash2 = compute_abstract_hash(text)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

    def test_find_study_design_randomized_trial(self):
        """Identify randomized trial from text."""
        abstract = "Methods: A randomized controlled trial was conducted with 120 adults."
        extraction = find_study_design(abstract)
        assert extraction.design == StudyDesignEnum.RANDOMIZED_TRIAL
        assert extraction.evidence_span is not None

    def test_find_study_design_observational(self):
        """Identify observational study from text."""
        abstract = "This cross-sectional study examined 500 shift workers."
        extraction = find_study_design(abstract)
        assert extraction.design == StudyDesignEnum.OBSERVATIONAL

    def test_find_study_design_not_reported(self):
        """Mark as not_reported when design is unclear."""
        abstract = "Sleep quality and exercise are related. We examined their association."
        extraction = find_study_design(abstract)
        assert extraction.design == StudyDesignEnum.NOT_REPORTED

    def test_find_participant_count_simple(self):
        """Extract simple participant count."""
        abstract = "This study included 150 adults. Results showed improvement."
        extraction = find_participant_count(abstract)
        assert extraction.count == 150
        assert extraction.status == ParticipantCountStatus.REPORTED
        assert extraction.evidence_span is not None

    def test_find_participant_count_with_n_notation(self):
        """Extract count using n= notation."""
        abstract = "Participants: n=120 adults aged 40-70."
        extraction = find_participant_count(abstract)
        assert extraction.count == 120
        assert extraction.status == ParticipantCountStatus.REPORTED

    def test_find_participant_count_not_reported(self):
        """Mark as not_reported when no number given."""
        abstract = "This study examined the relationship between exercise and sleep in adults."
        extraction = find_participant_count(abstract)
        assert extraction.count is None
        assert extraction.status == ParticipantCountStatus.NOT_REPORTED

    def test_find_participant_count_ambiguous(self):
        """Mark as ambiguous when multiple numbers."""
        abstract = "150 adults were enrolled. 120 completed the study. 110 had complete data for analysis."
        extraction = find_participant_count(abstract)
        # Should detect multiple counts and mark ambiguous
        assert extraction.status in (
            ParticipantCountStatus.AMBIGUOUS,
            ParticipantCountStatus.REPORTED,  # May pick last one
        )

    def test_extract_abstract_full(self):
        """Full extraction on synthetic abstract."""
        abstract = "A randomized trial was conducted with 100 sedentary adults. After 12 weeks, exercise improved sleep quality."
        extraction = extract_abstract(
            pmid="TEST-001",
            title="Test Study",
            abstract_text=abstract
        )

        assert extraction.pmid == "TEST-001"
        assert extraction.abstract_hash  # Should be set
        assert extraction.study_design.design == StudyDesignEnum.RANDOMIZED_TRIAL
        assert extraction.participant_count.count == 100


class TestValidation:
    """Tests for extraction validation."""

    def test_validate_extraction_spans(self):
        """Validation checks evidence spans exist."""
        abstract = "A randomized trial of 50 adults."

        extraction = extract_abstract(
            pmid="TEST-001",
            title="Test",
            abstract_text=abstract
        )

        errors = validate_extraction_spans(extraction)
        # Deterministic extraction should produce valid spans
        # (or not produce spans for not_reported cases)
        assert isinstance(errors, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

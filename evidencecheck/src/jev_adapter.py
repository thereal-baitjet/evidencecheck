"""
Jev Adapter: Interface to TypeSafe Jev for extraction review.

This adapter handles both mock (offline demo) and real (live) implementations.
Switches based on TYPESAFE_API_KEY environment variable.
"""

import os
import json
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
from extraction_schema import (
    AbstractExtraction,
    StudyDesignEnum,
)


@dataclass
class JevReviewResult:
    """Result from Jev review of an extraction."""
    question_id: str
    confidence: float  # 0.0-1.0, probability of yes
    flagged: bool  # True if confidence below threshold
    threshold: float
    is_mock: bool  # True if using mock adapter

    def __repr__(self) -> str:
        mode = "mock" if self.is_mock else "live"
        flag_text = " [FLAGGED]" if self.flagged else ""
        return f"JevReview({self.question_id}, conf={self.confidence:.2f}{flag_text}, {mode})"


class JevAdapterBase:
    """Base interface for Jev adaptation."""

    def __init__(self, confidence_threshold: float = 0.75):
        self.confidence_threshold = confidence_threshold

    def review_study_design(
        self,
        extraction: AbstractExtraction,
    ) -> JevReviewResult:
        """Ask: Does the abstract support the extracted study design?"""
        raise NotImplementedError

    def review_participant_count(
        self,
        extraction: AbstractExtraction,
    ) -> JevReviewResult:
        """Ask: Does the abstract support the extracted participant count?"""
        raise NotImplementedError

    def is_live(self) -> bool:
        """Return True if using live API, False if mock."""
        raise NotImplementedError


class JevMockAdapter(JevAdapterBase):
    """Mock adapter for offline demo. Returns synthetic confidence scores."""

    def __init__(self, confidence_threshold: float = 0.75):
        super().__init__(confidence_threshold)
        self.call_count = 0

    def _mock_confidence(self, extraction: AbstractExtraction, field: str) -> float:
        """
        Synthetic confidence based on extraction characteristics.

        Heuristics:
        - High confidence if status is "reported" and evidence span exists
        - Low confidence if status is "ambiguous" or "not_reported"
        - Medium confidence for edge cases
        """
        if field == "study_design":
            if extraction.study_design.design == StudyDesignEnum.NOT_REPORTED:
                return 0.3
            if extraction.study_design.evidence_span is None:
                return 0.4
            return 0.85

        elif field == "participant_count":
            if extraction.participant_count.status.value == "reported":
                if extraction.participant_count.evidence_span is not None:
                    return 0.88
                return 0.6
            elif extraction.participant_count.status.value == "ambiguous":
                return 0.45
            elif extraction.participant_count.status.value == "not_applicable":
                return 0.95
            else:  # not_reported
                return 0.5

        return 0.5

    def review_study_design(self, extraction: AbstractExtraction) -> JevReviewResult:
        self.call_count += 1
        confidence = self._mock_confidence(extraction, "study_design")

        return JevReviewResult(
            question_id="design_supported",
            confidence=confidence,
            flagged=confidence < self.confidence_threshold,
            threshold=self.confidence_threshold,
            is_mock=True
        )

    def review_participant_count(self, extraction: AbstractExtraction) -> JevReviewResult:
        self.call_count += 1
        confidence = self._mock_confidence(extraction, "participant_count")

        return JevReviewResult(
            question_id="count_supported",
            confidence=confidence,
            flagged=confidence < self.confidence_threshold,
            threshold=self.confidence_threshold,
            is_mock=True
        )

    def is_live(self) -> bool:
        return False


class JevLiveAdapter(JevAdapterBase):
    """Live adapter using TypeSafe API. Requires TYPESAFE_API_KEY."""

    def __init__(
        self,
        api_key: str,
        confidence_threshold: float = 0.75,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        super().__init__(confidence_threshold)
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.call_count = 0
        self.base_url = "https://api.typesafe.ai/v1/systemone"

        # Try importing TypeSafe SDK
        try:
            import typesafe
            self.typesafe = typesafe
            self.sdk_available = True
        except ImportError:
            self.sdk_available = False
            print("Warning: typesafe-sdk not installed. Install with: pip install -r requirements-live.txt")

    def review_study_design(self, extraction: AbstractExtraction) -> JevReviewResult:
        """Ask Jev: Does this abstract support the extracted study design?"""
        if not self.sdk_available:
            raise RuntimeError("TypeSafe SDK not available. Install with: pip install -r requirements-live.txt")

        self.call_count += 1

        question_text = f"""The abstract describes a study with design: {extraction.study_design.design.value}.

Abstract: {extraction.abstract_text[:500]}...

Does the abstract clearly support this study design classification? Look for explicit methodological language (randomization, observational approach, etc.) that matches the assigned design."""

        confidence = self._call_jev(
            state=extraction.abstract_text,
            question_id="design_supported",
            instructions=question_text
        )

        return JevReviewResult(
            question_id="design_supported",
            confidence=confidence,
            flagged=confidence < self.confidence_threshold,
            threshold=self.confidence_threshold,
            is_mock=False
        )

    def review_participant_count(self, extraction: AbstractExtraction) -> JevReviewResult:
        """Ask Jev: Does this abstract support the extracted participant count?"""
        if not self.sdk_available:
            raise RuntimeError("TypeSafe SDK not available. Install with: pip install -r requirements-live.txt")

        self.call_count += 1

        count_info = extraction.participant_count.count or "not reported"
        question_text = f"""The extraction identified {count_info} total participants.

Abstract: {extraction.abstract_text[:500]}...

Does the abstract explicitly state the total number of human participants who completed the primary study? (Do not count screened, per-arm, planned, or analyzed-only counts.)"""

        confidence = self._call_jev(
            state=extraction.abstract_text,
            question_id="count_supported",
            instructions=question_text
        )

        return JevReviewResult(
            question_id="count_supported",
            confidence=confidence,
            flagged=confidence < self.confidence_threshold,
            threshold=self.confidence_threshold,
            is_mock=False
        )

    def _call_jev(self, state: str, question_id: str, instructions: str) -> float:
        """Make a real Jev API call and extract confidence."""
        request_body = {
            "state": state,
            "model": "jev-latest",
            "questions": {
                question_id: {
                    "type": "noul",
                    "instructions": instructions
                }
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for attempt in range(self.max_retries):
            try:
                import requests
                response = requests.post(
                    self.base_url,
                    json=request_body,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()

                result = response.json()
                # Extract confidence from Noul response (probability of yes)
                confidence = result["answers"][question_id]["answer"]
                return float(confidence)

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"Jev API error (attempt {attempt + 1}/{self.max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"Jev API failed after {self.max_retries} attempts: {e}")
                    raise

    def is_live(self) -> bool:
        return True


def get_jev_adapter(
    confidence_threshold: float = 0.75,
    force_mock: bool = False
) -> JevAdapterBase:
    """
    Factory function to create the appropriate Jev adapter.

    Returns:
    - JevLiveAdapter if TYPESAFE_API_KEY is set and force_mock=False
    - JevMockAdapter otherwise
    """
    api_key = os.getenv("TYPESAFE_API_KEY")

    if api_key and not force_mock:
        print(f"Initializing live Jev adapter (confidence_threshold={confidence_threshold})")
        return JevLiveAdapter(api_key, confidence_threshold)
    else:
        print(f"Initializing mock Jev adapter (confidence_threshold={confidence_threshold})")
        return JevMockAdapter(confidence_threshold)

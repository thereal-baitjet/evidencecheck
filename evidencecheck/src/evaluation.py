"""
Evaluation logic: Compare extractions under three review gates.

Gate 1: No review (baseline)
Gate 2: Deterministic checks (schema validation + evidence span verification)
Gate 3: Deterministic + Jev review (flags uncertain items)
"""

import json
from typing import Optional, Dict, Any, List
from dataclasses import asdict
from extraction_schema import (
    AbstractExtraction,
    ExtractionComparison,
    StudyDesignEnum,
    ParticipantCountStatus,
)
from jev_adapter import JevAdapterBase, JevReviewResult


class EvaluationGate:
    """Logic for applying a review gate to an extraction."""

    @staticmethod
    def gate_no_review(extraction: AbstractExtraction) -> Dict[str, Any]:
        """Gate 1: No review. Return extraction as-is."""
        return {
            "study_design": {
                "design": extraction.study_design.design.value,
                "confidence": extraction.study_design.confidence,
                "evidence_span": extraction.study_design.evidence_span.text
                    if extraction.study_design.evidence_span else None,
            },
            "participant_count": {
                "count": extraction.participant_count.count,
                "status": extraction.participant_count.status.value,
                "evidence_span": extraction.participant_count.evidence_span.text
                    if extraction.participant_count.evidence_span else None,
            },
            "flagged": False,
            "review_reason": None,
        }

    @staticmethod
    def gate_deterministic(extraction: AbstractExtraction) -> Dict[str, Any]:
        """
        Gate 2: Deterministic checks.
        Validate schema consistency and evidence span existence.
        Flags if validation fails.
        """
        errors = extraction.validate_all()

        result = {
            "study_design": {
                "design": extraction.study_design.design.value,
                "confidence": extraction.study_design.confidence,
                "evidence_span": extraction.study_design.evidence_span.text
                    if extraction.study_design.evidence_span else None,
            },
            "participant_count": {
                "count": extraction.participant_count.count,
                "status": extraction.participant_count.status.value,
                "evidence_span": extraction.participant_count.evidence_span.text
                    if extraction.participant_count.evidence_span else None,
            },
            "flagged": len(errors) > 0,
            "review_reason": "; ".join(errors) if errors else None,
        }

        return result

    @staticmethod
    def gate_jev(
        extraction: AbstractExtraction,
        jev_adapter: Optional[JevAdapterBase] = None,
        skip_unflagged: bool = True,
    ) -> Dict[str, Any]:
        """
        Gate 3: Deterministic + Jev review.

        Process:
        1. Apply deterministic gate
        2. If not flagged, optionally skip Jev (faster)
        3. If flagged or skip_unflagged=False, ask Jev
        4. Flag if Jev confidence is low
        """
        if jev_adapter is None:
            raise ValueError("jev_adapter required for Jev gate")

        # First, deterministic gate
        det_result = EvaluationGate.gate_deterministic(extraction)

        # Decide whether to ask Jev
        ask_jev = not skip_unflagged or det_result["flagged"]

        jev_results = {}
        final_flagged = det_result["flagged"]
        final_reasons = [det_result["review_reason"]] if det_result["review_reason"] else []

        if ask_jev:
            # Ask Jev about both fields
            try:
                design_review = jev_adapter.review_study_design(extraction)
                jev_results["design"] = {
                    "confidence": design_review.confidence,
                    "flagged": design_review.flagged,
                    "threshold": design_review.threshold,
                }
                if design_review.flagged:
                    final_flagged = True
                    final_reasons.append(f"Study design confidence too low: {design_review.confidence:.2f}")
            except Exception as e:
                final_flagged = True
                final_reasons.append(f"Jev design review failed: {str(e)}")

            try:
                count_review = jev_adapter.review_participant_count(extraction)
                jev_results["count"] = {
                    "confidence": count_review.confidence,
                    "flagged": count_review.flagged,
                    "threshold": count_review.threshold,
                }
                if count_review.flagged:
                    final_flagged = True
                    final_reasons.append(f"Participant count confidence too low: {count_review.confidence:.2f}")
            except Exception as e:
                final_flagged = True
                final_reasons.append(f"Jev count review failed: {str(e)}")

        result = {
            "study_design": det_result["study_design"],
            "participant_count": det_result["participant_count"],
            "flagged": final_flagged,
            "review_reason": "; ".join(final_reasons) if final_reasons else None,
            "jev_results": jev_results,
            "jev_called": ask_jev,
            "jev_adapter": jev_adapter.__class__.__name__ if jev_adapter else None,
        }

        return result


class EvaluationMetrics:
    """Calculate evaluation metrics from comparison results."""

    @staticmethod
    def study_design_accuracy(
        comparisons: List[ExtractionComparison],
        gate: str,
    ) -> Dict[str, Any]:
        """
        Calculate study design accuracy for a gate.

        Metrics:
        - accuracy: fraction correct (where human label exists)
        - coverage: fraction with human labels
        - counts: {correct, incorrect, unlabeled}
        """
        if not comparisons:
            return {"accuracy": None, "coverage": None, "counts": {}}

        correct = 0
        incorrect = 0
        unlabeled = 0

        for comp in comparisons:
            if comp.human_study_design is None:
                unlabeled += 1
                continue

            acc = comp.design_accuracy(gate)
            if acc is True:
                correct += 1
            elif acc is False:
                incorrect += 1
            else:
                unlabeled += 1

        total_labeled = correct + incorrect
        accuracy = correct / total_labeled if total_labeled > 0 else None
        coverage = total_labeled / len(comparisons) if comparisons else None

        return {
            "accuracy": accuracy,
            "coverage": coverage,
            "counts": {
                "correct": correct,
                "incorrect": incorrect,
                "unlabeled": unlabeled,
            }
        }

    @staticmethod
    def participant_count_accuracy(
        comparisons: List[ExtractionComparison],
        gate: str,
    ) -> Dict[str, Any]:
        """Calculate participant count accuracy for a gate."""
        if not comparisons:
            return {"accuracy": None, "coverage": None, "counts": {}}

        correct = 0
        incorrect = 0
        unlabeled = 0

        for comp in comparisons:
            if comp.human_participant_count is None:
                unlabeled += 1
                continue

            acc = comp.count_accuracy(gate)
            if acc is True:
                correct += 1
            elif acc is False:
                incorrect += 1
            else:
                unlabeled += 1

        total_labeled = correct + incorrect
        accuracy = correct / total_labeled if total_labeled > 0 else None
        coverage = total_labeled / len(comparisons) if comparisons else None

        return {
            "accuracy": accuracy,
            "coverage": coverage,
            "counts": {
                "correct": correct,
                "incorrect": incorrect,
                "unlabeled": unlabeled,
            }
        }

    @staticmethod
    def review_rate(comparisons: List[ExtractionComparison], gate: str) -> float:
        """Fraction of extractions flagged for review under this gate."""
        if not comparisons:
            return 0.0

        flagged = sum(
            1 for comp in comparisons
            if comp.__dict__.get(f"gate_{gate}", {}).get("flagged", False)
        )
        return flagged / len(comparisons)

    @staticmethod
    def gate_error_rates(
        comparisons: List[ExtractionComparison],
        gate: str,
    ) -> Dict[str, Any]:
        """
        Calculate error rates by gate.

        - unflagged_error_rate: errors that gate did NOT catch (worst case)
        - flagged_correct_rate: correctly flagged items that are actually correct (false positive)
        """
        unflagged_errors = 0
        flagged_correct = 0
        unflagged_total = 0
        flagged_total = 0

        for comp in comparisons:
            gate_data = comp.__dict__.get(f"gate_{gate}", {})
            flagged = gate_data.get("flagged", False)

            # Check design accuracy
            design_acc = comp.design_accuracy(gate)
            if design_acc is not None:
                if flagged:
                    flagged_total += 1
                    if design_acc:  # Extraction is correct but flagged
                        flagged_correct += 1
                else:
                    unflagged_total += 1
                    if not design_acc:  # Error that wasn't caught
                        unflagged_errors += 1

        unflagged_error_rate = unflagged_errors / unflagged_total if unflagged_total > 0 else None
        flagged_false_positive_rate = flagged_correct / flagged_total if flagged_total > 0 else None

        return {
            "unflagged_error_rate": unflagged_error_rate,
            "flagged_false_positive_rate": flagged_false_positive_rate,
            "counts": {
                "unflagged_errors": unflagged_errors,
                "flagged_correct": flagged_correct,
            }
        }

    @staticmethod
    def summary_report(comparisons: List[ExtractionComparison]) -> Dict[str, Any]:
        """Generate a comprehensive evaluation summary."""
        return {
            "total_abstracts": len(comparisons),
            "gates": {
                "no_review": {
                    "design": EvaluationMetrics.study_design_accuracy(comparisons, "no_review"),
                    "count": EvaluationMetrics.participant_count_accuracy(comparisons, "no_review"),
                    "review_rate": EvaluationMetrics.review_rate(comparisons, "no_review"),
                    "errors": EvaluationMetrics.gate_error_rates(comparisons, "no_review"),
                },
                "deterministic": {
                    "design": EvaluationMetrics.study_design_accuracy(comparisons, "deterministic"),
                    "count": EvaluationMetrics.participant_count_accuracy(comparisons, "deterministic"),
                    "review_rate": EvaluationMetrics.review_rate(comparisons, "deterministic"),
                    "errors": EvaluationMetrics.gate_error_rates(comparisons, "deterministic"),
                },
                "jev": {
                    "design": EvaluationMetrics.study_design_accuracy(comparisons, "jev"),
                    "count": EvaluationMetrics.participant_count_accuracy(comparisons, "jev"),
                    "review_rate": EvaluationMetrics.review_rate(comparisons, "jev"),
                    "errors": EvaluationMetrics.gate_error_rates(comparisons, "jev"),
                },
            }
        }

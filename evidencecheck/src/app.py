"""
EvidenceCheck: Research portfolio for evaluating AI extraction accuracy on medical abstracts.

Streamlit app with corpus view, annotation interface, and evaluation dashboard.
"""

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from extraction_schema import (
    AbstractExtraction,
    ExtractionComparison,
    StudyDesignEnum,
    ParticipantCountStatus,
)
from extraction_utils import extract_abstract, validate_extraction_spans
from evaluation import EvaluationGate, EvaluationMetrics
from jev_adapter import get_jev_adapter


# Streamlit configuration
st.set_page_config(
    page_title="EvidenceCheck",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📋 EvidenceCheck")
st.markdown("Research portfolio evaluating AI extraction accuracy on medical abstracts.")


# ============================================================================
# Sidebar Configuration
# ============================================================================

st.sidebar.header("Configuration")

# Load synthetic fixtures or real corpus
corpus_path = Path(__file__).parent.parent / "data" / "fixtures" / "synthetic_abstracts.jsonl"

demo_mode = st.sidebar.checkbox(
    "📊 Demo Mode (Synthetic Abstracts)",
    value=True,
    help="Use synthetic abstracts for offline demo. Uncheck to load real corpus (if available)."
)

# Jev configuration
jev_enabled = st.sidebar.checkbox(
    "🤖 Enable Live Jev Review",
    value=False,
    help="Use live TypeSafe Jev API (requires TYPESAFE_API_KEY)"
)

jev_confidence_threshold = st.sidebar.slider(
    "Jev Confidence Threshold",
    min_value=0.0,
    max_value=1.0,
    value=0.75,
    step=0.05,
    help="Jev flags extractions with confidence below this threshold"
)

force_mock = not jev_enabled or not os.getenv("TYPESAFE_API_KEY")


# ============================================================================
# Load Corpus
# ============================================================================

@st.cache_resource
def load_corpus():
    """Load abstracts from fixture or corpus."""
    abstracts = []

    if demo_mode and corpus_path.exists():
        with open(corpus_path) as f:
            for line in f:
                data = json.loads(line.strip())
                abstracts.append(data)

    if not abstracts:
        st.warning("No corpus found. Using empty corpus.")

    return abstracts


corpus = load_corpus()
st.sidebar.info(f"Loaded {len(corpus)} abstracts")


# ============================================================================
# Initialize Session State
# ============================================================================

if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0

if "annotations" not in st.session_state:
    st.session_state.annotations = {}

if "comparisons" not in st.session_state:
    st.session_state.comparisons = {}

if "jev_adapter" not in st.session_state:
    st.session_state.jev_adapter = get_jev_adapter(
        confidence_threshold=jev_confidence_threshold,
        force_mock=force_mock
    )


# ============================================================================
# Navigation and Display Logic
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(
    ["📚 Corpus", "📝 Annotate", "🔍 Compare", "📊 Dashboard"]
)


# ============================================================================
# Tab 1: Corpus View
# ============================================================================

with tab1:
    st.header("Abstract Corpus")

    if not corpus:
        st.error("No abstracts loaded.")
    else:
        col1, col2 = st.columns([1, 4])

        with col1:
            st.session_state.current_idx = st.selectbox(
                "Select Abstract",
                range(len(corpus)),
                format_func=lambda i: f"{i+1}. {corpus[i].get('pmid', 'Unknown')}"
            )

        abstract_data = corpus[st.session_state.current_idx]

        with col2:
            st.subheader(abstract_data.get("title", "Untitled"))
            st.caption(f"PMID: {abstract_data['pmid']}")

        st.markdown("---")
        st.write(abstract_data.get("abstract", "No abstract text"))

        # Show extraction for this abstract
        if abstract_data["pmid"] not in st.session_state.comparisons:
            extraction = extract_abstract(
                pmid=abstract_data["pmid"],
                title=abstract_data.get("title", ""),
                abstract_text=abstract_data.get("abstract", "")
            )

            # Validate spans
            errors = validate_extraction_spans(extraction)
            if errors:
                st.warning(f"⚠️ Extraction validation errors: {errors}")

            # Apply gates
            gate_no_review = EvaluationGate.gate_no_review(extraction)
            gate_deterministic = EvaluationGate.gate_deterministic(extraction)

            comparison = ExtractionComparison(
                pmid=abstract_data["pmid"],
                abstract_text=abstract_data.get("abstract", ""),
                initial_extraction=extraction,
                gate_no_review=gate_no_review,
                gate_deterministic=gate_deterministic,
                gate_jev={},
            )

            st.session_state.comparisons[abstract_data["pmid"]] = comparison

        comparison = st.session_state.comparisons[abstract_data["pmid"]]

        # Display extraction results
        st.subheader("Extraction Results")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Study Design:**")
            st.code(comparison.initial_extraction.study_design.design.value)
            if comparison.initial_extraction.study_design.evidence_span:
                st.caption(f"Evidence: \"{comparison.initial_extraction.study_design.evidence_span.text}\"")

        with col2:
            st.write("**Participant Count:**")
            count = comparison.initial_extraction.participant_count.count or "Not reported"
            st.code(f"{count} ({comparison.initial_extraction.participant_count.status.value})")
            if comparison.initial_extraction.participant_count.evidence_span:
                st.caption(f"Evidence: \"{comparison.initial_extraction.participant_count.evidence_span.text}\"")


# ============================================================================
# Tab 2: Annotation
# ============================================================================

with tab2:
    st.header("Human Annotation")
    st.markdown("Provide reference labels for evaluation.")

    if not corpus:
        st.error("No abstracts loaded.")
    else:
        abstract_data = corpus[st.session_state.current_idx]
        pmid = abstract_data["pmid"]

        st.subheader(f"PMID: {pmid}")
        st.write(abstract_data.get("title", ""))

        col1, col2 = st.columns(2)

        with col1:
            human_design = st.selectbox(
                "Study Design (Reference Label)",
                options=[d.value for d in StudyDesignEnum],
                key=f"design_{pmid}"
            )

        with col2:
            human_count = st.number_input(
                "Participant Count (Reference Label)",
                min_value=0,
                value=None,
                key=f"count_{pmid}",
                help="Enter the total human participant count, or leave blank if not reported."
            )

        if st.button("Save Annotation"):
            comparison = st.session_state.comparisons[pmid]
            comparison.human_study_design = StudyDesignEnum(human_design)
            comparison.human_participant_count = human_count
            comparison.human_annotator = "user"
            comparison.human_annotation_timestamp = datetime.utcnow().isoformat() + "Z"

            st.success(f"✅ Saved annotation for {pmid}")


# ============================================================================
# Tab 3: Comparison
# ============================================================================

with tab3:
    st.header("Gate Comparison")
    st.markdown("Compare extraction performance across three review gates.")

    if not st.session_state.comparisons:
        st.info("No extractions yet. Navigate to Corpus tab first.")
    else:
        abstract_data = corpus[st.session_state.current_idx]
        pmid = abstract_data["pmid"]
        comparison = st.session_state.comparisons[pmid]

        st.subheader(f"PMID: {pmid}")

        # Prepare Jev gate results
        if not comparison.gate_jev and jev_enabled:
            try:
                gate_jev = EvaluationGate.gate_jev(
                    comparison.initial_extraction,
                    jev_adapter=st.session_state.jev_adapter
                )
                comparison.gate_jev = gate_jev
            except Exception as e:
                st.error(f"Jev review failed: {e}")

        # Display all three gates
        gate_cols = st.columns(3)

        gates = [
            ("No Review", "gate_no_review"),
            ("Deterministic", "gate_deterministic"),
            ("Jev Review", "gate_jev")
        ]

        for col, (gate_name, gate_key) in zip(gate_cols, gates):
            with col:
                st.subheader(gate_name)

                gate_data = comparison.__dict__.get(gate_key, {})

                if not gate_data:
                    st.info("(Not yet evaluated)")
                else:
                    design = gate_data.get("study_design", {})
                    count = gate_data.get("participant_count", {})
                    flagged = gate_data.get("flagged", False)

                    if flagged:
                        st.warning(f"🚩 Flagged for review")
                        reason = gate_data.get("review_reason")
                        if reason:
                            st.caption(reason)
                    else:
                        st.success(f"✅ Passed")

                    st.markdown("**Design:**")
                    st.code(design.get("design", "N/A"))

                    st.markdown("**Count:**")
                    count_val = count.get("count") or f"({count.get('status', 'unknown')})"
                    st.code(str(count_val))


# ============================================================================
# Tab 4: Dashboard
# ============================================================================

with tab4:
    st.header("Evaluation Dashboard")
    st.markdown("Summary metrics across all abstracts.")

    if not st.session_state.comparisons:
        st.info("No evaluations yet. Annotate some abstracts first.")
    else:
        comparisons_list = list(st.session_state.comparisons.values())

        metrics = EvaluationMetrics.summary_report(comparisons_list)

        st.metric("Total Abstracts", metrics["total_abstracts"])

        st.markdown("---")

        st.subheader("Gate Comparison")

        for gate in ["no_review", "deterministic", "jev"]:
            gate_metrics = metrics["gates"][gate]

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    f"{gate.title()} — Design Accuracy",
                    f"{gate_metrics['design']['accuracy'] * 100:.1f}%" if gate_metrics['design']['accuracy'] is not None else "N/A"
                )

            with col2:
                st.metric(
                    f"{gate.title()} — Count Accuracy",
                    f"{gate_metrics['count']['accuracy'] * 100:.1f}%" if gate_metrics['count']['accuracy'] is not None else "N/A"
                )

            with col3:
                st.metric(
                    f"{gate.title()} — Review Rate",
                    f"{gate_metrics['review_rate'] * 100:.1f}%"
                )

            with col4:
                unflagged_err = gate_metrics['errors']['unflagged_error_rate']
                st.metric(
                    f"{gate.title()} — Unflagged Error Rate",
                    f"{unflagged_err * 100:.1f}%" if unflagged_err is not None else "N/A"
                )


# ============================================================================
# Footer
# ============================================================================

st.markdown("---")
st.markdown(
    """
    **EvidenceCheck** | Research portfolio for evaluating AI extraction accuracy
    Built with Streamlit, Pydantic, and TypeSafe Jev
    """
)

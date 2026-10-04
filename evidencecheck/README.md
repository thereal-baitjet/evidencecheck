# EvidenceCheck

A research portfolio project that evaluates whether AI accurately extracts facts from medical-study abstracts.

**Status**: Offline-first demonstration ready; live TypeSafe Jev integration optional (gated by API credential).

## Overview

EvidenceCheck answers: **Can a Jev review gate identify incorrect or unsupported study-design and participant-count extractions, and what fraction of papers does it send for human review?**

Using a small pilot of ~30 real PubMed abstracts about exercise and sleep in adults, the project:
1. Extracts structured facts: study design and participant count
2. Provides evidence spans (exact text citations)
3. Compares three gates: no review, deterministic checks, deterministic + Jev review
4. Reports metrics: accuracy, missingness, review rate, error types

**This is a research-methods project using published literature. It makes no diagnosis, treatment recommendation, or claim of clinical validation.**

---

## Setup

### Requirements
- macOS (tested on M4) or Linux
- Python 3.9+
- 16 GB RAM recommended

### Quick Start

```bash
# Clone or navigate to the project
cd evidencecheck

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run src/app.py
```

The app opens at `http://localhost:8501`.

### (Optional) Enable Live Jev Integration

To use live TypeSafe Jev review:

1. Obtain an API key: https://console.typesafe.ai/
2. Set the environment variable:
   ```bash
   export TYPESAFE_API_KEY="your-key-here"
   ```
3. In the app settings, enable "Live Jev Review" and set a budget limit.

The app works fully offline without this step.

---

## Architecture

### Core Components
- **Corpus View**: Browse paper metadata and abstracts
- **Annotation Screen**: Human labels for study design and participant count (hidden from model predictions until submission)
- **Extraction Schema**: Pydantic models with explicit missing/ambiguous states
- **Evidence Citation**: Every extracted value requires an exact text span from the abstract
- **Comparison Logic**: Evaluate performance under no-gate, deterministic, and Jev review conditions
- **Evaluation Dashboard**: Accuracy, coverage, review rate, error analysis
- **Exports**: CSV, JSON, Markdown results

### Jev Integration
The optional **Jev Adapter** routes uncertain extractions to TypeSafe's Jev model for review:
- Typed questions (Noul/Choice primitives)
- Configurable confidence thresholds
- Caching and budget limits
- Clear labeling of results

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** — Project setup and development guide
- **[PHASE_0_REPORT.md](PHASE_0_REPORT.md)** — Verification of TypeSafe integration and credential status
- **[docs/PROTOCOL.md](docs/PROTOCOL.md)** — Experiment design and data retrieval rules
- **[docs/ANNOTATION_GUIDE.md](docs/ANNOTATION_GUIDE.md)** — How to annotate abstracts (participant count definition)
- **[docs/DECISIONS.md](docs/DECISIONS.md)** — Architecture decisions and TypeSafe consultation records
- **[docs/GAUNTLET.md](docs/GAUNTLET.md)** — Test plan, failure cases, and verification steps
- **[reports/PILOT_REPORT.md](reports/PILOT_REPORT.md)** — Evaluation results or "pending" status

---

## Example Workflow

1. **Start the app**: `streamlit run src/app.py`
2. **Corpus View**: Browse 30 PubMed abstracts
3. **Annotation**: Label 10 development abstracts; freeze protocol
4. **Extract & Review**: Compare extraction quality under three conditions
5. **Dashboard**: View accuracy, review rates, error breakdown
6. **Export**: Download results as CSV or JSON
7. **Report**: Publish pilot findings (honest, labeled as pilot)

---

## Data Sources

- **PubMed Abstracts**: Retrieved via NCBI API
  - Query: "exercise sleep adults"
  - Results: ~30 deduplicated abstracts
  - Retrieval date and PMIDs recorded for reproducibility
  - Caching and hashing to prevent duplicate processing

- **Synthetic Fixtures**: For offline demo and testing
  - Clearly labeled as synthetic
  - Never mixed with empirical results
  - Used for end-to-end testing and feature development

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_schema.py -v

# Test with coverage
pytest tests/ --cov=src
```

Test cases cover:
- Schema validation and missing values
- Evidence span checking
- Comparison logic
- Export formats
- Label leakage prevention
- Offline demo end-to-end flow

---

## Extracting Facts

EvidenceCheck extracts two structured fields:

### Study Design
One of: `randomized_trial`, `other_interventional`, `observational`, `review`, `protocol`, `other`, `not_reported`

### Total Human Participant Count
An integer or null, with status: `reported`, `not_reported`, `ambiguous`, `not_applicable`

**Important**: For participant count, use an explicitly reported total for a completed primary human study. Do not silently substitute screened, per-arm, planned, analyzed, animal, or review-level totals. Ambiguity remains visible.

---

## Evaluation Metrics

- **Study Design Accuracy**: % correct (no-gate vs. deterministic vs. jev)
- **Participant Count Exact Match**: % correct on applicable records
- **Missingness/Ambiguity Performance**: Detection rate and false positive rate
- **Review Rate**: % of papers sent for human review
- **Error Rate (Unflagged)**: % of errors that bypass all gates
- **Coverage**: Denominator counts and exclusions

---

## Credential and Security

- **API Keys**: Stored in environment variables, never committed to git
- **.env.example**: Placeholders only; see CLAUDE.md for setup
- **No patient data**: This project uses published literature only
- **No uploads**: Abstracts are retrieved via public APIs or provided as fixtures

---

## Known Limitations

- **Pilot scale**: 30 abstracts is small and insufficient for clinical readiness
- **No clinician review**: Annotations are research/engineering judgments, not expert validation
- **TypeSafe Jev**: Confidence values are model outputs; usefulness is measured empirically on this task
- **Evaluation scope**: Study design and participant count only; does not evaluate other abstract content

---

## Next Steps

1. Install dependencies and run the offline demo
2. Review [docs/ANNOTATION_GUIDE.md](docs/ANNOTATION_GUIDE.md)
3. Annotate 10 development abstracts
4. Observe extraction comparison and review rates
5. Export results and review pilot findings

---

## Getting Started

### 1. One-Time Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Offline Demo (No API Key Needed)
```bash
export DEMO_MODE=true
streamlit run src/app.py
```
Then navigate to `http://localhost:8501` and explore the tabs.

### 3. Run Tests
```bash
pytest tests/test_extraction.py -v
```

### 4. Review the Protocol
See [docs/PROTOCOL.md](docs/PROTOCOL.md) for the research design and evaluation plan.

### 5. Check the Test Plan
See [docs/GAUNTLET.md](docs/GAUNTLET.md) for failure case testing and success criteria.

### 6. (Optional) Enable Live Jev
Requires TypeSafe API key from https://console.typesafe.ai/:
```bash
export TYPESAFE_API_KEY="your-key-here"
pip install -r requirements-live.txt
# Then in app settings, enable "Live Jev Review"
```

---

## Project Status

✅ **Phase 1**: Environment verification, schema design  
✅ **Phase 2**: Extraction logic, evaluation gates, Streamlit UI  
✅ **Phase 3**: Documentation, test plan, pilot report template  
⏳ **Phase 4**: Data collection (PubMed retrieval, annotation)  
⏳ **Phase 5**: Evaluation (run gates, calculate metrics)  
⏳ **Phase 6**: Reporting (fill PILOT_REPORT.md with actual results)  

---

## Documentation

- **[CLAUDE.md](CLAUDE.md)** — Project setup, testing, architecture
- **[PHASE_0_REPORT.md](PHASE_0_REPORT.md)** — TypeSafe integration verification
- **[docs/PROTOCOL.md](docs/PROTOCOL.md)** — Research protocol and evaluation design
- **[docs/ANNOTATION_GUIDE.md](docs/ANNOTATION_GUIDE.md)** — How to annotate abstracts
- **[docs/DECISIONS.md](docs/DECISIONS.md)** — Architecture decisions and TypeSafe patterns
- **[docs/GAUNTLET.md](docs/GAUNTLET.md)** — Test plan and failure case scenarios
- **[reports/PILOT_REPORT.md](reports/PILOT_REPORT.md)** — Evaluation results template (pending)

---

## Questions?

See [CLAUDE.md](CLAUDE.md) for implementation notes, or [docs/DECISIONS.md](docs/DECISIONS.md) for architecture rationale.

**Start**: `streamlit run src/app.py`

---

*Built with TypeSafe Jev integration (optional). Offline-first, transparent, research-methods approach.*

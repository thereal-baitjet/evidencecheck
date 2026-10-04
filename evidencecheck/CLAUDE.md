# Claude Code Project Guide: EvidenceCheck

## Context

**Owner**: Juan Santos  
**Goal**: Build a research portfolio project that evaluates whether AI extracts facts from medical-study abstracts accurately.  
**Stack**: Python + Streamlit (UI), Pydantic (schema), pandas (analysis), pytest (tests), JSON/JSONL (data)  
**Scope**: Small, runnable offline-first application with optional live TypeSafe Jev integration  

This is a research-methods project using published literature. It makes no diagnosis, treatment recommendation, or claim of clinical validation.

---

## Setup and Execution

### Environment Setup
```bash
cd evidencecheck
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the Application
```bash
streamlit run src/app.py
```

### Run Tests
```bash
pytest tests/ -v
```

### Live Jev (Optional, Requires Credential)
Set environment variable before running:
```bash
export TYPESAFE_API_KEY="<your-key-from-console.typesafe.ai>"
```
Then update config file to enable live review. Offline mode works without it.

---

## Key Files and Purposes

- **src/app.py** — Streamlit application entry point
- **src/extraction_schema.py** — Pydantic models for study design and participant count
- **src/jev_adapter.py** — TypeSafe Jev integration (mocked until credentials available)
- **src/evaluation.py** — Comparison logic and evaluation dashboard
- **docs/ANNOTATION_GUIDE.md** — How to annotate abstracts (participant count rules)
- **docs/DECISIONS.md** — Architecture and integration decisions (TypeSafe consultation records)
- **reports/PILOT_REPORT.md** — Evaluation results or explicit pending status
- **data/fixtures/** — Offline synthetic abstracts for demo
- **data/corpus/** — Real PubMed abstracts (to be retrieved via NCBI API)

---

## Design Decisions

### Offline-First, Live-Ready
- Core application runs entirely offline with synthetic data.
- Jev adapter is pluggable; no API calls until credential is configured and budget is enabled.
- Offline results are clearly labeled as such; live results labeled as "jev-reviewed".

### Evidence Spans Required
- Every extracted value must cite an exact text span from the abstract.
- Schema validation checks span existence in code.
- Missing or ambiguous cases remain explicit (not silently filled).

### Participant Count Definition
- Use explicitly reported total for completed primary human study only.
- Never silently substitute screened, per-arm, planned, analyzed, animal, or review-level counts.
- Ambiguity remains visible in the annotation guide and results.

---

## Testing Strategy

- **Unit tests**: Schema validation, evidence span checking, comparison logic
- **Integration tests**: Offline demo end-to-end flow
- **Fixtures**: Synthetic abstracts with known extraction scenarios (correct, missing, ambiguous)
- **No live API tests** until credentials are available (adapter is mocked)

---

## Data Handling

- **PubMed abstracts**: Retrieve via NCBI API, cache locally, hash for deduplication
- **Synthetic fixtures**: Clearly marked, never mixed with empirical results
- **Annotations**: Store with PMID, annotator identity, version, timestamp
- **API keys**: Never committed to git; use .env.example + environment variable only

---

## Evaluation Rigor

- **Development set**: 10 abstracts (tune prompts/thresholds here only)
- **Held-out set**: 20 abstracts (locked before prediction)
- **Human labels**: Required for credible evaluation; "pending" if unavailable
- **Reporting**: Counts, denominators, missingness rates, error types
- **Honesty**: Label pilot as small/insufficient for clinical readiness; report negative findings

---

## TypeSafe / Jev Integration Notes

- Jev is consulted for design and evaluation decisions, not for extracting free-form text.
- Runtime questions are typed (Noul/Choice/Score), with explicit unknowns.
- Jev confidence is a model output; usefulness measured on this task.
- Budget and timeout limits enforced in adapter; defaults to disabled.
- No silent model swaps; Jev results always labeled as such.

---

## When Asking Claude Code for Help

- Architectural decisions: Explain the constraint and competing options; I'll recommend one.
- Schema or evaluation design: Reference the annotation guide and research goal.
- Integration choices: Link to TypeSafe docs and ask for a narrowly scoped decision.
- Implementation: State what you're building (e.g., "Streamlit form for annotation") and I'll write or debug it.
- Testing: Describe the failure scenario; I'll write test cases and fix code.

Do not:
- Deploy or publish this project without explicit consent.
- Add cloud infrastructure, payment systems, or authentication.
- Modify the evaluation protocol without documenting the change.
- Commit API keys or private credentials.
- Claim research findings until human labels are reviewed.

---

## Repository Structure

```
evidencecheck/
├── src/
│   ├── app.py
│   ├── extraction_schema.py
│   ├── jev_adapter.py
│   ├── evaluation.py
│   └── utils.py
├── docs/
│   ├── PROTOCOL.md
│   ├── ANNOTATION_GUIDE.md
│   ├── DECISIONS.md
│   └── GAUNTLET.md
├── reports/
│   └── PILOT_REPORT.md
├── tests/
│   ├── test_schema.py
│   ├── test_evaluation.py
│   └── test_fixtures.py
├── data/
│   ├── corpus/
│   │   └── pubmed_abstracts.jsonl
│   └── fixtures/
│       └── synthetic_abstracts.jsonl
├── README.md
├── requirements.txt
├── .env.example
├── CLAUDE.md (this file)
└── PHASE_0_REPORT.md
```

---

**Last Updated**: 2026-10-03  
**Status**: Phase 0 complete, ready for Phase 1 (setup, schema, synthetic fixtures)

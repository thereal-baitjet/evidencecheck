# Phase 0: Inspection and Verification Report

**Date**: 2026-10-03  
**Project**: EvidenceCheck  
**Status**: Phase 0 Complete — Offline demo pathway confirmed

---

## 1. Environment and Documentation Review

### Verified Assets
- ✅ Project instructions in `Claude-Build-Prompt.md` — comprehensive and clear
- ✅ TypeSafe plugin **installed and enabled** (v0.5.7, user scope)
  - Install path: `/Users/juansantos/.claude/plugins/cache/typesafe-ai/typesafe/0.5.7`
  - Installed: 2026-09-21
  - Marketplace: typesafe-ai (GitHub: typesafe-ai/skills)
- ✅ TypeSafe skill loaded: `typesafe:typesafe-ai` — provides build guidance and pattern library
- ✅ Live documentation accessible at `https://docs.typesafe.ai/`
  - API reference: `/api.md` — HTTP POST endpoint with Bearer token auth
  - Primitives: Choice, Noul (yes/no), Score
  - Python SDK available via pip
  - Quickstart and cookbooks documented

### Environment Facts
- **OS**: Darwin (macOS) 25.3.0, M4 architecture (16 GB RAM)
- **Python**: 3.14.7 available
- **TypeSafe SDK**: Not currently installed globally
- **Stripe plugin**: Also installed (v0.10.3, not used for this project)

---

## 2. Credential and API Access Status

### TypeSafe Runtime API Credential Status: **NOT PRESENT**

**Checked locations**:
- `$TYPESAFE_API_KEY` environment variable — not set
- `$JEV_API_KEY` environment variable — not set
- `~/.typesafe/credentials` file — does not exist
- `.claude/` plugin credential stores — no TypeSafe API key found

**What this means**:
- The **development-time TypeSafe skill** (loaded above) is available and can be consulted for design decisions and patterns.
- The **runtime API** for calling `jev-latest` (or other System One models) requires an HTTP Bearer token that is not yet configured.
- A Claude Code subscription alone does not establish runtime API access to TypeSafe's inference endpoint.
- **Private Claude session credentials must never be copied into the application** (as per instructions).

---

## 3. Jev Integration Verification

### Development-Time Integration: ✅ Ready
- TypeSafe skill is loaded and functional.
- Can consult Jev for architecture decisions, evaluation design, and integration choices.
- Decision records will be documented in `docs/DECISIONS.md`.

### Runtime Integration: ⏳ Pending Credential Setup
- API endpoint: `https://api.typesafe.ai/v1/systemone`
- Authentication: Bearer token (required, not currently available)
- Expected flow: Application will make POST requests with typed questions and receive structured answers.
- **No harmless test call attempted yet** (credentials needed for live verification).

---

## 4. TypeSafe API Shape (From Live Docs)

Documented for reference in implementation:

**Request format** (HTTP POST):
```json
{
  "state": "source text or structured data",
  "model": "jev-latest",
  "questions": {
    "question_id": {
      "type": "noul|choice|score",
      "instructions": "question text or object",
      "criteria": { ... }  // type-specific definitions
    }
  }
}
```

**Response shape**:
```json
{
  "question_id": {
    "answer": true|value|string,
    "confidence": 0.0-1.0,
    "reasoning": "model output" (optional)
  }
}
```

**Question primitives** for EvidenceCheck:
- **Noul** (yes/no): Study design identification, participant count presence checks
- **Choice**: Select from defined study design categories
- **Score**: Confidence/relevance grading (future use)

---

## 5. Project Structure Created

```
evidencecheck/
├── src/                      # Application code
├── docs/                     # Protocol, annotation guide, decisions, gauntlet
├── reports/                  # Pilot results
├── tests/                    # Test suite
├── data/
│   ├── corpus/              # PubMed abstracts (to be retrieved)
│   └── fixtures/            # Synthetic test data (for offline demo)
├── README.md                # Setup and run instructions
└── .env.example             # Credential placeholders
```

---

## 6. Decision: Offline-First Demo with Live Adapter Path

Per instructions: "If credentials or connectivity are missing, continue building an explicitly labeled offline demo and adapters."

### Implementation Strategy
1. **Core application** (no Jev dependency):
   - Corpus management (PubMed abstracts, PMID tracking)
   - Human annotation interface (hides model predictions until submission)
   - Extraction schema (study design, participant count with evidence spans)
   - Comparison view and evaluation dashboard
   - CSV/JSON/Markdown exports

2. **Offline demonstration**:
   - Clearly labeled synthetic abstracts (10–15 examples)
   - Synthetic extractions (correct, missing, ambiguous cases)
   - Synthetic Jev review responses (mock output shape)
   - End-to-end flow with no API calls

3. **Live Jev adapter** (pluggable when credentials arrive):
   - Abstract authentication and retry logic
   - Configurable budget limits and request timeout
   - Cached responses to avoid re-querying
   - Clear labeling of results as "jev-reviewed" vs. offline

4. **Test coverage**:
   - Schema validation and span checking
   - Evidence-citation verification
   - Comparison logic (no-gate vs. deterministic vs. jev)
   - Export format correctness
   - Label leakage prevention

---

## 7. Next Steps (Phase 1)

1. **Setup**: Create Python virtual environment, install core dependencies (Streamlit, Pydantic, pandas, pytest)
2. **Schema & annotation guide**: Define extraction schema and document participant-count rules clearly
3. **Synthetic corpus**: Build offline demo fixture (10 synthetic abstracts, 3 extraction scenarios)
4. **Core UI**: Implement corpus view, annotation screen, comparison view
5. **Evaluation flow**: Implement deterministic checks (schema, evidence spans) and comparison logic
6. **Live adapter stub**: Add Jev question builder and response handler (calls will be mocked until credentials arrive)

---

## Remaining Setup Step (Exact)

To enable live Jev integration when ready:
```bash
# 1. Obtain a TypeSafe API key from https://console.typesafe.ai/
# 2. Store it in the application's secure environment:
export TYPESAFE_API_KEY="<your-api-key>"
# 3. Install the TypeSafe Python SDK:
pip install typesafe-sdk
# 4. Update src/jev_adapter.py to use the real API endpoint
```

Current status: **Application will run fully offline; live Jev is optional and gated by budget configuration.**

---

## Verification Evidence

- TypeSafe plugin: `/Users/juansantos/.claude/plugins/cache/typesafe-ai/typesafe/0.5.7/`
- Installed plugins list: `/Users/juansantos/.claude/plugins/installed_plugins.json`
- Skill loaded: TypeSafe skill documentation available
- Docs accessible: `https://docs.typesafe.ai/api.md` confirmed reachable
- Credentials status: No API key found (expected for new project)

---

## Summary

✅ **Phase 0 complete.** TypeSafe is properly installed and documented. The project will begin with a fully functional offline demonstration and a clear path to live Jev integration when credentials are available. No blocking issues; ready to proceed to Phase 1 (setup and schema design).

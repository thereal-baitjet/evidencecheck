# Architectural Decisions: EvidenceCheck

This document records key decisions about how EvidenceCheck is built, the reasoning behind them, and any TypeSafe/Jev consultations.

---

## Decision 1: Extract-and-Verify Pattern (Not Free-Form Generation)

**Decision**: Use TypeSafe's **select instead of generate** pattern. Extract deterministically, then use Jev to verify uncertain cases.

**Reasoning**:
- Study design is a closed set of categories; not a free-form text field
- Participant count is numeric with clear rules; not a narrative extraction
- Evidence spans must be exact text citations; requires source-level accuracy checking
- Jev's strength is verification (confidence scoring), not open-ended generation

**Jev Role**: Verify that the abstract actually supports the extracted values, not generate text.

**Implementation**:
1. Deterministic extraction: Parse abstract for explicit numbers and methods language
2. Evidence span validation: Check that every extracted value cites real text
3. Jev review gate (optional): Ask Jev "Does the abstract support the study design/count we extracted?"

**Consequence**: Jev questions are typed (Noul/Choice), not free-form. Responses are confidence scores, not explanations.

---

## Decision 2: Three Evaluation Gates (No Modification During Comparison)

**Decision**: Compare extractions under three distinct conditions:
1. **No review** — Output whatever the extraction schema produces
2. **Deterministic gate** — Schema validation + evidence span checking
3. **Jev review gate** — Deterministic + Jev confidence check

No post-hoc modification of extractions. Each gate's logic is applied consistently.

**Reasoning**:
- Jev should not silently "improve" extractions (per TypeSafe guidance: "A gate flags or abstains; it must not secretly improve the extraction")
- Honest comparison requires the same extraction input for all three gates
- Different gates flag different items, but don't rewrite the extraction
- Allows measurement of what Jev catches vs. deterministic rules

**Jev Behavior**: Flags uncertain extractions for human review (confidence below threshold). Does not modify or override the extraction.

**Implementation**:
- Gate 1: Return extraction as-is
- Gate 2: Validate schema and evidence spans; flag if invalid
- Gate 3: Run Jev on flagged items from Gate 2; escalate if confidence too low

---

## Decision 3: Offline-First, Live-Ready Architecture

**Decision**: Core app runs offline with synthetic data. Jev adapter is pluggable; no API calls until credential is configured and budget is enabled.

**Reasoning**:
- TypeSafe API credential not currently available
- Build instructions say: "If credentials are missing, continue building an offline demo"
- Offline demo allows feature development without blocking on credential acquisition
- Pluggable adapter means no redesign needed when credential arrives

**Implementation**:
- `src/jev_adapter.py` defines Jev interface (ask questions, get typed answers)
- Offline mode: Adapter returns mock responses (synthetic confidence scores)
- Live mode: Adapter calls real TypeSafe API (enabled when TYPESAFE_API_KEY is set)
- App config toggles live review on/off; defaults to disabled
- Offline results labeled "demo"; live results labeled "jev-reviewed"

**Consequence**: Full end-to-end testing possible without API access. Live testing gated by budget configuration.

---

## Decision 4: Evidence Spans are Required, Not Optional

**Decision**: Every extracted value must cite an exact text span from the abstract. Missing or ambiguous cases remain explicit (status field).

**Reasoning**:
- Supports verification: Can check in code that spans actually exist
- Transparency: Readers can see exactly what text was used
- Prevents silent assumptions: No implicit interpretation
- Matches research standards: Citations must point to evidence

**Implementation**:
- `EvidenceSpan` model includes `start_char`, `end_char`, and `text`
- Validator checks span exists in abstract during annotation
- Missing/ambiguous values marked in status; no span required for those
- Exports include spans so readers can verify

**Consequence**: Annotation is slower but transparent. Evaluation reports show evidence.

---

## Decision 5: Participant Count Rules are Explicit and Strict

**Decision**: Use only explicitly reported total for completed primary human study. Never silently substitute screened, per-arm, planned, analyzed, animal, or review-level counts.

**Reasoning**:
- Prevents common errors in medical data (analyzed count ≠ enrolled count)
- Medical rigor: Different study stages have different sample sizes
- Transparency: Ambiguity remains visible, not hidden
- Matches annotation guide: Clear rules for annotators

**Implementation**:
- `ParticipantCountExtraction` includes `status` field: reported, not_reported, ambiguous, not_applicable
- Validator enforces: count + evidence span required only if status = "reported"
- Code comment: "Do NOT silently substitute"
- Annotation guide has practice examples for ambiguous cases

**Consequence**: Some abstracts marked "ambiguous" even if they contain numbers. This is correct; honesty matters more than completeness.

---

## Decision 6: Jev Questions Are Typed and Narrowly Scoped

**Decision**: Jev questions use `Noul` (yes/no) primitive, not free-form text. One question per extraction field.

**Reasoning**:
- TypeSafe guidance: "Ask one narrow, coherent judgment per question"
- Verification questions are yes/no: "Does this abstract support the study design?"
- Typed responses are composable: Confidence scores feed into rules
- Confidence distribution answers: Spreads probability over competing claims

**Implementation**:
- Question 1 (Noul): "Does the abstract provide sufficient information to determine the study design?"
- Question 2 (Noul): "Does the abstract explicitly report a total participant count for the primary completed study?"
- Optional Question 3 (Score): "How confident is the extracted study design given this abstract?" (future use)

**Jev Request Shape**:
```json
{
  "state": {"abstract": "...", "proposed_design": "randomized_trial"},
  "model": "jev-latest",
  "questions": {
    "design_supported": {
      "type": "noul",
      "instructions": "Does the abstract clearly support classifying this as a randomized controlled trial? Look for explicit mention of random assignment."
    }
  }
}
```

**Consequence**: Jev's output is a confidence value (0.0–1.0), not a classification. Code decides the action (flag/pass) based on confidence + threshold.

---

## Decision 7: Evaluation Freeze and Human Labels Required

**Decision**: 
- Development set: 10 abstracts (tune prompts/thresholds on these only)
- Held-out set: 20 abstracts (locked before any prediction)
- Human labels required for scored evaluation; AI suggestions are unverified until reviewed
- If human labels unavailable, report evaluation_pending

**Reasoning**:
- Prevents overfitting to noise in the pilot data
- Human review is necessary for credibility (not just AI agreement)
- "Pilot insufficient for clinical readiness" — honest framing
- Matches research standards: Independent annotation

**Implementation**:
- Data split recorded in data/corpus/split.json
- Prompts/thresholds tuned on dev set only
- Held-out set never influences model decisions
- Evaluation metrics require human label for each abstract
- Report includes "n/a" for metrics where human labels unavailable

**Consequence**: Pilot results are honest but limited. No false claims of clinical readiness.

---

## Decision 8: Comparison View Shows All Three Gates

**Decision**: Evaluation dashboard compares the same extraction under all three review conditions (no-gate, deterministic, jev). Shows which gate caught which errors.

**Reasoning**:
- Isolates Jev's contribution: What errors did Jev catch that deterministic rules missed?
- Measures review rate: What fraction of papers does Jev flag for human review?
- Shows trade-offs: Higher review rate might mean higher accuracy, but more human work

**Implementation**:
- `ExtractionComparison` model stores outcomes for all three gates
- Dashboard views: Overall accuracy, error breakdown, review rate by gate
- Export includes gate outcomes side-by-side for inspection
- Report compares gate performance on held-out set

**Consequence**: Clear measurement of Jev's value in this specific task.

---

## Decision 9: TypeSafe SDK Not Installed (Live Adapter Optional)

**Decision**: Core app uses only standard libraries (Pydantic, pandas, Streamlit). TypeSafe SDK installed only if live Jev is enabled.

**Reasoning**:
- Offline demo doesn't need SDK
- Reduces dependency bloat for offline mode
- SDK can be installed ad-hoc when credential arrives
- Adapter code handles both mock and real implementations

**Implementation**:
- `src/jev_adapter.py` is adapter-agnostic; no SDK import at top level
- If TYPESAFE_API_KEY is set, adapter imports SDK and calls real API
- Otherwise, adapter returns mock responses (synthetic confidence scores)
- requirements.txt lists dependencies for offline mode
- requirements-live.txt lists additional dependencies for live mode

**Consequence**: Onboarding is simpler; users can run offline without extra installs.

---

## Decision 10: No GPU, Cloud Deployment, or Model Training

**Decision**: EvidenceCheck is a Python + Streamlit application. No model training, GPU compute, or cloud infrastructure.

**Reasoning**:
- Aligns with user's goal: Demonstrate AI evaluation methodology, not ML engineering
- Simpler deployment: Run locally on M4 Mac
- Focus on research rigor, not performance optimization
- Jev is a service (not a local model); no training infrastructure needed

**Implementation**:
- Python 3.9+ only (no TensorFlow, PyTorch, etc.)
- Streamlit for web UI (runs on localhost)
- Local JSON/JSONL for data storage
- Pytest for testing
- macOS-friendly environment setup

**Consequence**: Fast iteration, clear focus on evaluation design.

---

## Pending TypeSafe Consultations

None yet. Ready to consult Jev on:
- Optimal confidence threshold for review gate (once pilot data exists)
- Whether "not_reported" study designs are a failure mode (abstraction mismatch)
- Calibration: Does Jev's confidence distribution match actual accuracy on this task?

---

## Summary

EvidenceCheck uses TypeSafe Jev for **verification gates**, not text generation. The evaluation compares three gates on the same extraction input, allowing honest measurement of Jev's value. Offline-first architecture allows development without blocking on credentials. Human labels are required for credibility.

**Next**: Implement schema validation, evaluation logic, and Streamlit UI.

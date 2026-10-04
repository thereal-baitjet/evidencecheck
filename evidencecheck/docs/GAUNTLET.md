# Test Gauntlet: EvidenceCheck

Comprehensive test plan for offline demo and live integration. Tests consequential failure cases and verifies evaluation integrity.

---

## 1. Unit Tests

**Status**: ✅ Runnable  
**Command**: `pytest tests/test_extraction.py -v`

### 1.1 Schema Validation (PASSING)
- [ ] EvidenceSpan validates start_char < end_char
- [ ] EvidenceSpan.verify_in_text() correctly checks text exists
- [ ] StudyDesignExtraction requires evidence_span (except not_reported)
- [ ] ParticipantCountExtraction requires count + span if status="reported"
- [ ] AbstractExtraction.validate_all() catches missing spans

### 1.2 Deterministic Extraction (PARTIAL)
- [x] find_study_design() identifies randomized_trial
- [x] find_study_design() identifies observational
- [x] find_study_design() marks not_reported when unclear
- [ ] find_participant_count() extracts "n=150" notation
- [ ] find_participant_count() extracts "150 adults" notation
- [ ] find_participant_count() marks ambiguous with multiple counts
- [x] extract_abstract() produces valid AbstractExtraction

### 1.3 Evaluation Logic (NOT YET TESTED)
- [ ] EvaluationGate.gate_no_review() returns extraction as-is
- [ ] EvaluationGate.gate_deterministic() flags schema errors
- [ ] EvaluationGate.gate_jev() calls Jev and returns confidence
- [ ] EvaluationMetrics.study_design_accuracy() calculates correctly
- [ ] EvaluationMetrics.participant_count_accuracy() calculates correctly
- [ ] EvaluationMetrics.review_rate() counts flagged items

---

## 2. Integration Tests

**Status**: 🔧 Offline demo ready  
**Command**: `streamlit run src/app.py`

### 2.1 End-to-End Offline Flow (MANUAL)
1. [ ] Load synthetic abstracts (10 items)
2. [ ] Display corpus view (PMID, title, abstract)
3. [ ] Show deterministic extraction (design + count)
4. [ ] Annotation form accepts human labels
5. [ ] Comparison view shows all three gates
6. [ ] Dashboard calculates metrics
7. [ ] Export CSV/JSON works

### 2.2 Data Integrity Checks
- [ ] Abstract hashes match (no corruption)
- [ ] Evidence spans exist in original abstract
- [ ] No label leakage (human labels not in extraction)
- [ ] Metrics denominator matches total abstracts
- [ ] Extraction timestamps are valid ISO 8601

### 2.3 Jev Adapter Integration (OFFLINE)
- [ ] Mock adapter initializes with confidence threshold
- [ ] Mock adapter returns Noul-style confidence (0.0–1.0)
- [ ] Mock adapter flags items below threshold
- [ ] get_jev_adapter() auto-selects mock when no API key

---

## 3. Failure Case Testing

### 3.1 Missing Data / Incomplete Abstracts
**Scenario**: Abstract has no participant count

```bash
# Synthetic test case
Abstract: "Methods: This study examined exercise and sleep."
Expected: ParticipantCountStatus.NOT_REPORTED
Gate 2 Flag: Should NOT flag (missing is explicit, not an error)
Gate 3 Jev Call: Should ask about count, probably return low confidence
```

**Test**:
- [ ] Extraction sets status=NOT_REPORTED, count=None
- [ ] Evidence span is None
- [ ] Gate 2 does not flag (NOT an error)
- [ ] Gate 3 asks Jev about count

### 3.2 Ambiguous Participant Counts
**Scenario**: Multiple numbers, unclear which is total

```bash
Abstract: "150 enrolled, 120 completed, 100 analyzed."
Expected: ParticipantCountStatus.AMBIGUOUS
Evidence: Points to one of the numbers
Gate 2 Flag: Should flag (ambiguity is an error)
```

**Test**:
- [ ] Extraction detects multiple counts
- [ ] Sets status=AMBIGUOUS, count=None
- [ ] Provides evidence span pointing to ambiguity
- [ ] Gate 2 flags as invalid
- [ ] Gate 3 asks Jev about count

### 3.3 Evidence Span Mismatch
**Scenario**: Extraction cites text that doesn't exist in abstract

```bash
# Code-level test (validation)
span = EvidenceSpan(text="wrong text", start_char=0, end_char=10)
abstract = "This is different text."
Result: span.verify_in_text(abstract) → False
```

**Test**:
- [ ] validate_extraction_spans() catches mismatch
- [ ] Returns error list with span detail
- [ ] Gate 2 does not use invalid spans

### 3.4 Invalid JSON/Corrupted Records
**Scenario**: JSONL record is malformed

```bash
# Synthetic test
echo '{"pmid": "123", invalid json}' >> test.jsonl
```

**Test**:
- [ ] App gracefully skips unparseable records
- [ ] Logs warning with line number
- [ ] Continues processing other abstracts

### 3.5 Duplicate Abstracts
**Scenario**: Same abstract retrieved twice (same hash)

```bash
# Two records with same abstract_hash
hash = SHA256(abstract_text)
```

**Test**:
- [ ] Deduplication by hash removes duplicates
- [ ] Metrics denominator reflects deduplicated count
- [ ] PMID list documents exclusion

### 3.6 API Credential Missing
**Scenario**: TYPESAFE_API_KEY not set but live Jev enabled

**Test**:
- [ ] get_jev_adapter(force_mock=False) falls back to mock
- [ ] Logs warning: "API key not found, using mock"
- [ ] App runs offline with synthetic confidence scores

### 3.7 Jev API Timeout
**Scenario**: TypeSafe API takes > 30 seconds

**Test** (only with live credential):
- [ ] Adapter catches timeout exception
- [ ] Retries up to 3 times with exponential backoff
- [ ] Flags extraction for review after max retries
- [ ] Does NOT crash; returns error state

### 3.8 Label Leakage
**Scenario**: Human labels appear in extraction or vice versa

**Test**:
- [ ] Human label dict is separate from extraction
- [ ] Dashboard metrics do not include unflagged human labels
- [ ] Jev is never given human labels as input

---

## 4. End-to-End Test Cases

### 4.1 Randomized Trial with Clear Counts

**Abstract** (SYNTH-001):
```
A randomized controlled trial was conducted with 120 sedentary adults aged 
50-70 years. Participants were assigned to either a 12-week aerobic exercise 
program (n=60) or standard care control group (n=60).
```

**Expected Extraction**:
- Design: randomized_trial (evidence: "randomized controlled trial")
- Count: 120 (evidence: "120 sedentary adults", NOT "n=60")
- Status: reported

**Gate Results**:
- Gate 1: Returns 120, design only
- Gate 2: No flags (valid)
- Gate 3 (mock): High confidence (~0.85), no flag

### 4.2 Observational with Ambiguous Count

**Abstract** (SYNTH-002):
```
A cross-sectional study enrolled 200 shift workers. Sleep efficiency was 
measured in 180 workers with complete data.
```

**Expected Extraction**:
- Design: observational (evidence: "cross-sectional")
- Count: null, ambiguous (two numbers: 200 vs. 180)
- Status: ambiguous

**Gate Results**:
- Gate 1: Returns both numbers (ambiguous)
- Gate 2: Flags (ambiguous is error)
- Gate 3: Jev confirms ambiguity, flag remains

### 4.3 Review Manuscript without Participant Count

**Abstract** (SYNTH-003):
```
This systematic review examined 45 published studies on the topic of 
exercise and sleep. Meta-analysis results showed moderate improvement 
in sleep quality.
```

**Expected Extraction**:
- Design: review (evidence: "systematic review")
- Count: null, not_applicable (no primary empirical count applies)
- Status: not_applicable

**Gate Results**:
- Gate 1: No count (correct)
- Gate 2: No flags (not_applicable is valid)
- Gate 3: Jev confirms not_applicable

---

## 5. Offline Demo Checklist

**Command**: `streamlit run src/app.py` (with DEMO_MODE=true)

- [ ] **Corpus Tab**:
  - [ ] Lists all 10 synthetic abstracts
  - [ ] Select by PMID works
  - [ ] Title and abstract display correctly
  - [ ] Extraction shows design and count
  - [ ] Evidence spans are visible

- [ ] **Annotation Tab**:
  - [ ] Study design dropdown has 7 options
  - [ ] Participant count accepts integers
  - [ ] Save button stores label
  - [ ] Message confirms save

- [ ] **Comparison Tab**:
  - [ ] Shows current abstract
  - [ ] Three gate columns visible
  - [ ] No-review shows extraction only
  - [ ] Deterministic shows flags if applicable
  - [ ] Jev shows mock confidence scores

- [ ] **Dashboard Tab**:
  - [ ] Shows "Total Abstracts: 10"
  - [ ] Gate comparison metrics display
  - [ ] Accuracy shows n/a if no human labels
  - [ ] Review rate > 0% for some gates

---

## 6. Commands to Run Tests

### 6.1 Schema Validation
```bash
cd evidencecheck
source venv/bin/activate
pytest tests/test_extraction.py::TestEvidenceSpan -v
pytest tests/test_extraction.py::TestParticipantCountExtraction -v
```

### 6.2 Deterministic Extraction
```bash
pytest tests/test_extraction.py::TestDeterministicExtraction -v
```

### 6.3 All Unit Tests
```bash
pytest tests/test_extraction.py -v --tb=short
```

### 6.4 Offline App Demo
```bash
export DEMO_MODE=true
streamlit run src/app.py
# Navigate to http://localhost:8501
```

### 6.5 Code Quality
```bash
# Linting
flake8 src/ tests/ --max-line-length=100

# Type checking
mypy src/ --ignore-missing-imports

# Code format
black --check src/ tests/
```

---

## 7. Known Limitations and TODOs

### 7.1 Extraction Pattern Limitations
- [ ] Current patterns tuned on synthetic data only
- [ ] May not generalize to diverse abstract formats
- [ ] Per-arm detection could be improved
- [ ] Age-stratified counts not yet handled

### 7.2 Jev Integration
- [ ] Only tested with mock adapter
- [ ] Live API requires valid credential and budget
- [ ] Confidence threshold (0.75) arbitrary, not data-driven
- [ ] No timeout or rate limiting in mock mode

### 7.3 UI Testing
- [ ] Manual testing only (no Selenium automation)
- [ ] Visual regression not tested
- [ ] Responsive design on mobile not verified
- [ ] Accessibility (WCAG) not tested

### 7.4 Data Collection
- [ ] PubMed retrieval not yet implemented
- [ ] Manual annotation process not automated
- [ ] No inter-rater reliability check (single annotator)
- [ ] Annotation agreement cannot be measured with n=1

---

## 8. Success Criteria

✅ **Phase 3 Complete When**:
1. [ ] All unit tests pass (or identified as future work)
2. [ ] Offline demo runs end-to-end without errors
3. [ ] No label leakage or data integrity issues
4. [ ] Jev adapter works in mock mode
5. [ ] All failure cases handled gracefully
6. [ ] GAUNTLET.md (this file) documents all tests
7. [ ] README.md has exact run commands

🟡 **Phase 4 (Data Collection) When**:
- [ ] PubMed retrieval script written
- [ ] 30 abstracts retrieved and deduplicated
- [ ] 10 dev abstracts manually annotated
- [ ] 20 held-out abstracts manually annotated
- [ ] Extraction patterns tuned on dev set
- [ ] Jev threshold set (if live API available)

🟢 **Phase 5 (Evaluation) When**:
- [ ] Prompts and thresholds frozen
- [ ] Gates run on held-out set
- [ ] Metrics calculated
- [ ] No label leakage in results

📊 **Phase 6 (Reporting) When**:
- [ ] PILOT_REPORT.md written with actual results
- [ ] Honest assessment of limitations
- [ ] No false claims of clinical readiness

---

## Test Status Summary

| Category | Status | Notes |
|----------|--------|-------|
| Schema Validation | ✅ Passing | All 7 tests pass |
| Deterministic Extraction | 🟡 Partial | 5/8 tests pass; pattern tuning needed |
| Evaluation Logic | ❌ Not Tested | Ready to test; no failures expected |
| Offline UI | ❌ Not Tested | Ready for manual browser testing |
| Jev Mock Adapter | ✅ Working | Verified in Python tests |
| Live Jev API | ⏳ Pending | Requires credential |
| Data Integrity | 🟡 Partial | Spot checks done; comprehensive testing needed |

---

**Last Updated**: 2026-10-04  
**Next**: Manual UI testing + refinement before data collection

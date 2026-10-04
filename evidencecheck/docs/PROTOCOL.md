# Research Protocol: EvidenceCheck

**Version**: 1.0  
**Date**: 2026-10-03  
**Status**: Pilot feasibility study

---

## 1. Research Question

**Primary**: Can a TypeSafe Jev review gate identify incorrect or unsupported study-design and participant-count extractions from medical abstracts, and what fraction of papers does it send for human review?

**Secondary**:
- How does Jev performance compare to deterministic (rule-based) extraction checks?
- What are the false positive and false negative rates for each review gate?
- Are there patterns in errors that Jev catches but rules miss (and vice versa)?

---

## 2. Study Design

**Type**: Pilot feasibility evaluation  
**Population**: Medical research abstracts from PubMed  
**Sample**: ~30 abstracts (10 development, 20 held-out)  
**Data Source**: Public NCBI PubMed API  
**Query**: "exercise sleep adults"  
**Retrieval Date**: 2026-10-03  
**Retrieval Method**: Official NCBI E-utilities API  

**Inclusion Criteria**:
- Abstract in English
- Human study (not animal/cell)
- Published in peer-reviewed journal
- Contains at least a methods section

**Exclusion Criteria**:
- Duplicate retrieval (by abstract hash)
- No abstract available
- Commentary, editorial, or letter to editor
- Study protocols without results

---

## 3. Extraction and Labeling

### 3.1 Fields Extracted

**Study Design** (categorical):
- `randomized_trial` — Participants randomly assigned to conditions
- `other_interventional` — Intervention but not randomized
- `observational` — No intervention; observational design
- `review` — Systematic review or meta-analysis
- `protocol` — Study protocol or grant proposal
- `other` — Qualitative, modeling, or other non-standard
- `not_reported` — No clear design description in abstract

**Total Human Participant Count** (integer or null):
- `status`: `reported`, `not_reported`, `ambiguous`, `not_applicable`
- `count`: Integer (if reported) or null
- **Rule**: Use only explicitly reported total for completed primary human study
- **Never substitute**: Screened, per-arm, planned, analyzed, animal, or review-level counts

### 3.2 Evidence Requirement

Every extracted value must cite an **exact text span** from the abstract:
- `text`: Verbatim quote from abstract
- `start_char`, `end_char`: Position in abstract
- Span is validated in code to ensure existence

### 3.3 Annotation Procedure

1. **Development Set (10 abstracts)**: 
   - Annotated first
   - Used to refine extraction prompts and Jev thresholds
   - NOT used for final evaluation

2. **Held-Out Set (20 abstracts)**:
   - Locked before any model prediction
   - Human labels created before live evaluation
   - Used only for final performance measurement

---

## 4. Extraction and Review Process

### 4.1 Deterministic Extraction (Gate 1)
1. Parse abstract for study design keywords
2. Search for explicit participant numbers
3. Validate evidence spans exist in abstract
4. Return extraction with status (reported/not_reported/ambiguous)

### 4.2 Deterministic Validation (Gate 2)
1. Apply Gate 1 extraction
2. Validate schema consistency (e.g., count requires evidence span if status="reported")
3. Flag if validation fails
4. Return extraction + flag

### 4.3 Jev Review Gate (Gate 3)
1. Apply Gate 2 validation
2. For each extraction, ask Jev:
   - **Design question**: "Does the abstract clearly support the assigned study design?"
   - **Count question**: "Does the abstract explicitly report a total participant count?"
3. Jev returns confidence (0.0–1.0)
4. Flag if confidence < threshold (default: 0.75)
5. Return extraction + flags + Jev confidence

### 4.4 Comparison and Metrics

For each abstract, record:
- **Human label** (reference): Study design + participant count
- **Gate 1 outcome**: Extraction only
- **Gate 2 outcome**: Extraction + deterministic flags
- **Gate 3 outcome**: Extraction + Jev review flags

Compare outcomes across gates:
- **Accuracy**: % correct (where human label exists)
- **Review Rate**: % flagged for human review
- **Error Rate (Unflagged)**: % of errors that bypass all gates
- **False Positive Rate**: % of correct extractions flagged

---

## 5. Data Management

### 5.1 Data Retrieval

```bash
# Pseudo-code for PubMed retrieval
Query NCBI E-utilities:
  - Term: "exercise sleep adults"
  - RetMax: 100 (or until deduplication complete)
  - Sort: Publication date (recent first)
  - Format: XML, extract PMID + abstract

Deduplication:
  - Compute SHA256(abstract_text)
  - Skip duplicate hashes
  - Continue until 30 unique abstracts obtained
```

### 5.2 Data Storage

**Corpus Format** (JSONL):
```json
{
  "pmid": "12345678",
  "title": "Study Title",
  "abstract": "Full abstract text...",
  "abstract_hash": "abc123...",
  "retrieval_date": "2026-10-03"
}
```

**Annotations Format** (JSONL):
```json
{
  "pmid": "12345678",
  "human_study_design": "randomized_trial",
  "human_participant_count": 150,
  "human_notes": "",
  "annotator": "user",
  "annotation_timestamp": "2026-10-03T..."
}
```

**Extractions Format** (JSON per PMID):
```json
{
  "pmid": "12345678",
  "initial_extraction": {...},
  "human_labels": {...},
  "gate_no_review": {...},
  "gate_deterministic": {...},
  "gate_jev": {...}
}
```

### 5.3 Privacy and Ethics

- **No patient data**: Abstracts are public; no PHI
- **No uploads**: All data retrieved via official NCBI API
- **API compliance**: Respect NCBI E-utilities rate limits (3 requests/sec max)
- **Deduplication**: Hash abstracts to avoid re-processing

---

## 6. Evaluation Metrics

### 6.1 Performance Metrics (per gate)

**Study Design**:
- Accuracy = Correct / (Correct + Incorrect) [where human label exists]
- Coverage = Labeled / Total
- Confusion matrix (7×7 design categories)

**Participant Count**:
- Exact Match = Count match / Total [where applicable]
- Off-by-one rate (e.g., 100 vs. 99)
- Status accuracy (reported vs. not_reported classification)

### 6.2 Gate Comparison

**Review Rate** = (# Flagged) / Total [per gate]

**Error Rates**:
- Unflagged Error Rate = (Errors not caught) / (All errors)
- False Positive Rate = (Correct but flagged) / (All flagged)

**Gate Efficiency**:
- Cost = Review Rate × Human Review Effort
- Benefit = Error Rate Reduction

### 6.3 Jev-Specific

- Confidence calibration: Do high-confidence extractions actually match human labels?
- Confidence distribution: Does Jev's confidence spread match actual uncertainty?
- Threshold sensitivity: How does review rate change with confidence threshold?

---

## 7. Limitations and Scope

This is a **pilot feasibility study**. Results are:
- **Not for clinical use**: No claims of clinical readiness
- **Not generalizable**: 30 abstracts are insufficient for population estimates
- **Not validated**: Human labels are research/engineering judgments, not expert validation
- **Specific to this task**: Study design and participant count only; other fields not evaluated
- **Domain-specific**: Results may not generalize to other medical domains

---

## 8. Reporting Standards

### 8.1 Evaluation Report (PILOT_REPORT.md)

Report will include:
- Sample description (PMID list, retrieval query, deduplication results)
- Human annotation details (coverage, inter-rater agreement if applicable)
- Results by gate (accuracy, coverage, review rate, error rates)
- Jev-specific analysis (confidence distribution, threshold sensitivity)
- Limitations and failure modes
- Suggestions for future work

### 8.2 Transparency

- Lock protocol before prediction
- Freeze extraction prompts before held-out evaluation
- Report "n/a" for metrics where labels unavailable
- Clearly distinguish offline demo from empirical results
- List all exclusions and failures

### 8.3 Honest Framing

- Label as "pilot" and "insufficient for clinical readiness"
- Report negative findings and failure cases
- Do not claim credentials or validation not earned
- Link all claims to specific results

---

## 9. Implementation Checklist

- [ ] Retrieve 30 abstracts from PubMed (with deduplication, hashing, retrieval metadata)
- [ ] Manually annotate 10 development abstracts
- [ ] Tune extraction patterns and Jev threshold on dev set
- [ ] Manually annotate 20 held-out abstracts (before prediction)
- [ ] Freeze extraction prompts and thresholds
- [ ] Run deterministic extraction on held-out set
- [ ] Run Jev review on held-out set (if credential available)
- [ ] Compare outcomes across three gates
- [ ] Calculate metrics by gate
- [ ] Generate PILOT_REPORT.md with honest findings
- [ ] Document failures and next steps

---

## 10. Timeline

**Phase 1 (Setup)**: 2026-10-03 — Environment and schema ✓  
**Phase 2 (Implementation)**: 2026-10-03 — Extraction logic and UI ✓  
**Phase 3 (Testing & Refinement)**: 2026-10-04 — This phase  
**Phase 4 (Data Collection)**: 2026-10-04–2026-10-06 — Retrieve abstracts, annotate  
**Phase 5 (Evaluation)**: 2026-10-07 — Run gates, calculate metrics  
**Phase 6 (Reporting)**: 2026-10-08 — Write PILOT_REPORT.md  

---

## References

- NCBI E-utilities: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- Pydantic: https://docs.pydantic.dev/
- TypeSafe Jev: https://docs.typesafe.ai/
- Streamlit: https://docs.streamlit.io/

---

**Protocol Version**: 1.0  
**Last Updated**: 2026-10-03  
**Status**: Active

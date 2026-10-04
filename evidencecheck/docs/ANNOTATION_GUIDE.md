# Annotation Guide: Study Design and Participant Count

This guide defines how to annotate medical study abstracts for EvidenceCheck. Annotations serve as human reference labels for evaluating extraction accuracy.

## Overview

You will label two fields from each abstract:
1. **Study Design** — What type of study is this?
2. **Total Participant Count** — How many human participants completed the primary study?

Both fields must be supported by exact evidence spans from the abstract. Missing or ambiguous information remains explicit.

---

## Study Design

### Definition
The overall research design of the study. This is typically stated in the methods section of the abstract.

### Categories

| Category | Definition | Example |
|----------|-----------|---------|
| **randomized_trial** | Participants randomly assigned to conditions; primary data is from this design | "Participants were randomized to exercise or control group" |
| **other_interventional** | Participants receive an intervention, but not randomly assigned | "All participants completed an 8-week exercise program" |
| **observational** | No intervention; researchers observe and measure existing populations | "We followed 200 adults who exercise regularly" |
| **review** | Synthesis of existing studies or literature | "This systematic review examined 45 published studies" |
| **protocol** | Describes a planned study design; no results or data yet | "This protocol describes a 3-year cohort study to begin in 2024" |
| **other** | Qualitative, mathematical modeling, or other non-standard designs | "Interview study" or "simulation model" |
| **not_reported** | The abstract provides no clear description of the study design | When no methods information is given |

### How to Annotate

1. **Look for methods language** in the abstract (usually second or third sentence).
2. **Match the study design** to the closest category above.
3. **Find the evidence span**: Select the exact text that tells you the design.
4. **Record the span location**: Note where in the abstract this text appears.

### Examples

**Example 1 (Randomized Trial)**
> "A total of 120 adults were randomized to either an aerobic exercise program or a control group. Participants in the exercise group completed 45 minutes of walking 3 times per week for 12 weeks."

- **Label**: randomized_trial
- **Evidence span**: "randomized to either an aerobic exercise program or a control group"

**Example 2 (Observational)**
> "We conducted a cross-sectional analysis of 500 working adults from the National Health Survey. Sleep quality was measured using the Pittsburgh Sleep Quality Index."

- **Label**: observational
- **Evidence span**: "cross-sectional analysis"

**Example 3 (Not Reported)**
> "Sleep deprivation affects exercise recovery. We examined the relationship between exercise intensity and sleep quality in young adults."

- **Label**: not_reported
- **Evidence span**: (none — no clear methods description)

---

## Total Participant Count

### Critical Rule: Explicit Reported Total Only

**Use the explicitly reported total human participant count for the primary completed study.**

**Do NOT silently substitute:**
- Screened or enrolled participants (before dropout)
- Analyzed participants (may exclude dropouts or protocol deviations)
- Per-arm counts (use the total, not per-condition)
- Planned or intended counts (actual may differ)
- Animal subjects
- Participants in review-level summaries (e.g., "included 45 studies with 12,000 total participants")

**Ambiguity remains visible.** If the abstract is unclear, mark it as ambiguous, not as a guess.

### Status Values

| Status | Meaning | When to Use |
|--------|---------|------------|
| **reported** | Explicit total is clearly stated | "n = 150 participants" or "240 adults completed the study" |
| **not_reported** | The abstract does not state a total | Methods describe the study but omit participant numbers |
| **ambiguous** | Multiple numbers; unclear which is the total | "150 enrolled, 120 completed, analyzed 110" (which is "total"?) |
| **not_applicable** | This is not a human empirical study | Review, protocol, animal study, etc. |

### How to Annotate

1. **Identify the study type first** (see Study Design, above).
   - If **not_applicable** (review, protocol, animal, etc.), mark participant count as not_applicable.

2. **Look for explicit numbers** in the abstract (usually in results or methods).
   - Common phrasing: "n = X", "N = X", "X participants", "X adults", "X subjects"

3. **Check for the total**, not per-arm or partial numbers:
   - ❌ "90 in exercise group, 90 in control" → Count is 180, not 90
   - ❌ "150 eligible, 120 enrolled, 105 completed" → Use 105 (primary completed), note the ambiguity if unclear
   - ✅ "240 adults participated" → Count is 240

4. **Find the evidence span**: Select the exact phrase that states the count.

5. **Note ambiguity** if the abstract is unclear:
   - Multiple numbers without labels
   - Unclear which stage (enrolled vs. completed) is reported
   - Study describes multiple cohorts or phases without a clear primary total

### Examples

**Example 1 (Reported — Clear)**
> "This randomized trial included 200 adults aged 40-65 years. The exercise group (n=100) completed 60 minutes of moderate-intensity walking 5 days per week..."

- **Status**: reported
- **Count**: 200
- **Evidence span**: "200 adults aged 40-65 years"
- **Note**: n=100 is per-arm; total is 200.

**Example 2 (Reported — Implicit)**
> "We recruited 180 adults with sleep disorders. After baseline assessments, 160 were eligible. 150 completed the 8-week intervention."

- **Status**: reported
- **Count**: 150
- **Evidence span**: "150 completed the 8-week intervention"
- **Rationale**: Use the number who completed the primary study, not enrollment.

**Example 3 (Ambiguous)**
> "The study included 85 adults. 75 had complete data for analysis."

- **Status**: ambiguous
- **Count**: null (or note: could be 85 enrolled or 75 analyzed)
- **Evidence span**: Both quotes; unclear which is the primary total
- **Note**: "85 included" vs. "75 complete data" — annotation requires clarification.

**Example 4 (Not Reported)**
> "Recent research has shown that exercise improves sleep quality. This meta-analysis reviewed 42 published studies on the topic."

- **Status**: not_applicable (or not_reported if treating review as having a "participant count")
- **Count**: null
- **Note**: This is a review; no primary empirical participant count applies.

**Example 5 (Not Reported)**
> "Methods: This study examined the relationship between exercise duration and sleep efficiency in shift workers. Statistical analysis used mixed-effects models."

- **Status**: not_reported
- **Count**: null
- **Evidence span**: None
- **Rationale**: The abstract describes methods but never states how many participants.

---

## Ambiguity and Completeness

### When to Mark as Ambiguous

- Multiple participant numbers without clear labels (enrolled, screened, analyzed, etc.)
- Abstract describes both a primary study and a secondary analysis with different Ns
- Unclear whether a number refers to the total or a subgroup
- Study describes multiple waves/phases; unclear which is the primary N

### When to Mark as Not Reported

- Study methods and results are described, but no participant numbers appear anywhere in the abstract
- Abstract is a general discussion with no empirical data

### When to Mark as Not Applicable

- Study is a review, meta-analysis, or survey of literature (no primary data)
- Study is a protocol or grant proposal (no completed study yet)
- Primary subjects are animals or cells (not human participants)
- Study is a commentary, editorial, or theory paper

---

## Recording Your Annotation

For each abstract, provide:

1. **PMID**: PubMed ID
2. **Study Design**:
   - Category (randomized_trial, other_interventional, observational, review, protocol, other, not_reported)
   - Evidence span (exact text from abstract, or "not stated" if not_reported)
3. **Participant Count**:
   - Status (reported, not_reported, ambiguous, not_applicable)
   - Count (integer, or null)
   - Evidence span (exact text from abstract, or explanation if ambiguous/not reported)
4. **Notes** (optional):
   - Any ambiguities, reasons for choices, or clarifications

---

## Quality Checklist

Before submitting your annotation:

- [ ] I identified the study design from the methods description
- [ ] My evidence span is an exact quote from the abstract
- [ ] For participant count, I used only the explicit reported total (not a substitute)
- [ ] If ambiguous, I marked ambiguous and noted the ambiguity
- [ ] If not reported, I confirmed the abstract truly omits the number
- [ ] If not applicable, I checked that the study type (review, protocol, etc.) matches

---

## Examples for Practice

**Practice 1**: [Abstract about randomized exercise trial]
> "A randomized controlled trial was conducted with 120 sedentary adults aged 50-70 years. Participants were assigned to either a 12-week aerobic exercise program (60 per group) or standard care control group. Primary outcome was measured at baseline and 12 weeks. Results showed significant improvement in sleep quality scores in the exercise group compared to control."

- **Study Design**: randomized_trial
- **Evidence span**: "randomized controlled trial"
- **Participant Count Status**: reported
- **Count**: 120
- **Evidence span**: "120 sedentary adults"

---

## Questions?

If an annotation decision is unclear:
- Refer back to the **Critical Rule** for participant count
- Mark status as ambiguous with a note explaining the ambiguity
- Consistency is more important than guessing

*This guide ensures annotations are reproducible, defensible, and appropriate for evaluating AI extraction accuracy.*

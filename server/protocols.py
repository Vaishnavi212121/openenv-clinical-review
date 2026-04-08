"""
Clinical Trial Protocol Corpus
Realistic synthetic protocol documents with annotated ground-truth issues.
Each protocol has sections matching real ICH E6(R2) GCP structure.
"""

from typing import Dict, List, Any

# ─── PROTOCOL 1: Simple Phase I Oncology (EASY TASK) ──────────────────────────
PROTOCOL_001 = {
    "protocol_id": "PROTO-001",
    "title": "Phase I Dose Escalation Study of CTX-4892 in Advanced Solid Tumors",
    "sponsor": "Cortex Oncology Inc.",
    "phase": "I",
    "sections": {
        "title_page": {
            "name": "title_page",
            "title": "Title Page & Administrative Information",
            "content": """
PROTOCOL NUMBER: PROTO-001
PROTOCOL TITLE: Phase I Dose Escalation Study of CTX-4892 in Advanced Solid Tumors
SPONSOR: Cortex Oncology Inc.
PRINCIPAL INVESTIGATOR: [PLACEHOLDER]
VERSION: 1.0
DATE: 2024-03-15

IND Number: [NOT PROVIDED]
EudraCT Number: [NOT PROVIDED]
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-001"]
        },
        "background": {
            "name": "background",
            "title": "Background & Rationale",
            "content": """
CTX-4892 is a novel small molecule inhibitor of the PI3K/mTOR pathway. Preclinical 
studies in murine xenograft models demonstrated tumor regression at doses of 10-50 mg/kg.
The compound has a half-life of approximately 8 hours in rats.

No human pharmacokinetic data is available. The proposed starting dose of 25mg is based 
on allometric scaling from rat studies using a safety factor of 10.

Rationale for patient selection: Patients with solid tumors who have exhausted standard 
of care options represent an appropriate population for first-in-human dose escalation.
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        },
        "objectives": {
            "name": "objectives",
            "title": "Study Objectives & Endpoints",
            "content": """
PRIMARY OBJECTIVE:
- To determine the maximum tolerated dose (MTD) of CTX-4892

SECONDARY OBJECTIVES:
- To characterize the pharmacokinetic profile of CTX-4892
- To document antitumor activity

NOTE: No primary endpoint definition is provided. No statistical analysis plan is referenced.
The primary objective does not specify a timeframe or dose-limiting toxicity (DLT) assessment 
window. Recommended Phase II dose (RP2D) determination criteria are absent.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-002"]
        },
        "eligibility": {
            "name": "eligibility",
            "title": "Eligibility Criteria",
            "content": """
INCLUSION CRITERIA:
1. Age ≥ 18 years
2. Histologically confirmed advanced solid tumor
3. ECOG Performance Status 0-2
4. Adequate organ function:
   - ANC ≥ 1.5 x 10^9/L
   - Platelets ≥ 100 x 10^9/L
   - Creatinine ≤ 1.5 x ULN
5. Life expectancy ≥ 3 months

EXCLUSION CRITERIA:
1. Prior treatment with PI3K inhibitors
2. Active CNS metastases
3. Pregnancy or breastfeeding
4. Known HIV infection
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        },
        "study_design": {
            "name": "study_design",
            "title": "Study Design",
            "content": """
This is an open-label, dose escalation study using a 3+3 design.

DOSE LEVELS: 25mg, 50mg, 100mg, 200mg, 400mg QD oral administration

DOSE ESCALATION RULES:
- If 0/3 DLTs: escalate to next dose level
- If 1/3 DLTs: expand cohort to 6 patients
- If ≥2/3 or ≥2/6 DLTs: MTD exceeded, de-escalate

DLT ASSESSMENT WINDOW: [NOT SPECIFIED]

TREATMENT CYCLES: 28-day cycles. No maximum number of cycles defined.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-003"]
        },
        "safety_monitoring": {
            "name": "safety_monitoring",
            "title": "Safety Monitoring",
            "content": """
Adverse events will be graded per CTCAE v5.0.

DOSE MODIFICATIONS: [TABLE TO BE INSERTED]

STOPPING RULES: Study will be stopped if unexpected serious toxicity is observed.

Data Safety Monitoring Board (DSMB): Not planned for this Phase I study.

Serious Adverse Event reporting: Will follow applicable regulatory requirements.
IND Safety Reporting: 7-day reports for unexpected fatal/life-threatening SUSARs.
15-day reports for other unexpected serious suspected adverse reactions.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-004"]
        },
        "statistical_analysis": {
            "name": "statistical_analysis",
            "title": "Statistical Analysis Plan",
            "content": """
This is a Phase I study; no formal hypothesis testing is planned.
Safety and PK data will be summarized descriptively.

Sample size: Approximately 18-30 patients depending on DLTs observed.
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        }
    },
    "ground_truth_issues": [
        {
            "issue_id": "ISSUE-001",
            "category": "missing_element",
            "severity": "major",
            "description": "IND and EudraCT numbers are missing from the title page — required regulatory identifiers",
            "location": "title_page",
            "required_by": "ICH E6(R2) Section 6.1"
        },
        {
            "issue_id": "ISSUE-002",
            "category": "missing_element",
            "severity": "major",
            "description": "Primary endpoint not defined; DLT assessment window not specified; RP2D determination criteria absent",
            "location": "objectives",
            "required_by": "ICH E6(R2) Section 6.4"
        },
        {
            "issue_id": "ISSUE-003",
            "category": "missing_element",
            "severity": "critical",
            "description": "DLT assessment window is not specified — this is a critical omission for a dose escalation study",
            "location": "study_design",
            "required_by": "FDA Guidance for Phase I Studies"
        },
        {
            "issue_id": "ISSUE-004",
            "category": "missing_element",
            "severity": "major",
            "description": "Dose modification table is missing (placeholder only); stopping rules are vague with no specific criteria",
            "location": "safety_monitoring",
            "required_by": "ICH E6(R2) Section 6.8"
        }
    ]
}

# ─── PROTOCOL 2: Phase III Cardiovascular (MEDIUM TASK) ───────────────────────
PROTOCOL_002 = {
    "protocol_id": "PROTO-002",
    "title": "Phase III RCT of Vorixafen vs Warfarin for Stroke Prevention in AF",
    "sponsor": "CardioVance Therapeutics",
    "phase": "III",
    "sections": {
        "title_page": {
            "name": "title_page",
            "title": "Title Page",
            "content": """
PROTOCOL: VORTEX-3
TITLE: Randomized Controlled Trial of Vorixafen vs Warfarin for Stroke Prevention 
in Non-Valvular Atrial Fibrillation
SPONSOR: CardioVance Therapeutics
VERSION: 2.1 | DATE: 2024-06-01
IND: 145-882 | EudraCT: 2024-001234-56
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        },
        "background": {
            "name": "background",
            "title": "Background & Rationale",
            "content": """
Atrial fibrillation (AF) affects approximately 33 million people worldwide and is the 
leading cause of cardioembolic stroke. Warfarin, while effective, requires frequent INR 
monitoring and has a narrow therapeutic window.

Vorixafen is a direct thrombin inhibitor with predictable pharmacokinetics not requiring 
routine coagulation monitoring. Phase II data showed non-inferior stroke prevention with 
a favorable bleeding profile (major bleeding rate: 2.1% vs 3.4% for warfarin).
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        },
        "eligibility": {
            "name": "eligibility",
            "title": "Eligibility Criteria",
            "content": """
INCLUSION CRITERIA:
1. Age ≥ 18 years
2. Documented non-valvular AF (paroxysmal, persistent, or permanent)
3. CHA₂DS₂-VASc score ≥ 2
4. eGFR ≥ 30 mL/min/1.73m²
5. Able to provide written informed consent

EXCLUSION CRITERIA:
1. Mechanical heart valves
2. Active bleeding or high bleeding risk
3. Concomitant use of strong P-gp inhibitors
4. Severe hepatic impairment (Child-Pugh C)
5. Pregnancy
6. Prior stroke within 7 days  ← CONFLICT: inclusion allows CHA2DS2-VASc ≥2 (stroke history = 2pts)
   but exclusion does not address stable post-stroke patients (only acute <7 days)
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-005", "ISSUE-006"]
        },
        "study_design": {
            "name": "study_design",
            "title": "Study Design & Randomization",
            "content": """
DESIGN: Double-blind, double-dummy, randomized, active-controlled, non-inferiority trial

RANDOMIZATION: 1:1 ratio stratified by:
- CHA₂DS₂-VASc score (2-3 vs ≥4)
- Geographic region

BLINDING: Double-blind with matching placebos for both arms
- Vorixafen 150mg BID + warfarin placebo + sham INR monitoring
- Warfarin (target INR 2-3) + vorixafen placebo

SAMPLE SIZE: 8,000 patients (4,000 per arm)
Non-inferiority margin: HR ≤ 1.12 for primary endpoint
Power: 90% assuming 1.5%/year event rate, 3-year follow-up

NOTE: The non-inferiority margin of 1.12 retains only ~50% of warfarin's benefit 
vs placebo — this may not meet regulatory acceptability standards (typically ≤1.10
for stroke prevention trials per FDA guidance).
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-007"]
        },
        "endpoints": {
            "name": "endpoints",
            "title": "Endpoints",
            "content": """
PRIMARY ENDPOINT:
- Composite of stroke (ischemic or hemorrhagic) or systemic embolism at 24 months
  
SECONDARY ENDPOINTS:
1. All-cause mortality
2. Major bleeding (ISTH criteria)  
3. Net clinical benefit (primary endpoint + major bleeding)
4. Stroke severity (mRS at 90 days post-event)
5. Quality of life (EQ-5D-5L at 6, 12, 24 months)

SAFETY ENDPOINTS:
- All bleeding events (major, clinically relevant non-major, minor)
- Liver function abnormalities
- Acute coronary syndrome

MISSING: No adjudication committee for primary endpoint events is mentioned.
No definition of "systemic embolism" provided.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-008"]
        },
        "safety_monitoring": {
            "name": "safety_monitoring",
            "title": "Safety Monitoring",
            "content": """
DSMB: Independent DSMB will conduct pre-specified interim analyses at 25%, 50%, 75% 
of primary events. O'Brien-Fleming spending function for efficacy stopping.

STOPPING RULES:
- Efficacy: Cross O'Brien-Fleming boundary (p < 0.00001, 0.0014, 0.0094 at interim analyses)
- Harm: Predefined excess major bleeding (RR > 1.5, p < 0.01)
- Futility: Conditional power < 20%

SAE Reporting: Per ICH E6(R2) within 24 hours to sponsor, 7/15 days to regulatory authorities.
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        },
        "statistical_analysis": {
            "name": "statistical_analysis",
            "title": "Statistical Analysis Plan",
            "content": """
PRIMARY ANALYSIS: Modified ITT (mITT) — all randomized patients who received ≥1 dose

Non-inferiority test: One-sided 97.5% CI for HR; NI declared if upper bound ≤ 1.12

MISSING: No per-protocol (PP) sensitivity analysis described. 
ICH E9(R1) requires both mITT and PP analyses for NI trials.
Missing handling of patients who switch from warfarin due to subtherapeutic INR.

MULTIPLICITY: Hierarchical testing procedure for secondary endpoints not described.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-009", "ISSUE-010"]
        },
        "consent": {
            "name": "consent",
            "title": "Informed Consent",
            "content": """
Written informed consent will be obtained from all participants prior to any 
study-related procedures. The informed consent form will include all elements 
required by ICH E6(R2) and applicable regulations.

Re-consent will be required for protocol amendments that materially affect 
participant risk or study procedures.

For participants who lack capacity: legally authorized representative consent 
will be obtained per local regulations.
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        }
    },
    "ground_truth_issues": [
        {
            "issue_id": "ISSUE-005",
            "category": "eligibility_conflict",
            "severity": "major",
            "description": "CHA₂DS₂-VASc ≥2 inclusion allows stroke history patients, but exclusion only bars acute stroke (≤7 days) — creates ambiguity for stable post-stroke patients",
            "location": "eligibility",
            "required_by": "Protocol internal consistency"
        },
        {
            "issue_id": "ISSUE-006",
            "category": "missing_element",
            "severity": "minor",
            "description": "No washout period or transition strategy specified for patients switching from existing anticoagulation",
            "location": "eligibility",
            "required_by": "Clinical practice standards"
        },
        {
            "issue_id": "ISSUE-007",
            "category": "statistical_flaw",
            "severity": "critical",
            "description": "NI margin of 1.12 retains only ~50% of warfarin's vs-placebo benefit — regulatory guidance typically requires ≥50% effect retention (HR ≤ 1.10) for stroke prevention",
            "location": "study_design",
            "required_by": "FDA NI Trial Guidance 2016"
        },
        {
            "issue_id": "ISSUE-008",
            "category": "missing_element",
            "severity": "major",
            "description": "No clinical events adjudication committee described; 'systemic embolism' not defined — creates endpoint ascertainment bias risk",
            "location": "endpoints",
            "required_by": "ICH E6(R2) / FDA RCT Guidance"
        },
        {
            "issue_id": "ISSUE-009",
            "category": "statistical_flaw",
            "severity": "critical",
            "description": "Per-protocol sensitivity analysis absent — required by ICH E9(R1) for non-inferiority trials to confirm NI conclusion is robust",
            "location": "statistical_analysis",
            "required_by": "ICH E9(R1) Section 5.3"
        },
        {
            "issue_id": "ISSUE-010",
            "category": "statistical_flaw",
            "severity": "major",
            "description": "No multiplicity adjustment described for secondary endpoints hierarchy; no handling of warfarin arm INR non-compliance",
            "location": "statistical_analysis",
            "required_by": "ICH E9 / FDA Multiple Endpoints Guidance"
        }
    ]
}

# ─── PROTOCOL 3: Full Phase II/III Pediatric Immunology (HARD TASK) ───────────
PROTOCOL_003 = {
    "protocol_id": "PROTO-003",
    "title": "Phase II/III Adaptive Study of Belumosudil in Pediatric cGVHD",
    "sponsor": "Helix BioPharma",
    "phase": "II/III",
    "sections": {
        "title_page": {
            "name": "title_page",
            "title": "Title Page",
            "content": """
PROTOCOL: HELIX-cGVHD-P01
TITLE: Adaptive Phase II/III Study of Belumosudil Biosimilar (HLX-77) in 
Pediatric Chronic Graft-versus-Host Disease Refractory to ≥2 Prior Lines
SPONSOR: Helix BioPharma
PHASE: II/III Adaptive
VERSION: 1.3 | DATE: 2024-09-01
IND: 219-445 | Pediatric Study Plan (PIP): EMA/PIP/2024/1234
            """.strip(),
            "has_issues": False,
            "issue_ids": []
        },
        "background": {
            "name": "background",
            "title": "Background & Rationale",
            "content": """
Chronic graft-versus-host disease (cGVHD) remains a leading cause of non-relapse 
morbidity and mortality after allogeneic hematopoietic stem cell transplant (allo-HSCT). 
Pediatric cGVHD differs from adult disease in manifestations, scoring, and tolerability.

Belumosudil (ROCK2 inhibitor) received FDA approval for adult cGVHD (≥2 prior lines) 
in 2021. No pediatric pharmacokinetic or efficacy data exists. This study investigates 
HLX-77, a biosimilar candidate, in the pediatric population.

NOTE: Belumosudil is a small molecule, not a biologic — the term "biosimilar" is 
scientifically incorrect and potentially misleading to regulators and IRBs.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-011"]
        },
        "eligibility": {
            "name": "eligibility",
            "title": "Eligibility Criteria",
            "content": """
INCLUSION CRITERIA:
1. Age 2 to <18 years at enrollment
2. Confirmed cGVHD per 2014 NIH Consensus Criteria
3. ≥2 prior lines of systemic therapy for cGVHD
4. Karnofsky/Lansky performance score ≥ 60
5. Adequate organ function per protocol Appendix B [NOT ATTACHED]
6. Willing to use contraception (applicable to post-pubertal patients)

EXCLUSION CRITERIA:
1. Active acute GvHD
2. Relapsed underlying malignancy
3. Active uncontrolled infection
4. QTc > 480ms on screening ECG
5. Concurrent use of strong CYP3A4 inducers

MISSING: No lower age-specific organ function thresholds provided.
Age group 2-6 years may require different Lansky vs Karnofsky cutoffs.
Contraception requirement references "post-pubertal" without definition or 
pregnancy testing requirement specified for applicable patients.
No definition of "adequate" in reference to Appendix B (which is missing).
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-012", "ISSUE-013"]
        },
        "study_design": {
            "name": "study_design",
            "title": "Adaptive Study Design",
            "content": """
PHASE II: Open-label, single arm, 24 patients, primary endpoint ORR at Week 24
PHASE II→III DECISION: If ORR ≥ 30%, proceed to Phase III
PHASE III: Randomized 2:1 (HLX-77 vs best available therapy), 90 patients

ADAPTIVE ELEMENTS:
- Sample size re-estimation at 50% enrollment (Phase III)
- Possible dose adjustment based on PK/PD data (age-based dosing refinement)

DOSE:
- Adults (≥12 years, ≥40kg): 200mg BID (approved adult dose)
- Pediatric (<12 years or <40kg): Weight-based dosing TBD per PK modeling

PROBLEM: Pediatric dosing for <12 years is "TBD" — no dose rationale, 
no PK model referenced, no allometric scaling justification provided.
Phase II dosing for this subgroup is therefore undefined at protocol submission.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-014"]
        },
        "endpoints": {
            "name": "endpoints",
            "title": "Endpoints",
            "content": """
PHASE II PRIMARY: Overall Response Rate (ORR) per 2014 NIH cGVHD Response Criteria at Week 24
PHASE III PRIMARY: Failure-Free Survival (FFS) at 12 months
  - FFS = time to first of: cGVHD progression, non-relapse mortality, or new systemic therapy

SECONDARY ENDPOINTS (both phases):
1. Duration of response
2. Patient-reported outcomes (Lee Symptom Scale — adult version)
3. Corticosteroid dose reduction ≥ 50%
4. Overall survival

PEDIATRIC CONCERN: Lee Symptom Scale is validated for adults only. 
No pediatric-appropriate PRO instrument (e.g., PedsQL, Skindex-16 modified) 
is specified. FDA/EMA require age-appropriate COA instruments in pediatric studies.

ALSO: FFS definition includes "new systemic therapy" which could penalize 
temporary infections requiring steroids, conflating disease progression with 
standard supportive care.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-015", "ISSUE-016"]
        },
        "safety_monitoring": {
            "name": "safety_monitoring",
            "title": "Safety Monitoring",
            "content": """
DSMB: Independent DSMB with pediatric oncology, statistics, and bioethics representation
Meetings: After every 12 patients in Phase II, quarterly in Phase III

STOPPING RULES: Defined per DSMB charter (DSMB Charter referenced but not provided)

PEDIATRIC SAFETY SPECIFICS:
- Growth monitoring: Height/weight every 3 months
- Neurodevelopmental assessments: Annually (per Appendix C — NOT ATTACHED)
- Vaccine immunogenicity substudy: Optional, 20 patients

MISSING: 
- Pregnancy testing schedule for applicable patients not specified
- Long-term follow-up plan for pediatric-specific outcomes absent
- No pediatric-specific AE monitoring plan (children may manifest toxicity differently)
- Maximum cumulative steroid dose thresholds not defined
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-017", "ISSUE-018"]
        },
        "pharmacokinetics": {
            "name": "pharmacokinetics",
            "title": "Pharmacokinetics & Pharmacodynamics",
            "content": """
PK SAMPLING: Rich sampling in first 12 Phase II patients (per PK schedule, Appendix D)
Population PK model will be developed to support pediatric dose optimization.

PK PARAMETERS: Cmax, AUC0-24, t1/2, CL/F, Vd/F

BIOANALYTICAL METHOD: LC-MS/MS assay for HLX-77 plasma concentration
Validated per FDA Bioanalytical Method Guidance — LLOQ: 1.0 ng/mL

PBPK: No physiologically-based PK model referenced despite age range spanning 
2-18 years — significant developmental PK differences expected (ontogeny of 
CYP enzymes, body composition, renal maturation). FDA typically requires PBPK 
for such age span.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-019"]
        },
        "consent": {
            "name": "consent",
            "title": "Informed Consent & Assent",
            "content": """
PARENTAL/GUARDIAN CONSENT: Required for all participants under 18.
Legally authorized representative consent per local regulations.

CHILD ASSENT:
- Age 7-11: Written assent using age-appropriate language (Appendix E — NOT ATTACHED)
- Age ≥12: Full assent with option to independently consent per local law
- Age <7: Assent waived per IRB discretion

RE-CONSENT: Required for protocol amendments affecting risk/procedures

MISSING: No provision for what happens when a participant turns 18 during the study.
Transition from parental consent + assent to independent adult consent not addressed.
This is a common oversight in pediatric studies with longer follow-up.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-020"]
        },
        "statistical_analysis": {
            "name": "statistical_analysis",
            "title": "Statistical Analysis Plan",
            "content": """
PHASE II: Exact binomial 95% CI around ORR. Go/no-go decision: ORR ≥ 30% (null: 15%)
One-sided alpha = 0.10, power = 80%

PHASE III: Stratified log-rank test for FFS (strata: age group, cGVHD severity)
Sample size: 90 patients provides 80% power to detect HR = 0.55 (alpha = 0.05, two-sided)
assuming 12-month FFS of 30% in BAT arm.

ADAPTIVE ELEMENTS:
- Blinded sample size re-estimation at 50% information time
- Dose adaptation rule: If median PK AUC <50% of adult, increase dose in next cohort

MISSING: 
- No alpha-spending across Phase II and Phase III (type I error inflation in seamless design)
- Operating characteristics of adaptive design not described (simulation results absent)
- No multiplicity adjustment between Phase II/III primary endpoints
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-021", "ISSUE-022"]
        },
        "regulatory_strategy": {
            "name": "regulatory_strategy",
            "title": "Regulatory Considerations",
            "content": """
REGULATORY PATHWAY: FDA — Supplemental NDA to belumosudil NDA (213426)
EMA — Pending pediatric indication extension

ORPHAN DESIGNATION: Applied for (cGVHD in pediatric patients)
BREAKTHROUGH THERAPY: Not applied for

PEDIATRIC REQUIREMENTS:
- FDA PREA: Applicable — pediatric study required for supplement
- EMA PIP: Approved (referenced above)
- Written Request: Not sought (opportunity missed for pediatric exclusivity)

IMPORTANT MISSING ELEMENT: No bridging strategy described to justify HLX-77 
biosimilarity/comparability to reference belumosudil. For a "biosimilar" of a 
small molecule (which is inherently contradictory), no analytical comparability 
data or BE study is referenced.
            """.strip(),
            "has_issues": True,
            "issue_ids": ["ISSUE-023"]
        }
    },
    "ground_truth_issues": [
        {
            "issue_id": "ISSUE-011",
            "category": "regulatory_noncompliance",
            "severity": "major",
            "description": "Belumosudil is a small molecule — labeling it a 'biosimilar' is scientifically incorrect and will cause regulatory confusion; correct term is 'generic' or 'follow-on product'",
            "location": "background",
            "required_by": "FDA Biosimilar Guidance / scientific accuracy"
        },
        {
            "issue_id": "ISSUE-012",
            "category": "missing_element",
            "severity": "critical",
            "description": "Appendix B (organ function thresholds) is not attached — eligibility Criterion 5 references it but it is absent, making the protocol incomplete",
            "location": "eligibility",
            "required_by": "Protocol completeness"
        },
        {
            "issue_id": "ISSUE-013",
            "category": "eligibility_conflict",
            "severity": "major",
            "description": "Contraception requirement references 'post-pubertal patients' without definition; no pregnancy testing schedule specified for applicable female patients",
            "location": "eligibility",
            "required_by": "ICH E11(R1) / FDA Pediatric Studies Guidance"
        },
        {
            "issue_id": "ISSUE-014",
            "category": "dosing_error",
            "severity": "critical",
            "description": "Pediatric dose for patients <12 years is listed as 'TBD' — no defined dose means Phase II cannot proceed ethically in this subgroup",
            "location": "study_design",
            "required_by": "FDA Pediatric Rule 21 CFR 312"
        },
        {
            "issue_id": "ISSUE-015",
            "category": "regulatory_noncompliance",
            "severity": "major",
            "description": "Lee Symptom Scale is an adult-validated instrument; no pediatric-appropriate PRO tool specified — FDA/EMA require age-validated COA instruments",
            "location": "endpoints",
            "required_by": "FDA Patient-Focused Drug Development Guidance"
        },
        {
            "issue_id": "ISSUE-016",
            "category": "eligibility_conflict",
            "severity": "minor",
            "description": "FFS composite endpoint includes 'new systemic therapy' which conflates disease progression with supportive care (e.g., antibiotics with steroids) — needs precise definition",
            "location": "endpoints",
            "required_by": "Protocol internal consistency"
        },
        {
            "issue_id": "ISSUE-017",
            "category": "missing_element",
            "severity": "major",
            "description": "Appendices C and D are referenced but not attached; no pregnancy testing schedule for applicable patients",
            "location": "safety_monitoring",
            "required_by": "Protocol completeness"
        },
        {
            "issue_id": "ISSUE-018",
            "category": "safety_gap",
            "severity": "major",
            "description": "No long-term pediatric follow-up plan; no pediatric-specific toxicity monitoring plan; missing DSMB charter",
            "location": "safety_monitoring",
            "required_by": "ICH E11(R1) / FDA Pediatric Safety Guidance"
        },
        {
            "issue_id": "ISSUE-019",
            "category": "safety_gap",
            "severity": "major",
            "description": "No PBPK modeling despite 2–18 year age range with major developmental PK differences — FDA typically requires this for pediatric programs spanning early childhood",
            "location": "pharmacokinetics",
            "required_by": "FDA PBPK Guidance / ICH E11(R1)"
        },
        {
            "issue_id": "ISSUE-020",
            "category": "consent_violation",
            "severity": "major",
            "description": "No procedure for participants who turn 18 during the study — transition from parental consent to independent adult consent not addressed",
            "location": "consent",
            "required_by": "ICH E6(R2) / 21 CFR 50"
        },
        {
            "issue_id": "ISSUE-021",
            "category": "statistical_flaw",
            "severity": "critical",
            "description": "Seamless adaptive Phase II/III design lacks alpha-spending across phases — type I error inflation unaddressed in a regulatory submission context",
            "location": "statistical_analysis",
            "required_by": "FDA Adaptive Design Guidance 2019"
        },
        {
            "issue_id": "ISSUE-022",
            "category": "statistical_flaw",
            "severity": "major",
            "description": "No simulation results describing operating characteristics of the adaptive design — FDA requires this for adaptive trial submissions",
            "location": "statistical_analysis",
            "required_by": "FDA Adaptive Design Guidance 2019 Section IV.C"
        },
        {
            "issue_id": "ISSUE-023",
            "category": "regulatory_noncompliance",
            "severity": "critical",
            "description": "No bioequivalence or analytical comparability study referenced to bridge HLX-77 to reference belumosudil — fundamental regulatory requirement for any follow-on product",
            "location": "regulatory_strategy",
            "required_by": "FDA 505(j) / 505(b)(2) requirements"
        }
    ]
}

# Master registry
PROTOCOLS: Dict[str, Any] = {
    "PROTO-001": PROTOCOL_001,
    "PROTO-002": PROTOCOL_002,
    "PROTO-003": PROTOCOL_003,
}

TASK_PROTOCOL_MAP = {
    "task_easy": "PROTO-001",
    "task_medium": "PROTO-002",
    "task_hard": "PROTO-003",
}

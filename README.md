# 🏥 ClinicalTrialReviewEnv

[![openenv](https://img.shields.io/badge/openenv-1.0-blue)](https://huggingface.co/spaces/openenv/clinical-trial-review)
[![HuggingFace](https://img.shields.io/badge/🤗-Spaces-yellow)](https://huggingface.co/spaces/openenv/clinical-trial-review)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An **OpenEnv-compliant environment** for training and evaluating AI agents on **clinical trial protocol review** — a high-stakes, real-world task performed daily by regulatory affairs specialists, clinical research associates, and IRB reviewers.

---

## Motivation

Clinical trial protocols are dense, multi-section regulatory documents that must comply with ICH E6(R2) GCP guidelines, FDA guidance, and EMA requirements. Errors in protocols — missing endpoint definitions, eligibility conflicts, underpowered statistical designs, or absent safety monitoring plans — can delay drug development, expose patients to risk, or cause regulatory rejection.

Protocol review is currently a bottleneck: scarce experts, high cognitive load, and inconsistent standards. This environment provides:

- **A benchmark** for evaluating LLMs and agents on real regulatory reasoning
- **A training ground** for RL agents to learn systematic document review skills
- **A testbed** for multi-step reasoning, information gathering, and structured decision-making

---

## Environment Description

The agent acts as a regulatory reviewer examining clinical trial protocols. Each episode presents a protocol document divided into sections (title page, background, eligibility, endpoints, etc.). The agent must:

1. **Navigate** sections strategically
2. **Identify** protocol issues (missing elements, conflicts, flaws)
3. **Flag** issues with category, severity, description, and location
4. **Submit** a complete review within a step budget

### Real-World Domain

Protocols follow real ICH E6(R2) structure and contain authentic issues drawn from:
- FDA Warning Letters and Complete Response Letters
- Published protocol amendments and deviations
- Common GCP audit findings

---

## Action Space

| Action Type | Parameters | Description |
|------------|-----------|-------------|
| `read_section` | `section_name: str` | Navigate to and read a protocol section |
| `raise_flag` | `flag: {category, severity, description, location}` | Flag an identified issue |
| `clear_flag` | `flag_id: str` | Remove a previously raised flag (false positive correction) |
| `submit_review` | — | Finalize and submit the review (ends episode) |
| `request_clarification` | `clarification_query: str` | Get a hint about current section (costs a step) |

**Flag Categories:** `missing_element` · `eligibility_conflict` · `safety_gap` · `dosing_error` · `consent_violation` · `statistical_flaw` · `regulatory_noncompliance`

**Flag Severities:** `critical` · `major` · `minor`

---

## Observation Space

```python
Observation(
    protocol_id: str,              # e.g. "PROTO-001"
    task_id: str,                  # e.g. "task_easy"
    task_description: str,         # Full task instructions
    document_section: str,         # Currently viewed section name
    document_text: str,            # Full text of current section
    available_sections: List[str], # All section names in protocol
    sections_reviewed: List[str],  # Sections agent has visited
    flags_raised: List[Flag],      # All flags raised so far
    step_number: int,
    max_steps: int,
    clarifications_used: int,
    done: bool,
    info: dict,                    # Metadata (protocol title, phase, etc.)
)
```

---

## Tasks

### Task 1 — Missing Required Elements (Easy)
**Protocol:** Phase I Dose Escalation Study (PROTO-001)  
**Max Steps:** 10  
**Ground Truth Issues:** 4 (1 critical, 2 major, 1 minor)  
**Objective:** Identify all missing required elements per ICH E6(R2) GCP  
**Expected Baseline Score:** ~0.72

The protocol is missing IND numbers, primary endpoint definitions, a DLT assessment window, and a dose modification table. A focused agent that reads all sections and correctly categorizes findings should score >0.85.

### Task 2 — Eligibility & Statistical Conflicts (Medium)
**Protocol:** Phase III Cardiovascular RCT (PROTO-002)  
**Max Steps:** 15  
**Ground Truth Issues:** 6 (2 critical, 3 major, 1 minor)  
**Objective:** Find eligibility criteria conflicts AND statistical design flaws  
**Expected Baseline Score:** ~0.54

Issues include a non-inferiority margin that fails to retain 50% of the reference drug's effect, a missing per-protocol analysis required by ICH E9(R1), and eligibility criteria with ambiguous post-stroke patient handling. Requires multi-category awareness.

### Task 3 — Full Safety & Compliance Audit (Hard)
**Protocol:** Adaptive Phase II/III Pediatric cGVHD Trial (PROTO-003)  
**Max Steps:** 25  
**Ground Truth Issues:** 13 (4 critical, 7 major, 2 minor)  
**Objective:** Comprehensive audit across all 9 sections, all issue categories  
**Expected Baseline Score:** ~0.31

A complex, multi-layered pediatric adaptive trial with issues spanning regulatory misclassification (calling a small molecule a "biosimilar"), undefined pediatric dosing, missing PBPK modeling, adult-only PRO instruments in a pediatric study, adaptive design alpha-spending errors, and missing transition-to-adulthood consent procedures. Even frontier models will miss several issues.

---

## Reward Function

The reward is **dense** — providing signal throughout the episode, not just at submission:

| Signal | Value | Trigger |
|--------|-------|---------|
| Navigate to new section with issues | +0.04 | `read_section` on unread section that has GT issues |
| Navigate to new section (no issues) | +0.01 | `read_section` on clean section |
| Re-read section | -0.01 | Inefficiency penalty |
| True positive flag (critical) | up to +0.15 | Flag matches GT critical issue |
| True positive flag (major) | up to +0.08 | Flag matches GT major issue |
| True positive flag (minor) | up to +0.03 | Flag matches GT minor issue |
| False positive flag | -0.03 | Flag doesn't match any GT issue |
| Clarification request | -0.02 | Information cost |
| Submission score (terminal) | score × 0.5 | Final score on episode end |
| Timeout | -0.05 | Running out of steps |

**Partial credit:** Description quality and category accuracy both contribute. An agent that finds the right section and category but gives a vague description gets ~40% credit for that issue.

---

## Grader Design

Each grader is **deterministic** and uses:
- **Weighted recall** (critical = 3× weight for hard task)
- **Fuzzy description matching** (keyword overlap + sequence similarity)
- **Location matching** (section must be correct)
- **Precision penalty** (false positive rate)
- **Efficiency bonus** (for submitting with steps remaining)
- **Coverage score** (hard task penalizes not reading enough sections)

Grader `grade()` calls are fully reproducible given the same flag list.

---

## Baseline Scores

Run with GPT-4o (temperature=0.1, seed=42):

| Task | Score | TP | FP | FN | Critical Found |
|------|-------|----|----|----|-|
| task_easy | 0.72 | 3/4 | 1 | 1 | 1/1 |
| task_medium | 0.54 | 4/6 | 2 | 2 | 1/2 |
| task_hard | 0.31 | 5/13 | 3 | 8 | 1/4 |
| **Average** | **0.52** | | | | |

---

## Setup & Usage

### Local (Python)

```bash
# Clone
git clone https://huggingface.co/spaces/openenv/clinical-trial-review
cd clinical-trial-review

# Install
pip install -r requirements.txt

# Run environment directly
python -c "
from env import ClinicalTrialReviewEnv, Action
env = ClinicalTrialReviewEnv('task_easy')
obs = env.reset()
print(obs.available_sections)
obs, reward, done, info = env.step(Action(action_type='read_section', section_name='title_page'))
print(obs.document_text[:200])
"

# Run tests
python -m pytest tests/ -v

# Run baseline (requires OPENAI_API_KEY)
export OPENAI_API_KEY=your_key
python baseline/run_baseline.py
```

### Docker

```bash
# Build
docker build -t clinical-trial-review .

# Run
docker run -p 7860:7860 clinical-trial-review

# API available at http://localhost:7860
# Docs at http://localhost:7860/docs
```

### API Usage

```bash
# Start episode
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task_medium"}'

# Execute action
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "action": {
      "action_type": "read_section",
      "section_name": "eligibility"
    }
  }'

# Validate spec compliance
curl http://localhost:7860/validate
```

### HuggingFace Spaces

The environment is deployed at: `https://huggingface.co/spaces/openenv/clinical-trial-review`

---

## Project Structure

```
clinical-trial-review/
├── openenv.yaml              # OpenEnv spec metadata
├── app.py                    # FastAPI application (HF Spaces entry point)
├── requirements.txt
├── Dockerfile
├── env/
│   ├── __init__.py
│   ├── models.py             # Pydantic: Observation, Action, Reward, EpisodeState
│   ├── environment.py        # ClinicalTrialReviewEnv (reset/step/state)
│   └── protocols.py          # Protocol corpus with ground truth annotations
├── graders/
│   ├── __init__.py
│   └── graders.py            # EasyGrader, MediumGrader, HardGrader
├── baseline/
│   └── run_baseline.py       # OpenAI API baseline inference script
└── tests/
    └── test_environment.py   # Full test suite
```

---

## OpenEnv Compliance

- ✅ Typed `Observation`, `Action`, `Reward`, `EpisodeState` Pydantic models
- ✅ `step(action) → (observation, reward, done, info)`
- ✅ `reset() → observation`
- ✅ `state() → EpisodeState`
- ✅ `openenv.yaml` with full metadata
- ✅ 3 tasks: easy → medium → hard
- ✅ Scores in [0.0, 1.0]
- ✅ Dense reward function with partial progress signals
- ✅ Deterministic graders
- ✅ Working Dockerfile
- ✅ HF Spaces deployment
- ✅ Baseline inference script

---

## License

MIT License. Protocol content is synthetic, created for benchmarking purposes only.

---

## Citation

```bibtex
@software{clinical_trial_review_env,
  title  = {ClinicalTrialReviewEnv: An OpenEnv Environment for Clinical Trial Protocol Review},
  year   = {2024},
  url    = {https://huggingface.co/spaces/openenv/clinical-trial-review},
}
```

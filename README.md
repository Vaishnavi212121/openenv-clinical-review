---
title: Clinical Trial Review
emoji: 🏥
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 7860
---

# 🏥 ClinicalTrialReviewEnv

[![openenv](https://img.shields.io/badge/openenv-1.0-blue)](https://huggingface.co/spaces/Vaishu901821/clinical-trial-review)
[![HuggingFace](https://img.shields.io/badge/🤗-Spaces-yellow)](https://huggingface.co/spaces/Vaishu901821/clinical-trial-review)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

An **OpenEnv-compliant environment** for training and evaluating AI agents on **clinical trial protocol review** — a high-stakes, real-world task performed daily by regulatory affairs specialists, clinical research associates, and IRB reviewers.

---

## 🚀 Quick Submission Links
* **GitHub Repository**: [https://github.com/Vaishnavi212121/openenv-clinical-review](https://github.com/Vaishnavi212121/openenv-clinical-review)
* **Hugging Face Space**: [https://huggingface.co/spaces/Vaishu901821/clinical-trial-review](https://huggingface.co/spaces/Vaishu901821/clinical-trial-review)

---

## Motivation
Clinical trial protocols are dense regulatory documents that must comply with ICH E6(R2) GCP guidelines. Errors such as missing endpoint definitions or eligibility conflicts can delay drug development or expose patients to risk. 

This environment provides:
- **A benchmark** for evaluating LLMs on regulatory reasoning.
- **A training ground** for RL agents to learn systematic document review.
- **A testbed** for multi-step reasoning and structured decision-making.

---

## Environment Description
The agent acts as a regulatory reviewer. Each episode presents a protocol divided into sections (Title Page, Eligibility, Endpoints, etc.). The agent must:
1. **Navigate** sections strategically.
2. **Identify** protocol issues (missing elements, conflicts, flaws).
3. **Flag** issues with category, severity, and description.
4. **Submit** the review within the step budget.

---

## Tasks
### Task 1 — Missing Required Elements (Easy)
Identify missing elements like IND numbers and DLT windows in a Phase I Oncology protocol.

### Task 2 — Eligibility & Statistical Conflicts (Medium)
Detect conflicts between inclusion/exclusion criteria and identify statistical flaws in a Phase III RCT.

### Task 3 — Full Safety & Compliance Audit (Hard)
Comprehensive audit of a pediatric adaptive trial involving complex regulatory misclassifications and dosing errors.

---

## Action & Observation Space
The environment uses **Pydantic-validated models** for strict type compliance:
- **Actions**: `read_section`, `raise_flag`, `clear_flag`, `submit_review`, `request_clarification`.
- **Observations**: Current section text, available sections, flags raised, and progress metadata.

---

## Setup & Local Testing

### 1. Installation
```bash
git clone [https://github.com/Vaishnavi212121/openenv-clinical-review](https://github.com/Vaishnavi212121/openenv-clinical-review)
cd openenv-clinical-review
pip install -r requirements.txt

2. Run Local Test
Bash
python test_local.py
3. OpenEnv Deployment
Bash
openenv push
OpenEnv Compliance
✅ Typed Pydantic models (Observation, Action, Reward)

✅ Deterministic grader logic

✅ Dense reward function with partial credit

✅ openenv.yaml metadata compliance

✅ 3 difficulty tiers (Easy, Medium, Hard)

License
MIT License. Protocol content is synthetic, created for benchmarking purposes only.


### **Final Checklist**
1. **Save** the README.md.
2. **Run** `openenv push` in your terminal.
3. **Submit** both the GitHub and Hugging Face URLs to the [Scaler Hackathon Page](https://www.scaler.com/school-of-technology/meta-pytorch-hackathon) now.
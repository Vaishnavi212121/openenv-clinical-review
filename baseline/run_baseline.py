"""
Baseline Inference Script — ClinicalTrialReviewEnv
Uses OpenAI API client (compatible with any OpenAI-compatible endpoint).
Reads credentials from environment variables.

Usage:
    export OPENAI_API_KEY=your_key_here
    export OPENAI_BASE_URL=https://api.openai.com/v1   # optional
    export OPENAI_MODEL=gpt-4o                          # optional
    python baseline/run_baseline.py

Reproduces baseline scores across all 3 tasks.
"""

import os
import sys
import json
import time
from typing import Any, Dict, List

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from env import ClinicalTrialReviewEnv, Action

# ─── Config ───────────────────────────────────────────────────────────────────

API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
TASK_IDS = ["task_easy", "task_medium", "task_hard"]
SEED = 42


# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert regulatory affairs specialist and clinical research associate 
with deep knowledge of ICH E6(R2) GCP guidelines, FDA guidance documents, and EMA regulations.

You are reviewing clinical trial protocols to identify issues. You interact with an environment 
through structured JSON actions.

AVAILABLE ACTIONS (respond with exactly one JSON action per turn):

1. Read a section:
{"action_type": "read_section", "section_name": "<name>"}

2. Raise a flag for an issue found:
{"action_type": "raise_flag", "flag": {
  "category": "<missing_element|eligibility_conflict|safety_gap|dosing_error|consent_violation|statistical_flaw|regulatory_noncompliance>",
  "severity": "<critical|major|minor>",
  "description": "<clear description of the issue>",
  "location": "<section_name>"
}}

3. Submit your review when done:
{"action_type": "submit_review"}

STRATEGY:
- Read each available section systematically
- Raise flags for genuine regulatory or scientific issues
- Be specific in descriptions — reference the relevant guideline when possible
- Use correct severity: critical=patient safety or regulatory hold risk, major=significant compliance gap, minor=documentation/clarity issue
- Submit when you've reviewed all relevant sections

Respond with ONLY valid JSON — no preamble, no explanation outside JSON."""


def build_user_message(obs_dict: Dict[str, Any], history: List[Dict]) -> str:
    """Build the user message with current observation."""
    flags_summary = ""
    if obs_dict.get("flags_raised"):
        flags_summary = f"\n\nFLAGS RAISED SO FAR ({len(obs_dict['flags_raised'])}):\n"
        for f in obs_dict["flags_raised"]:
            flags_summary += f"  [{f['flag_id']}] {f['severity'].upper()} {f['category']}: {f['description'][:80]}...\n"

    sections_info = f"Reviewed: {obs_dict['sections_reviewed']} | Available: {obs_dict['available_sections']}"
    
    return f"""=== CLINICAL PROTOCOL REVIEW ===
Task: {obs_dict['task_description'][:200]}...

Protocol ID: {obs_dict['protocol_id']} | Step: {obs_dict['step_number']}/{obs_dict['max_steps']}
{sections_info}

=== CURRENT SECTION: {obs_dict['document_section']} ===
{obs_dict['document_text']}
{flags_summary}

What is your next action? (JSON only)"""


def run_agent(client: OpenAI, task_id: str) -> Dict[str, Any]:
    """Run the baseline agent on a single task."""
    print(f"\n{'='*60}")
    print(f"Running task: {task_id}")
    print('='*60)

    env = ClinicalTrialReviewEnv(task_id=task_id)
    obs = env.reset()
    obs_dict = obs.model_dump()

    conversation_history: List[Dict] = []
    task_result = None
    total_reward = 0.0
    step = 0

    while not obs_dict.get("done", False):
        user_msg = build_user_message(obs_dict, conversation_history)
        conversation_history.append({"role": "user", "content": user_msg})

        # Call LLM
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    *conversation_history[-10:],  # Last 10 turns for context window management
                ],
                temperature=0.1,
                seed=SEED,
                max_tokens=512,
            )
            raw = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"  [ERROR] API call failed: {e}")
            break

        # Parse action
        try:
            # Handle potential markdown fences
            clean = raw.replace("```json", "").replace("```", "").strip()
            action_dict = json.loads(clean)
            action = Action(**action_dict)
        except Exception as e:
            print(f"  [WARN] Invalid action JSON: {e} | Raw: {raw[:100]}")
            # Default fallback
            if obs_dict["sections_reviewed"]:
                unread = [s for s in obs_dict["available_sections"] 
                         if s not in obs_dict["sections_reviewed"]]
                if unread:
                    action = Action(action_type="read_section", section_name=unread[0])
                else:
                    action = Action(action_type="submit_review")
            else:
                action = Action(action_type="read_section", 
                               section_name=obs_dict["available_sections"][0])

        # Execute action
        obs, reward, done, info = env.step(action)
        obs_dict = obs.model_dump()
        total_reward += reward.value
        step += 1

        print(f"  Step {step:2d} | {action.action_type:30s} | reward={reward.value:+.3f} | "
              f"cumulative={reward.cumulative:+.4f}")

        conversation_history.append({"role": "assistant", "content": raw})

        if done and "task_result" in info:
            task_result = info["task_result"]
        
        time.sleep(0.3)  # Rate limiting courtesy

    if task_result is None:
        task_result = env._compute_final_score().model_dump()

    print(f"\n  ✅ TASK COMPLETE")
    print(f"     Score:      {task_result['score']:.4f}")
    print(f"     TP/FP/FN:   {task_result['true_positives']}/{task_result['false_positives']}/{task_result['false_negatives']}")
    print(f"     Critical:   {task_result['critical_issues_found']}/{task_result['critical_issues_total']}")
    print(f"     Steps used: {task_result['steps_used']}/{task_result['max_steps']}")
    print(f"     Passed:     {task_result['passed']}")

    return {
        "task_id": task_id,
        "score": task_result["score"],
        "task_result": task_result,
        "steps": step,
        "total_reward": round(total_reward, 4),
    }


def main():
    if not API_KEY:
        print("ERROR: OPENAI_API_KEY not set.")
        print("  export OPENAI_API_KEY=your_key_here")
        sys.exit(1)

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    print(f"Baseline Run — ClinicalTrialReviewEnv")
    print(f"Model: {MODEL}")
    print(f"Tasks: {TASK_IDS}")

    results = []
    for task_id in TASK_IDS:
        result = run_agent(client, task_id)
        results.append(result)

    print("\n" + "="*60)
    print("BASELINE RESULTS SUMMARY")
    print("="*60)
    print(f"{'Task':<20} {'Score':>8} {'Steps':>8} {'Passed':>8}")
    print("-"*50)
    for r in results:
        print(f"{r['task_id']:<20} {r['score']:>8.4f} {r['steps']:>8} {str(r['task_result']['passed']):>8}")

    avg_score = sum(r["score"] for r in results) / len(results)
    print("-"*50)
    print(f"{'AVERAGE':<20} {avg_score:>8.4f}")
    print("="*60)

    # Save results
    with open("baseline_results.json", "w") as f:
        json.dump({
            "model": MODEL,
            "results": results,
            "average_score": avg_score,
        }, f, indent=2)
    print("\nResults saved to baseline_results.json")


if __name__ == "__main__":
    main()

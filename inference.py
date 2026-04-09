#!/usr/bin/env python3
"""
Inference Script for ClinicalTrialReviewEnv
Uses the hackathon's provided LLM proxy (API_BASE_URL + API_KEY)
Makes actual API calls through their proxy
"""

import os
import sys
import json

# Add repo to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get API credentials from environment (provided by hackathon)
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ.get("MODEL", "gpt-4o")

print(f"[INFO] Using API_BASE_URL: {API_BASE_URL}", flush=True)
print(f"[INFO] Using MODEL: {MODEL}", flush=True)
sys.stdout.flush()

# Import OpenAI client to use their proxy
try:
    from openai import OpenAI
except ImportError:
    print("[ERROR] openai package not installed", flush=True)
    sys.exit(1)

# Import environment
try:
    from environment import ClinicalTrialReviewEnv
    from models import Action
except ImportError:
    from env.environment import ClinicalTrialReviewEnv
    from env.models import Action


def run_task_with_llm(task_id: str = "task_easy"):
    """Run task using LLM through the hackathon's proxy."""
    
    print(f"[START] task={task_id}", flush=True)
    sys.stdout.flush()
    
    try:
        # Initialize OpenAI client with hackathon's proxy
        # CRITICAL: Use the provided API_BASE_URL and API_KEY
        client = OpenAI(
            api_key=API_KEY,
            base_url=API_BASE_URL
        )
        
        # Create environment
        env = ClinicalTrialReviewEnv(task_id=task_id)
        obs = env.reset()
        
        print(f"[INFO] Protocol: {obs.protocol_id}, Sections: {len(obs.available_sections)}", flush=True)
        sys.stdout.flush()
        
        step_count = 0
        done = False
        
        # Build system prompt for the LLM
        system_prompt = """You are an expert regulatory affairs specialist reviewing clinical trial protocols.
You will receive observations about a clinical trial protocol and must decide what action to take.
You can:
1. read_section: Navigate to a protocol section
2. raise_flag: Flag an issue found
3. submit_review: Submit your review when done

Respond with valid JSON with the action format."""
        
        # Simple strategy: read sections and submit
        while not done and step_count < obs.max_steps:
            step_count += 1
            
            # Build observation message
            obs_message = f"""
Current Protocol: {obs.protocol_id}
Current Section: {obs.document_section}
Sections Read: {len(obs.sections_reviewed)}
Available Sections: {obs.available_sections}
Step: {step_count}/{obs.max_steps}

Section Content (first 200 chars):
{obs.document_text[:200]}

What action should you take next? Respond with JSON like:
{{"action_type": "read_section", "section_name": "..."}}, or
{{"action_type": "submit_review"}}
"""
            
            # Call LLM through the HACKATHON'S PROXY
            # This is the critical part - making the API call through their endpoint
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": obs_message}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                
                # Parse LLM response
                llm_response = response.choices[0].message.content.strip()
                
                # Try to extract JSON
                try:
                    action_dict = json.loads(llm_response)
                except json.JSONDecodeError:
                    # If LLM doesn't return valid JSON, default to reading next section
                    if step_count < len(obs.available_sections):
                        action_dict = {
                            "action_type": "read_section",
                            "section_name": obs.available_sections[step_count % len(obs.available_sections)]
                        }
                    else:
                        action_dict = {"action_type": "submit_review"}
                
                # Execute action
                action = Action(**action_dict)
                obs, reward, done, info = env.step(action)
                
                # Print step result
                print(
                    f"[STEP] step={step_count} reward={reward.value:.4f} cumulative={reward.cumulative:.4f}",
                    flush=True
                )
                sys.stdout.flush()
                
            except Exception as e:
                print(f"[INFO] LLM call error (step {step_count}): {str(e)}", flush=True)
                # Fallback: just read next section or submit
                if step_count < len(obs.available_sections):
                    action = Action(
                        action_type="read_section",
                        section_name=obs.available_sections[step_count % len(obs.available_sections)]
                    )
                else:
                    action = Action(action_type="submit_review")
                
                obs, reward, done, info = env.step(action)
                print(
                    f"[STEP] step={step_count} reward={reward.value:.4f} cumulative={reward.cumulative:.4f}",
                    flush=True
                )
                sys.stdout.flush()
        
        # Get final score
        final_score = env._compute_final_score()
        
        print(
            f"[END] task={task_id} score={final_score.score:.4f} steps={step_count} passed={final_score.passed}",
            flush=True
        )
        sys.stdout.flush()
        
        return {
            "task_id": task_id,
            "score": final_score.score,
            "steps": step_count,
            "passed": final_score.passed,
        }
    
    except Exception as e:
        print(f"[ERROR] {task_id}: {str(e)}", flush=True)
        sys.stdout.flush()
        
        # Still print END block even on error
        print(f"[END] task={task_id} score=0.0000 steps=0 passed=False", flush=True)
        sys.stdout.flush()
        
        return {"task_id": task_id, "error": str(e)}


def main():
    """Run inference on all tasks using the hackathon's LLM proxy."""
    
    print("=" * 60, flush=True)
    print("ClinicalTrialReviewEnv - LLM-Based Inference", flush=True)
    print("=" * 60, flush=True)
    sys.stdout.flush()
    
    # Check that we have API credentials
    if not API_KEY:
        print("[WARNING] API_KEY not set in environment", flush=True)
        print("[WARNING] Using default/empty credentials", flush=True)
        sys.stdout.flush()
    
    tasks = ["task_easy", "task_medium", "task_hard"]
    results = []
    
    # Run each task
    for task_id in tasks:
        print()
        sys.stdout.flush()
        
        result = run_task_with_llm(task_id)
        results.append(result)
        
        print()
        sys.stdout.flush()
    
    # Summary
    print("=" * 60, flush=True)
    print("Summary", flush=True)
    print("=" * 60, flush=True)
    
    for result in results:
        if "error" not in result:
            print(
                f"{result['task_id']}: score={result['score']:.4f}, "
                f"steps={result['steps']}, passed={result['passed']}",
                flush=True
            )
        else:
            print(f"{result['task_id']}: ERROR - {result['error']}", flush=True)
    
    if results and any("error" not in r for r in results):
        avg_score = sum(r.get("score", 0) for r in results if "error" not in r) / len([r for r in results if "error" not in r])
        print(f"Average Score: {avg_score:.4f}", flush=True)
    
    print()
    sys.stdout.flush()


if __name__ == "__main__":
    main()

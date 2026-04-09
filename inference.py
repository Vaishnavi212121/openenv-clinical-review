"""
Inference Script for ClinicalTrialReviewEnv
Prints structured output for hackathon validator: [START]/[STEP]/[END] blocks
"""

import sys
import os

# Add repo to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from environment import ClinicalTrialReviewEnv
    from models import Action
except ImportError:
    from env.environment import ClinicalTrialReviewEnv
    from env.models import Action


def run_inference_task(task_id: str = "task_easy"):
    """
    Run a single task and print structured output.
    
    Output format required by hackathon validator:
    [START] task=TASK_ID
    [STEP] step=N reward=R cumulative=C
    [END] task=TASK_ID score=S steps=N
    """
    
    try:
        # Print START marker
        print(f"[START] task={task_id}", flush=True)
        
        # Create environment
        env = ClinicalTrialReviewEnv(task_id=task_id)
        obs = env.reset()
        
        print(f"[INFO] Protocol: {obs.protocol_id}, Sections: {len(obs.available_sections)}, Max steps: {obs.max_steps}", flush=True)
        
        step_count = 0
        done = False
        
        # Run a simple strategy: read all sections then submit
        while not done and step_count < obs.max_steps:
            if step_count < len(obs.available_sections):
                # Read next section
                section_name = obs.available_sections[step_count % len(obs.available_sections)]
                action = Action(
                    action_type="read_section",
                    section_name=section_name
                )
            else:
                # Submit review when done reading
                action = Action(action_type="submit_review")
            
            # Execute action
            obs, reward, done, info = env.step(action)
            step_count += 1
            
            # Print STEP marker (required by validator)
            print(
                f"[STEP] step={step_count} reward={reward.value:.4f} cumulative={reward.cumulative:.4f}",
                flush=True
            )
        
        # Get final score
        final_state = env.state()
        final_score = env._compute_final_score()
        
        # Print END marker (required by validator)
        print(
            f"[END] task={task_id} score={final_score.score:.4f} steps={step_count} passed={final_score.passed}",
            flush=True
        )
        
        return {
            "task_id": task_id,
            "score": final_score.score,
            "steps": step_count,
            "passed": final_score.passed,
            "true_positives": final_score.true_positives,
            "false_positives": final_score.false_positives,
        }
    
    except Exception as e:
        print(f"[ERROR] task={task_id} error={str(e)}", flush=True)
        return {"task_id": task_id, "error": str(e)}


def main():
    """Run inference on all tasks."""
    
    print("=" * 60, flush=True)
    print("ClinicalTrialReviewEnv - Inference Runner", flush=True)
    print("=" * 60, flush=True)
    print()
    
    tasks = ["task_easy", "task_medium", "task_hard"]
    results = []
    
    # Run each task
    for task_id in tasks:
        print()
        result = run_inference_task(task_id)
        results.append(result)
        print()
    
    # Summary
    print("=" * 60, flush=True)
    print("Summary", flush=True)
    print("=" * 60, flush=True)
    
    for result in results:
        if "error" not in result:
            print(
                f"{result['task_id']}: score={result['score']:.4f}, "
                f"steps={result['steps']}, passed={result['passed']}, "
                f"tp={result['true_positives']}, fp={result['false_positives']}",
                flush=True
            )
        else:
            print(f"{result['task_id']}: ERROR - {result['error']}", flush=True)
    
    avg_score = sum(r.get("score", 0) for r in results if "error" not in r) / len(results)
    print()
    print(f"Average Score: {avg_score:.4f}", flush=True)
    print()


if __name__ == "__main__":
    main()

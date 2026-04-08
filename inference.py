import os
import httpx
import json

# These environment variables are required by the Scaler validator
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

def run_inference():
    print(f"--- Starting Inference for {MODEL_NAME} ---")
    
    # 1. Reset the environment
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        reset_response = client.post("/reset", json={"task_id": "task_easy"})
        if reset_response.status_code != 200:
            print(f"Failed to reset: {reset_response.text}")
            return
            
        data = reset_response.json()
        session_id = data["session_id"]
        print(f"Session Started: {session_id}")

        # 2. Take one dummy step (Read the first section)
        step_payload = {
            "session_id": session_id,
            "action": {
                "action_type": "read_section",
                "section_name": "title_page"
            }
        }
        step_response = client.post("/step", json=step_payload)
        
        if step_response.status_code == 200:
            print("Step Successful: Action 'read_section' executed.")
            print(f"Reward: {step_response.json().get('reward', {}).get('value')}")
        else:
            print(f"Step Failed: {step_response.text}")

if __name__ == "__main__":
    run_inference()
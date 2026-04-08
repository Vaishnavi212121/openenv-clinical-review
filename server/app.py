"""
FastAPI Application — ClinicalTrialReviewEnv
Serves the OpenEnv environment as a REST API for Hugging Face Spaces deployment.
"""

import uuid
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

import sys
import os
import logging

logger = logging.getLogger(__name__)

# This line is the magic key for Docker
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from environment import ClinicalTrialReviewEnv
from models import Action



# ─── Session Store ────────────────────────────────────────────────────────────

sessions: Dict[str, ClinicalTrialReviewEnv] = {}


# ─── Request/Response Models ──────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_easy"

class StepRequest(BaseModel):
    session_id: str
    action: Dict[str, Any]


# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="ClinicalTrialReviewEnv API",
    version="1.0.0",
    # This is the critical line for Hugging Face
    root_path="/spaces/Vaishu901821/clinical-trial-review",
    root_path_in_servers=False 
)

# Also, ensure you have a root route defined so the home page isn't empty
@app.get("/")
async def read_root():
    return {"status": "Running", "message": "Clinical Trial Review API is live!"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Root ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>ClinicalTrialReviewEnv — OpenEnv</title>
    <style>
        body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #e0e0e0; 
               max-width : 800px; margin: 60px auto; padding: 20px; }
        h1 { color: #4fc3f7; border-bottom : 1px solid #333; padding-bottom : 10px; }
        h2 { color: #81c784; }
        .badge { background: #1a237e; color: #90caf9; padding: 3px 8px; border-radius: 4px; 
                 font-size: 12px; margin: 2px; display: inline-block; }
        .endpoint { background: #1a1a1a; border: 1px solid #333; padding: 12px; 
                    border-radius: 6px; margin: 8px 0; }
        .method { color: #a5d6a7; font-weight: bold; }
        code { background: #1e1e1e; padding: 2px 6px; border-radius: 3px; color: #f48fb1; }
        a { color: #4fc3f7; }
    </style>
</head>
<body>
    <h1>🏥 ClinicalTrialReviewEnv</h1>
    <p>
        <span class="badge">openenv</span>
        <span class="badge">healthcare</span>
        <span class="badge">regulatory</span>
        <span class="badge">v1.0.0</span>
    </p>
    <p>An OpenEnv environment for training and evaluating AI agents on clinical trial 
    protocol review — a high-stakes real-world task performed by regulatory specialists.</p>

    <h2>Quick Start</h2>
    <div class="endpoint">
        <span class="method">POST</span> <code>/reset</code> — Start a new episode<br>
        Body: <code>{"task_id": "task_easy"}</code>
    </div>
    <div class="endpoint">
        <span class="method">POST</span> <code>/step</code> — Execute an action<br>
        Body: <code>{"session_id": "...", "action": {"action_type": "read_section", "section_name": "title_page"}}</code>
    </div>
    <div class="endpoint">
        <span class="method">GET</span> <code>/state/{session_id}</code> — Get full environment state
    </div>
    <div class="endpoint">
        <span class="method">GET</span> <code>/tasks</code> — List available tasks
    </div>
    <div class="endpoint">
        <span class="method">GET</span> <code>/validate</code> — OpenEnv spec validation
    </div>

    <h2>Tasks</h2>
    <ul>
        <li><strong>task_easy</strong> — Missing Required Elements (Phase I Protocol)</li>
        <li><strong>task_medium</strong> — Eligibility & Statistical Conflicts (Phase III RCT)</li>
        <li><strong>task_hard</strong> — Full Safety & Compliance Audit (Pediatric Adaptive Trial)</li>
    </ul>

    <p><a href="/docs">📖 Interactive API Docs</a> | <a href="/openenv.yaml">📄 openenv.yaml</a></p>
</body>
</html>
"""


# ─── OpenEnv Endpoints ────────────────────────────────────────────────────────

@app.post("/reset")
async def reset(req: Optional[ResetRequest] = None): 
    try:
        # 1. Determine the task_id (fallback to "task_easy" if body is empty)
        task_id = "task_easy"
        if req and req.task_id:
            task_id = req.task_id
            
        # 2. Initialize your environment
        env = ClinicalTrialReviewEnv(task_id=task_id)
        obs = env.reset()
        
        # 3. Create session (Keep your existing session logic here)
        import uuid
        session_id = str(uuid.uuid4())
        sessions[session_id] = env
        
        return {
            "session_id": session_id,
            "task_id": task_id,
            "observation": obs.model_dump() if hasattr(obs, 'model_dump') else obs,
        }
    except Exception as e:
        # This helps you see what's wrong in the Hugging Face logs
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step")
async def step(req: StepRequest):
    """Execute one action in the environment."""
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")
    
    env = sessions[req.session_id]
    
    try:
        action = Action(**req.action)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid action: {e}")
    
    try:
        obs, reward, done, info = env.step(action)
        return {
            "observation": obs.model_dump(),
            "reward": reward.model_dump(),
            "done": done,
            "info": info,
        }
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state/{session_id}")
async def get_state(session_id: str):
    """Get the full internal environment state."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    env = sessions[session_id]
    try:
        state = env.state()
        return state.model_dump()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks")
async def list_tasks():
    """List available tasks with descriptions."""
    return {
        "tasks": [
            {
                "id": "task_easy",
                "name": "Missing Required Elements Check",
                "difficulty": "easy",
                "max_steps": 10,
                "description": "Review a Phase I oncology protocol for missing required elements per ICH E6(R2).",
                "target_categories": ["missing_element"],
            },
            {
                "id": "task_medium",
                "name": "Eligibility Criteria Conflict & Statistical Flaw Detection",
                "difficulty": "medium",
                "max_steps": 15,
                "description": "Find eligibility conflicts and statistical flaws in a Phase III cardiovascular RCT.",
                "target_categories": ["eligibility_conflict", "statistical_flaw", "missing_element"],
            },
            {
                "id": "task_hard",
                "name": "Full Protocol Safety & Compliance Audit",
                "difficulty": "hard",
                "max_steps": 25,
                "description": "Comprehensive audit of a complex adaptive pediatric trial with 13 ground-truth issues.",
                "target_categories": [
                    "missing_element", "eligibility_conflict", "dosing_error",
                    "safety_gap", "consent_violation", "statistical_flaw", "regulatory_noncompliance"
                ],
            },
        ]
    }


@app.get("/validate")
async def validate():
    """OpenEnv spec validation endpoint."""
    try:
        # Quick smoke test
        env = ClinicalTrialReviewEnv("task_easy")
        obs = env.reset()
        assert obs.protocol_id
        assert obs.available_sections
        
        action = Action(action_type="read_section", section_name=obs.available_sections[0])
        obs2, reward, done, info = env.step(action)
        assert reward.value is not None
        
        state = env.state()
        assert state.task_id == "task_easy"
        
        return {
            "valid": True,
            "spec_version": "openenv-1.0",
            "checks": {
                "reset_returns_observation": True,
                "step_returns_obs_reward_done_info": True,
                "state_returns_episode_state": True,
                "typed_models": True,
                "reward_in_range": -1.0 <= reward.value <= 1.0,
            }
        }
    except Exception as e:
        return {"valid": False, "error": str(e)}


@app.get("/openenv.yaml")
async def get_yaml():
    """Serve the openenv.yaml spec file."""
    import os
    yaml_path = os.path.join(os.path.dirname(__file__), "openenv.yaml")
    if os.path.exists(yaml_path):
        with open(yaml_path) as f:
            content = f.read()
        return HTMLResponse(content=content, media_type="text/yaml")
    raise HTTPException(status_code=404, detail="openenv.yaml not found")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": "ClinicalTrialReviewEnv", "version": "1.0.0"}
def main():
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=7860, reload=False)

if __name__ == "__main__":
    main()
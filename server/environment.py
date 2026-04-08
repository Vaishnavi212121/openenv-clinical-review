"""
ClinicalTrialReviewEnv — Main Environment Class
Implements the full OpenEnv interface: step() / reset() / state()
FIXED: Flexible imports for HF Spaces compatibility
"""

from __future__ import annotations

import uuid
import copy
from typing import Any, Dict, Optional, Tuple

# ─── Fixed imports: Try both package and root-level structures ───────────────

try:
    # Try env/ package structure first
    from models import (
        Observation, Action, Reward, EpisodeState, TaskResult,
        ProtocolFlag, ActionType, FlagCategory, FlagSeverity
    )
    from env.protocols import PROTOCOLS, TASK_PROTOCOL_MAP
except ImportError:
    # Fallback to root-level imports (for HF Spaces)
    from models import (
        Observation, Action, Reward, EpisodeState, TaskResult,
        ProtocolFlag, ActionType, FlagCategory, FlagSeverity
    )
try:
    from protocols import PROTOCOLS, TASK_PROTOCOL_MAP
except ImportError:
    from env.protocols import PROTOCOLS, TASK_PROTOCOL_MAP
try:
    from graders.graders import get_grader
except ImportError:
    # Alternative import path
    from graders import get_grader


TASK_CONFIGS = {
    "task_easy": {
        "name": "Missing Required Elements Check",
        "description": (
            "Review a Phase I oncology protocol and identify all missing required elements "
            "per ICH E6(R2) GCP guidelines. Flag each missing element with category "
            "'missing_element', appropriate severity (critical/major/minor), a description "
            "of what is missing, and the section location. Submit your review when complete."
        ),
        "max_steps": 10,
        "difficulty": "easy",
        "target_categories": ["missing_element"],
    },
    "task_medium": {
        "name": "Eligibility Criteria Conflict & Statistical Flaw Detection",
        "description": (
            "Review a Phase III cardiovascular RCT protocol. Identify: (1) eligibility "
            "criteria conflicts or ambiguities between inclusion/exclusion criteria, and "
            "(2) statistical design flaws that would not meet regulatory standards. Use "
            "categories 'eligibility_conflict' and 'statistical_flaw' respectively. "
            "Also flag any missing elements you find. Submit when complete."
        ),
        "max_steps": 15,
        "difficulty": "medium",
        "target_categories": ["eligibility_conflict", "statistical_flaw", "missing_element"],
    },
    "task_hard": {
        "name": "Full Protocol Safety & Compliance Audit",
        "description": (
            "Conduct a comprehensive audit of a complex adaptive Phase II/III pediatric "
            "clinical trial protocol. Identify ALL issues across ALL sections including: "
            "missing elements, eligibility conflicts, dosing errors, safety gaps, consent "
            "violations, statistical flaws, and regulatory non-compliance issues. "
            "This protocol has numerous serious issues. You must review most sections "
            "and submit a complete audit. Prioritize critical and major issues."
        ),
        "max_steps": 25,
        "difficulty": "hard",
        "target_categories": [
            "missing_element", "eligibility_conflict", "dosing_error",
            "safety_gap", "consent_violation", "statistical_flaw", "regulatory_noncompliance"
        ],
    },
}


class ClinicalTrialReviewEnv:
    """
    OpenEnv-compliant environment for clinical trial protocol review.
    
    Simulates the real-world task of reviewing clinical trial protocols for 
    compliance, safety gaps, and eligibility/statistical issues — a task 
    performed by regulatory affairs specialists and clinical research associates.
    
    API:
        env = ClinicalTrialReviewEnv(task_id="task_easy")
        obs = env.reset()
        obs, reward, done, info = env.step(action)
        state = env.state()
    """

    def __init__(self, task_id: str = "task_easy"):
        if task_id not in TASK_CONFIGS:
            raise ValueError(f"Unknown task_id: '{task_id}'. Valid: {list(TASK_CONFIGS.keys())}")
        self.task_id = task_id
        self.config = TASK_CONFIGS[task_id]
        self.protocol_id = TASK_PROTOCOL_MAP[task_id]
        self.protocol = PROTOCOLS[self.protocol_id]
        self.grader = get_grader(task_id)
        self._state: Optional[EpisodeState] = None
        self._flag_counter = 0

    # ─── OpenEnv Core API ─────────────────────────────────────────────────────

    def reset(self) -> Observation:
        """Reset environment to initial state. Returns first observation."""
        self._flag_counter = 0
        sections = list(self.protocol["sections"].keys())
        first_section = sections[0]

        self._state = EpisodeState(
            protocol_id=self.protocol_id,
            task_id=self.task_id,
            difficulty=self.config["difficulty"],
            current_section=first_section,
            sections_reviewed=[],
            flags_raised=[],
            ground_truth_issues=copy.deepcopy(self.protocol["ground_truth_issues"]),
            step_number=0,
            max_steps=self.config["max_steps"],
            cumulative_reward=0.0,
            done=False,
            clarifications_used=0,
            submitted=False,
        )
        return self._build_observation()

    def step(self, action: Action | Dict[str, Any]) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Execute one action in the environment.
        
        Returns:
            observation: Current state visible to agent
            reward: Step reward with component breakdown
            done: Whether episode is complete
            info: Additional diagnostic information
        """
        if self._state is None:
            raise RuntimeError("Call reset() before step()")
        if self._state.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        # Normalize action
        if isinstance(action, dict):
            action = Action(**action)

        if not action.validate_action():
            return self._handle_invalid_action(action)

        self._state.step_number += 1
        step_reward_value = 0.0
        reward_components = {}
        info: Dict[str, Any] = {"action_type": action.action_type}
        done = False

        # ── READ SECTION ──────────────────────────────────────────────────────
        if action.action_type == ActionType.READ_SECTION:
            result = self._action_read_section(action)
            step_reward_value = result["reward"]
            reward_components = result["components"]
            info.update(result["info"])

        # ── RAISE FLAG ────────────────────────────────────────────────────────
        elif action.action_type == ActionType.RAISE_FLAG:
            result = self._action_raise_flag(action)
            step_reward_value = result["reward"]
            reward_components = result["components"]
            info.update(result["info"])

        # ── CLEAR FLAG ────────────────────────────────────────────────────────
        elif action.action_type == ActionType.CLEAR_FLAG:
            result = self._action_clear_flag(action)
            step_reward_value = result["reward"]
            reward_components = result["components"]
            info.update(result["info"])

        # ── SUBMIT REVIEW ─────────────────────────────────────────────────────
        elif action.action_type == ActionType.SUBMIT_REVIEW:
            result = self._action_submit()
            step_reward_value = result["reward"]
            reward_components = result["components"]
            info.update(result["info"])
            done = True
            self._state.submitted = True

        # ── REQUEST CLARIFICATION ─────────────────────────────────────────────
        elif action.action_type == ActionType.REQUEST_CLARIFICATION:
            result = self._action_clarification(action)
            step_reward_value = result["reward"]
            reward_components = result["components"]
            info.update(result["info"])

        # Check if out of steps
        if self._state.step_number >= self._state.max_steps and not done:
            done = True
            step_reward_value += -0.05  # Small penalty for running out of steps
            reward_components["timeout_penalty"] = -0.05
            info["timeout"] = True

        self._state.done = done
        self._state.cumulative_reward += step_reward_value

        reward = Reward(
            value=step_reward_value,
            cumulative=self._state.cumulative_reward,
            components=reward_components,
            reason=info.get("reason", "")
        )

        return self._build_observation(), reward, done, info

    def state(self) -> EpisodeState:
        """Get full internal state of the environment."""
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self._state

    # ─── Action Handlers ──────────────────────────────────────────────────────

    def _action_read_section(self, action: Action) -> Dict[str, Any]:
        section_name = action.section_name
        
        if section_name not in self.protocol["sections"]:
            return {
                "reward": -0.02,
                "components": {"invalid_section": -0.02},
                "info": {"error": f"Section '{section_name}' not found"}
            }
        
        sections = self.protocol["sections"]
        reward = 0.0
        components = {}

        if section_name not in self._state.sections_reviewed:
            self._state.sections_reviewed.append(section_name)
            if sections[section_name].get("has_issues", False):
                reward += 0.04
                components["new_section_with_issues"] = 0.04
            else:
                reward += 0.01
                components["new_section_no_issues"] = 0.01
        else:
            reward += -0.01
            components["repeated_read"] = -0.01

        return {
            "reward": reward,
            "components": components,
            "info": {
                "section_loaded": section_name,
                "has_issues": sections[section_name].get("has_issues", False),
                "reason": f"Navigated to section: {section_name}"
            }
        }

    def _action_raise_flag(self, action: Action) -> Dict[str, Any]:
        flag_data = action.flag
        if not flag_data:
            return {"reward": -0.05, "components": {"invalid_flag": -0.05}, "info": {}}

        try:
            category = FlagCategory(flag_data.get("category", "missing_element"))
            severity = FlagSeverity(flag_data.get("severity", "minor"))
        except ValueError:
            return {
                "reward": -0.03,
                "components": {"invalid_enum": -0.03},
                "info": {"error": "Invalid category or severity value"}
            }

        self._flag_counter += 1
        flag_id = f"FLAG-{self._flag_counter:03d}"

        flag = ProtocolFlag(
            flag_id=flag_id,
            category=category,
            severity=severity,
            description=flag_data.get("description", ""),
            location=flag_data.get("location", self._state.current_section),
            step_raised=self._state.step_number,
        )
        self._state.flags_raised.append(flag)

        reward, components = self._score_flag_intermediate(flag)

        return {
            "reward": reward,
            "components": components,
            "info": {"flag_raised": flag_id, "reason": f"Flag raised: {flag_id} ({severity.value} {category.value})"}
        }

    def _action_clear_flag(self, action: Action) -> Dict[str, Any]:
        flag_id = action.flag_id
        original_len = len(self._state.flags_raised)
        self._state.flags_raised = [f for f in self._state.flags_raised if f.flag_id != flag_id]
        
        if len(self._state.flags_raised) < original_len:
            return {
                "reward": 0.01,
                "components": {"flag_cleared": 0.01},
                "info": {"flag_cleared": flag_id, "reason": f"Cleared flag {flag_id}"}
            }
        return {
            "reward": -0.01,
            "components": {"flag_not_found": -0.01},
            "info": {"error": f"Flag {flag_id} not found"}
        }

    def _action_submit(self) -> Dict[str, Any]:
        result = self._compute_final_score()
        terminal_reward = result.score * 0.5
        return {
            "reward": terminal_reward,
            "components": {"submission_score": terminal_reward},
            "info": {"task_result": result.model_dump(), "reason": f"Review submitted. Score: {result.score:.3f}"}
        }

    def _action_clarification(self, action: Action) -> Dict[str, Any]:
        self._state.clarifications_used += 1
        current = self._state.current_section
        has_issues = self.protocol["sections"].get(current, {}).get("has_issues", False)
        hint = f"Section '{current}' {'DOES' if has_issues else 'does NOT'} contain protocol issues."
        return {
            "reward": -0.02,
            "components": {"clarification_cost": -0.02},
            "info": {"clarification": hint, "reason": f"Clarification used (#{self._state.clarifications_used})"}
        }

    # ─── Intermediate Reward Shaping ──────────────────────────────────────────

    def _score_flag_intermediate(self, flag: ProtocolFlag) -> Tuple[float, Dict[str, float]]:
        """Provide partial credit signal immediately when a flag is raised."""
        gt_issues = self._state.ground_truth_issues
        components = {}

        try:
            from graders.graders import _match_flag_to_gt
        except ImportError:
            from graders import _match_flag_to_gt

        match_id, quality = _match_flag_to_gt(flag, gt_issues)

        if match_id:
            gt_issue = next(g for g in gt_issues if g["issue_id"] == match_id)
            sev_weight = {"critical": 0.15, "major": 0.08, "minor": 0.03}.get(gt_issue["severity"], 0.05)
            partial_reward = sev_weight * quality
            components["true_positive_partial"] = partial_reward

            already_found = sum(
                1 for f in self._state.flags_raised[:-1]
                if _match_flag_to_gt(f, [gt_issue])[0] is not None
            )
            if already_found > 0:
                partial_reward *= 0.1
                components["duplicate_penalty"] = -partial_reward * 0.9

            return partial_reward, components
        else:
            fp_penalty = -0.03
            components["false_positive_penalty"] = fp_penalty
            return fp_penalty, components

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _build_observation(self) -> Observation:
        state = self._state
        current_sec = self.protocol["sections"].get(state.current_section, {})
        
        return Observation(
            protocol_id=state.protocol_id,
            task_id=state.task_id,
            task_description=self.config["description"],
            document_section=state.current_section,
            document_text=current_sec.get("content", ""),
            available_sections=list(self.protocol["sections"].keys()),
            sections_reviewed=list(state.sections_reviewed),
            flags_raised=list(state.flags_raised),
            step_number=state.step_number,
            max_steps=state.max_steps,
            clarifications_used=state.clarifications_used,
            done=state.done,
            info={
                "protocol_title": self.protocol["title"],
                "protocol_phase": self.protocol["phase"],
                "task_name": self.config["name"],
                "target_categories": self.config["target_categories"],
                "sections_with_issues_hint": sum(
                    1 for s in self.protocol["sections"].values() if s.get("has_issues")
                ),
            }
        )

    def _compute_final_score(self) -> TaskResult:
        state = self._state
        return self.grader.grade(
            task_id=self.task_id,
            flags_raised=state.flags_raised,
            ground_truth_issues=state.ground_truth_issues,
            steps_used=state.step_number,
            max_steps=state.max_steps,
            sections_reviewed=state.sections_reviewed,
            all_sections=list(self.protocol["sections"].keys()),
            submitted=state.submitted,
        )

    def _handle_invalid_action(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        self._state.step_number += 1
        penalty = -0.05
        self._state.cumulative_reward += penalty
        reward = Reward(
            value=penalty,
            cumulative=self._state.cumulative_reward,
            components={"invalid_action": penalty},
            reason="Invalid action format"
        )
        return self._build_observation(), reward, False, {"error": "Invalid action", "action_type": action.action_type}

    # ─── Convenience ──────────────────────────────────────────────────────────

    @property
    def available_tasks(self) -> list:
        return list(TASK_CONFIGS.keys())

    def __repr__(self):
        if self._state:
            return (f"ClinicalTrialReviewEnv(task={self.task_id}, "
                    f"step={self._state.step_number}/{self._state.max_steps}, "
                    f"flags={len(self._state.flags_raised)}, done={self._state.done})")
        return f"ClinicalTrialReviewEnv(task={self.task_id}, not started)"
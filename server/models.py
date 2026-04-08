"""
OpenEnv Clinical Trial Review — Typed Models
All Observation, Action, Reward, and State types as Pydantic models.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class ActionType(str, Enum):
    READ_SECTION = "read_section"
    RAISE_FLAG = "raise_flag"
    CLEAR_FLAG = "clear_flag"
    SUBMIT_REVIEW = "submit_review"
    REQUEST_CLARIFICATION = "request_clarification"


class FlagCategory(str, Enum):
    MISSING_ELEMENT = "missing_element"
    ELIGIBILITY_CONFLICT = "eligibility_conflict"
    SAFETY_GAP = "safety_gap"
    DOSING_ERROR = "dosing_error"
    CONSENT_VIOLATION = "consent_violation"
    STATISTICAL_FLAW = "statistical_flaw"
    REGULATORY_NONCOMPLIANCE = "regulatory_noncompliance"


class FlagSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class TaskDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ─── Sub-Models ───────────────────────────────────────────────────────────────

class ProtocolFlag(BaseModel):
    """A flag raised by the agent during review."""
    flag_id: str = Field(..., description="Unique identifier for this flag")
    category: FlagCategory
    severity: FlagSeverity
    description: str = Field(..., max_length=500)
    location: str = Field(..., description="Section + reference where the issue was found")
    step_raised: int = Field(..., ge=0)

    class Config:
        use_enum_values = True


class ProtocolSection(BaseModel):
    """A section of the clinical trial protocol document."""
    name: str
    title: str
    content: str
    has_issues: bool = False
    issue_ids: List[str] = Field(default_factory=list)


# ─── Core OpenEnv Types ───────────────────────────────────────────────────────

class Observation(BaseModel):
    """
    What the agent sees at each step.
    Contains the current document section text, review progress, and raised flags.
    """
    protocol_id: str
    task_id: str
    task_description: str
    document_section: str = Field(..., description="Name of the currently viewed section")
    document_text: str = Field(..., description="Full text of the current section")
    available_sections: List[str] = Field(..., description="All section names in this protocol")
    sections_reviewed: List[str] = Field(default_factory=list)
    flags_raised: List[ProtocolFlag] = Field(default_factory=list)
    step_number: int = Field(..., ge=0)
    max_steps: int = Field(..., gt=0)
    clarifications_used: int = Field(default=0)
    done: bool = False
    info: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class Action(BaseModel):
    """
    What the agent can do at each step.
    Navigate sections, raise/clear flags, request clarification, or submit review.
    """
    action_type: ActionType
    # For read_section
    section_name: Optional[str] = None
    # For raise_flag
    flag: Optional[Dict[str, str]] = None
    # For clear_flag
    flag_id: Optional[str] = None
    # For request_clarification
    clarification_query: Optional[str] = None

    class Config:
        use_enum_values = True

    def validate_action(self) -> bool:
        if self.action_type == ActionType.READ_SECTION:
            return self.section_name is not None
        if self.action_type == ActionType.RAISE_FLAG:
            return self.flag is not None and all(
                k in self.flag for k in ["category", "severity", "description", "location"]
            )
        if self.action_type == ActionType.CLEAR_FLAG:
            return self.flag_id is not None
        if self.action_type == ActionType.REQUEST_CLARIFICATION:
            return self.clarification_query is not None
        if self.action_type == ActionType.SUBMIT_REVIEW:
            return True
        return False


class Reward(BaseModel):
    """
    Reward signal for the current step.
    Provides dense partial-credit signals across the episode.
    """
    value: float = Field(..., ge=-1.0, le=1.0, description="Step reward [-1.0, 1.0]")
    cumulative: float = Field(..., description="Total reward accumulated this episode")
    components: Dict[str, float] = Field(
        default_factory=dict,
        description="Breakdown of reward components for interpretability"
    )
    reason: str = Field(default="", description="Human-readable explanation")

    class Config:
        use_enum_values = True


class EpisodeState(BaseModel):
    """Full internal state of the environment (for state() call)."""
    protocol_id: str
    task_id: str
    difficulty: TaskDifficulty
    current_section: str
    sections_reviewed: List[str]
    flags_raised: List[ProtocolFlag]
    ground_truth_issues: List[Dict[str, Any]]
    step_number: int
    max_steps: int
    cumulative_reward: float
    done: bool
    clarifications_used: int
    submitted: bool

    class Config:
        use_enum_values = True


class TaskResult(BaseModel):
    """Final result after episode completion."""
    task_id: str
    score: float = Field(..., ge=0.0, le=1.0)
    true_positives: int
    false_positives: int
    false_negatives: int
    critical_issues_found: int
    critical_issues_total: int
    steps_used: int
    max_steps: int
    efficiency_bonus: float
    final_reward: float
    passed: bool
    breakdown: Dict[str, Any] = Field(default_factory=dict)
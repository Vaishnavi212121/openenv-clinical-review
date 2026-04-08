"""
Test suite for ClinicalTrialReviewEnv
Run: python -m pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from env import ClinicalTrialReviewEnv, Action, Observation, Reward, EpisodeState
from env.models import ActionType, FlagCategory, FlagSeverity


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(params=["task_easy", "task_medium", "task_hard"])
def env_all_tasks(request):
    return ClinicalTrialReviewEnv(task_id=request.param)


@pytest.fixture
def easy_env():
    return ClinicalTrialReviewEnv(task_id="task_easy")


@pytest.fixture
def medium_env():
    return ClinicalTrialReviewEnv(task_id="task_medium")


@pytest.fixture
def hard_env():
    return ClinicalTrialReviewEnv(task_id="task_hard")


# ─── Core OpenEnv Spec Tests ──────────────────────────────────────────────────

class TestOpenEnvSpec:
    """Tests that verify compliance with the OpenEnv specification."""

    def test_reset_returns_observation(self, env_all_tasks):
        obs = env_all_tasks.reset()
        assert isinstance(obs, Observation)

    def test_reset_produces_clean_state(self, easy_env):
        obs1 = easy_env.reset()
        action = Action(action_type=ActionType.READ_SECTION, 
                       section_name=obs1.available_sections[0])
        easy_env.step(action)
        
        obs2 = easy_env.reset()
        assert obs2.step_number == 0
        assert len(obs2.sections_reviewed) == 0
        assert len(obs2.flags_raised) == 0
        assert not obs2.done

    def test_step_returns_four_tuple(self, easy_env):
        easy_env.reset()
        action = Action(action_type=ActionType.READ_SECTION, section_name="title_page")
        result = easy_env.step(action)
        assert len(result) == 4
        obs, reward, done, info = result
        assert isinstance(obs, Observation)
        assert isinstance(reward, Reward)
        assert isinstance(done, bool)
        assert isinstance(info, dict)

    def test_state_returns_episode_state(self, easy_env):
        easy_env.reset()
        state = easy_env.state()
        assert isinstance(state, EpisodeState)

    def test_reward_in_valid_range(self, env_all_tasks):
        obs = env_all_tasks.reset()
        for section in obs.available_sections[:3]:
            action = Action(action_type=ActionType.READ_SECTION, section_name=section)
            _, reward, done, _ = env_all_tasks.step(action)
            assert -1.0 <= reward.value <= 1.0
            if done:
                break

    def test_episode_terminates(self, easy_env):
        easy_env.reset()
        done = False
        steps = 0
        while not done and steps < 50:
            action = Action(action_type=ActionType.SUBMIT_REVIEW)
            _, _, done, _ = easy_env.step(action)
            steps += 1
        assert done, "Episode must terminate"

    def test_cannot_step_before_reset(self, easy_env):
        with pytest.raises(RuntimeError):
            action = Action(action_type=ActionType.READ_SECTION, section_name="title_page")
            easy_env.step(action)

    def test_cannot_step_after_done(self, easy_env):
        easy_env.reset()
        action = Action(action_type=ActionType.SUBMIT_REVIEW)
        _, _, done, _ = easy_env.step(action)
        assert done
        with pytest.raises(RuntimeError):
            easy_env.step(action)


# ─── Observation Space Tests ──────────────────────────────────────────────────

class TestObservationSpace:
    def test_observation_has_required_fields(self, easy_env):
        obs = easy_env.reset()
        assert obs.protocol_id
        assert obs.task_id
        assert obs.task_description
        assert obs.document_section
        assert obs.document_text
        assert obs.available_sections
        assert obs.step_number == 0
        assert obs.max_steps > 0
        assert not obs.done

    def test_sections_update_on_read(self, easy_env):
        obs = easy_env.reset()
        initial_reviewed = len(obs.sections_reviewed)
        section = obs.available_sections[0]
        action = Action(action_type=ActionType.READ_SECTION, section_name=section)
        obs2, _, _, _ = easy_env.step(action)
        assert section in obs2.sections_reviewed

    def test_flags_appear_in_observation(self, easy_env):
        easy_env.reset()
        action = Action(
            action_type=ActionType.RAISE_FLAG,
            flag={
                "category": "missing_element",
                "severity": "major",
                "description": "IND number is missing from the title page",
                "location": "title_page"
            }
        )
        obs, _, _, _ = easy_env.step(action)
        assert len(obs.flags_raised) == 1
        assert obs.flags_raised[0].flag_id == "FLAG-001"


# ─── Action Space Tests ───────────────────────────────────────────────────────

class TestActionSpace:
    def test_read_valid_section(self, easy_env):
        obs = easy_env.reset()
        action = Action(action_type=ActionType.READ_SECTION, 
                       section_name=obs.available_sections[0])
        obs2, reward, done, info = easy_env.step(action)
        assert not done
        assert obs2.document_section == obs.available_sections[0]

    def test_read_invalid_section(self, easy_env):
        easy_env.reset()
        action = Action(action_type=ActionType.READ_SECTION, 
                       section_name="nonexistent_section_xyz")
        _, reward, done, info = easy_env.step(action)
        assert reward.value < 0  # Penalty for invalid section
        assert not done

    def test_raise_flag_creates_flag(self, easy_env):
        easy_env.reset()
        action = Action(
            action_type=ActionType.RAISE_FLAG,
            flag={
                "category": "missing_element",
                "severity": "critical",
                "description": "DLT window not specified",
                "location": "study_design"
            }
        )
        obs, _, _, _ = easy_env.step(action)
        assert len(obs.flags_raised) == 1

    def test_clear_flag_removes_flag(self, easy_env):
        easy_env.reset()
        # First raise a flag
        easy_env.step(Action(
            action_type=ActionType.RAISE_FLAG,
            flag={"category": "missing_element", "severity": "minor",
                  "description": "test", "location": "title_page"}
        ))
        # Then clear it
        obs, _, _, _ = easy_env.step(Action(
            action_type=ActionType.CLEAR_FLAG, flag_id="FLAG-001"
        ))
        assert len(obs.flags_raised) == 0

    def test_submit_ends_episode(self, easy_env):
        easy_env.reset()
        _, _, done, _ = easy_env.step(Action(action_type=ActionType.SUBMIT_REVIEW))
        assert done

    def test_clarification_costs_step(self, easy_env):
        easy_env.reset()
        _, reward, _, _ = easy_env.step(Action(
            action_type=ActionType.REQUEST_CLARIFICATION,
            clarification_query="Does title_page have issues?"
        ))
        assert reward.value < 0


# ─── Reward Function Tests ────────────────────────────────────────────────────

class TestRewardFunction:
    def test_reward_has_components(self, easy_env):
        easy_env.reset()
        _, reward, _, _ = easy_env.step(Action(
            action_type=ActionType.READ_SECTION, section_name="title_page"
        ))
        assert len(reward.components) > 0

    def test_true_positive_flag_gives_positive_reward(self, easy_env):
        easy_env.reset()
        # Navigate to title_page (known to have missing IND number)
        easy_env.step(Action(action_type=ActionType.READ_SECTION, section_name="title_page"))
        _, reward, _, _ = easy_env.step(Action(
            action_type=ActionType.RAISE_FLAG,
            flag={
                "category": "missing_element",
                "severity": "major",
                "description": "IND number and EudraCT number are missing from the title page",
                "location": "title_page"
            }
        ))
        assert reward.value > 0, "True positive flag should give positive reward"

    def test_false_positive_flag_gives_penalty(self, easy_env):
        easy_env.reset()
        easy_env.step(Action(action_type=ActionType.READ_SECTION, section_name="background"))
        _, reward, _, _ = easy_env.step(Action(
            action_type=ActionType.RAISE_FLAG,
            flag={
                "category": "safety_gap",
                "severity": "critical",
                "description": "Completely fabricated issue that does not exist",
                "location": "background"
            }
        ))
        assert reward.value < 0, "False positive flag should give penalty"

    def test_cumulative_reward_tracks_correctly(self, easy_env):
        easy_env.reset()
        total = 0.0
        for section in ["title_page", "objectives"]:
            _, reward, done, _ = easy_env.step(Action(
                action_type=ActionType.READ_SECTION, section_name=section
            ))
            total += reward.value
            assert abs(reward.cumulative - total) < 0.01
            if done:
                break


# ─── Grader Tests ─────────────────────────────────────────────────────────────

class TestGraders:
    def test_perfect_easy_score(self, easy_env):
        """Agent that finds all issues should score ~1.0."""
        from env.protocols import PROTOCOLS, TASK_PROTOCOL_MAP
        protocol = PROTOCOLS[TASK_PROTOCOL_MAP["task_easy"]]
        
        easy_env.reset()
        # Read all sections
        for section in protocol["sections"]:
            easy_env.step(Action(action_type=ActionType.READ_SECTION, section_name=section))
        # Raise all GT flags
        for issue in protocol["ground_truth_issues"]:
            easy_env.step(Action(
                action_type=ActionType.RAISE_FLAG,
                flag={
                    "category": issue["category"],
                    "severity": issue["severity"],
                    "description": issue["description"],
                    "location": issue["location"]
                }
            ))
        _, _, done, info = easy_env.step(Action(action_type=ActionType.SUBMIT_REVIEW))
        assert done
        score = info["task_result"]["score"]
        assert score > 0.7, f"Perfect agent should score >0.7, got {score}"

    def test_zero_action_score_near_zero(self, easy_env):
        """Agent that does nothing should score ~0."""
        easy_env.reset()
        _, _, done, info = easy_env.step(Action(action_type=ActionType.SUBMIT_REVIEW))
        assert done
        score = info["task_result"]["score"]
        assert score < 0.2, f"Do-nothing agent should score <0.2, got {score}"

    def test_score_between_zero_and_one(self, env_all_tasks):
        obs = env_all_tasks.reset()
        for section in obs.available_sections:
            _, _, done, info = env_all_tasks.step(Action(
                action_type=ActionType.READ_SECTION, section_name=section
            ))
            if done:
                break
        _, _, done, info = env_all_tasks.step(Action(action_type=ActionType.SUBMIT_REVIEW))
        if done and "task_result" in info:
            score = info["task_result"]["score"]
            assert 0.0 <= score <= 1.0

    def test_hard_task_harder_than_easy(self):
        """Hard task baseline should be lower than easy task baseline."""
        from env.protocols import PROTOCOLS, TASK_PROTOCOL_MAP
        
        def score_zero_action(task_id):
            env = ClinicalTrialReviewEnv(task_id=task_id)
            env.reset()
            _, _, _, info = env.step(Action(action_type=ActionType.SUBMIT_REVIEW))
            return info["task_result"]["score"]
        
        easy_score = score_zero_action("task_easy")
        hard_score = score_zero_action("task_hard")
        assert easy_score >= hard_score, "Easy task should not be harder than hard task"


# ─── Determinism Tests ────────────────────────────────────────────────────────

class TestDeterminism:
    def test_same_actions_same_score(self, easy_env):
        """Identical action sequences must produce identical scores."""
        def run():
            env = ClinicalTrialReviewEnv(task_id="task_easy")
            env.reset()
            env.step(Action(action_type=ActionType.READ_SECTION, section_name="title_page"))
            env.step(Action(
                action_type=ActionType.RAISE_FLAG,
                flag={"category": "missing_element", "severity": "major",
                      "description": "IND number missing", "location": "title_page"}
            ))
            _, _, _, info = env.step(Action(action_type=ActionType.SUBMIT_REVIEW))
            return info["task_result"]["score"]
        
        assert run() == run(), "Same actions must produce same score (deterministic)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

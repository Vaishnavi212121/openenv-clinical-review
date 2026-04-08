from env.environment import ClinicalTrialReviewEnv
from models import Action, ActionType

def test_environment():
    # 1. Initialize
    print("🚀 Initializing Environment...")
    env = ClinicalTrialReviewEnv(task_id="task_easy")
    
    # 2. Test Reset
    print("🔄 Testing reset()...")
    obs = env.reset()
    assert obs.step_number == 0
    assert obs.document_section == "title_page"
    print(f"✅ Reset Successful. Current Section: {obs.document_section}")

    # 3. Test Step (Navigation)
    print("📂 Testing step() - Navigation...")
    nav_action = Action(action_type=ActionType.READ_SECTION, section_name="eligibility")
    obs, reward, done, info = env.step(nav_action)
    assert obs.document_section == "eligibility"
    print(f"✅ Navigation Successful. Reward: {reward.value}")

    # 4. Test Step (Raising a Flag)
    print("🚩 Testing step() - Raising Flag...")
    flag_action = Action(
        action_type=ActionType.RAISE_FLAG,
        flag={
            "category": "missing_element",
            "severity": "major",
            "description": "Missing IND number",
            "location": "title_page"
        }
    )
    obs, reward, done, info = env.step(flag_action)
    assert len(obs.flags_raised) == 1
    print(f"✅ Flagging Successful. Cumulative Reward: {reward.cumulative}")

    # 5. Test Submission
    print("🏁 Testing step() - Submission...")
    submit_action = Action(action_type=ActionType.SUBMIT_REVIEW)
    obs, reward, done, info = env.step(submit_action)
    assert done is True
    assert "task_result" in info
    print(f"✅ Submission Successful. Final Score: {info['task_result']['score']}")

if __name__ == "__main__":
    try:
        test_environment()
        print("\n✨ ALL LOCAL TESTS PASSED!")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
from env.environment import ClinicalTrialReviewEnv
from models import Action

class OpenEnvClient:
    def __init__(self, task_id: str):
        self.env = ClinicalTrialReviewEnv(task_id=task_id)

    def reset(self):
        obs = self.env.reset()
        return obs.model_dump()

    def step(self, action_dict: dict):
        action = Action(**action_dict)
        obs, reward, done, info = self.env.step(action)
        return obs.model_dump(), reward.model_dump(), done, info
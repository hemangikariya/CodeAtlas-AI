from backend.app.copilot.base_generator import BaseGenerator


class SprintPlanner(BaseGenerator):
    """
    Feature 9: Sprint Planner
    Generates epics, user stories, estimations, tasks, and sprint breakdowns.
    """

    def __init__(self):
        super().__init__("SprintPlanner", "sprint_planner")

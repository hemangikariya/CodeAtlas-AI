from backend.app.copilot.base_generator import BaseGenerator


class ImplementationPlanner(BaseGenerator):
    """
    Feature 10: Implementation Planner
    Generates roadmap timelines, development phases, and risk mitigations.
    """

    def __init__(self):
        super().__init__("ImplementationPlanner", "implementation_planner")

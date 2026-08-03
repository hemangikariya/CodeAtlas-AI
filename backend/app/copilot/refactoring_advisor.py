from backend.app.copilot.base_generator import BaseGenerator


class RefactoringAdvisor(BaseGenerator):
    """
    Feature 7: Refactoring Advisor
    Generates recommendations on SOLID designs, smells, classes, performance upgrades.
    """

    def __init__(self):
        super().__init__("RefactoringAdvisor", "refactoring_advisor")

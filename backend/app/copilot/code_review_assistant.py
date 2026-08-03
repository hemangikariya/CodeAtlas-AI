from backend.app.copilot.base_generator import BaseGenerator


class CodeReviewAssistant(BaseGenerator):
    """
    Feature 8: Code Review Assistant
    Generates code reviews highlighting bugs, maintainability risks, and performance.
    """

    def __init__(self):
        super().__init__("CodeReviewAssistant", "code_review_assistant")

from backend.app.copilot.base_generator import BaseGenerator


class ADRGenerator(BaseGenerator):
    """
    Feature 3: ADR Generator
    Generates Architecture Decision Records documenting problems, contexts, trade-offs, and decisions.
    """

    def __init__(self):
        super().__init__("ADRGenerator", "adr_generator")

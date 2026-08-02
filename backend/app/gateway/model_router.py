class ModelRouter:
    """
    Evaluates requested tasks to select optimal LLM models dynamically,
    maximizing execution speed and accuracy.
    """

    @staticmethod
    def route_task(task_type: str) -> str:
        """
        Maps a task keyword to a target model name.
        """
        ttype = task_type.strip().lower()
        
        # High capacity reasoning tasks
        if ttype in ["planning", "architecture", "security", "synthesis", "refactoring"]:
            return "gemini-1.5-pro"
            
        # Fast completions/eval tasks
        return "gemini-1.5-flash"

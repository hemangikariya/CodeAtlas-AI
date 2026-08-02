class VersionManager:
    """
    Manages custom override mappings and version resolution for prompt template files.
    """

    def __init__(self):
        self._versions = {}

    def set_version(self, name: str, version: str) -> None:
        """
        Registers a active version for the prompt. (e.g. name='planner', version='v2')
        """
        self._versions[name.strip().lower()] = version.strip()

    def resolve_name(self, name: str) -> str:
        """
        Resolves template file name by applying mapped version strings if present.
        """
        key = name.strip().lower()
        if key in self._versions:
            return f"{name}_{self._versions[key]}"
        return name


# Global version manager instance
prompt_version_manager = VersionManager()

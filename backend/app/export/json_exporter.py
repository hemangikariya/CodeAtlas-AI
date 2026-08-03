import json


class JSONExporter:
    """
    Exports a structured artifact into formatted JSON.
    """

    @staticmethod
    def export(artifact: dict) -> str:
        return json.dumps(artifact, indent=2)

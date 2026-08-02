from typing import Dict, Any, List


class JSONSchemaValidator:
    """
    Validates JSON object compatibility against standard JSON schema properties.
    """

    def validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """
        Validates presence and types of required fields defined in schema.
        """
        if not isinstance(data, dict):
            return False

        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in data:
                return False

        properties = schema.get("properties", {})
        for key, value in data.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "array" and not isinstance(value, list):
                    return False
                elif expected_type == "integer" and not isinstance(value, int) and not isinstance(value, bool):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                elif expected_type == "object" and not isinstance(value, dict):
                    return False
                elif expected_type == "string" and not isinstance(value, str):
                    return False

        return True

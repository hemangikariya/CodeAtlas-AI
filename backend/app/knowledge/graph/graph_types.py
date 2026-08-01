from enum import Enum
from typing import Dict, Any, Optional
import uuid

class NodeType(str, Enum):
    REPOSITORY = "REPOSITORY"
    SNAPSHOT = "SNAPSHOT"
    FOLDER = "FOLDER"
    FILE = "FILE"
    CLASS = "CLASS"
    METHOD = "METHOD"
    FUNCTION = "FUNCTION"
    INTERFACE = "INTERFACE"
    ENUM = "ENUM"
    API_ENDPOINT = "API_ENDPOINT"
    CONFIG_FILE = "CONFIG_FILE"

class EdgeType(str, Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    DEFINES = "DEFINES"
    CONTAINS = "CONTAINS"
    IMPLEMENTS = "IMPLEMENTS"
    EXTENDS = "EXTENDS"
    REFERENCES = "REFERENCES"
    DEPENDS_ON = "DEPENDS_ON"

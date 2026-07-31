from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseParser(ABC):
    @abstractmethod
    def get_supported_extensions(self) -> List[str]:
        """
        Return a list of file extensions this parser supports (e.g. ['.py']).
        """
        pass

    @abstractmethod
    def parse(self, code_content: str, file_path: str) -> Dict[str, Any]:
        """
        Parse raw source code content and extract structural metadata.
        Returns a dictionary in the following format:
        {
            "classes": List[Dict[str, Any]],
            "functions": List[Dict[str, Any]],
            "methods": List[Dict[str, Any]],
            "interfaces": List[Dict[str, Any]],
            "enums": List[Dict[str, Any]],
            "imports": List[Dict[str, Any]],
            "chunks": List[Dict[str, Any]],
            "metadata": Dict[str, Any]
        }
        """
        pass

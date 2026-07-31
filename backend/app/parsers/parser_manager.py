import os
from typing import Dict, Any, Optional
from backend.app.parsers.base_parser import BaseParser
from backend.app.parsers.python_parser import PythonParser
from backend.app.parsers.javascript_parser import JavaScriptParser

class ParserManager:
    def __init__(self):
        # Register parsers dynamically
        self.parsers: Dict[str, BaseParser] = {}
        
        py_parser = PythonParser()
        js_parser = JavaScriptParser()
        
        # Map extensions to parser instances
        for ext in py_parser.get_supported_extensions():
            self.parsers[ext] = py_parser
        for ext in js_parser.get_supported_extensions():
            self.parsers[ext] = js_parser

    def get_parser_for_file(self, file_path: str) -> Optional[BaseParser]:
        _, ext = os.path.splitext(file_path)
        return self.parsers.get(ext.lower())

    def parse_file(self, code_content: str, file_path: str) -> Dict[str, Any]:
        parser = self.get_parser_for_file(file_path)
        if parser:
            return parser.parse(code_content, file_path)
        
        # Fallback parser for non-supported formats (e.g. JSON, README, configuration files)
        filename = os.path.basename(file_path)
        chunk_type = "CONFIG"
        if filename.lower() == "readme.md" or filename.lower().endswith(".md"):
            chunk_type = "README"
            
        return {
            "classes": [],
            "functions": [],
            "methods": [],
            "interfaces": [],
            "enums": [],
            "imports": [],
            "chunks": [{
                "name": filename,
                "type": chunk_type,
                "content": code_content,
                "start_line": 1,
                "end_line": max(1, len(code_content.splitlines())),
                "metadata": {}
            }],
            "metadata": {
                "loc": len(code_content.splitlines()),
                "language": "Text/Configuration"
            }
        }
settings_parser_manager = ParserManager()

from typing import List, Dict, Any
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from backend.app.parsers.base_parser import BaseParser

class PythonParser(BaseParser):
    def __init__(self):
        self.language = Language(tspython.language())
        self.parser = Parser(self.language)

    def get_supported_extensions(self) -> List[str]:
        return [".py"]

    def parse(self, code_content: str, file_path: str) -> Dict[str, Any]:
        results = {
            "classes": [],
            "functions": [],
            "methods": [],
            "interfaces": [],
            "enums": [],
            "imports": [],
            "chunks": [],
            "metadata": {
                "loc": len(code_content.splitlines()),
                "language": "Python"
            }
        }

        try:
            tree = self.parser.parse(bytes(code_content, "utf8"))
            root = tree.root_node
            
            # Extract imports, classes, and functions recursively
            self._traverse_node(root, code_content, results)
            
            # Module-level chunk fallback if nothing was extracted
            if not results["chunks"]:
                results["chunks"].append({
                    "name": "module",
                    "type": "MODULE",
                    "content": code_content,
                    "start_line": 1,
                    "end_line": max(1, len(code_content.splitlines())),
                    "metadata": {}
                })
                
        except Exception as e:
            # Fallback error recovery
            results["metadata"]["error"] = str(e)
            results["chunks"].append({
                "name": "module_failed",
                "type": "MODULE",
                "content": code_content,
                "start_line": 1,
                "end_line": max(1, len(code_content.splitlines())),
                "metadata": {"error": str(e)}
            })

        return results

    def _traverse_node(self, node, code: str, results: Dict[str, Any], current_class: str = ""):
        node_type = node.type
        
        if node_type == "import_statement" or node_type == "import_from_statement":
            # Extract raw import text
            import_text = code[node.start_byte:node.end_byte]
            results["imports"].append({
                "raw": import_text,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1
            })
            
        elif node_type == "class_definition":
            # Extract class name
            name_node = node.child_by_field_name("name")
            class_name = code[name_node.start_byte:name_node.end_byte] if name_node else "UnknownClass"
            class_content = code[node.start_byte:node.end_byte]
            
            class_info = {
                "name": class_name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "signature": f"class {class_name}"
            }
            results["classes"].append(class_info)
            results["chunks"].append({
                "name": class_name,
                "type": "CLASS",
                "content": class_content,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "metadata": {}
            })
            
            # Recurse inside class body with updated class identifier context
            body_node = node.child_by_field_name("body")
            if body_node:
                for child in body_node.children:
                    self._traverse_node(child, code, results, current_class=class_name)
            return

        elif node_type == "function_definition":
            name_node = node.child_by_field_name("name")
            func_name = code[name_node.start_byte:name_node.end_byte] if name_node else "anonymous_func"
            func_content = code[node.start_byte:node.end_byte]
            
            func_info = {
                "name": func_name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "signature": f"def {func_name}"
            }
            
            if current_class:
                # Class method
                func_info["class_name"] = current_class
                results["methods"].append(func_info)
                results["chunks"].append({
                    "name": f"{current_class}.{func_name}",
                    "type": "METHOD",
                    "content": func_content,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "metadata": {"class": current_class}
                })
            else:
                # Top-level module function
                results["functions"].append(func_info)
                results["chunks"].append({
                    "name": func_name,
                    "type": "FUNCTION",
                    "content": func_content,
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "metadata": {}
                })

        # Recurse children if any
        for child in node.children:
            self._traverse_node(child, code, results, current_class)

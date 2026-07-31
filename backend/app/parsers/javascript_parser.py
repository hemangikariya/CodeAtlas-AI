from typing import List, Dict, Any
import tree_sitter_javascript as tsjavascript
import tree_sitter_typescript as tstypescript
from tree_sitter import Language, Parser
from backend.app.parsers.base_parser import BaseParser

class JavaScriptParser(BaseParser):
    def __init__(self):
        # Retrieve precompiled typescript/tsx parser which is a superset of JS
        try:
            self.language = Language(tstypescript.language_tsx())
        except Exception:
            try:
                self.language = Language(tstypescript.language_typescript())
            except Exception:
                self.language = Language(tsjavascript.language())
        self.parser = Parser(self.language)

    def get_supported_extensions(self) -> List[str]:
        return [".js", ".jsx", ".ts", ".tsx"]

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
                "language": "JavaScript/TypeScript"
            }
        }

        try:
            tree = self.parser.parse(bytes(code_content, "utf8"))
            root = tree.root_node
            
            # Recurse traversal
            self._traverse_node(root, code_content, results)
            
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
        
        if node_type == "import_statement":
            import_text = code[node.start_byte:node.end_byte]
            results["imports"].append({
                "raw": import_text,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1
            })
            
        elif node_type == "class_declaration" or node_type == "class":
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
            
            body_node = node.child_by_field_name("body")
            if body_node:
                for child in body_node.children:
                    self._traverse_node(child, code, results, current_class=class_name)
            return

        elif node_type == "method_definition":
            name_node = node.child_by_field_name("name")
            method_name = code[name_node.start_byte:name_node.end_byte] if name_node else "anonymous_method"
            method_content = code[node.start_byte:node.end_byte]
            
            results["methods"].append({
                "name": method_name,
                "class_name": current_class,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "signature": f"{method_name}()"
            })
            results["chunks"].append({
                "name": f"{current_class}.{method_name}" if current_class else method_name,
                "type": "METHOD",
                "content": method_content,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "metadata": {"class": current_class} if current_class else {}
            })

        elif node_type == "function_declaration":
            name_node = node.child_by_field_name("name")
            func_name = code[name_node.start_byte:name_node.end_byte] if name_node else "anonymous_func"
            func_content = code[node.start_byte:node.end_byte]
            
            results["functions"].append({
                "name": func_name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "signature": f"function {func_name}"
            })
            results["chunks"].append({
                "name": func_name,
                "type": "FUNCTION",
                "content": func_content,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "metadata": {}
            })

        elif node_type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            name = code[name_node.start_byte:name_node.end_byte] if name_node else "UnknownInterface"
            content = code[node.start_byte:node.end_byte]
            
            results["interfaces"].append({
                "name": name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1
            })
            results["chunks"].append({
                "name": name,
                "type": "INTERFACE",
                "content": content,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "metadata": {}
            })

        elif node_type == "enum_declaration":
            name_node = node.child_by_field_name("name")
            name = code[name_node.start_byte:name_node.end_byte] if name_node else "UnknownEnum"
            content = code[node.start_byte:node.end_byte]
            
            results["enums"].append({
                "name": name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1
            })
            results["chunks"].append({
                "name": name,
                "type": "ENUM",
                "content": content,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "metadata": {}
            })

        # Recurse children
        for child in node.children:
            self._traverse_node(child, code, results, current_class)

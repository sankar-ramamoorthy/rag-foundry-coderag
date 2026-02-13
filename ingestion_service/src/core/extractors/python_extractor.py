"""
ingestion_service/src/core/extractors/python_extractor.py

PythonASTExtractor

Extracts code artifacts from Python source files:

- MODULE
- CLASS
- FUNCTION
- METHOD
- IMPORT
- CALL (unresolved)

Returns structured dictionaries only, suitable for ingestion into the Codebase KG.
"""

import ast
from typing import List, Dict, Optional


class PythonASTExtractor(ast.NodeVisitor):
    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.module_name = relative_path.replace("/", ".").rstrip(".py")
        self.artifacts: List[Dict] = []

    def extract(self, source_code: str) -> List[Dict]:
        tree = ast.parse(source_code)
        annotate_parents(tree)  # <-- ensure parent links are set
        # Add module artifact
        self.artifacts.append({
            "artifact_type": "MODULE",
            "id": self.relative_path,
            "name": self.module_name,
            "metadata": {},
        })
        self.visit(tree)
        return self.artifacts

    # ----------------------------
    # Visitor methods
    # ----------------------------
    def visit_ClassDef(self, node: ast.ClassDef):
        canonical_id = f"{self.relative_path}#{node.name}"
        self.artifacts.append({
            "artifact_type": "CLASS",
            "id": canonical_id,
            "name": node.name,
            "metadata": {
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "bases": [ast.unparse(base) for base in node.bases] if node.bases else [],
            },
        })
        # Visit methods inside class
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        parent_class = self._get_parent_class(node)
        if parent_class:
            # It's a method
            canonical_id = f"{self.relative_path}#{parent_class}.{node.name}"
            artifact_type = "METHOD"
        else:
            canonical_id = f"{self.relative_path}#{node.name}"
            artifact_type = "FUNCTION"

        self.artifacts.append({
            "artifact_type": artifact_type,
            "id": canonical_id,
            "name": node.name,
            "metadata": {
                "lineno": node.lineno,
                "col_offset": node.col_offset,
                "args": [arg.arg for arg in node.args.args],
            },
        })
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.artifacts.append({
                "artifact_type": "IMPORT",
                "id": f"{self.relative_path}#import:{alias.name}",
                "name": alias.name,
                "metadata": {
                    "asname": alias.asname,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                },
            })

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.artifacts.append({
                "artifact_type": "IMPORT",
                "id": f"{self.relative_path}#import:{module}.{alias.name}",
                "name": alias.name,
                "metadata": {
                    "module": module,
                    "asname": alias.asname,
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                },
            })

    def visit_Call(self, node: ast.Call):
        # Unresolved function/method call
        try:
            if isinstance(node.func, ast.Attribute):
                func_name = f"{ast.unparse(node.func.value)}.{node.func.attr}"
            else:
                func_name = ast.unparse(node.func)
        except Exception:
            func_name = "<unknown>"

        self.artifacts.append({
            "artifact_type": "CALL",
            "id": f"{self.relative_path}#call:{func_name}",
            "name": func_name,
            "metadata": {
                "lineno": node.lineno,
                "col_offset": node.col_offset,
            },
        })
        self.generic_visit(node)

    # ----------------------------
    # Helpers
    # ----------------------------
    def _get_parent_class(self, node: ast.AST) -> Optional[str]:
        """Check if the node is nested inside a class."""
        current = getattr(node, "parent", None)
        while current:
            if isinstance(current, ast.ClassDef):
                return current.name
            current = getattr(current, "parent", None)
        return None


# ----------------------------
# Utility: set parents for nested nodes
# ----------------------------
def annotate_parents(tree: ast.AST):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            setattr(child, "parent", node)

#!/usr/bin/env python3
"""
Modan2 Code Indexing System
Build comprehensive index of the codebase including symbols, relationships, and metadata
"""

import ast
import json
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class Modan2Indexer:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.index_dir = project_root / ".index"
        self.symbols = defaultdict(list)
        self.qt_signals = defaultdict(list)
        self.qt_slots = defaultdict(list)
        self.db_models = {}
        self.call_graph = defaultdict(set)
        self.import_graph = defaultdict(set)
        self.file_stats = {}

    def build_full_index(self):
        """Build complete index of the project"""
        logger.info(f"Starting indexing of {self.project_root}")

        # Collect all Python files recursively, excluding generated/irrelevant dirs
        exclude_parts = {".index", "dist", "build", "__pycache__"}
        python_files = [
            p for p in self.project_root.rglob("**/*.py") if not any(part in exclude_parts for part in p.parts)
        ]
        logger.info(f"Found {len(python_files)} Python files (recursive)")

        # Process each file
        for py_file in python_files:
            if ".index" in str(py_file):
                continue
            logger.info(f"Processing {py_file.name}")
            self.process_file(py_file)

        # Save indexes
        self.save_indexes()
        self.generate_summary()

    def process_file(self, filepath: Path):
        """Process a single Python file"""
        try:
            with open(filepath, encoding="utf-8") as f:
                source = f.read()

            # Basic file stats
            self.file_stats[str(filepath.name)] = {
                "lines": len(source.splitlines()),
                "size": len(source),
                "modified": datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
            }

            # Parse AST
            tree = ast.parse(source, str(filepath))

            # Extract various elements
            self.extract_symbols(tree, filepath)
            self.extract_qt_elements(source, filepath)
            self.extract_imports(tree, filepath)

            # Special processing for known files
            if filepath.name == "MdModel.py":
                self.extract_db_models(tree, filepath)
            elif "Dialog" in filepath.name:
                self.extract_dialog_info(tree, source, filepath)

        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")

    def extract_symbols(self, tree: ast.AST, filepath: Path):
        """Extract functions, classes, and methods"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "file": filepath.name,
                    "line": node.lineno,
                    "type": "class",
                    "methods": [],
                    "bases": [self.get_name(base) for base in node.bases],
                }

                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "line": item.lineno,
                            "params": [arg.arg for arg in item.args.args],
                            "decorators": [self.get_name(d) for d in item.decorator_list],
                        }
                        class_info["methods"].append(method_info)

                        # Track special methods
                        if item.name.startswith("on_") and item.name.endswith("_triggered"):
                            self.qt_slots["actions"].append(
                                {"class": node.name, "method": item.name, "file": filepath.name, "line": item.lineno}
                            )
                        elif "clicked" in item.name or "changed" in item.name:
                            self.qt_slots["ui_handlers"].append(
                                {"class": node.name, "method": item.name, "file": filepath.name, "line": item.lineno}
                            )

                self.symbols["classes"].append(class_info)

            elif isinstance(node, ast.FunctionDef) and not self.is_nested(node):
                func_info = {
                    "name": node.name,
                    "file": filepath.name,
                    "line": node.lineno,
                    "type": "function",
                    "params": [arg.arg for arg in node.args.args],
                    "decorators": [self.get_name(d) for d in node.decorator_list],
                }
                self.symbols["functions"].append(func_info)

    def extract_qt_elements(self, source: str, filepath: Path):
        """Extract Qt signals, slots, and connections using AST (handles lambda/partial)."""
        try:
            tree = ast.parse(source, str(filepath))
        except Exception:
            # Fallback to regex if AST parse fails
            signal_pattern = r"(\w+)\s*=\s*(?:pyqtSignal|Signal)\((.*?)\)"
            for match in re.finditer(signal_pattern, source):
                self.qt_signals["definitions"].append(
                    {"name": match.group(1), "signature": match.group(2), "file": filepath.name}
                )
            connect_pattern = r"(\w+)\.(\w+)\.connect\(([^)]+)\)"
            for match in re.finditer(connect_pattern, source):
                self.qt_signals["connections"].append(
                    {"object": match.group(1), "signal": match.group(2), "slot": match.group(3), "file": filepath.name}
                )
            return

        def expr_to_str(node: ast.AST) -> str:
            if isinstance(node, ast.Attribute):
                return f"{expr_to_str(node.value)}.{node.attr}"
            if isinstance(node, ast.Name):
                return node.id
            if isinstance(node, ast.Call):
                fn = expr_to_str(node.func)
                # Show only first arg for partial-like calls
                if fn.endswith("partial") and node.args:
                    return f"{fn}({expr_to_str(node.args[0])}, …)"
                return f"{fn}(…)"
            if isinstance(node, ast.Lambda):
                return "lambda"
            if isinstance(node, ast.Constant):
                return repr(node.value)
            return node.__class__.__name__

        # pyqtSignal definitions: simple Assign with Call to pyqtSignal/Signal
        for n in ast.walk(tree):
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
                fn_name = expr_to_str(n.value.func)
                if fn_name in ("pyqtSignal", "Signal"):
                    for tgt in n.targets:
                        if isinstance(tgt, ast.Name):
                            sig = {
                                "name": tgt.id,
                                "signature": ",".join([expr_to_str(a) for a in n.value.args]),
                                "file": filepath.name,
                            }
                            self.qt_signals["definitions"].append(sig)

        # signal.connect(slot) calls
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "connect":
                # Expect n.func.value to be Attribute: <object>.<signal>
                obj = signal = None
                if isinstance(n.func.value, ast.Attribute):
                    signal = n.func.value.attr
                    obj = expr_to_str(n.func.value.value)
                else:
                    obj = expr_to_str(n.func.value)
                slot = expr_to_str(n.args[0]) if n.args else ""
                entry = {"object": obj, "signal": signal or "unknown", "slot": slot, "file": filepath.name}
                self.qt_signals["connections"].append(entry)
                # Heuristic: QAction actions
                if isinstance(n.func.value, ast.Attribute):
                    if n.func.value.attr == "triggered" or (obj and "action" in obj.lower()):
                        self.qt_signals["actions"].append({"action": obj, "handler": slot, "file": filepath.name})

    def extract_db_models(self, tree: ast.AST, filepath: Path):
        """Extract Peewee database models"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a Peewee model
                if any("Model" in self.get_name(base) for base in node.bases):
                    model_info = {
                        "name": node.name,
                        "file": filepath.name,
                        "line": node.lineno,
                        "fields": [],
                        "meta": {},
                    }

                    for item in node.body:
                        # Extract fields
                        if isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    field_type = self.get_field_type(item.value)
                                    if field_type:
                                        model_info["fields"].append({"name": target.id, "type": field_type})

                        # Extract Meta class
                        elif isinstance(item, ast.ClassDef) and item.name == "Meta":
                            for meta_item in item.body:
                                if isinstance(meta_item, ast.Assign):
                                    for target in meta_item.targets:
                                        if isinstance(target, ast.Name):
                                            model_info["meta"][target.id] = self.get_value(meta_item.value)

                    self.db_models[node.name] = model_info

    def extract_dialog_info(self, tree: ast.AST, source: str, filepath: Path):
        """Extract dialog-specific information"""
        source_lines = source.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "Dialog" in node.name:
                # Limit parsing to the class block for better precision
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", None)
                if end is None:
                    body_lines = [getattr(n, "lineno", start) for n in node.body]
                    end = max(body_lines) if body_lines else start

                class_src = "\n".join(source_lines[start - 1 : end])

                dialog_info = {
                    "name": node.name,
                    "file": filepath.name,
                    "line": node.lineno,
                    "widgets": [],
                    "layouts": [],
                    "connections": [],
                }

                # Find widget creations within class only
                widget_pattern = r"\bself\.(\w+)\s*=\s*(Q\w+)\("
                for match in re.finditer(widget_pattern, class_src):
                    dialog_info["widgets"].append({"name": match.group(1), "type": match.group(2)})

                # Find layout creations within class only
                layout_pattern = r"\b(Q(?:HBox|VBox|Grid|Form)Layout)\("
                for match in re.finditer(layout_pattern, class_src):
                    dialog_info["layouts"].append(match.group(1))

                self.symbols["dialogs"].append(dialog_info)

    def extract_imports(self, tree: ast.AST, filepath: Path):
        """Extract import statements"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.import_graph[filepath.name].add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self.import_graph[filepath.name].add(node.module)

    def save_indexes(self):
        """Save all indexes to JSON files"""
        # Ensure index subdirectories exist
        (self.index_dir / "symbols").mkdir(parents=True, exist_ok=True)
        (self.index_dir / "graphs").mkdir(parents=True, exist_ok=True)
        # Save symbols
        symbols_file = self.index_dir / "symbols" / "symbols.json"
        with open(symbols_file, "w", encoding="utf-8") as f:
            json.dump(dict(self.symbols), f, indent=2, default=str)
        logger.info(f"Saved symbols to {symbols_file}")

        # Save Qt signals/slots
        qt_file = self.index_dir / "graphs" / "qt_signals.json"
        with open(qt_file, "w", encoding="utf-8") as f:
            json.dump({"signals": dict(self.qt_signals), "slots": dict(self.qt_slots)}, f, indent=2, default=str)
        logger.info(f"Saved Qt elements to {qt_file}")

        # Save database models
        if self.db_models:
            models_file = self.index_dir / "graphs" / "db_models.json"
            with open(models_file, "w", encoding="utf-8") as f:
                json.dump(self.db_models, f, indent=2, default=str)
            logger.info(f"Saved database models to {models_file}")

        # Save import graph
        import_file = self.index_dir / "graphs" / "imports.json"
        with open(import_file, "w", encoding="utf-8") as f:
            json.dump({k: list(v) for k, v in self.import_graph.items()}, f, indent=2)
        logger.info(f"Saved import graph to {import_file}")

        # Save file statistics
        stats_file = self.index_dir / "symbols" / "file_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(self.file_stats, f, indent=2)
        logger.info(f"Saved file statistics to {stats_file}")

    def generate_summary(self):
        """Generate index summary"""
        summary = {
            "generated": datetime.now().isoformat(),
            "statistics": {
                "files": len(self.file_stats),
                "classes": len(self.symbols["classes"]),
                "functions": len(self.symbols["functions"]),
                "dialogs": len(self.symbols["dialogs"]),
                "db_models": len(self.db_models),
                "qt_signals": len(self.qt_signals.get("definitions", [])),
                "qt_connections": len(self.qt_signals.get("connections", [])),
                "total_lines": sum(f["lines"] for f in self.file_stats.values()),
            },
            "files": self.file_stats,
        }

        summary_file = self.index_dir / "index_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info(f"Generated summary: {summary['statistics']}")
        return summary

    # Helper methods
    def get_name(self, node):
        """Get name from AST node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_name(node.value)}.{node.attr}"
        elif isinstance(node, str):
            return node
        return str(node.__class__.__name__)

    def get_value(self, node):
        """Get value from AST node"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):
            return node.s
        elif isinstance(node, ast.Name):
            return node.id
        return None

    def get_field_type(self, node):
        """Get Peewee field type from AST node"""
        if isinstance(node, ast.Call):
            func_name = self.get_name(node.func)
            if "Field" in func_name:
                return func_name
        return None

    def is_nested(self, node):
        """Check if a function is nested inside a class"""
        # This is a simplified check
        return False


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    indexer = Modan2Indexer(project_root)

    try:
        indexer.build_full_index()
        logger.info("Indexing completed successfully!")
    except Exception as e:
        logger.error(f"Indexing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Modan2 Code Search Tool
Search and query the code index
"""

import argparse
import json
import sys
from pathlib import Path


class CodeSearcher:
    def __init__(self, index_dir: Path):
        self.index_dir = index_dir
        self.project_root = index_dir.parent
        self.symbols = self.load_json("symbols/symbols.json")
        self.qt_data = self.load_json("graphs/qt_signals.json")
        self.db_models = self.load_json("graphs/db_models.json")
        self.imports = self.load_json("graphs/imports.json")
        self.file_stats = self.load_json("symbols/file_stats.json")
        self.summary = self.load_json("index_summary.json")

    def load_json(self, path: str) -> dict:
        """Load JSON file from index directory"""
        file_path = self.index_dir / path
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return {}

    def search_symbols(self, query: str, symbol_type: str | None = None) -> list[dict]:
        """Search for symbols by name"""
        results = []
        query_lower = query.lower()

        # Search in specified type or all types
        types_to_search = [symbol_type] if symbol_type else ["classes", "functions", "dialogs"]

        for stype in types_to_search:
            if stype in self.symbols:
                for item in self.symbols[stype]:
                    if query_lower in item["name"].lower():
                        results.append(
                            {"type": stype, "name": item["name"], "file": item["file"], "line": item["line"]}
                        )

                    # Also search in methods for classes
                    if stype == "classes" and "methods" in item:
                        for method in item["methods"]:
                            if query_lower in method["name"].lower():
                                results.append(
                                    {
                                        "type": "method",
                                        "name": f"{item['name']}.{method['name']}",
                                        "file": item["file"],
                                        "line": method["line"],
                                    }
                                )

        return results

    def find_qt_connections(self, signal_or_slot: str) -> list[dict]:
        """Find Qt signal/slot connections"""
        results = []
        query_lower = signal_or_slot.lower()

        # Search in signal connections
        if "connections" in self.qt_data.get("signals", {}):
            for conn in self.qt_data["signals"]["connections"]:
                if query_lower in conn.get("signal", "").lower() or query_lower in conn.get("slot", "").lower():
                    results.append(
                        {
                            "type": "connection",
                            "signal": f"{conn['object']}.{conn['signal']}",
                            "slot": conn["slot"],
                            "file": conn["file"],
                        }
                    )

        # Search in action connections
        if "actions" in self.qt_data.get("signals", {}):
            for action in self.qt_data["signals"]["actions"]:
                if query_lower in action.get("action", "").lower() or query_lower in action.get("handler", "").lower():
                    results.append(
                        {
                            "type": "action",
                            "action": action["action"],
                            "handler": action["handler"],
                            "file": action["file"],
                        }
                    )

        return results

    def find_wait_cursor_methods(self) -> list[dict]:
        """Find methods that use wait cursor by scanning sources"""
        patterns = ["QApplication.setOverrideCursor", "QApplication.restoreOverrideCursor"]

        # Map line numbers to enclosing function/method using AST
        def build_spans(py_path: Path):
            try:
                src = py_path.read_text(encoding="utf-8")
            except Exception:
                return [], ""
            tree = None
            try:
                tree = __import__("ast").parse(src, str(py_path))
            except Exception:
                return [], src
            spans = []  # (start, end, qualname)
            for node in __import__("ast").walk(tree):
                if isinstance(node, __import__("ast").FunctionDef):
                    start = getattr(node, "lineno", 1)
                    end = getattr(node, "end_lineno", None)
                    if end is None and node.body:
                        end = getattr(node.body[-1], "lineno", start)
                    qual = node.name
                    # Try to prefix with class if inside class
                    parent_class = getattr(node, "parent_class", None)
                    if parent_class:
                        qual = f"{parent_class}.{qual}"
                    spans.append((start, end or start, qual))
                elif isinstance(node, __import__("ast").ClassDef):
                    for item in node.body:
                        if isinstance(item, __import__("ast").FunctionDef):
                            item.parent_class = node.name
            return spans, src

        results: list[dict] = []
        for filename in self.file_stats.keys():
            py_path = self.project_root / filename
            if not py_path.exists():
                # Try to locate in subdirs if stats stored as basename
                found = list(self.project_root.rglob(f"**/{filename}"))
                py_path = found[0] if found else None
            if not py_path or not py_path.exists():
                continue
            # Read source and quickly check for patterns
            try:
                src = py_path.read_text(encoding="utf-8")
            except Exception:
                continue
            if not any(p in src for p in patterns):
                continue
            spans, _ = build_spans(py_path)
            lines = src.splitlines()
            for i, line in enumerate(lines, start=1):
                if any(p in line for p in patterns):
                    # Find enclosing function span
                    method = None
                    for start, end, qual in spans:
                        if start <= i <= end:
                            method = qual
                            break
                    results.append({"file": filename, "method": method or "<module>", "line": i})
        return results

    def find_database_usage(self, model_name: str) -> list[dict]:
        """Find where database models are used"""
        results = []

        if model_name in self.db_models:
            model_info = self.db_models[model_name]
            results.append(
                {
                    "type": "model_definition",
                    "name": model_name,
                    "file": model_info["file"],
                    "line": model_info["line"],
                    "fields": model_info["fields"],
                }
            )

        # Search for model usage in imports
        for file, imports in self.imports.items():
            if "MdModel" in imports or model_name in str(imports):
                results.append({"type": "import", "file": file, "imports": "MdModel"})

        return results

    def get_file_info(self, filename: str) -> dict:
        """Get information about a specific file"""
        if filename in self.file_stats:
            info = self.file_stats[filename]

            # Count symbols in this file
            classes = len([c for c in self.symbols.get("classes", []) if c["file"] == filename])
            functions = len([f for f in self.symbols.get("functions", []) if f["file"] == filename])

            return {
                "file": filename,
                "lines": info["lines"],
                "size": info["size"],
                "modified": info["modified"],
                "classes": classes,
                "functions": functions,
            }
        return {}

    def get_project_stats(self) -> dict:
        """Get overall project statistics"""
        return self.summary.get("statistics", {})

    def find_dialog_widgets(self, dialog_name: str) -> list[dict]:
        """Find widgets in a specific dialog"""
        results = []

        for dialog in self.symbols.get("dialogs", []):
            if dialog_name.lower() in dialog["name"].lower():
                results.append(
                    {
                        "dialog": dialog["name"],
                        "file": dialog["file"],
                        "widgets": dialog.get("widgets", []),
                        "layouts": dialog.get("layouts", []),
                    }
                )

        return results


def print_results(results: list[dict], title: str):
    """Pretty print search results"""
    print(f"\n{title}")
    print("=" * 60)

    if not results:
        print("No results found")
        return

    for r in results:
        if "line" in r and "name" in r:
            print(f"  {r.get('type', 'symbol'):12} {r['name']:40} {r['file']}:{r['line']}")
        elif "method" in r and "file" in r:
            print(f"  {r['file']:30} {r['method']:40} line:{r.get('line', '?')}")
        else:
            print(f"  {r}")


def main():
    parser = argparse.ArgumentParser(description="Search Modan2 code index")
    parser.add_argument("--symbol", "-s", help="Search for symbol by name")
    parser.add_argument("--type", "-t", choices=["class", "function", "method", "dialog"], help="Filter by symbol type")
    parser.add_argument("--qt", help="Find Qt signal/slot connections")
    parser.add_argument("--wait-cursor", action="store_true", help="Find methods using wait cursor")
    parser.add_argument("--model", "-m", help="Find database model usage")
    parser.add_argument("--file", "-f", help="Get file information")
    parser.add_argument("--stats", action="store_true", help="Show project statistics")
    parser.add_argument("--dialog", "-d", help="Find dialog widgets")

    args = parser.parse_args()

    # Initialize searcher
    index_dir = Path(__file__).parent.parent / ".index"
    if not index_dir.exists():
        print("Error: Index not found. Run build_index.py first.")
        sys.exit(1)

    searcher = CodeSearcher(index_dir)

    # Execute searches based on arguments
    if args.symbol:
        # Map CLI type to internal keys
        type_map = {"class": "classes", "function": "functions", "dialog": "dialogs", "method": "method"}
        sym_type = type_map.get(args.type) if args.type else None
        results = searcher.search_symbols(args.symbol, sym_type)
        print_results(results, f"Symbol search: '{args.symbol}'")

    elif args.qt:
        results = searcher.find_qt_connections(args.qt)
        print_results(results, f"Qt connections: '{args.qt}'")

    elif args.wait_cursor:
        results = searcher.find_wait_cursor_methods()
        print_results(results, "Methods using wait cursor")

    elif args.model:
        results = searcher.find_database_usage(args.model)
        print_results(results, f"Database model: '{args.model}'")

    elif args.file:
        info = searcher.get_file_info(args.file)
        if info:
            print(f"\nFile: {args.file}")
            print("=" * 60)
            for key, value in info.items():
                print(f"  {key:12}: {value}")
        else:
            print(f"File '{args.file}' not found in index")

    elif args.dialog:
        results = searcher.find_dialog_widgets(args.dialog)
        print_results(results, f"Dialog: '{args.dialog}'")

    elif args.stats:
        stats = searcher.get_project_stats()
        print("\nProject Statistics")
        print("=" * 60)
        for key, value in stats.items():
            print(f"  {key:20}: {value:,}")

    else:
        # Interactive mode
        print("Modan2 Code Search")
        print("=" * 60)
        stats = searcher.get_project_stats()
        print(
            f"Index contains: {stats.get('classes', 0)} classes, "
            f"{stats.get('functions', 0)} functions, "
            f"{stats.get('dialogs', 0)} dialogs"
        )
        print("\nUse --help to see available search options")


if __name__ == "__main__":
    main()

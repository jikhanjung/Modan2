#!/usr/bin/env python3
"""
Generate detailed symbol cards for important Modan2 components
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SymbolCardGenerator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.index_dir = project_root / ".index"
        self.cards_dir = self.index_dir / "cards"

        # Load existing indexes
        self.symbols = self.load_json("symbols/symbols.json")
        self.qt_data = self.load_json("graphs/qt_signals.json")
        self.db_models = self.load_json("graphs/db_models.json")

    def load_json(self, path: str) -> dict:
        file_path = self.index_dir / path
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return {}

    def generate_all_cards(self):
        """Generate cards for all important symbols"""
        logger.info("Generating symbol cards...")

        # Generate cards for key dialogs
        self.generate_dialog_cards()

        # Generate cards for database models
        self.generate_model_cards()

        # Generate cards for key classes
        self.generate_class_cards()

        # Generate special cards
        self.generate_special_cards()

        logger.info("Symbol cards generation complete")

    def generate_dialog_cards(self):
        """Generate cards for dialog classes"""
        dialogs = self.symbols.get("dialogs", [])

        for dialog in dialogs:
            if "Dialog" not in dialog["name"]:
                continue

            card = {
                "symbol": dialog["name"],
                "kind": "dialog",
                "file": dialog["file"],
                "line": dialog["line"],
                "widgets": dialog.get("widgets", []),
                "layouts": dialog.get("layouts", []),
                "qt_connections": self.find_qt_connections_for_class(dialog["name"]),
                "methods": self.find_methods_for_class(dialog["name"]),
                "performance": self.analyze_performance(dialog["name"]),
            }

            self.save_card(card, "dialogs")
            logger.info(f"Generated card for {dialog['name']}")

    def generate_model_cards(self):
        """Generate cards for database models"""
        for model_name, model_info in self.db_models.items():
            card = {
                "symbol": model_name,
                "kind": "peewee_model",
                "file": model_info["file"],
                "line": model_info["line"],
                "fields": model_info["fields"],
                "meta": model_info.get("meta", {}),
                "relationships": self.analyze_model_relationships(model_name),
                "usage": self.find_model_usage(model_name),
            }

            self.save_card(card, "models")
            logger.info(f"Generated card for model {model_name}")

    def generate_class_cards(self):
        """Generate cards for important classes"""
        important_classes = ["ModanMainWindow", "ModanController", "ObjectViewer2D", "ObjectViewer3D", "MdDatasetOps"]

        for class_data in self.symbols.get("classes", []):
            if class_data["name"] not in important_classes:
                continue

            card = {
                "symbol": class_data["name"],
                "kind": "class",
                "file": class_data["file"],
                "line": class_data["line"],
                "bases": class_data.get("bases", []),
                "methods": class_data.get("methods", []),
                "qt_metadata": self.extract_qt_metadata(class_data),
                "complexity": self.calculate_complexity(class_data),
            }

            self.save_card(card, "classes")
            logger.info(f"Generated card for class {class_data['name']}")

    def generate_special_cards(self):
        """Generate special analysis cards"""

        # Wait cursor usage card
        wait_cursor_card = {
            "symbol": "wait_cursor_usage",
            "kind": "analysis",
            "description": "Methods that use wait cursor for long operations",
            "methods": [
                {
                    "file": "ModanDialogs.py",
                    "method": "cbxShapeGrid_state_changed",
                    "line": 2402,
                    "context": "Shape grid toggling",
                },
                {"file": "ModanDialogs.py", "method": "pick_shape", "line": 4072, "context": "Chart point selection"},
                {
                    "file": "ModanDialogs.py",
                    "method": "NewAnalysisDialog.btnOK_clicked",
                    "line": 1710,
                    "context": "Analysis execution",
                },
                {
                    "file": "Modan2.py",
                    "method": "on_action_analyze_dataset_triggered",
                    "line": 659,
                    "context": "Analysis trigger",
                },
            ],
        }
        self.save_card(wait_cursor_card, "special")

        # Progress dialog usage card
        progress_card = {
            "symbol": "progress_dialog_usage",
            "kind": "analysis",
            "description": "Dialogs with progress indicators",
            "dialogs": [
                {
                    "name": "NewAnalysisDialog",
                    "file": "ModanDialogs.py",
                    "features": [
                        "Progress bar at bottom",
                        "Status messages",
                        "Auto-close on completion",
                        "Centered on screen",
                    ],
                },
                {
                    "name": "ProgressDialog",
                    "file": "ModanDialogs.py",
                    "features": ["Generic progress dialog", "Stop button", "Custom text format"],
                },
            ],
        }
        self.save_card(progress_card, "special")

        logger.info("Generated special analysis cards")

    def find_qt_connections_for_class(self, class_name: str) -> list[dict]:
        """Find Qt connections for a class"""
        connections = []

        # Search in signals
        for conn in self.qt_data.get("signals", {}).get("connections", []):
            if class_name in str(conn.get("slot", "")):
                connections.append(conn)

        return connections

    def find_methods_for_class(self, class_name: str) -> list[str]:
        """Find methods for a class"""
        for cls in self.symbols.get("classes", []):
            if cls["name"] == class_name:
                return [m["name"] for m in cls.get("methods", [])]
        return []

    def analyze_performance(self, class_name: str) -> dict:
        """Analyze performance characteristics"""
        perf = {"requires_wait_cursor": False, "has_progress": False, "blocking_operations": []}

        # Check for known performance patterns
        if "Analysis" in class_name:
            perf["requires_wait_cursor"] = True
            perf["has_progress"] = True
            perf["blocking_operations"].append("analysis computation")

        if "Exploration" in class_name:
            perf["requires_wait_cursor"] = True
            perf["blocking_operations"].append("shape grid rendering")

        return perf

    def analyze_model_relationships(self, model_name: str) -> dict:
        """Analyze database model relationships"""
        relationships = {"belongs_to": [], "has_many": []}

        # Check fields for foreign keys
        if model_name in self.db_models:
            for field in self.db_models[model_name].get("fields", []):
                if "ForeignKey" in field.get("type", ""):
                    relationships["belongs_to"].append(field["name"])

        return relationships

    def find_model_usage(self, model_name: str) -> list[str]:
        """Find where a model is used"""
        usage = []

        # Simple heuristic - check class names
        for cls in self.symbols.get("classes", []):
            if "Controller" in cls["name"] or "Dialog" in cls["name"]:
                usage.append(cls["name"])

        return usage[:5]  # Limit to top 5

    def extract_qt_metadata(self, class_data: dict) -> dict:
        """Extract Qt-specific metadata"""
        qt_meta = {
            "is_widget": any(base in ["QWidget", "QDialog", "QMainWindow"] for base in class_data.get("bases", [])),
            "signals": [],
            "slots": [],
        }

        # Find slots
        for method in class_data.get("methods", []):
            if "pyqtSlot" in method.get("decorators", []):
                qt_meta["slots"].append(method["name"])
            elif method["name"].startswith("on_") and method["name"].endswith("_triggered"):
                qt_meta["slots"].append(method["name"])

        return qt_meta

    def calculate_complexity(self, class_data: dict) -> dict:
        """Calculate class complexity metrics"""
        return {
            "method_count": len(class_data.get("methods", [])),
            "inheritance_depth": len(class_data.get("bases", [])),
            "estimated_loc": len(class_data.get("methods", [])) * 20,  # Rough estimate
        }

    def save_card(self, card: dict, category: str):
        """Save a symbol card to JSON file"""
        filename = f"{card['symbol']}.json"
        filepath = self.cards_dir / category / filename

        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(card, f, indent=2, default=str)


def main():
    project_root = Path(__file__).parent.parent
    generator = SymbolCardGenerator(project_root)
    generator.generate_all_cards()

    # Generate summary
    cards_count = sum(1 for _ in (project_root / ".index" / "cards").rglob("*.json"))
    logger.info(f"Generated {cards_count} symbol cards")


if __name__ == "__main__":
    main()

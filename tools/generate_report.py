#!/usr/bin/env python3
"""
Generate .index/INDEX_REPORT.md from the current JSON index
"""

from pathlib import Path
import json
from datetime import datetime


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def format_stats_table(stats: dict) -> str:
    rows = [
        ("Total Files", stats.get('files', 0)),
        ("Total Lines", stats.get('total_lines', 0)),
        ("Classes", stats.get('classes', 0)),
        ("Functions", stats.get('functions', 0)),
        ("Dialogs", stats.get('dialogs', 0)),
        ("Database Models", stats.get('db_models', 0)),
        ("Qt Signal Definitions", stats.get('qt_signals', 0)),
        ("Qt Connections", stats.get('qt_connections', 0)),
    ]
    lines = ["| Metric | Count |", "|--------|-------|"]
    for k, v in rows:
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def top_files_by_lines(files: dict, n: int = 5):
    sorted_files = sorted(files.items(), key=lambda kv: kv[1].get('lines', 0), reverse=True)
    return sorted_files[:n]


def most_complex_classes(symbols: dict, n: int = 4):
    classes = symbols.get('classes', [])
    scored = [(c['name'], len(c.get('methods', [])), c['file'], c['line']) for c in classes]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:n]


def list_dialogs(symbols: dict):
    return [d['name'] for d in symbols.get('dialogs', []) if 'Dialog' in d.get('name', '')]


def list_models(db_models: dict):
    return list(db_models.keys())


def main():
    repo_root = Path(__file__).parent.parent
    idx_dir = repo_root / '.index'
    summary = load_json(idx_dir / 'index_summary.json')
    symbols = load_json(idx_dir / 'symbols' / 'symbols.json')
    qt = load_json(idx_dir / 'graphs' / 'qt_signals.json')
    db = load_json(idx_dir / 'graphs' / 'db_models.json')

    generated = datetime.now().strftime('%Y-%m-%d')
    stats = summary.get('statistics', {})
    files = summary.get('files', {})

    dialogs = list_dialogs(symbols)
    models = list_models(db)
    largest = top_files_by_lines(files)
    complex_classes = most_complex_classes(symbols)

    # Assemble report
    out = []
    out.append("# Modan2 Code Index Report")
    out.append("")
    out.append(f"**Generated**: {generated}  ")
    out.append("**Index Version**: 1.1")
    out.append("")
    out.append("## Project Statistics")
    out.append("")
    out.append(format_stats_table(stats))
    out.append("")
    out.append("## Key Components Indexed")
    out.append("")
    out.append(f"### 1. Dialog Classes ({len(dialogs)})")
    for d in dialogs:
        out.append(f"- `{d}`")
    out.append("")
    out.append(f"### 2. Database Models ({len(models)})")
    for m in models:
        out.append(f"- `{m}`")
    out.append("")
    out.append("## Qt Signal/Slot Analysis")
    out.append("")
    cons = len(qt.get('connections', [])) if isinstance(qt, list) else len(qt.get('signals', {}).get('connections', []))
    defs = len(qt.get('definitions', [])) if isinstance(qt, list) else len(qt.get('signals', {}).get('definitions', []))
    out.append(f"- Signal definitions: {defs}")
    out.append(f"- Connections: {cons}")
    out.append("")
    out.append("## Code Complexity Metrics")
    out.append("")
    out.append("### Largest Files (by lines)")
    for fname, meta in largest:
        out.append(f"1. `{fname}` - {meta.get('lines', 0):,} lines")
    out.append("")
    out.append("### Most Complex Classes (by method count)")
    for name, mcount, file, line in complex_classes:
        out.append(f"1. `{name}` - {mcount} methods ({file}:{line})")
    out.append("")
    out.append("## Recommendations")
    out.append("")
    out.append("- Split very large UI files into focused modules.")
    out.append("- Extract common dialog base behaviors (validation/progress).")
    out.append("- Expand unit tests for core logic and indexing edge cases.")
    out.append("")
    out.append("## Tools Created/Used")
    out.append("")
    out.append("- `tools/build_index.py` - Build project index (AST+regex)")
    out.append("- `tools/search_index.py` - Query/search the index")
    out.append("- `tools/generate_cards.py` - Generate symbol cards")
    out.append("- `tools/generate_report.py` - Generate this report from JSON")
    out.append("")
    out.append("## Usage")
    out.append("")
    out.append("To rebuild the index:")
    out.append("\n```bash\npython tools/build_index.py\n```\n")
    out.append("To generate the report:")
    out.append("\n```bash\npython tools/generate_report.py\n```\n")

    # Write
    idx_dir.mkdir(exist_ok=True)
    (idx_dir / 'INDEX_REPORT.md').write_text("\n".join(out), encoding='utf-8')
    print("Wrote .index/INDEX_REPORT.md")


if __name__ == '__main__':
    main()


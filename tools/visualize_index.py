#!/usr/bin/env python3
"""
Modan2 Code Index Visualizer
Generates an interactive HTML dashboard from the code index
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndexVisualizer:
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.index_dir = self.project_root / '.index'
        
    def load_index_data(self) -> Dict[str, Any]:
        """Load all index data"""
        data = {}
        
        # Load summary
        summary_path = self.index_dir / 'index_summary.json'
        if summary_path.exists():
            with open(summary_path, 'r') as f:
                data['summary'] = json.load(f)
        
        # Load symbols
        symbols_path = self.index_dir / 'symbols' / 'symbols.json'
        if symbols_path.exists():
            with open(symbols_path, 'r') as f:
                data['symbols'] = json.load(f)
        
        # Load file stats
        stats_path = self.index_dir / 'symbols' / 'file_stats.json'
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                data['file_stats'] = json.load(f)
        
        # Load Qt signals
        qt_path = self.index_dir / 'graphs' / 'qt_signals.json'
        if qt_path.exists():
            with open(qt_path, 'r') as f:
                data['qt_signals'] = json.load(f)
        
        # Load DB models
        db_path = self.index_dir / 'graphs' / 'db_models.json'
        if db_path.exists():
            with open(db_path, 'r') as f:
                data['db_models'] = json.load(f)
        
        return data
    
    def generate_html_dashboard(self) -> str:
        """Generate interactive HTML dashboard"""
        data = self.load_index_data()
        
        # Prepare data for visualizations
        file_data = self.prepare_file_treemap(data.get('file_stats', {}))
        class_data = self.prepare_class_bubble(data.get('symbols', {}))
        qt_network = self.prepare_qt_network(data.get('qt_signals', {}))
        stats = data.get('summary', {}).get('statistics', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modan2 Code Index Visualization</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-top: 5px;
        }}
        .chart-container {{
            margin-bottom: 40px;
        }}
        .chart-title {{
            font-size: 1.3em;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .visualization {{
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Modan2 Code Index Visualization</h1>
        <div class="subtitle">Interactive dashboard for code structure analysis</div>
        
        <!-- Statistics Cards -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats.get('files', 0):,}</div>
                <div class="stat-label">Files</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('total_lines', 0):,}</div>
                <div class="stat-label">Lines of Code</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('classes', 0):,}</div>
                <div class="stat-label">Classes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('functions', 0):,}</div>
                <div class="stat-label">Functions</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('qt_connections', 0):,}</div>
                <div class="stat-label">Qt Connections</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats.get('dialogs', 0):,}</div>
                <div class="stat-label">Dialogs</div>
            </div>
        </div>
        
        <!-- File Size Treemap -->
        <div class="chart-container">
            <div class="chart-title">📁 File Size Distribution</div>
            <div id="treemap" class="visualization"></div>
        </div>
        
        <!-- Class Complexity Bubble Chart -->
        <div class="chart-container">
            <div class="chart-title">🔮 Class Complexity (Method Count)</div>
            <div id="bubble" class="visualization"></div>
        </div>
        
        <!-- Qt Connections Sankey Diagram -->
        <div class="chart-container">
            <div class="chart-title">🔗 Qt Signal/Slot Connections</div>
            <div id="sankey" class="visualization"></div>
        </div>
        
        <!-- File Types Pie Chart -->
        <div class="chart-container">
            <div class="chart-title">📊 Code Distribution by Component</div>
            <div id="pie" class="visualization"></div>
        </div>
    </div>
    
    <script>
        // File Size Treemap
        var treemapData = [{json.dumps(file_data)}];
        var treemapLayout = {{
            margin: {{t: 0, l: 0, r: 0, b: 0}},
            height: 500
        }};
        Plotly.newPlot('treemap', treemapData, treemapLayout);
        
        // Class Complexity Bubble Chart
        var bubbleData = [{json.dumps(class_data)}];
        var bubbleLayout = {{
            height: 500,
            xaxis: {{title: 'Line Number'}},
            yaxis: {{title: 'File'}},
            margin: {{l: 150}}
        }};
        Plotly.newPlot('bubble', bubbleData, bubbleLayout);
        
        // Qt Connections Sankey
        var sankeyData = [{json.dumps(qt_network)}];
        var sankeyLayout = {{
            height: 600,
            font: {{size: 10}}
        }};
        Plotly.newPlot('sankey', sankeyData, sankeyLayout);
        
        // Component Distribution Pie
        var pieData = [{{
            type: 'pie',
            labels: ['UI Dialogs', 'Components', 'Models', 'Statistics', 'Tests', 'Tools'],
            values: [
                {len(data.get('symbols', {}).get('dialogs', []))},
                {len([c for c in data.get('symbols', {}).get('classes', []) if 'Component' in c.get('name', '')])},
                {len(data.get('db_models', {}))},
                {len([f for f in data.get('symbols', {}).get('functions', []) if 'MdStatistics' in f.get('file', '')])},
                {len([f for f, s in data.get('file_stats', {}).items() if 'test' in f.lower()])},
                {len([f for f, s in data.get('file_stats', {}).items() if 'tools' in f])}
            ],
            hole: 0.4,
            marker: {{
                colors: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#43e97b']
            }}
        }}];
        var pieLayout = {{
            height: 400,
            margin: {{t: 0, b: 0}}
        }};
        Plotly.newPlot('pie', pieData, pieLayout);
    </script>
</body>
</html>
"""
        return html
    
    def prepare_file_treemap(self, file_stats: Dict) -> Dict:
        """Prepare data for file size treemap"""
        labels = ['Modan2']  # Root
        parents = ['']
        values = [0]
        
        for filename, stats in file_stats.items():
            labels.append(filename)
            parents.append('Modan2')
            values.append(stats.get('lines', 0))
        
        return {
            'type': 'treemap',
            'labels': labels,
            'parents': parents,
            'values': values,
            'textinfo': 'label+value',
            'marker': {'colorscale': 'Viridis'}
        }
    
    def prepare_class_bubble(self, symbols: Dict) -> Dict:
        """Prepare data for class complexity bubble chart"""
        classes = symbols.get('classes', [])
        
        x = []  # Line number
        y = []  # File name
        sizes = []  # Method count
        text = []  # Class name
        
        for cls in classes[:30]:  # Top 30 classes
            x.append(cls.get('line', 0))
            y.append(cls.get('file', 'Unknown'))
            method_count = len(cls.get('methods', []))
            sizes.append(method_count * 3)  # Scale for visibility
            text.append(f"{cls.get('name', 'Unknown')}<br>{method_count} methods")
        
        return {
            'type': 'scatter',
            'mode': 'markers',
            'x': x,
            'y': y,
            'text': text,
            'marker': {
                'size': sizes,
                'color': sizes,
                'colorscale': 'Viridis',
                'showscale': True,
                'colorbar': {'title': 'Methods'}
            },
            'hovertemplate': '%{text}<extra></extra>'
        }
    
    def prepare_qt_network(self, qt_signals: Dict) -> Dict:
        """Prepare data for Qt connections Sankey diagram"""
        connections = qt_signals.get('connections', [])[:50]  # Limit to 50 for readability
        
        # Create unique node list
        nodes = []
        node_map = {}
        
        for conn in connections:
            source = f"{conn.get('object', 'Unknown')}.{conn.get('signal', 'signal')}"
            target = conn.get('slot', 'Unknown')
            
            if source not in node_map:
                node_map[source] = len(nodes)
                nodes.append(source)
            if target not in node_map:
                node_map[target] = len(nodes)
                nodes.append(target)
        
        # Create links
        links = {
            'source': [],
            'target': [],
            'value': []
        }
        
        for conn in connections:
            source = f"{conn.get('object', 'Unknown')}.{conn.get('signal', 'signal')}"
            target = conn.get('slot', 'Unknown')
            
            links['source'].append(node_map[source])
            links['target'].append(node_map[target])
            links['value'].append(1)
        
        return {
            'type': 'sankey',
            'node': {
                'pad': 15,
                'thickness': 20,
                'line': {'color': 'black', 'width': 0.5},
                'label': nodes
            },
            'link': links
        }
    
    def save_dashboard(self, output_path: Path = None):
        """Save dashboard to HTML file"""
        if output_path is None:
            output_path = self.project_root / 'modan2_code_visualization.html'
        
        html = self.generate_html_dashboard()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Dashboard saved to {output_path}")
        logger.info(f"Open in browser: file://{output_path.absolute()}")
        
        return output_path

def main():
    visualizer = IndexVisualizer()
    output_path = visualizer.save_dashboard()
    
    # Try to open in browser (WSL-compatible)
    import platform
    import subprocess
    
    if 'microsoft' in platform.uname().release.lower():  # WSL detection
        # Convert WSL path to Windows path
        windows_path = str(output_path.absolute()).replace('/mnt/d', 'D:').replace('/', '\\')
        try:
            # Open with Windows default browser
            subprocess.run(['cmd.exe', '/c', 'start', windows_path])
            logger.info(f"Opening in Windows browser: {windows_path}")
        except Exception as e:
            logger.info(f"Could not auto-open browser: {e}")
            logger.info(f"Please open manually: {windows_path}")
    else:
        # Non-WSL environment
        import webbrowser
        webbrowser.open(f"file://{output_path.absolute()}")

if __name__ == "__main__":
    main()
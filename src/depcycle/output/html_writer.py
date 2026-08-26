"""HTML output writer for interactive dependency graphs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..graph.graph import DependencyGraph
from ..graph.node import ModuleType
from .base import IOutputWriter


class HtmlWriter(IOutputWriter):
    """Serialize a dependency graph to a self-contained HTML document."""

    def write(self, graph: DependencyGraph, dest: Optional[Path] = None) -> None:
        html = self._build_html(graph)

        if dest is None:
            print(html)
            return

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    def _build_html(self, graph: DependencyGraph) -> str:
        project = str(getattr(graph, "_project_root", ""))
        nodes = []
        edges = []

        for node in sorted(graph.nodes.values(), key=lambda n: n.name):
            nodes.append({
                "id": node.name,
                "type": node.module_type.value,
                "file": str(node.file_path) if node.file_path else "",
                "dependencies": len(node.dependencies),
            })
            for dep in sorted(node.dependencies, key=lambda d: d.name):
                edges.append({
                    "source": node.name,
                    "target": dep.name,
                })

        cycles = []
        for cycle in graph.find_cycles():
            cycles.append([node.name for node in cycle])

        summary = {
            "total_modules": len(graph.nodes),
            "local": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.LOCAL),
            "stdlib": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.STDLIB),
            "third_party": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.THIRD_PARTY),
            "unknown": sum(1 for node in graph.nodes.values() if node.module_type == ModuleType.UNKNOWN),
            "cycles_found": len(cycles),
        }

        node_json = json.dumps(nodes)
        edge_json = json.dumps(edges)
        cycle_json = json.dumps(cycles)
        summary_json = json.dumps(summary)

        return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>DepCycle</title>
  <script src=\"https://cdn.jsdelivr.net/npm/d3@7\"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f7f7f7; }}
    #app {{ display: flex; height: 100vh; }}
    .sidebar {{ width: 260px; background: #fff; border-right: 1px solid #ddd; padding: 16px; box-sizing: border-box; }}
    .content {{ flex: 1; position: relative; }}
    svg {{ width: 100%; height: 100%; background: #f0f0f0; }}
    .node {{ stroke: #333; stroke-width: 1.2px; }}
    .node.local {{ fill: #BBDEFB; }}
    .node.third_party {{ fill: #FFE0B2; }}
    .node.stdlib {{ fill: #EEEEEE; }}
    .node.unknown {{ fill: #EDE7F6; }}
    .node.cycle {{ stroke: #D32F2F; stroke-width: 3; }}
    .label {{ font-size: 12px; fill: #111; pointer-events: none; }}
    .legend {{ margin-top: 12px; }}
    .legend-item {{ display: flex; align-items: center; margin: 6px 0; }}
    .legend-swatch {{ width: 12px; height: 12px; margin-right: 8px; border-radius: 2px; border: 1px solid #444; }}
    .warning {{ background: #fdecea; color: #9f1d1d; border: 1px solid #f5c6c7; padding: 8px 10px; margin-bottom: 12px; border-radius: 4px; }}
  </style>
</head>
<body>
  <div id=\"app\">
    <aside class=\"sidebar\">
      <h2>DepCycle</h2>
      <div id=\"project\">{project}</div>
      <div id=\"warning\" class=\"warning\" style=\"display: none;\">Cycle detected</div>
      <div><strong>Modules:</strong> <span id=\"total-modules\">{summary['total_modules']}</span></div>
      <div><strong>Local:</strong> {summary['local']}</div>
      <div><strong>Stdlib:</strong> {summary['stdlib']}</div>
      <div><strong>Third-party:</strong> {summary['third_party']}</div>
      <div><strong>Unknown:</strong> {summary['unknown']}</div>
      <div><strong>Edges:</strong> <span id=\"total-edges\">{len(edges)}</span></div>
      <div class=\"legend\">
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#BBDEFB\"></span>Local</div>
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#FFE0B2\"></span>Third-party</div>
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#EEEEEE\"></span>Stdlib</div>
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#EDE7F6\"></span>Unknown</div>
      </div>
    </aside>
    <div class=\"content\">
      <svg id=\"graph\"></svg>
    </div>
  </div>

  <script>
    const nodes = {node_json};
    const edges = {edge_json};
    const cycles = {cycle_json};
    const summary = {summary_json};

    if (cycles.length) {{
      document.getElementById('warning').style.display = 'block';
      document.getElementById('warning').textContent = 'Cycle detected: ' + cycles.map(c => c.join(' -> ')).join(' | ');
    }}

    const svg = d3.select('#graph');
    const width = svg.node().clientWidth || 900;
    const height = svg.node().clientHeight || 700;

    const colorMap = {{
      local: '#BBDEFB',
      third_party: '#FFE0B2',
      stdlib: '#EEEEEE',
      unknown: '#EDE7F6'
    }};

    const link = svg.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', '#666')
      .attr('stroke-width', 1.5);

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(function(d) {{ return d.id; }}).distance(90))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const node = svg.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag()
        .on('start', function(event) {{ if (!event.active) simulation.alphaTarget(0.3).restart(); }})
        .on('drag', function(event) {{ event.subject.x = event.x; event.subject.y = event.y; }})
        .on('end', function(event) {{ if (!event.active) simulation.alphaTarget(0); }})
      );

    node.append('circle')
      .attr('r', 18)
      .attr('class', function(d) {{ return 'node ' + d.type; }})
      .attr('fill', function(d) {{ return colorMap[d.type] || '#EDE7F6'; }});

    node.append('text')
      .attr('class', 'label')
      .attr('text-anchor', 'middle')
      .attr('dy', 4)
      .text(function(d) {{ return d.id.split('.').slice(-1)[0]; }});

    simulation.on('tick', function() {{
      link
        .attr('x1', function(d) {{ return d.source.x; }})
        .attr('y1', function(d) {{ return d.source.y; }})
        .attr('x2', function(d) {{ return d.target.x; }})
        .attr('y2', function(d) {{ return d.target.y; }});

      node.attr('transform', function(d) {{ return 'translate(' + d.x + ',' + d.y + ')'; }});
    }});
  </script>
</body>
</html>
"""

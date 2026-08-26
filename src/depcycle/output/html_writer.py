"""HTML output writer for interactive dependency graphs."""

from __future__ import annotations

import json
from pathlib import Path

from ..graph.graph import DependencyGraph
from ..graph.node import ModuleType
from .base import IOutputWriter, project_label, relative_file_path


class HtmlWriter(IOutputWriter):
    """Serialize a dependency graph to a self-contained HTML document."""

    def write(self, graph: DependencyGraph, dest: Path | None = None) -> None:
        html = self._build_html(graph)

        if dest is None:
            print(html)
            return

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    def _build_html(self, graph: DependencyGraph) -> str:
        project = project_label(graph)
        nodes = []
        edges = []

        for node in sorted(graph.nodes.values(), key=lambda n: n.name):
            nodes.append({
                "id": node.name,
                "type": node.module_type.value,
                "file": relative_file_path(graph, node.file_path),
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
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f7f7f7; color: #17202a; }}
    #app {{ display: flex; height: 100vh; }}
    .sidebar {{ width: 320px; flex: 0 0 320px; background: #fff; border-right: 1px solid #d9e2ec; padding: 24px 20px; box-sizing: border-box; overflow-y: auto; }}
    .sidebar.collapsed {{ width: 0; flex-basis: 0; padding-left: 0; padding-right: 0; border-right: 0; overflow: hidden; }}
    .brand {{ margin: 0; color: #102a43; font-size: 25px; letter-spacing: 0; }}
    .eyebrow {{ color: #829ab1; font-size: 11px; font-weight: 700; letter-spacing: 0; text-transform: uppercase; margin: 24px 0 5px; }}
    .content {{ flex: 1; position: relative; }}
    .graph-header {{ position: absolute; z-index: 2; top: 18px; left: 22px; right: 22px; display: flex; align-items: center; justify-content: space-between; gap: 16px; pointer-events: none; }}
    .graph-heading {{ display: flex; align-items: center; gap: 10px; pointer-events: auto; }}
    .graph-title {{ margin: 0; color: #243b53; font-size: 14px; font-weight: 700; }}
    .graph-meta {{ color: #829ab1; font-size: 12px; margin-top: 3px; }}
    .graph-toolbar {{ display: flex; gap: 6px; pointer-events: auto; }}
    .panel-toggle {{ width: 32px; height: 32px; border: 1px solid #bcccdc; border-radius: 4px; background: rgba(255, 255, 255, .94); color: #243b53; font-size: 20px; font-weight: 400; line-height: 1; cursor: pointer; box-shadow: 0 1px 3px rgba(16, 42, 67, .12); }}
    .panel-toggle:hover {{ background: #fff; border-color: #829ab1; }}
    svg {{ width: 100%; height: 100%; background: #f4f7f9; }}
    .node {{ stroke: #333; stroke-width: 1.2px; cursor: pointer; }}
    .node.local {{ fill: #BBDEFB; }}
    .node.third_party {{ fill: #FFE0B2; }}
    .node.stdlib {{ fill: #EEEEEE; }}
    .node.unknown {{ fill: #EDE7F6; }}
    .node.cycle {{ stroke: #D32F2F; stroke-width: 3; }}
    .label {{ font-family: monospace; font-size: 11px; fill: #111; pointer-events: none; }}
    .legend {{ margin-top: 12px; }}
    .legend-item {{ display: flex; align-items: center; margin: 6px 0; }}
    .legend-swatch {{ width: 12px; height: 12px; margin-right: 8px; border-radius: 2px; border: 1px solid #444; }}
    .warning {{ background: #fff5f5; color: #9f1d1d; border: 1px solid #f5c6c7; padding: 11px 12px; margin: 18px 0; border-radius: 4px; line-height: 1.35; overflow-wrap: anywhere; }}
    .project {{ color: #52606d; font-size: 12px; line-height: 1.4; overflow-wrap: anywhere; margin-bottom: 16px; }}
    .edge {{ fill: none; stroke: #657786; stroke-width: 1.6px; marker-end: url(#arrow); }}
    .edge.cycle {{ stroke: #D32F2F; stroke-width: 2.8px; }}
    .node.dim, .edge.dim {{ opacity: 0.14; }}
    .node.selected {{ stroke: #111; stroke-width: 3px; }}
    .hint {{ color: #52606d; font-size: 12px; margin-top: 18px; line-height: 1.4; }}
    .stats {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px 16px; margin: 18px 0; }}
    .stat {{ border-bottom: 1px solid #e6edf3; padding-bottom: 8px; }}
    .stat-label {{ display: block; color: #627d98; font-size: 11px; margin-bottom: 2px; }}
    .stat-value {{ color: #102a43; font-size: 19px; font-weight: 700; }}
    .section-title {{ color: #486581; font-size: 11px; font-weight: 700; text-transform: uppercase; margin: 22px 0 8px; }}
    .zoom-controls button {{ min-width: 34px; height: 32px; border: 1px solid #bcccdc; border-radius: 4px; background: rgba(255, 255, 255, .94); color: #243b53; font-size: 17px; font-weight: 700; line-height: 1; cursor: pointer; box-shadow: 0 1px 3px rgba(16, 42, 67, .12); }}
    .zoom-controls button:last-child {{ padding: 0 10px; font-size: 12px; }}
    .zoom-controls button:hover {{ background: #fff; border-color: #829ab1; }}
  </style>
</head>
<body>
  <div id=\"app\">
    <aside class=\"sidebar\">
      <h1 class=\"brand\">DepCycle</h1>
      <div class=\"eyebrow\">Dependency report</div>
      <div id=\"project\" class=\"project\">{project}</div>
      <div id=\"warning\" class=\"warning\" style=\"display: none;\">Cycle detected</div>
      <div class=\"section-title\">Overview</div>
      <div class=\"stats\">
        <div class=\"stat\"><span class=\"stat-label\">Modules</span><span class=\"stat-value\" id=\"total-modules\">{summary['total_modules']}</span></div>
        <div class=\"stat\"><span class=\"stat-label\">Edges</span><span class=\"stat-value\" id=\"total-edges\">{len(edges)}</span></div>
        <div class=\"stat\"><span class=\"stat-label\">Local</span><span class=\"stat-value\">{summary['local']}</span></div>
        <div class=\"stat\"><span class=\"stat-label\">Stdlib</span><span class=\"stat-value\">{summary['stdlib']}</span></div>
        <div class=\"stat\"><span class=\"stat-label\">Third-party</span><span class=\"stat-value\">{summary['third_party']}</span></div>
        <div class=\"stat\"><span class=\"stat-label\">Unknown</span><span class=\"stat-value\">{summary['unknown']}</span></div>
      </div>
      <div class=\"section-title\">Node types</div>
      <div class=\"legend\">
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#BBDEFB\"></span>Local</div>
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#FFE0B2\"></span>Third-party</div>
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#EEEEEE\"></span>Stdlib</div>
        <div class=\"legend-item\"><span class=\"legend-swatch\" style=\"background:#EDE7F6\"></span>Unknown</div>
      </div>
      <div class=\"hint\">Arrows show import direction. Click a module to highlight its direct dependencies and dependents.</div>
    </aside>
    <div class=\"content\">
      <div class=\"graph-header\">
        <div class=\"graph-heading\">
          <button id=\"panel-toggle\" class=\"panel-toggle\" type=\"button\" title=\"Hide report panel\" aria-label=\"Hide report panel\">‹</button>
          <div>
            <div class=\"graph-title\">Dependency map</div>
            <div class=\"graph-meta\">{summary['total_modules']} modules · {len(edges)} directed edges</div>
          </div>
        </div>
        <div class=\"graph-toolbar zoom-controls\" aria-label=\"Graph zoom controls\">
          <button id=\"zoom-in\" type=\"button\" title=\"Zoom in\" aria-label=\"Zoom in\">+</button>
          <button id=\"zoom-out\" type=\"button\" title=\"Zoom out\" aria-label=\"Zoom out\">−</button>
          <button id=\"zoom-fit\" type=\"button\" title=\"Fit graph to view\">Fit</button>
        </div>
      </div>
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
    const graphLayer = svg.append('g');
    const zoom = d3.zoom()
      .scaleExtent([0.25, 3])
      .on('zoom', function(event) {{ graphLayer.attr('transform', event.transform); }});
    svg.call(zoom);

    const colorMap = {{
      local: '#BBDEFB',
      third_party: '#FFE0B2',
      stdlib: '#EEEEEE',
      unknown: '#EDE7F6'
    }};

    const defs = svg.append('defs');
    defs.append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 9)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5Z')
      .attr('fill', '#657786');

    const cycleEdges = new Set();
    cycles.forEach(function(cycle) {{
      for (let i = 0; i < cycle.length - 1; i += 1) {{
        cycleEdges.add(cycle[i] + '->' + cycle[i + 1]);
      }}
    }});

    // Give dependencies a left-to-right reading order before applying gentle force spacing.
    const incoming = new Map(nodes.map(function(d) {{ return [d.id, 0]; }}));
    const outgoing = new Map(nodes.map(function(d) {{ return [d.id, []]; }}));
    edges.forEach(function(edge) {{
      incoming.set(edge.target, (incoming.get(edge.target) || 0) + 1);
      outgoing.get(edge.source).push(edge.target);
    }});
    const queue = nodes.filter(function(d) {{ return incoming.get(d.id) === 0; }}).map(function(d) {{ return d.id; }});
    const layers = new Map(nodes.map(function(d) {{ return [d.id, 0]; }}));
    while (queue.length) {{
      const current = queue.shift();
      outgoing.get(current).forEach(function(target) {{
        layers.set(target, Math.max(layers.get(target), layers.get(current) + 1));
        incoming.set(target, incoming.get(target) - 1);
        if (incoming.get(target) === 0) queue.push(target);
      }});
    }}
    const unresolvedLayer = Math.max.apply(null, Array.from(layers.values())) + 1;
    nodes.forEach(function(d) {{
      if (incoming.get(d.id) > 0) layers.set(d.id, unresolvedLayer);
      d.layer = layers.get(d.id);
    }});
    cycles.forEach(function(cycle) {{
      cycle.slice(0, -1).forEach(function(moduleName, index) {{
        const node = nodes.find(function(d) {{ return d.id === moduleName; }});
        if (node) node.layer = unresolvedLayer + index;
      }});
    }});
    const maxLayer = nodes.length ? Math.max.apply(null, nodes.map(function(d) {{ return d.layer; }})) : 0;
    const layerWidth = maxLayer ? Math.min(160, Math.max(60, (width - 300) / maxLayer)) : 0;

    const link = graphLayer.append('g')
      .selectAll('path')
      .data(edges)
      .join('path')
      .attr('class', function(d) {{ return 'edge' + (cycleEdges.has(d.source + '->' + d.target) ? ' cycle' : ''); }});

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(function(d) {{ return d.id; }}).distance(130))
      .force('charge', d3.forceManyBody().strength(-450))
      .force('collide', d3.forceCollide(42))
      .force('x', d3.forceX(function(d) {{ return maxLayer ? 80 + d.layer * layerWidth : width / 2; }}).strength(0.9))
      .force('y', d3.forceY(height / 2).strength(0.08))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const node = graphLayer.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag()
        .on('start', function(event) {{
          if (!event.active) simulation.alphaTarget(0.3).restart();
          event.subject.fx = event.subject.x;
          event.subject.fy = event.subject.y;
        }})
        .on('drag', function(event) {{
          event.subject.fx = event.x;
          event.subject.fy = event.y;
        }})
        .on('end', function(event) {{
          if (!event.active) simulation.alphaTarget(0);
        }})
      );

    node.append('circle')
      .attr('r', 10)
      .attr('class', function(d) {{ return 'node ' + d.type; }})
      .attr('fill', function(d) {{ return colorMap[d.type] || '#EDE7F6'; }});

    node.append('text')
      .attr('class', 'label')
      .attr('text-anchor', 'start')
      .attr('x', 14)
      .attr('dy', 4)
      .text(function(d) {{ return d.id.split('.').slice(-2).join('.'); }});

    node.append('title')
      .text(function(d) {{ return d.id + ' (' + d.type + ')\\n' + (d.file || 'external module') + '\\n' + d.dependencies + ' direct dependencies'; }});

    function endpoint(source, target, distance) {{
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const length = Math.sqrt(dx * dx + dy * dy) || 1;
      return {{ x: source.x + (dx / length) * distance, y: source.y + (dy / length) * distance }};
    }}

    function edgePath(edge) {{
      const start = endpoint(edge.source, edge.target, 11);
      const end = endpoint(edge.target, edge.source, 14);
      return 'M' + start.x + ',' + start.y + 'L' + end.x + ',' + end.y;
    }}

    node.on('click', function(event, selected) {{
      const related = new Set([selected.id]);
      edges.forEach(function(edge) {{
        if (edge.source.id === selected.id) related.add(edge.target.id);
        if (edge.target.id === selected.id) related.add(edge.source.id);
      }});
      node.classed('dim', function(d) {{ return !related.has(d.id); }})
        .classed('selected', function(d) {{ return d.id === selected.id; }});
      link.classed('dim', function(edge) {{ return edge.source.id !== selected.id && edge.target.id !== selected.id; }});
      event.stopPropagation();
    }});

    node.on('dblclick', function(event, selected) {{
      selected.fx = null;
      selected.fy = null;
      simulation.alpha(0.25).restart();
      event.stopPropagation();
    }});

    svg.on('click', function() {{
      node.classed('dim', false).classed('selected', false);
      link.classed('dim', false);
    }});

    simulation.on('tick', function() {{
      nodes.forEach(function(d) {{
        if (d.fx == null && d.fy == null) {{
          d.x = Math.max(40, Math.min(width - 200, d.x));
          d.y = Math.max(55, Math.min(height - 40, d.y));
        }}
      }});
      link.attr('d', edgePath);

      node.attr('transform', function(d) {{ return 'translate(' + d.x + ',' + d.y + ')'; }});
    }});

    function arrangeInitialLayout() {{
      const groups = new Map();
      nodes.forEach(function(d) {{
        if (!groups.has(d.layer)) groups.set(d.layer, []);
        groups.get(d.layer).push(d);
      }});
      groups.forEach(function(group) {{
        group.sort(function(a, b) {{ return a.id.localeCompare(b.id); }});
        const gap = Math.max(70, Math.min(120, (height - 140) / Math.max(1, group.length)));
        const startY = height / 2 - ((group.length - 1) * gap) / 2;
        group.forEach(function(d, index) {{
          d.x = maxLayer ? Math.min(width - 200, 80 + d.layer * layerWidth) : width / 2;
          d.y = startY + index * gap;
        }});
      }});
      link.attr('d', edgePath);
      node.attr('transform', function(d) {{ return 'translate(' + d.x + ',' + d.y + ')'; }});
    }}

    function fitGraph() {{
      const bounds = graphLayer.node().getBBox();
      if (!bounds.width || !bounds.height) return;
      const padding = 56;
      const viewWidth = svg.node().clientWidth || width;
      const viewHeight = svg.node().clientHeight || height;
      const scale = Math.max(0.55, Math.min(1, (viewWidth - padding * 2) / bounds.width, (viewHeight - padding * 2) / bounds.height));
      const x = (viewWidth - bounds.width * scale) / 2 - bounds.x * scale;
      const y = (viewHeight - bounds.height * scale) / 2 - bounds.y * scale;
      svg.call(zoom.transform, d3.zoomIdentity.translate(x, y).scale(scale));
    }}

    arrangeInitialLayout();
    fitGraph();
    document.getElementById('zoom-in').addEventListener('click', function() {{ svg.transition().call(zoom.scaleBy, 1.25); }});
    document.getElementById('zoom-out').addEventListener('click', function() {{ svg.transition().call(zoom.scaleBy, 0.8); }});
    document.getElementById('zoom-fit').addEventListener('click', fitGraph);
    document.getElementById('panel-toggle').addEventListener('click', function(event) {{
      const sidebar = document.querySelector('.sidebar');
      const collapsed = sidebar.classList.toggle('collapsed');
      event.currentTarget.textContent = collapsed ? '›' : '‹';
      event.currentTarget.title = collapsed ? 'Show report panel' : 'Hide report panel';
      event.currentTarget.setAttribute('aria-label', event.currentTarget.title);
      window.setTimeout(fitGraph, 0);
    }});
  </script>
</body>
</html>
"""

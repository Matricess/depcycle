"""HTML output writer for interactive dependency graphs."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path

from .base import GraphExport, IOutputWriter


class HtmlWriter(IOutputWriter):
    """
    Serialize a dependency graph to a self-contained interactive HTML document.

    D3 is responsible for rendering, interaction, zooming, and selection.
    ELK is used as an optional layout enhancement; a deterministic layered
    fallback keeps the graph visible when ELK cannot initialize or fails.
    """

    _D3_ASSET = "assets/d3.v7.min.js"
    _ELK_ASSET = "assets/elk.bundled.min.js"

    @staticmethod
    def _json_for_script(value: object) -> str:
        """Serialize data safely for embedding inside an HTML script block."""
        return (
            json.dumps(
                value,
                ensure_ascii=False,
            )
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029")
        )

    @classmethod
    def _read_asset(cls, asset_name: str) -> str:
        """Read a bundled JavaScript asset from the package."""
        try:
            resource = files("depcycle.output").joinpath(
                asset_name,
            )

            return resource.read_text(
                encoding="utf-8",
            )
        except (
            FileNotFoundError,
            ModuleNotFoundError,
            OSError,
        ) as exc:
            raise RuntimeError(f"Required HTML asset is missing: {asset_name}") from exc

    @classmethod
    def _load_javascript_assets(cls) -> tuple[str, str]:
        """Load the bundled D3 and ELK JavaScript sources."""
        return (
            cls._read_asset(cls._D3_ASSET),
            cls._read_asset(cls._ELK_ASSET),
        )

    @staticmethod
    def _template() -> str:
        """Return the HTML template."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
  />
  <title>DepCycle</title>

  <link
    rel="icon"
    type="image/svg+xml"
    href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23102a43'/%3E%3Cpath d='M18 20h28M18 20v24M46 20v24M18 44h28' fill='none' stroke='%23ffffff' stroke-width='5' stroke-linecap='round'/%3E%3Ccircle cx='18' cy='20' r='6' fill='%23ffffff'/%3E%3Ccircle cx='46' cy='20' r='6' fill='%23ffffff'/%3E%3Ccircle cx='18' cy='44' r='6' fill='%23ffffff'/%3E%3Ccircle cx='46' cy='44' r='6' fill='%23ffffff'/%3E%3C/svg%3E"
  />

  <script>
__D3_SOURCE__
  </script>

  <script>
__ELK_SOURCE__
  </script>

  <style>
    :root {
      --bg: #f4f7fa;
      --panel: #ffffff;
      --border: #d9e2ec;
      --text: #243b53;
      --muted: #627d98;
      --soft: #829ab1;
      --local-fill: #dbeafe;
      --local-border: #2563eb;
      --third-fill: #ffedd5;
      --third-border: #ea580c;
      --stdlib-fill: #f1f5f9;
      --stdlib-border: #64748b;
      --unknown-fill: #ede9fe;
      --unknown-border: #7c3aed;
      --edge: #7b8794;
      --cycle: #d32f2f;
      --selected: #102a43;
      --shadow: rgba(16, 42, 67, 0.10);
    }

    * {
      box-sizing: border-box;
    }

    html,
    body {
      width: 100%;
      height: 100%;
      margin: 0;
    }

    body {
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;
      background: var(--bg);
      color: var(--text);
      overflow: hidden;
    }

    button,
    input {
      font: inherit;
    }

    button {
      appearance: none;
    }

    #app {
      display: flex;
      width: 100%;
      height: 100vh;
    }

    .sidebar {
      width: 340px;
      flex: 0 0 340px;
      padding: 22px 20px;
      background: var(--panel);
      border-right: 1px solid var(--border);
      overflow-y: auto;
      transition:
        width 0.18s ease,
        flex-basis 0.18s ease,
        padding 0.18s ease;
    }

    .sidebar.collapsed {
      width: 0;
      flex-basis: 0;
      padding-left: 0;
      padding-right: 0;
      border-right: 0;
      overflow: hidden;
    }

    .brand {
      margin: 0;
      color: #102a43;
      font-size: 26px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }

    .eyebrow {
      margin: 5px 0 18px;
      color: var(--soft);
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .project {
      margin-bottom: 16px;
      color: #52606d;
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }

    .section-title {
      margin: 20px 0 9px;
      color: #486581;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .warning {
      display: none;
      margin: 0 0 18px;
      padding: 11px 12px;
      background: #fff5f5;
      border: 1px solid #f5c6c7;
      border-radius: 6px;
      color: #9f1d1d;
      font-size: 12px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }

    .search {
      display: flex;
      gap: 7px;
    }

    .search input {
      width: 100%;
      min-width: 0;
      height: 35px;
      padding: 0 10px;
      border: 1px solid var(--border);
      border-radius: 5px;
      outline: none;
      color: var(--text);
      background: #fff;
    }

    .search input:focus {
      border-color: var(--soft);
      box-shadow: 0 0 0 2px rgba(98, 125, 152, 0.12);
    }

    .focus-controls {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 6px;
    }

    .focus-controls button,
    .details-reset {
      min-width: 0;
      height: 34px;
      padding: 0 8px;
      border: 1px solid var(--border);
      border-radius: 5px;
      background: #fff;
      color: #334e68;
      font-size: 11px;
      cursor: pointer;
    }

    .focus-controls button:hover,
    .details-reset:hover {
      border-color: var(--soft);
      background: #f8fafc;
    }

    .focus-controls button.active {
      border-color: #2563eb;
      background: #eff6ff;
      color: #1d4ed8;
    }

    .stats {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 14px;
    }

    .stat {
      padding-bottom: 8px;
      border-bottom: 1px solid #e6edf3;
    }

    .stat-label {
      display: block;
      margin-bottom: 2px;
      color: var(--muted);
      font-size: 10px;
    }

    .stat-value {
      color: #102a43;
      font-size: 19px;
      font-weight: 700;
    }

    .legend-item {
      display: flex;
      align-items: center;
      margin: 7px 0;
      color: #334e68;
      font-size: 12px;
    }

    .legend-swatch {
      width: 12px;
      height: 12px;
      margin-right: 8px;
      border: 1px solid #444;
      border-radius: 3px;
      flex: 0 0 12px;
    }

    .hint {
      margin-top: 18px;
      color: var(--muted);
      font-size: 11px;
      line-height: 1.5;
    }

    .details-card {
      padding: 12px;
      border: 1px solid var(--border);
      border-radius: 7px;
      background: #f8fafc;
    }

    .details-empty {
      color: var(--muted);
      font-size: 11px;
      line-height: 1.5;
    }

    .details-name {
      margin-bottom: 5px;
      color: #102a43;
      font-size: 15px;
      font-weight: 700;
      word-break: break-word;
    }

    .details-type {
      display: inline-block;
      margin-bottom: 10px;
      padding: 3px 7px;
      border-radius: 999px;
      background: #e6edf3;
      color: #334e68;
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .details-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-bottom: 10px;
    }

    .details-metric {
      padding: 7px 8px;
      border: 1px solid #e6edf3;
      border-radius: 5px;
      background: #fff;
    }

    .details-metric-label {
      display: block;
      margin-bottom: 2px;
      color: var(--muted);
      font-size: 9px;
    }

    .details-metric-value {
      color: #102a43;
      font-size: 15px;
      font-weight: 700;
    }

    .details-file {
      margin-bottom: 10px;
      color: #52606d;
      font-family: monospace;
      font-size: 9px;
      line-height: 1.45;
      overflow-wrap: anywhere;
    }

    .details-cycle {
      margin-top: 6px;
      padding: 8px;
      border: 1px solid #f5c6c7;
      border-radius: 5px;
      background: #fff5f5;
      color: #9f1d1d;
      font-size: 10px;
      line-height: 1.4;
    }

    .details-reset {
      width: 100%;
    }

    .content {
      position: relative;
      flex: 1;
      min-width: 0;
      height: 100%;
    }

    .graph-header {
      position: absolute;
      z-index: 5;
      top: 16px;
      left: 16px;
      right: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      pointer-events: none;
    }

    .graph-heading,
    .graph-toolbar {
      pointer-events: auto;
    }

    .graph-heading {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .graph-title {
      color: #243b53;
      font-size: 14px;
      font-weight: 700;
    }

    .graph-meta {
      margin-top: 2px;
      color: var(--soft);
      font-size: 11px;
    }

    .toolbar {
      display: flex;
      gap: 6px;
    }

    .toolbar button,
    .panel-toggle {
      min-width: 34px;
      height: 34px;
      padding: 0 10px;
      border: 1px solid #bcccdc;
      border-radius: 5px;
      background: rgba(255, 255, 255, 0.95);
      color: #243b53;
      cursor: pointer;
      box-shadow: 0 1px 3px var(--shadow);
    }

    .toolbar button:hover,
    .panel-toggle:hover {
      background: #fff;
      border-color: var(--soft);
    }

    .toolbar button {
      font-size: 16px;
      font-weight: 700;
    }

    .toolbar button:last-child {
      font-size: 12px;
    }

    .panel-toggle {
      width: 34px;
      padding: 0;
      font-size: 21px;
      line-height: 1;
    }

    #graph {
      width: 100%;
      height: 100%;
      background:
        radial-gradient(
          circle at 1px 1px,
          rgba(98, 125, 152, 0.15) 1px,
          transparent 0
        );
      background-size: 24px 24px;
      background-color: var(--bg);
      cursor: grab;
    }

    #graph:active {
      cursor: grabbing;
    }

    .edge {
      fill: none;
      stroke: var(--edge);
      stroke-width: 1.7px;
      marker-end: url(#arrow);
      transition:
        opacity 0.15s ease,
        stroke-width 0.15s ease;
    }

    .edge.cycle {
      stroke: var(--cycle);
      stroke-width: 3px;
      marker-end: url(#arrow-cycle);
    }

    .edge.dim {
      opacity: 0.10;
    }

    .edge.focused {
      stroke-width: 2.8px;
    }

    .node-group {
      cursor: pointer;
    }

    .node {
      stroke-width: 1.5px;
      transition:
        opacity 0.15s ease,
        stroke-width 0.15s ease;
    }

    .node.local {
      fill: var(--local-fill);
      stroke: var(--local-border);
    }

    .node.third_party {
      fill: var(--third-fill);
      stroke: var(--third-border);
    }

    .node.stdlib {
      fill: var(--stdlib-fill);
      stroke: var(--stdlib-border);
    }

    .node.unknown {
      fill: var(--unknown-fill);
      stroke: var(--unknown-border);
    }

    .node.cycle {
      stroke: var(--cycle);
      stroke-width: 3px;
    }

    .node.selected {
      stroke: var(--selected);
      stroke-width: 3px;
    }

    .node.dim {
      opacity: 0.14;
    }

    .node.focused {
      stroke-width: 2.4px;
    }

    .node-label {
      fill: #102a43;
      font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Arial,
        sans-serif;
      font-size: 12px;
      font-weight: 600;
      pointer-events: none;
      user-select: none;
    }

    .node-label.small {
      font-size: 11px;
    }

    .node-subtitle {
      fill: #627d98;
      font-family: monospace;
      font-size: 9px;
      pointer-events: none;
      user-select: none;
    }

    .node-group.search-match .node {
      stroke: #111827;
      stroke-width: 3px;
    }

    .empty-state {
      position: absolute;
      z-index: 4;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      padding: 14px 16px;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.94);
      color: var(--muted);
      font-size: 12px;
      box-shadow: 0 2px 10px var(--shadow);
      pointer-events: none;
      display: none;
    }

    @media (max-width: 720px) {
      .sidebar {
        width: 280px;
        flex-basis: 280px;
      }

      .graph-toolbar button {
        min-width: 30px;
        padding: 0 7px;
      }

      .graph-meta {
        display: none;
      }
    }
  </style>
</head>

<body>
  <div id="app">
    <aside class="sidebar">
      <h1 class="brand">DepCycle</h1>

      <div class="eyebrow">
        Dependency report
      </div>

      <div
        id="project"
        class="project"
      ></div>

      <div
        id="warning"
        class="warning"
      ></div>

      <div class="section-title">
        Search
      </div>

      <div class="search">
        <input
          id="search"
          type="search"
          placeholder="Search modules..."
          autocomplete="off"
        />
      </div>

      <div class="section-title">
        Focus
      </div>

      <div class="focus-controls">
        <button
          id="focus-one"
          type="button"
          title="Focus one hop"
        >
          1 hop
        </button>

        <button
          id="focus-two"
          type="button"
          title="Focus two hops"
        >
          2 hops
        </button>

        <button
          id="focus-reset"
          type="button"
          title="Reset focus"
        >
          Reset
        </button>
      </div>

      <div class="section-title">
        Overview
      </div>

      <div class="stats">
        <div class="stat">
          <span class="stat-label">Modules</span>
          <span
            class="stat-value"
            id="total-modules"
          ></span>
        </div>

        <div class="stat">
          <span class="stat-label">Edges</span>
          <span
            class="stat-value"
            id="total-edges"
          ></span>
        </div>

        <div class="stat">
          <span class="stat-label">Local</span>
          <span
            class="stat-value"
            id="total-local"
          ></span>
        </div>

        <div class="stat">
          <span class="stat-label">Stdlib</span>
          <span
            class="stat-value"
            id="total-stdlib"
          ></span>
        </div>

        <div class="stat">
          <span class="stat-label">Third-party</span>
          <span
            class="stat-value"
            id="total-third-party"
          ></span>
        </div>

        <div class="stat">
          <span class="stat-label">Unknown</span>
          <span
            class="stat-value"
            id="total-unknown"
          ></span>
        </div>
      </div>

      <div class="section-title">
        Selected module
      </div>

      <div
        id="details"
        class="details-card"
      >
        <div class="details-empty">
          Click a module to inspect it.
        </div>
      </div>

      <div class="section-title">
        Node types
      </div>

      <div>
        <div class="legend-item">
          <span
            class="legend-swatch"
            style="background:#dbeafe;border-color:#2563eb"
          ></span>
          Local
        </div>

        <div class="legend-item">
          <span
            class="legend-swatch"
            style="background:#ffedd5;border-color:#ea580c"
          ></span>
          Third-party
        </div>

        <div class="legend-item">
          <span
            class="legend-swatch"
            style="background:#f1f5f9;border-color:#64748b"
          ></span>
          Stdlib
        </div>

        <div class="legend-item">
          <span
            class="legend-swatch"
            style="background:#ede9fe;border-color:#7c3aed"
          ></span>
          Unknown
        </div>
      </div>

      <div class="hint">
        Arrows show import direction.
        Click a module to inspect it and
        highlight direct relationships.
        Use Focus to explore larger graphs.
      </div>
    </aside>

    <main class="content">
      <div class="graph-header">
        <div class="graph-heading">
          <button
            id="panel-toggle"
            class="panel-toggle"
            type="button"
            title="Hide report panel"
            aria-label="Hide report panel"
          >
            ‹
          </button>

          <div>
            <div class="graph-title">
              Dependency map
            </div>

            <div
              class="graph-meta"
              id="graph-meta"
            ></div>
          </div>
        </div>

        <div
          class="graph-toolbar toolbar"
          aria-label="Graph controls"
        >
          <button
            id="zoom-in"
            type="button"
            title="Zoom in"
            aria-label="Zoom in"
          >
            +
          </button>

          <button
            id="zoom-out"
            type="button"
            title="Zoom out"
            aria-label="Zoom out"
          >
            −
          </button>

          <button
            id="zoom-fit"
            type="button"
            title="Fit graph"
            aria-label="Fit graph"
          >
            Fit
          </button>
        </div>
      </div>

      <svg id="graph"></svg>

      <div
        id="empty-state"
        class="empty-state"
      >
        No modules match your search.
      </div>
    </main>
  </div>

  <script>
    const nodes = __NODE_JSON__;
    const edges = __EDGE_JSON__;
    const cycles = __CYCLE_JSON__;
    const summary = __SUMMARY_JSON__;
    const project = __PROJECT_JSON__;

    const svg = d3.select('#graph');
    const svgNode = svg.node();

    document.getElementById('project').textContent =
      project;

    document.getElementById('total-modules').textContent =
      summary.total_modules;

    document.getElementById('total-edges').textContent =
      edges.length;

    document.getElementById('total-local').textContent =
      summary.local;

    document.getElementById('total-stdlib').textContent =
      summary.stdlib;

    document.getElementById('total-third-party').textContent =
      summary.third_party;

    document.getElementById('total-unknown').textContent =
      summary.unknown;

    document.getElementById('graph-meta').textContent =
      summary.total_modules +
      ' modules · ' +
      edges.length +
      ' directed edges';

    const warning =
      document.getElementById('warning');

    if (cycles.length) {
      warning.style.display = 'block';

      warning.textContent =
        cycles
          .map(function(cycle) {
            return (
              'Cycle: ' +
              cycle.nodes.join(' → ')
            );
          })
          .join(' | ');
    }

    const denseGraph = nodes.length > 80;

    const state = {
      selectedId: null,
      focusDepth: null,
      searchQuery: '',
      layoutReady: false,
      sidebarCollapsed: false,
    };

    const graphLayer =
      svg.append('g');

    const defs =
      svg.append('defs');

    defs
      .append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr(
        'd',
        'M0,-5L10,0L0,5Z',
      )
      .attr(
        'fill',
        '#7b8794',
      );

    defs
      .append('marker')
      .attr('id', 'arrow-cycle')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr(
        'd',
        'M0,-5L10,0L0,5Z',
      )
      .attr(
        'fill',
        '#d32f2f',
      );

    const zoom = d3.zoom()
      .scaleExtent([0.15, 4])
      .on('zoom', function(event) {
        graphLayer.attr(
          'transform',
          event.transform,
        );
      });

    svg.call(zoom);

    const nodeById =
      new Map(
        nodes.map(function(node) {
          return [
            node.id,
            node,
          ];
        })
      );

    const outgoing =
      new Map(
        nodes.map(function(node) {
          return [
            node.id,
            [],
          ];
        })
      );

    const incoming =
      new Map(
        nodes.map(function(node) {
          return [
            node.id,
            [],
          ];
        })
      );

    edges.forEach(function(edge) {
      const outgoingTargets =
        outgoing.get(edge.source);

      if (outgoingTargets) {
        outgoingTargets.push(edge.target);
      }

      const incomingSources =
        incoming.get(edge.target);

      if (incomingSources) {
        incomingSources.push(edge.source);
      }
    });

    const cycleNodeIds =
      new Set();

    cycles.forEach(function(cycle) {
      cycle.nodes
        .slice(0, -1)
        .forEach(function(name) {
          cycleNodeIds.add(name);
        });
    });

    function createFallbackLayout() {
      const remainingIncoming =
        new Map(
          nodes.map(function(node) {
            return [
              node.id,
              incoming.get(node.id).length,
            ];
          })
        );

      const layers =
        new Map(
          nodes.map(function(node) {
            return [
              node.id,
              0,
            ];
          })
        );

      const queue =
        nodes
          .filter(function(node) {
            return (
              remainingIncoming.get(
                node.id,
              ) === 0
            );
          })
          .map(function(node) {
            return node.id;
          });

      let queueIndex = 0;

      while (
        queueIndex < queue.length
      ) {
        const current =
          queue[queueIndex++];

        const currentLayer =
          layers.get(current) || 0;

        const targets =
          outgoing.get(current) || [];

        targets.forEach(function(target) {
          layers.set(
            target,
            Math.max(
              layers.get(target) || 0,
              currentLayer + 1,
            ),
          );

          remainingIncoming.set(
            target,
            remainingIncoming.get(target) - 1,
          );

          if (
            remainingIncoming.get(target) ===
            0
          ) {
            queue.push(target);
          }
        });
      }

      let maxLayer =
        Math.max.apply(
          null,
          Array.from(
            layers.values(),
          ),
        );

      if (!Number.isFinite(maxLayer)) {
        maxLayer = 0;
      }

      nodes.forEach(function(node) {
        if (
          remainingIncoming.get(node.id) > 0
        ) {
          maxLayer += 1;

          layers.set(
            node.id,
            maxLayer,
          );
        }
      });

      const grouped =
        new Map();

      nodes.forEach(function(node) {
        const layer =
          layers.get(node.id) || 0;

        if (!grouped.has(layer)) {
          grouped.set(
            layer,
            [],
          );
        }

        grouped.get(layer).push(node);
      });

      const nodeWidth =
        denseGraph ? 42 : 190;

      const nodeHeight =
        denseGraph ? 28 : 58;

      const horizontalGap =
        denseGraph ? 60 : 100;

      const verticalGap =
        denseGraph ? 24 : 28;

      Array.from(grouped.keys())
        .sort(function(a, b) {
          return a - b;
        })
        .forEach(function(layer) {
          const group =
            grouped.get(layer);

          const x =
            layer *
            (
              nodeWidth +
              horizontalGap
            ) +
            50;

          group
            .slice()
            .sort(function(a, b) {
              return a.id.localeCompare(
                b.id,
              );
            })
            .forEach(
              function(node, index) {
                node.x = x;

                node.y =
                  index *
                  (
                    nodeHeight +
                    verticalGap
                  ) +
                  70;

                node.width =
                  nodeWidth;

                node.height =
                  nodeHeight;
              },
            );
        });
    }

    function routeEdge(
      edge,
      allowBackwards = true,
    ) {
      const source =
        nodeById.get(edge.source);

      const target =
        nodeById.get(edge.target);

      if (!source || !target) {
        edge.points = [];
        return;
      }

      const sourceX =
        source.x +
        source.width;

      const sourceY =
        source.y +
        source.height / 2;

      const targetX =
        target.x;

      const targetY =
        target.y +
        target.height / 2;

      if (
        targetX >= sourceX &&
        Math.abs(
          sourceY - targetY,
        ) < 2
      ) {
        edge.points = [
          {
            x: sourceX,
            y: sourceY,
          },
          {
            x: targetX,
            y: targetY,
          },
        ];

        return;
      }

      if (
        allowBackwards &&
        targetX < sourceX
      ) {
        const loopOffset = 46;

        const leftX =
          Math.min(
            source.x,
            target.x,
          ) -
          loopOffset;

        edge.points = [
          {
            x: sourceX,
            y: sourceY,
          },
          {
            x: sourceX + 18,
            y: sourceY,
          },
          {
            x: sourceX + 18,
            y: source.y -
              14,
          },
          {
            x: leftX,
            y: source.y -
              14,
          },
          {
            x: leftX,
            y: target.y +
              target.height +
              14,
          },
          {
            x: targetX - 18,
            y: target.y +
              target.height +
              14,
          },
          {
            x: targetX - 18,
            y: targetY,
          },
          {
            x: targetX,
            y: targetY,
          },
        ];

        return;
      }

      const middleX =
        sourceX +
        (
          targetX -
          sourceX
        ) / 2;

      edge.points = [
        {
          x: sourceX,
          y: sourceY,
        },
        {
          x: middleX,
          y: sourceY,
        },
        {
          x: middleX,
          y: targetY,
        },
        {
          x: targetX,
          y: targetY,
        },
      ];
    }

    function routeAllEdges() {
      edges.forEach(function(edge) {
        routeEdge(edge);
      });
    }

    createFallbackLayout();
    routeAllEdges();

    const link =
      graphLayer
        .append('g')
        .attr('class', 'links')
        .selectAll('path')
        .data(edges)
        .join('path')
        .attr('class', function(edge) {
          return (
            'edge' +
            (
              edge.in_cycle
                ? ' cycle'
                : ''
            )
          );
        });

    const nodeSelection =
      graphLayer
        .append('g')
        .attr('class', 'nodes')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr(
          'class',
          'node-group',
        );

    nodeSelection
      .append('rect')
      .attr(
        'class',
        function(node) {
          return (
            'node ' +
            node.type +
            (
              cycleNodeIds.has(node.id)
                ? ' cycle'
                : ''
            )
          );
        },
      )
      .attr(
        'rx',
        denseGraph ? 5 : 8,
      )
      .attr(
        'ry',
        denseGraph ? 5 : 8,
      )
      .attr(
        'width',
        function(node) {
          return node.width;
        },
      )
      .attr(
        'height',
        function(node) {
          return node.height;
        },
      );

    nodeSelection
      .append('text')
      .attr(
        'class',
        function() {
          return (
            'node-label' +
            (
              denseGraph
                ? ' small'
                : ''
            )
          );
        },
      )
      .attr(
        'x',
        function(node) {
          return denseGraph
            ? node.width / 2
            : 14;
        },
      )
      .attr(
        'y',
        function(node) {
          return denseGraph
            ? node.height / 2 + 4
            : 24;
        },
      )
      .attr(
        'text-anchor',
        denseGraph
          ? 'middle'
          : 'start',
      )
      .text(function(node) {
        if (denseGraph) {
          return node.id
            .split('.')
            .slice(-1)
            .join('');
        }

        return node.id
          .split('.')
          .slice(-2)
          .join('.');
      });

    nodeSelection
      .append('text')
      .attr(
        'class',
        'node-subtitle',
      )
      .attr(
        'x',
        14,
      )
      .attr(
        'y',
        42,
      )
      .text(function(node) {
        if (denseGraph) {
          return '';
        }

        return node.type === 'local'
          ? node.file
          : node.type;
      });

    nodeSelection
      .append('title')
      .text(function(node) {
        return (
          node.id +
          '\\n' +
          node.type +
          '\\n' +
          (
            node.file ||
            'external module'
          ) +
          '\\n' +
          node.dependencies +
          ' direct dependencies'
        );
      });

    function renderPositions() {
      nodeSelection.attr(
        'transform',
        function(node) {
          return (
            'translate(' +
            node.x +
            ',' +
            node.y +
            ')'
          );
        },
      );

      link.attr(
        'd',
        function(edge) {
          if (
            !edge.points ||
            edge.points.length < 2
          ) {
            return '';
          }

          return (
            'M' +
            edge.points
              .map(function(point) {
                return (
                  point.x +
                  ',' +
                  point.y
                );
              })
              .join('L')
          );
        },
      );
    }

    function updateDetails(node) {
      const details =
        document.getElementById(
          'details',
        );

      if (!node) {
        details.innerHTML =
          '<div class="details-empty">' +
          'Click a module to inspect it.' +
          '</div>';

        return;
      }

      const directDependencies =
        outgoing.get(node.id) || [];

      const directDependents =
        incoming.get(node.id) || [];

      const cycle =
        cycles.find(function(item) {
          return item.nodes
            .slice(0, -1)
            .includes(node.id);
        });

      details.innerHTML = `
        <div class="details-name">
          ${escapeHtml(node.id)}
        </div>

        <div class="details-type">
          ${escapeHtml(node.type)}
        </div>

        <div class="details-grid">
          <div class="details-metric">
            <span class="details-metric-label">
              Dependencies
            </span>
            <span class="details-metric-value">
              ${directDependencies.length}
            </span>
          </div>

          <div class="details-metric">
            <span class="details-metric-label">
              Dependents
            </span>
            <span class="details-metric-value">
              ${directDependents.length}
            </span>
          </div>
        </div>

        <div class="details-file">
          ${escapeHtml(
            node.file ||
            'external module',
          )}
        </div>

        ${
          cycle
            ? `
              <div class="details-cycle">
                Cycle:
                ${escapeHtml(
                  cycle.nodes.join(
                    ' → ',
                  ),
                )}
              </div>
            `
            : ''
        }

        <div style="margin-top:10px">
          <button
            id="details-reset"
            class="details-reset"
            type="button"
          >
            Clear selection
          </button>
        </div>
      `;

      const reset =
        document.getElementById(
          'details-reset',
        );

      if (reset) {
        reset.addEventListener(
          'click',
          clearSelection,
        );
      }
    }

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function getNeighborhood(
      startId,
      depth,
    ) {
      const visited =
        new Set([
          startId,
        ]);

      let frontier =
        new Set([
          startId,
        ]);

      for (
        let level = 0;
        level < depth;
        level += 1
      ) {
        const next =
          new Set();

        frontier.forEach(function(id) {
          const nextOutgoing =
            outgoing.get(id) || [];

          const nextIncoming =
            incoming.get(id) || [];

          nextOutgoing.forEach(
            function(target) {
              next.add(target);
            },
          );

          nextIncoming.forEach(
            function(source) {
              next.add(source);
            },
          );
        });

        next.forEach(function(id) {
          visited.add(id);
        });

        frontier = next;
      }

      return visited;
    }

    function applyVisualState() {
      const focusedIds =
        state.selectedId && state.focusDepth
          ? getNeighborhood(
              state.selectedId,
              state.focusDepth,
            )
          : null;

      const searchValue =
        state.searchQuery
          .trim()
          .toLowerCase();

      const searchMatches =
        searchValue
          ? new Set(
              nodes
                .filter(function(node) {
                  return node.id
                    .toLowerCase()
                    .includes(
                      searchValue,
                    );
                })
                .map(function(node) {
                  return node.id;
                }),
            )
          : null;

      nodeSelection
        .classed(
          'dim',
          function(node) {
            if (!focusedIds) {
              return false;
            }

            return !focusedIds.has(
              node.id,
            );
          },
        )
        .classed(
          'focused',
          function(node) {
            return Boolean(
              focusedIds &&
              focusedIds.has(
                node.id,
              ),
            );
          },
        )
        .classed(
          'selected',
          function(node) {
            return (
              node.id ===
              state.selectedId
            );
          },
        )
        .classed(
          'search-match',
          function(node) {
            return Boolean(
              searchMatches &&
              searchMatches.has(
                node.id,
              ),
            );
          },
        );

      link
        .classed(
          'dim',
          function(edge) {
            if (!focusedIds) {
              return false;
            }

            return !(
              focusedIds.has(
                edge.source,
              ) &&
              focusedIds.has(
                edge.target,
              )
            );
          },
        )
        .classed(
          'focused',
          function(edge) {
            return Boolean(
              focusedIds &&
              focusedIds.has(
                edge.source,
              ) &&
              focusedIds.has(
                edge.target,
              ),
            );
          },
        );

      document
        .getElementById('focus-one')
        .classList.toggle(
          'active',
          state.focusDepth === 1,
        );

      document
        .getElementById('focus-two')
        .classList.toggle(
          'active',
          state.focusDepth === 2,
        );
    }

    function clearSelection() {
      state.selectedId = null;
      state.focusDepth = null;

      nodeSelection
        .classed('dim', false)
        .classed('selected', false)
        .classed('focused', false);

      link
        .classed('dim', false)
        .classed('focused', false);

      updateDetails(null);
      applyVisualState();
    }

    function selectNode(selected) {
      state.selectedId =
        selected.id;

      state.focusDepth = null;

      updateDetails(selected);
      applyVisualState();
    }

    function focusSelected(depth) {
      if (!state.selectedId) {
        return;
      }

      state.focusDepth =
        depth;

      applyVisualState();
    }

    function centerOnNode(
      node,
      scale = 1.1,
    ) {
      if (!node) {
        return;
      }

      const viewWidth =
        svgNode.clientWidth || 1000;

      const viewHeight =
        svgNode.clientHeight || 700;

      const x =
        viewWidth / 2 -
        (
          node.x +
          node.width / 2
        ) *
          scale;

      const y =
        viewHeight / 2 -
        (
          node.y +
          node.height / 2
        ) *
          scale;

      svg
        .transition()
        .duration(250)
        .call(
          zoom.transform,
          d3.zoomIdentity
            .translate(x, y)
            .scale(scale),
        );
    }

    function updateSearch(query) {
      state.searchQuery =
        query;

      const value =
        query.trim().toLowerCase();

      const matches =
        nodes.filter(function(node) {
          return !value ||
            node.id
              .toLowerCase()
              .includes(value);
        });

      const emptyState =
        document.getElementById(
          'empty-state',
        );

      emptyState.style.display =
        value && matches.length === 0
          ? 'block'
          : 'none';

      applyVisualState();

      if (
        value &&
        matches.length === 1
      ) {
        centerOnNode(
          matches[0],
          1.15,
        );
      }
    }

    function fitGraph() {
      const bounds =
        graphLayer
          .node()
          .getBBox();

      if (
        !bounds.width ||
        !bounds.height
      ) {
        return;
      }

      const viewWidth =
        svgNode.clientWidth || 1000;

      const viewHeight =
        svgNode.clientHeight || 700;

      const padding = 54;

      const scale =
        Math.min(
          1,
          (
            viewWidth -
            padding * 2
          ) / bounds.width,
          (
            viewHeight -
            padding * 2
          ) / bounds.height,
        );

      const safeScale =
        Math.max(
          0.15,
          scale,
        );

      const x =
        (
          viewWidth -
          bounds.width *
            safeScale
        ) /
          2 -
        bounds.x *
          safeScale;

      const y =
        (
          viewHeight -
          bounds.height *
            safeScale
        ) /
          2 -
        bounds.y *
          safeScale;

      svg.call(
        zoom.transform,
        d3.zoomIdentity
          .translate(x, y)
          .scale(safeScale),
      );
    }

    function applyElkResult(layout) {
      if (
        !layout ||
        !Array.isArray(
          layout.children,
        )
      ) {
        throw new Error(
          'ELK returned an invalid layout.',
        );
      }

      const positioned =
        new Map(
          layout.children.map(
            function(child) {
              return [
                child.id,
                child,
              ];
            },
          ),
        );

      nodes.forEach(
        function(node) {
          const child =
            positioned.get(node.id);

          if (!child) {
            return;
          }

          node.x =
            child.x;

          node.y =
            child.y;

          node.width =
            child.width;

          node.height =
            child.height;
        },
      );

      const routedEdges =
        new Map();

      (
        layout.edges || []
      ).forEach(function(edge) {
        const points = [];

        (
          edge.sections || []
        ).forEach(
          function(section) {
            points.push(
              section.startPoint,
            );

            (
              section.bendPoints ||
              []
            ).forEach(
              function(point) {
                points.push(point);
              },
            );

            points.push(
              section.endPoint,
            );
          },
        );

        routedEdges.set(
          edge.id,
          points,
        );
      });

      edges.forEach(
        function(edge, index) {
          const points =
            routedEdges.get(
              'edge-' + index,
            );

          if (
            points &&
            points.length >= 2
          ) {
            edge.points =
              points;
          }
        },
      );

      renderPositions();

      state.layoutReady =
        true;

      window.setTimeout(
        fitGraph,
        20,
      );
    }

    function tryElkLayout() {
      if (
        typeof ELK === 'undefined'
      ) {
        fitGraph();
        return;
      }

      let elk;

      try {
        elk = new ELK();
      } catch (error) {
        console.warn(
          'ELK initialization failed; using fallback layout.',
          error,
        );

        fitGraph();
        return;
      }

      const children =
        nodes.map(function(node) {
          return {
            id: node.id,
            width: denseGraph
              ? 42
              : 190,
            height: denseGraph
              ? 28
              : 58,
          };
        });

      const elkEdges =
        edges.map(function(edge, index) {
          return {
            id:
              'edge-' +
              index,
            sources: [
              edge.source,
            ],
            targets: [
              edge.target,
            ],
          };
        });

      Promise.resolve()
        .then(function() {
          return elk.layout({
            id: 'root',
            children: children,
            edges: elkEdges,
            layoutOptions: {
              'elk.algorithm':
                'layered',

              'elk.direction':
                'RIGHT',

              'elk.edgeRouting':
                'ORTHOGONAL',

              'elk.layered.spacing.nodeNodeBetweenLayers':
                denseGraph
                  ? '45'
                  : '85',

              'elk.spacing.nodeNode':
                denseGraph
                  ? '24'
                  : '40',

              'elk.layered.considerModelOrder.strategy':
                'NODES_AND_EDGES',
            },
          });
        })
        .then(
          applyElkResult,
        )
        .catch(function(error) {
          console.warn(
            'ELK layout failed; keeping deterministic fallback layout.',
            error,
          );

          renderPositions();
          fitGraph();
        });
    }

    nodeSelection.on(
      'click',
      function(event, selected) {
        selectNode(selected);
        event.stopPropagation();
      },
    );

    nodeSelection.call(
      d3.drag()
        .on(
          'start',
          function(event) {
            event.sourceEvent.stopPropagation();
          },
        )
        .on(
          'drag',
          function(event, selected) {
            selected.x =
              event.x -
              selected.width / 2;

            selected.y =
              event.y -
              selected.height / 2;

            edges.forEach(
              function(edge) {
                if (
                  edge.source ===
                    selected.id ||
                  edge.target ===
                    selected.id
                ) {
                  routeEdge(edge);
                }
              },
            );

            renderPositions();
          },
        ),
    );

    svg.on(
      'click',
      clearSelection,
    );

    document
      .getElementById('zoom-in')
      .addEventListener(
        'click',
        function() {
          svg
            .transition()
            .call(
              zoom.scaleBy,
              1.2,
            );
        },
      );

    document
      .getElementById('zoom-out')
      .addEventListener(
        'click',
        function() {
          svg
            .transition()
            .call(
              zoom.scaleBy,
              0.83,
            );
        },
      );

    document
      .getElementById('zoom-fit')
      .addEventListener(
        'click',
        fitGraph,
      );

    document
      .getElementById('search')
      .addEventListener(
        'input',
        function(event) {
          updateSearch(
            event.target.value,
          );
        },
      );

    document
      .getElementById('search')
      .addEventListener(
        'keydown',
        function(event) {
          if (
            event.key ===
            'Escape'
          ) {
            event.currentTarget.value =
              '';

            updateSearch('');
          }

          if (
            event.key === 'Enter'
          ) {
            const value =
              event.currentTarget.value
                .trim()
                .toLowerCase();

            if (!value) {
              return;
            }

            const match =
              nodes.find(
                function(node) {
                  return node.id
                    .toLowerCase()
                    .includes(
                      value,
                    );
                },
              );

            if (match) {
              selectNode(match);
              centerOnNode(
                match,
                1.2,
              );
            }
          }
        },
      );

    document
      .getElementById('focus-one')
      .addEventListener(
        'click',
        function() {
          focusSelected(1);
        },
      );

    document
      .getElementById('focus-two')
      .addEventListener(
        'click',
        function() {
          focusSelected(2);
        },
      );

    document
      .getElementById('focus-reset')
      .addEventListener(
        'click',
        function() {
          state.focusDepth =
            null;

          applyVisualState();
        },
      );

    document
      .getElementById('panel-toggle')
      .addEventListener(
        'click',
        function(event) {
          const sidebar =
            document.querySelector(
              '.sidebar',
            );

          const collapsed =
            sidebar.classList.toggle(
              'collapsed',
            );

          state.sidebarCollapsed =
            collapsed;

          event.currentTarget
            .textContent =
            collapsed
              ? '›'
              : '‹';

          event.currentTarget.title =
            collapsed
              ? 'Show report panel'
              : 'Hide report panel';

          event.currentTarget
            .setAttribute(
              'aria-label',
              event.currentTarget
                .title,
            );

          window.setTimeout(
            fitGraph,
            220,
          );
        },
      );

    if (
      typeof ResizeObserver !==
      'undefined'
    ) {
      const observer =
        new ResizeObserver(
          function() {
            window.requestAnimationFrame(
              fitGraph,
            );
          },
        );

      observer.observe(
        document.querySelector(
          '.content',
        ),
      );
    } else {
      window.addEventListener(
        'resize',
        fitGraph,
      );
    }

    renderPositions();

    fitGraph();

    tryElkLayout();
  </script>
</body>
</html>
"""

    def _render_html(
        self,
        export: GraphExport,
    ) -> str:
        """Render the graph export as self-contained HTML."""
        d3_source, elk_source = self._load_javascript_assets()

        html = self._template()

        replacements = {
            "__D3_SOURCE__": d3_source,
            "__ELK_SOURCE__": elk_source,
            "__NODE_JSON__": self._json_for_script(
                export.nodes,
            ),
            "__EDGE_JSON__": self._json_for_script(
                export.edges,
            ),
            "__CYCLE_JSON__": self._json_for_script(
                export.cycles,
            ),
            "__SUMMARY_JSON__": self._json_for_script(
                export.summary,
            ),
            "__PROJECT_JSON__": self._json_for_script(
                export.project,
            ),
        }

        for placeholder, value in replacements.items():
            html = html.replace(
                placeholder,
                value,
            )

        return html

    def write(
        self,
        export: GraphExport,
        dest: Path | None = None,
    ) -> None:
        """Write the HTML representation to stdout or a file."""
        html = self._render_html(export)

        if dest is None:
            print(html, end="")
            return

        dest.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        dest.write_text(
            html,
            encoding="utf-8",
        )

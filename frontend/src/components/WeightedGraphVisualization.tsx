import type { GraphNode, GraphNodeLabel, GraphTraceEdge, SearchResponse, TraceFrame, WeightedGraphEdge } from "../lib/types";

interface Props {
  result: SearchResponse | null;
  frame: TraceFrame | null;
}

export function WeightedGraphVisualization({ result, frame }: Props) {
  const graph = result?.graph;
  const nodes = graph?.nodes ?? [];
  const edges = graph?.edges ?? [];
  const labels = new Map((frame?.node_labels ?? []).map((label) => [label.node_id, label]));
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const activeEdgeKey = frame?.active_edge ? edgeKey(frame.active_edge) : "";
  const pathEdges = new Set(pathToEdges(result?.graph_path ?? []));
  const parentEdges = new Set((frame?.parent_edges ?? []).map(edgeKey));
  const policyEdges = new Set((frame?.policy_edges ?? []).map(edgeKey));
  const frontier = new Set(frame?.frontier_nodes ?? []);
  const settled = new Set(frame?.settled_nodes ?? []);
  const updated = new Set(frame?.updated_nodes ?? []);
  const bounds = graphBounds(nodes);

  return (
    <div className="visualization-panel">
      <div className="panel-heading">
        <h2>Weighted Graph</h2>
        <span className="status-pill">{frame ? `Frame ${frame.index + 1} of ${result?.trace.length ?? 1}` : "No trace"}</span>
      </div>
      <svg
        className="graph-svg"
        role="img"
        aria-label="Weighted graph visualization"
        viewBox={`${bounds.x} ${bounds.y} ${bounds.width} ${bounds.height}`}
        data-testid="weighted-graph-visualization"
      >
        <defs>
          <marker id="arrow-default" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" className="graph-arrow" />
          </marker>
        </defs>
        {edges.map((edge) => {
          const source = nodeById.get(edge.source);
          const target = nodeById.get(edge.target);
          if (!source || !target) {
            return null;
          }
          const key = edgeKey(edge);
          const points = edgePoints(source, target);
          const classes = [
            "graph-edge",
            activeEdgeKey === key ? "active" : "",
            pathEdges.has(key) ? "path" : "",
            parentEdges.has(key) ? "parent" : "",
            policyEdges.has(key) ? "policy" : "",
          ]
            .filter(Boolean)
            .join(" ");
          return (
            <g key={key}>
              <line className={classes} x1={points.x1} y1={points.y1} x2={points.x2} y2={points.y2} markerEnd="url(#arrow-default)" />
              <text className="edge-cost" x={(points.x1 + points.x2) / 2} y={(points.y1 + points.y2) / 2 - 8} textAnchor="middle">
                {formatNumber(edge.cost)}
              </text>
            </g>
          );
        })}
        {nodes.map((node) => {
          const label = labels.get(node.id);
          const classes = [
            "graph-node",
            graph?.start === node.id ? "start" : "",
            graph?.goal === node.id ? "goal" : "",
            frontier.has(node.id) ? "frontier" : "",
            settled.has(node.id) ? "settled" : "",
            updated.has(node.id) ? "updated" : "",
            frame?.current_node === node.id ? "current" : "",
            (result?.graph_path ?? []).includes(node.id) ? "path" : "",
          ]
            .filter(Boolean)
            .join(" ");
          const x = node.x ?? 0;
          const y = node.y ?? 0;
          return (
            <g key={node.id}>
              <circle className={classes} cx={x} cy={y} r="28" />
              <text className="graph-node-title" x={x} y={y - 4} textAnchor="middle">
                {node.label ?? node.id}
              </text>
              <text className="graph-node-values" x={x} y={y + 14} textAnchor="middle">
                {nodeLabelText(label)}
              </text>
              <title>{nodeTooltip(node, label)}</title>
            </g>
          );
        })}
      </svg>
      <div className="legend graph-legend" aria-label="Weighted graph legend">
        <span><i className="legend-chip graph-current" />Current</span>
        <span><i className="legend-chip graph-frontier" />Open</span>
        <span><i className="legend-chip graph-settled" />Settled</span>
        <span><i className="legend-chip graph-path" />Optimal path</span>
      </div>
      <div className="frame-metrics" aria-label="Current frame metrics">
        <span><strong>{frame?.settled_nodes?.length ?? 0}</strong> settled</span>
        <span><strong>{frame?.frontier_nodes?.length ?? 0}</strong> open</span>
        <span><strong>{result?.stats.total_cost ?? "n/a"}</strong> total cost</span>
        {result?.stats.sweep_count ? <span><strong>{result.stats.sweep_count}</strong> sweeps</span> : null}
      </div>
      {frame?.priority_queue?.length ? (
        <div className="queue-strip" aria-label="Priority queue">
          {frame.priority_queue.map((item) => (
            <span key={`${item.node_id}-${item.priority}`}>
              {item.node_id} ({formatNumber(item.priority)})
            </span>
          ))}
        </div>
      ) : null}
      <p className="frame-message">{frame?.message ?? "Run an algorithm to create a weighted graph trace."}</p>
    </div>
  );
}

function edgeKey(edge: Pick<WeightedGraphEdge | GraphTraceEdge, "source" | "target">): string {
  return `${edge.source}->${edge.target}`;
}

function pathToEdges(path: string[]): string[] {
  const edges = [];
  for (let index = 0; index < path.length - 1; index += 1) {
    edges.push(`${path[index]}->${path[index + 1]}`);
  }
  return edges;
}

function graphBounds(nodes: GraphNode[]) {
  if (!nodes.length) {
    return { x: 0, y: 0, width: 640, height: 420 };
  }
  const xs = nodes.map((node) => node.x ?? 0);
  const ys = nodes.map((node) => node.y ?? 0);
  const minX = Math.min(...xs) - 80;
  const minY = Math.min(...ys) - 80;
  const maxX = Math.max(...xs) + 80;
  const maxY = Math.max(...ys) + 80;
  return { x: minX, y: minY, width: Math.max(320, maxX - minX), height: Math.max(260, maxY - minY) };
}

function edgePoints(source: GraphNode, target: GraphNode) {
  const sx = source.x ?? 0;
  const sy = source.y ?? 0;
  const tx = target.x ?? 0;
  const ty = target.y ?? 0;
  const dx = tx - sx;
  const dy = ty - sy;
  const length = Math.hypot(dx, dy) || 1;
  const offset = 32;
  return {
    x1: sx + (dx / length) * offset,
    y1: sy + (dy / length) * offset,
    x2: tx - (dx / length) * offset,
    y2: ty - (dy / length) * offset,
  };
}

function nodeLabelText(label: GraphNodeLabel | undefined): string {
  if (!label) {
    return "";
  }
  if (label.value !== null && label.value !== undefined) {
    return `V=${formatNumber(label.value)}`;
  }
  if (label.f !== null && label.f !== undefined) {
    return `g=${formatNumber(label.g)} f=${formatNumber(label.f)}`;
  }
  if (label.g !== null && label.g !== undefined) {
    return `g=${formatNumber(label.g)}`;
  }
  return "";
}

function nodeTooltip(node: GraphNode, label: GraphNodeLabel | undefined): string {
  const parts = [node.id];
  if (label?.g !== null && label?.g !== undefined) {
    parts.push(`g=${formatNumber(label.g)}`);
  }
  if (label?.h !== null && label?.h !== undefined) {
    parts.push(`h=${formatNumber(label.h)}`);
  }
  if (label?.f !== null && label?.f !== undefined) {
    parts.push(`f=${formatNumber(label.f)}`);
  }
  if (label?.value !== null && label?.value !== undefined) {
    parts.push(`V=${formatNumber(label.value)}`);
  }
  return parts.join(", ");
}

function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "inf";
  }
  return Number.isInteger(value) ? String(value) : value.toFixed(2);
}

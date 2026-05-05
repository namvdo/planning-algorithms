import type { WeightedGraphProblem } from "./types";

export function parseGraphText(graphText: string): { graph: WeightedGraphProblem | null; error: string | null } {
  let parsed: unknown;
  try {
    parsed = JSON.parse(graphText);
  } catch {
    return { graph: null, error: "Graph must be valid JSON." };
  }

  if (!isRecord(parsed)) {
    return { graph: null, error: "Graph must be a JSON object." };
  }

  if (!Array.isArray(parsed.nodes) || parsed.nodes.length === 0) {
    return { graph: null, error: "Graph must contain at least one node." };
  }
  if (!Array.isArray(parsed.edges)) {
    return { graph: null, error: "Graph edges must be an array." };
  }
  if (typeof parsed.start !== "string" || typeof parsed.goal !== "string") {
    return { graph: null, error: "Graph start and goal must be node ids." };
  }

  const nodes = [];
  const ids = new Set<string>();
  for (const rawNode of parsed.nodes) {
    if (!isRecord(rawNode) || typeof rawNode.id !== "string" || !rawNode.id.trim()) {
      return { graph: null, error: "Each graph node needs a non-empty id." };
    }
    if (ids.has(rawNode.id)) {
      return { graph: null, error: "Graph node ids must be unique." };
    }
    ids.add(rawNode.id);
    nodes.push({
      id: rawNode.id,
      label: typeof rawNode.label === "string" ? rawNode.label : null,
      x: typeof rawNode.x === "number" ? rawNode.x : null,
      y: typeof rawNode.y === "number" ? rawNode.y : null,
      heuristic: typeof rawNode.heuristic === "number" ? rawNode.heuristic : 0,
    });
  }

  if (!ids.has(parsed.start) || !ids.has(parsed.goal)) {
    return { graph: null, error: "Graph start and goal must reference existing nodes." };
  }

  const edges = [];
  for (const rawEdge of parsed.edges) {
    if (!isRecord(rawEdge) || typeof rawEdge.source !== "string" || typeof rawEdge.target !== "string" || typeof rawEdge.cost !== "number") {
      return { graph: null, error: "Each graph edge needs source, target, and numeric cost." };
    }
    if (!ids.has(rawEdge.source) || !ids.has(rawEdge.target)) {
      return { graph: null, error: "Every graph edge must reference existing nodes." };
    }
    if (rawEdge.cost <= 0) {
      return { graph: null, error: "Graph edge costs must be positive." };
    }
    edges.push({ source: rawEdge.source, target: rawEdge.target, cost: rawEdge.cost });
  }

  return { graph: { nodes, edges, start: parsed.start, goal: parsed.goal }, error: null };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

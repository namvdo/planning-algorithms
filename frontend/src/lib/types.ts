export type SearchAlgorithm =
  | "forward"
  | "backward"
  | "bidirectional"
  | "dijkstra"
  | "astar"
  | "forward_value_iteration"
  | "backward_value_iteration";
export type SearchStatus = "found" | "not_found";
export type ProblemKind = "grid" | "weighted_graph";

export interface State {
  row: number;
  col: number;
}

export interface PlanStep {
  index: number;
  from_state: State;
  to_state: State;
  action: string;
}

export interface SearchTreeEdge {
  from_state: State;
  to_state: State;
  action: string;
}

export interface GraphNode {
  id: string;
  label: string | null;
  x: number | null;
  y: number | null;
  heuristic: number;
}


export interface WeightedGraphEdge {
  source: string;
  target: string;
  cost: number;
}


export interface WeightedGraphProblem {
  nodes: GraphNode[];
  edges: WeightedGraphEdge[];
  start: string;
  goal: string;
}

export interface GraphNodeLabel {
  node_id: string;
  g: number | null;
  h: number | null;
  f: number | null;
  value: number | null;
  residual: number | null;
}

export interface GraphTraceEdge {
  source: string;
  target: string;
  cost: number;
}

export interface RelaxationEvent {
  source: string;
  target: string;
  cost: number;
  previous: number | null;
  updated: number | null;
  improved: boolean;
}

export interface QueueItem {
  node_id: string;
  priority: number;
  g: number | null;
  h: number | null;
  value: number | null;
}

export interface TraceFrame {
  index: number;
  phase: string;
  message: string;
  current: State | null;
  frontier: State[];
  visited: State[];
  backward_frontier: State[];
  backward_visited: State[];
  forward_tree_edges: SearchTreeEdge[];
  backward_tree_edges: SearchTreeEdge[];
  discovered: State[];
  meeting_state: State | null;
  plan_prefix: State[];
  current_node: string | null;
  frontier_nodes: string[];
  visited_nodes: string[];
  settled_nodes: string[];
  updated_nodes: string[];
  node_labels: GraphNodeLabel[];
  active_edge: GraphTraceEdge | null;
  parent_edges: GraphTraceEdge[];
  policy_edges: GraphTraceEdge[];
  relaxation: RelaxationEvent | null;
  priority_queue: QueueItem[];
}

export interface SearchStats {
  expanded_count: number;
  visited_count: number;
  max_frontier_size: number;
  path_length: number | null;
  trace_length: number;
  total_cost: number | null;
  relaxation_count: number;
  sweep_count: number;
}

export interface SearchResponse {
  algorithm: SearchAlgorithm;
  status: SearchStatus;
  start: State;
  goal: State;
  rows: number;
  cols: number;
  plan: PlanStep[];
  graph: WeightedGraphProblem | null;
  graph_path: string[];
  trace: TraceFrame[];
  stats: SearchStats;
}

export interface JudgeCaseResult {
  name: string;
  passed: boolean;
  message: string;
  expected_length: number | null;
  actual_length: number | null;
}

export interface CodeEvaluationResponse {
  algorithm: SearchAlgorithm;
  passed: boolean;
  cases: JudgeCaseResult[];
  stdout: string;
  stderr: string;
  duration_ms: number;
}

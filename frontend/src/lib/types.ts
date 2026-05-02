export type SearchAlgorithm = "forward" | "backward" | "bidirectional";
export type SearchStatus = "found" | "not_found";

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

export interface TraceFrame {
  index: number;
  phase: string;
  message: string;
  current: State | null;
  frontier: State[];
  visited: State[];
  backward_frontier: State[];
  backward_visited: State[];
  discovered: State[];
  meeting_state: State | null;
  plan_prefix: State[];
}

export interface SearchStats {
  expanded_count: number;
  visited_count: number;
  max_frontier_size: number;
  path_length: number | null;
  trace_length: number;
}

export interface SearchResponse {
  algorithm: SearchAlgorithm;
  status: SearchStatus;
  start: State;
  goal: State;
  rows: number;
  cols: number;
  plan: PlanStep[];
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

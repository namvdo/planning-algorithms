from enum import StrEnum

from pydantic import BaseModel, Field


class SearchAlgorithm(StrEnum):
    FORWARD = "forward"
    BACKWARD = "backward"
    BIDIRECTIONAL = "bidirectional"
    DIJKSTRA = "dijkstra"
    ASTAR = "astar"
    FORWARD_VALUE_ITERATION = "forward_value_iteration"
    BACKWARD_VALUE_ITERATION = "backward_value_iteration"

class SearchStatus(StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"


class State(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)


class SearchRequest(BaseModel):
    algorithm: SearchAlgorithm
    grid: list[str] | None = None
    graph: "WeightedGraphProblem | None" = None
    start: State | None = None
    goal: State | None = None


class PlanStep(BaseModel):
    index: int
    from_state: State
    to_state: State
    action: str


class SearchTreeEdge(BaseModel):
    from_state: State
    to_state: State
    action: str


class GraphNode(BaseModel):
    id: str
    label: str | None = None
    x: float | None = None
    y: float | None = None
    heuristic: float = 0.0


class WeightedGraphEdge(BaseModel):
    source: str
    target: str
    cost: float = Field(gt=0)


class WeightedGraphProblem(BaseModel):
    nodes: list[GraphNode] = Field(min_length=1)
    edges: list[WeightedGraphEdge] = Field(default_factory=list)
    start: str
    goal: str


class GraphNodeLabel(BaseModel):
    node_id: str
    g: float | None = None
    h: float | None = None
    f: float | None = None
    value: float | None = None
    residual: float | None = None


class GraphTraceEdge(BaseModel):
    source: str
    target: str
    cost: float


class RelaxationEvent(BaseModel):
    source: str
    target: str
    cost: float
    previous: float | None = None
    updated: float | None = None
    improved: bool


class QueueItem(BaseModel):
    node_id: str
    priority: float
    g: float | None = None
    h: float | None = None
    value: float | None = None


class TraceFrame(BaseModel):
    index: int
    phase: str
    message: str
    current: State | None = None
    frontier: list[State] = Field(default_factory=list)
    visited: list[State] = Field(default_factory=list)
    backward_frontier: list[State] = Field(default_factory=list)
    backward_visited: list[State] = Field(default_factory=list)
    forward_tree_edges: list[SearchTreeEdge] = Field(default_factory=list)
    backward_tree_edges: list[SearchTreeEdge] = Field(default_factory=list)
    discovered: list[State] = Field(default_factory=list)
    meeting_state: State | None = None
    plan_prefix: list[State] = Field(default_factory=list)
    current_node: str | None = None
    frontier_nodes: list[str] = Field(default_factory=list)
    visited_nodes: list[str] = Field(default_factory=list)
    settled_nodes: list[str] = Field(default_factory=list)
    updated_nodes: list[str] = Field(default_factory=list)
    node_labels: list[GraphNodeLabel] = Field(default_factory=list)
    active_edge: GraphTraceEdge | None = None
    parent_edges: list[GraphTraceEdge] = Field(default_factory=list)
    policy_edges: list[GraphTraceEdge] = Field(default_factory=list)
    relaxation: RelaxationEvent | None = None
    priority_queue: list[QueueItem] = Field(default_factory=list)


class SearchStats(BaseModel):
    expanded_count: int
    visited_count: int
    max_frontier_size: int
    path_length: int | None
    trace_length: int
    total_cost: float | None = None
    relaxation_count: int = 0
    sweep_count: int = 0


class SearchResponse(BaseModel):
    algorithm: SearchAlgorithm
    status: SearchStatus
    start: State
    goal: State
    rows: int
    cols: int
    plan: list[PlanStep]
    graph: WeightedGraphProblem | None = None
    graph_path: list[str] = Field(default_factory=list)
    trace: list[TraceFrame]
    stats: SearchStats


class CodeEvaluationRequest(BaseModel):
    algorithm: SearchAlgorithm
    grid: list[str] = Field(min_length=1)
    code: str = Field(min_length=1, max_length=20_000)
    start: State | None = None
    goal: State | None = None


class CodeVisualizationRequest(CodeEvaluationRequest):
    pass


class JudgeCaseResult(BaseModel):
    name: str
    passed: bool
    message: str
    expected_length: int | None = None
    actual_length: int | None = None


class CodeEvaluationResponse(BaseModel):
    algorithm: SearchAlgorithm
    passed: bool
    cases: list[JudgeCaseResult]
    stdout: str = ""
    stderr: str = ""
    duration_ms: int

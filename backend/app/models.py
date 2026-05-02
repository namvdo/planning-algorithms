from enum import StrEnum

from pydantic import BaseModel, Field


class SearchAlgorithm(StrEnum):
    FORWARD = "forward"
    BACKWARD = "backward"
    BIDIRECTIONAL = "bidirectional"


class SearchStatus(StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"


class State(BaseModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)


class SearchRequest(BaseModel):
    algorithm: SearchAlgorithm
    grid: list[str] = Field(min_length=1)
    start: State | None = None
    goal: State | None = None


class PlanStep(BaseModel):
    index: int
    from_state: State
    to_state: State
    action: str


class TraceFrame(BaseModel):
    index: int
    phase: str
    message: str
    current: State | None = None
    frontier: list[State] = Field(default_factory=list)
    visited: list[State] = Field(default_factory=list)
    backward_frontier: list[State] = Field(default_factory=list)
    backward_visited: list[State] = Field(default_factory=list)
    discovered: list[State] = Field(default_factory=list)
    meeting_state: State | None = None
    plan_prefix: list[State] = Field(default_factory=list)


class SearchStats(BaseModel):
    expanded_count: int
    visited_count: int
    max_frontier_size: int
    path_length: int | None
    trace_length: int


class SearchResponse(BaseModel):
    algorithm: SearchAlgorithm
    status: SearchStatus
    start: State
    goal: State
    rows: int
    cols: int
    plan: list[PlanStep]
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

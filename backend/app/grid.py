from dataclasses import dataclass
from typing import Iterable, Literal

from fastapi import HTTPException

from app.models import State

GridState = tuple[int, int]
Action = Literal["up", "down", "left", "right"]

DIRECTIONS: dict[Action, GridState] = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}

INVERSE: dict[Action, Action] = {
    "up": "down",
    "down": "up",
    "left": "right",
    "right": "left",
}


@dataclass(frozen=True)
class GridProblem:
    grid: tuple[str, ...]
    start: GridState
    goal: GridState
    walls: frozenset[GridState]
    rows: int
    cols: int

    def in_bounds(self, state: GridState) -> bool:
        row, col = state
        return 0 <= row < self.rows and 0 <= col < self.cols

    def is_free(self, state: GridState) -> bool:
        return self.in_bounds(state) and state not in self.walls

    def get_actions(self, state: GridState) -> list[Action]:
        actions: list[Action] = []
        row, col = state
        for action, (dr, dc) in DIRECTIONS.items():
            next_state = (row + dr, col + dc)
            if self.is_free(next_state):
                actions.append(action)
        return actions

    def transition(self, state: GridState, action: Action) -> GridState:
        dr, dc = DIRECTIONS[action]
        return state[0] + dr, state[1] + dc

    def get_inverse_actions(self, state: GridState) -> list[Action]:
        actions: list[Action] = []
        row, col = state
        for action in DIRECTIONS:
            dr, dc = DIRECTIONS[INVERSE[action]]
            previous = (row + dr, col + dc)
            if self.is_free(previous):
                actions.append(action)
        return actions

    def inverse_transition(self, state: GridState, action: Action) -> GridState:
        dr, dc = DIRECTIONS[INVERSE[action]]
        return state[0] + dr, state[1] + dc


def parse_grid(grid: Iterable[str], start: State | None = None, goal: State | None = None) -> GridProblem:
    rows = tuple(row.rstrip("\n") for row in grid)
    if not rows:
        raise HTTPException(status_code=422, detail="Grid must contain at least one row.")

    cols = len(rows[0])
    if cols == 0:
        raise HTTPException(status_code=422, detail="Grid rows must not be empty.")

    if any(len(row) != cols for row in rows):
        raise HTTPException(status_code=422, detail="Grid must be rectangular.")

    walls: set[GridState] = set()
    starts: list[GridState] = []
    goals: list[GridState] = []
    allowed = {"S", "G", ".", "#", " "}

    for row_index, row in enumerate(rows):
        for col_index, char in enumerate(row):
            if char not in allowed:
                raise HTTPException(
                    status_code=422,
                    detail=f"Unsupported grid character {char!r} at row {row_index}, col {col_index}.",
                )
            state = (row_index, col_index)
            if char == "#":
                walls.add(state)
            elif char == "S":
                starts.append(state)
            elif char == "G":
                goals.append(state)

    resolved_start = _resolve_endpoint("start", starts, start)
    resolved_goal = _resolve_endpoint("goal", goals, goal)

    problem = GridProblem(
        grid=rows,
        start=resolved_start,
        goal=resolved_goal,
        walls=frozenset(walls),
        rows=len(rows),
        cols=cols,
    )
    _validate_endpoint(problem, "start", resolved_start)
    _validate_endpoint(problem, "goal", resolved_goal)
    return problem


def _resolve_endpoint(name: str, markers: list[GridState], override: State | None) -> GridState:
    if override is not None:
        return (override.row, override.col)
    if len(markers) != 1:
        raise HTTPException(status_code=422, detail=f"Grid must contain exactly one {name} marker.")
    return markers[0]


def _validate_endpoint(problem: GridProblem, name: str, state: GridState) -> None:
    if not problem.in_bounds(state):
        raise HTTPException(status_code=422, detail=f"{name.title()} state is outside the grid.")
    if state in problem.walls:
        raise HTTPException(status_code=422, detail=f"{name.title()} state must not be a wall.")


import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.grid import DIRECTIONS, GridProblem, parse_grid
from app.main import app
from app.models import SearchAlgorithm, State
from app.search import run_search
from app.weighted_graph import run_weighted_graph_search


GRID = [
    "S.....#.",
    ".####...",
    "....#..G",
    "..#.....",
]

NO_PATH_GRID = [
    "S#G",
    "###",
    "...",
]

GRID_ALGORITHMS = [SearchAlgorithm.FORWARD, SearchAlgorithm.BACKWARD, SearchAlgorithm.BIDIRECTIONAL]

SAMPLE_GRAPH = {
    "nodes": [
        {"id": "S", "x": 40, "y": 120, "heuristic": 7},
        {"id": "A", "x": 190, "y": 50, "heuristic": 5},
        {"id": "B", "x": 190, "y": 190, "heuristic": 6},
        {"id": "C", "x": 340, "y": 120, "heuristic": 2},
        {"id": "G", "x": 490, "y": 120, "heuristic": 0},
    ],
    "edges": [
        {"source": "S", "target": "A", "cost": 4},
        {"source": "S", "target": "B", "cost": 2},
        {"source": "B", "target": "A", "cost": 1},
        {"source": "A", "target": "C", "cost": 3},
        {"source": "B", "target": "C", "cost": 8},
        {"source": "A", "target": "G", "cost": 10},
        {"source": "C", "target": "G", "cost": 2},
    ],
    "start": "S",
    "goal": "G",
}


def test_forward_search_finds_valid_shortest_plan() -> None:
    response = run_search(parse_grid(GRID), SearchAlgorithm.FORWARD)

    assert response.status == "found"
    assert response.stats.path_length == 9
    assert response.plan[0].from_state == response.start
    assert response.plan[-1].to_state == response.goal
    assert _plan_reaches_goal(parse_grid(GRID), response.plan)


def test_backward_search_returns_forward_executable_plan() -> None:
    problem = parse_grid(GRID)
    response = run_search(problem, SearchAlgorithm.BACKWARD)

    assert response.status == "found"
    assert response.stats.path_length == 9
    assert _plan_reaches_goal(problem, response.plan)


def test_bidirectional_search_returns_plan_and_meeting_state() -> None:
    problem = parse_grid(GRID)
    response = run_search(problem, SearchAlgorithm.BIDIRECTIONAL)

    assert response.status == "found"
    assert response.stats.path_length == 9
    assert response.trace[-1].meeting_state is not None
    assert _plan_reaches_goal(problem, response.plan)


def test_forward_search_records_tree_edges_for_discovered_states() -> None:
    response = run_search(parse_grid(GRID), SearchAlgorithm.FORWARD)
    final_frame = response.trace[-1]

    assert final_frame.forward_tree_edges
    assert len(final_frame.forward_tree_edges) == len(final_frame.visited) - 1


def test_backward_search_records_reverse_tree_edges() -> None:
    response = run_search(parse_grid(GRID), SearchAlgorithm.BACKWARD)
    final_frame = response.trace[-1]

    assert final_frame.backward_tree_edges
    assert len(final_frame.backward_tree_edges) == len(final_frame.backward_visited) - 1


def test_bidirectional_search_records_both_search_trees() -> None:
    response = run_search(parse_grid(GRID), SearchAlgorithm.BIDIRECTIONAL)
    final_frame = response.trace[-1]

    assert final_frame.forward_tree_edges
    assert final_frame.backward_tree_edges


@pytest.mark.parametrize("algorithm", GRID_ALGORITHMS)
def test_no_path_returns_not_found(algorithm: SearchAlgorithm) -> None:
    response = run_search(parse_grid(NO_PATH_GRID), algorithm)

    assert response.status == "not_found"
    assert response.plan == []
    assert response.stats.path_length is None


@pytest.mark.parametrize("algorithm", GRID_ALGORITHMS)
def test_start_equals_goal_is_found_with_empty_plan(algorithm: SearchAlgorithm) -> None:
    problem = parse_grid(["S"], goal=State(row=0, col=0))
    response = run_search(problem, algorithm)

    assert response.status == "found"
    assert response.plan == []
    assert response.stats.path_length == 0


@pytest.mark.parametrize(
    "grid, message",
    [
        (["S.", "G"], "rectangular"),
        (["SXG"], "Unsupported"),
        (["S.."], "goal"),
        (["G.."], "start"),
    ],
)
def test_invalid_grid_cases(grid: list[str], message: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        parse_grid(grid)

    assert message in str(exc_info.value.detail)


def test_api_returns_trace_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/chapter2/search/trace",
        json={"algorithm": "forward", "grid": GRID},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["algorithm"] == "forward"
    assert payload["status"] == "found"
    assert payload["trace"]
    assert payload["stats"]["path_length"] == 9


@pytest.mark.parametrize("algorithm", GRID_ALGORITHMS)
def test_trace_visited_sets_grow_monotonically(algorithm: SearchAlgorithm) -> None:
    response = run_search(parse_grid(GRID), algorithm)
    forward_seen: set[tuple[int, int]] = set()
    backward_seen: set[tuple[int, int]] = set()

    for frame in response.trace:
        visited = {(state.row, state.col) for state in frame.visited}
        backward_visited = {(state.row, state.col) for state in frame.backward_visited}
        if visited:
            assert forward_seen <= visited
        if backward_visited:
            assert backward_seen <= backward_visited
        forward_seen |= visited
        backward_seen |= backward_visited


@pytest.mark.parametrize(
    "algorithm",
    [
        SearchAlgorithm.DIJKSTRA,
        SearchAlgorithm.ASTAR,
        SearchAlgorithm.FORWARD_VALUE_ITERATION,
        SearchAlgorithm.BACKWARD_VALUE_ITERATION,
    ],
)
def test_weighted_graph_algorithms_return_optimal_path(algorithm: SearchAlgorithm) -> None:
    from app.models import WeightedGraphProblem

    response = run_weighted_graph_search(WeightedGraphProblem.model_validate(SAMPLE_GRAPH), algorithm)

    assert response.status == "found"
    assert response.graph_path == ["S", "B", "A", "C", "G"]
    assert response.stats.total_cost == 8
    assert response.trace
    assert any(frame.node_labels for frame in response.trace)
    assert any(frame.relaxation and frame.relaxation.improved for frame in response.trace)


def test_weighted_graph_trace_api() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/chapter2/search/trace",
        json={"algorithm": "dijkstra", "graph": SAMPLE_GRAPH},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["algorithm"] == "dijkstra"
    assert payload["graph_path"] == ["S", "B", "A", "C", "G"]
    assert payload["stats"]["total_cost"] == 8


def _plan_reaches_goal(problem: GridProblem, plan: list) -> bool:
    state = problem.start
    for step in plan:
        action = step.action
        assert action in DIRECTIONS
        dr, dc = DIRECTIONS[action]
        expected = (state[0] + dr, state[1] + dc)
        actual = (step.to_state.row, step.to_state.col)
        assert (step.from_state.row, step.from_state.col) == state
        assert actual == expected
        assert problem.is_free(actual)
        state = actual
    return state == problem.goal

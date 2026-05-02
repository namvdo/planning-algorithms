import pytest
from fastapi import HTTPException

from app.code_judge import default_algorithm_code, evaluate_code, visualize_code
from app.models import SearchAlgorithm


GRID = [
    "S.....#.",
    ".####...",
    "....#..G",
    "..#.....",
]


def test_default_forward_code_passes_judge() -> None:
    result = evaluate_code(SearchAlgorithm.FORWARD, GRID, default_algorithm_code(SearchAlgorithm.FORWARD))

    assert result.passed
    assert all(case.passed for case in result.cases)


def test_default_backward_code_passes_judge() -> None:
    result = evaluate_code(SearchAlgorithm.BACKWARD, GRID, default_algorithm_code(SearchAlgorithm.BACKWARD))

    assert result.passed
    assert all(case.passed for case in result.cases)


def test_default_bidirectional_code_passes_judge() -> None:
    result = evaluate_code(SearchAlgorithm.BIDIRECTIONAL, GRID, default_algorithm_code(SearchAlgorithm.BIDIRECTIONAL))

    assert result.passed
    assert all(case.passed for case in result.cases)


def test_incorrect_code_fails_judge() -> None:
    code = """
def forward_search(x_init, is_goal, get_actions, transition):
    return ["right"]
"""
    result = evaluate_code(SearchAlgorithm.FORWARD, GRID, code)

    assert not result.passed
    assert any(not case.passed for case in result.cases)


def test_timing_out_code_fails_judge() -> None:
    code = """
def forward_search(x_init, is_goal, get_actions, transition):
    while True:
        pass
"""
    result = evaluate_code(SearchAlgorithm.FORWARD, GRID, code)

    assert not result.passed
    assert all("Timed out" in case.message for case in result.cases)


def test_visualize_code_uses_submitted_code_for_trace() -> None:
    code = """
def forward_search(x_init, is_goal, get_actions, transition):
    return ["right", "right", "right"]
"""
    result = visualize_code(SearchAlgorithm.FORWARD, ["S..G"], code)

    assert result.status == "found"
    assert result.stats.path_length == 3
    assert result.trace[-1].message.startswith("Submitted code reached the goal")


def test_visualize_code_rejects_broken_submitted_code() -> None:
    code = """
def forward_search(x_init, is_goal, get_actions, transition):
    return ["right"]
"""
    with pytest.raises(HTTPException) as exc_info:
        visualize_code(SearchAlgorithm.FORWARD, GRID, code)

    assert exc_info.value.status_code == 422

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path

from fastapi import HTTPException

from app.grid import DIRECTIONS, GridProblem, parse_grid
from app.models import (
    CodeEvaluationResponse,
    JudgeCaseResult,
    PlanStep,
    SearchAlgorithm,
    SearchResponse,
    SearchStats,
    SearchStatus,
    SearchTreeEdge,
    State,
    TraceFrame,
)
from app.search import run_search

TIMEOUT_SECONDS = 2.0

RUNNER = r"""
import importlib.util
import json
import sys
import traceback
from collections import deque

DIRECTIONS = {
    "up": (-1, 0),
    "down": (1, 0),
    "left": (0, -1),
    "right": (0, 1),
}
INVERSE = {"up": "down", "down": "up", "left": "right", "right": "left"}


def parse_grid(grid):
    start = goal = None
    walls = set()
    for r, row in enumerate(grid):
        for c, char in enumerate(row):
            if char == "S":
                start = (r, c)
            elif char == "G":
                goal = (r, c)
            elif char == "#":
                walls.add((r, c))
    return start, goal, walls, len(grid), len(grid[0])


def make_problem(grid):
    start, goal, walls, rows, cols = parse_grid(grid)

    def is_free(state):
        r, c = state
        return 0 <= r < rows and 0 <= c < cols and state not in walls

    def is_goal(state):
        return state == goal

    def get_actions(state):
        r, c = state
        actions = []
        for action, (dr, dc) in DIRECTIONS.items():
            nxt = (r + dr, c + dc)
            if is_free(nxt):
                actions.append(action)
        return actions

    def transition(state, action):
        dr, dc = DIRECTIONS[action]
        return (state[0] + dr, state[1] + dc)

    def get_inverse_actions(state):
        r, c = state
        actions = []
        for action in DIRECTIONS:
            dr, dc = DIRECTIONS[INVERSE[action]]
            prev = (r + dr, c + dc)
            if is_free(prev):
                actions.append(action)
        return actions

    def inverse_transition(state, action):
        dr, dc = DIRECTIONS[INVERSE[action]]
        return (state[0] + dr, state[1] + dc)

    return {
        "start": start,
        "goal": goal,
        "is_goal": is_goal,
        "get_actions": get_actions,
        "transition": transition,
        "get_inverse_actions": get_inverse_actions,
        "inverse_transition": inverse_transition,
    }


def normalize_plan(raw_plan):
    if raw_plan is None:
        return None
    if not isinstance(raw_plan, list):
        raise TypeError("Plan must be a list of action strings or (state, action) pairs.")
    actions = []
    for item in raw_plan:
        if isinstance(item, str):
            actions.append(item)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            actions.append(item[1])
        else:
            raise TypeError("Each plan step must be an action string or a pair like ((row, col), action).")
    return actions


def normalize_result(raw_result):
    if isinstance(raw_result, dict):
        return {
            "actions": normalize_plan(raw_result.get("actions")),
            "trace": raw_result.get("trace"),
        }
    return {"actions": normalize_plan(raw_result), "trace": None}


def execute_case(module, algorithm, grid):
    problem = make_problem(grid)
    if algorithm == "forward":
        fn = getattr(module, "forward_search")
        raw_plan = fn(problem["start"], problem["is_goal"], problem["get_actions"], problem["transition"])
    elif algorithm == "backward":
        fn = getattr(module, "backward_search")
        raw_plan = fn(problem["start"], problem["goal"], problem["get_inverse_actions"], problem["inverse_transition"])
    else:
        fn = getattr(module, "bidirectional_search")
        raw_plan = fn(
            problem["start"],
            problem["goal"],
            problem["get_actions"],
            problem["transition"],
            problem["get_inverse_actions"],
            problem["inverse_transition"],
        )
    return normalize_result(raw_plan)


def main():
    payload_path, solution_path = sys.argv[1], sys.argv[2]
    payload = json.loads(open(payload_path).read())
    spec = importlib.util.spec_from_file_location("user_solution", solution_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    outputs = []
    for case in payload["cases"]:
        try:
            result = execute_case(module, payload["algorithm"], case["grid"])
            outputs.append({"name": case["name"], "actions": result["actions"], "trace": result["trace"], "error": None})
        except Exception:
            outputs.append({"name": case["name"], "actions": None, "error": traceback.format_exc(limit=5)})
    print(json.dumps({"outputs": outputs}))


if __name__ == "__main__":
    main()
"""


def evaluate_code(
    algorithm: SearchAlgorithm,
    grid: list[str],
    code: str,
    start: State | None = None,
    goal: State | None = None,
) -> CodeEvaluationResponse:
    cases = _build_cases(algorithm, grid, start, goal)
    payload = {"algorithm": algorithm.value, "cases": [{"name": name, "grid": case.grid} for name, case, _ in cases]}
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="planning-code-judge-") as temp_dir:
        temp = Path(temp_dir)
        solution_path = temp / "user_solution.py"
        runner_path = temp / "runner.py"
        payload_path = temp / "payload.json"
        solution_path.write_text(code, encoding="utf-8")
        runner_path.write_text(RUNNER, encoding="utf-8")
        payload_path.write_text(json.dumps(payload), encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(runner_path), str(payload_path), str(solution_path)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env={"PYTHONPATH": "", "PATH": os.environ.get("PATH", "")},
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            return CodeEvaluationResponse(
                algorithm=algorithm,
                passed=False,
                cases=[
                    JudgeCaseResult(
                        name=name,
                        passed=False,
                        message=f"Timed out after {TIMEOUT_SECONDS:.1f}s.",
                        expected_length=expected_length,
                    )
                    for name, _, expected_length in cases
                ],
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                duration_ms=duration_ms,
            )

    duration_ms = int((time.monotonic() - started) * 1000)
    if completed.returncode != 0:
        return CodeEvaluationResponse(
            algorithm=algorithm,
            passed=False,
            cases=[
                JudgeCaseResult(
                    name=name,
                    passed=False,
                    message="Python execution failed before the judge could run this case.",
                    expected_length=expected_length,
                )
                for name, _, expected_length in cases
            ],
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_ms=duration_ms,
        )

    try:
        result_payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return CodeEvaluationResponse(
            algorithm=algorithm,
            passed=False,
            cases=[
                JudgeCaseResult(
                    name=name,
                    passed=False,
                    message="Judge could not parse the submitted program output.",
                    expected_length=expected_length,
                )
                for name, _, expected_length in cases
            ],
            stdout=completed.stdout,
            stderr=completed.stderr,
            duration_ms=duration_ms,
        )

    output_by_name = {item["name"]: item for item in result_payload["outputs"]}
    judged_cases = []
    for name, problem, expected_length in cases:
        output = output_by_name.get(name, {})
        judged_cases.append(_judge_case(name, problem, output.get("actions"), output.get("error"), expected_length))

    return CodeEvaluationResponse(
        algorithm=algorithm,
        passed=all(case.passed for case in judged_cases),
        cases=judged_cases,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_ms=duration_ms,
    )


def visualize_code(
    algorithm: SearchAlgorithm,
    grid: list[str],
    code: str,
    start: State | None = None,
    goal: State | None = None,
) -> SearchResponse:
    problem = parse_grid(grid, start, goal)
    expected_length = run_search(problem, algorithm).stats.path_length
    output, stdout, stderr, duration_ms = _execute_current_grid(algorithm, problem, code)

    judge_result = _judge_case("Current grid", problem, output.get("actions"), output.get("error"), expected_length)
    if not judge_result.passed:
        detail = judge_result.message
        if stderr:
            detail = f"{detail}\n{stderr.strip()}"
        raise HTTPException(status_code=422, detail=detail)

    return _search_response_from_actions(
        algorithm=algorithm,
        problem=problem,
        actions=output.get("actions"),
        trace_payload=output.get("trace"),
        duration_ms=duration_ms,
        stdout=stdout,
    )


def _execute_current_grid(
    algorithm: SearchAlgorithm,
    problem: GridProblem,
    code: str,
) -> tuple[dict, str, str, int]:
    payload = {"algorithm": algorithm.value, "cases": [{"name": "Current grid", "grid": problem.grid}]}
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="planning-code-visualize-") as temp_dir:
        temp = Path(temp_dir)
        solution_path = temp / "user_solution.py"
        runner_path = temp / "runner.py"
        payload_path = temp / "payload.json"
        solution_path.write_text(code, encoding="utf-8")
        runner_path.write_text(RUNNER, encoding="utf-8")
        payload_path.write_text(json.dumps(payload), encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(runner_path), str(payload_path), str(solution_path)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env={"PYTHONPATH": "", "PATH": os.environ.get("PATH", "")},
            )
        except subprocess.TimeoutExpired as exc:
            duration_ms = int((time.monotonic() - started) * 1000)
            return (
                {"name": "Current grid", "actions": None, "error": f"Timed out after {TIMEOUT_SECONDS:.1f}s."},
                exc.stdout or "",
                exc.stderr or "",
                duration_ms,
            )

    duration_ms = int((time.monotonic() - started) * 1000)
    if completed.returncode != 0:
        return (
            {"name": "Current grid", "actions": None, "error": "Python execution failed before visualization could run."},
            completed.stdout,
            completed.stderr,
            duration_ms,
        )

    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
        output = payload["outputs"][0]
    except (IndexError, KeyError, json.JSONDecodeError):
        output = {"name": "Current grid", "actions": None, "error": "Could not parse submitted program output."}
    return output, completed.stdout, completed.stderr, duration_ms


def _search_response_from_actions(
    algorithm: SearchAlgorithm,
    problem: GridProblem,
    actions: list[str] | None,
    trace_payload: list[dict] | None,
    duration_ms: int,
    stdout: str,
) -> SearchResponse:
    if actions is None:
        trace = [
            TraceFrame(
                index=0,
                phase="submitted-code",
                message="Submitted code reported that no plan exists.",
                current=State(row=problem.start[0], col=problem.start[1]),
                visited=[State(row=problem.start[0], col=problem.start[1])],
                plan_prefix=[State(row=problem.start[0], col=problem.start[1])],
            )
        ]
        return SearchResponse(
            algorithm=algorithm,
            status=SearchStatus.NOT_FOUND,
            start=State(row=problem.start[0], col=problem.start[1]),
            goal=State(row=problem.goal[0], col=problem.goal[1]),
            rows=problem.rows,
            cols=problem.cols,
            plan=[],
            trace=trace,
            stats=SearchStats(expanded_count=0, visited_count=1, max_frontier_size=0, path_length=None, trace_length=1),
        )

    steps, _ = _plan_steps_from_actions(problem, actions)
    traced_response = _search_response_from_submitted_trace(algorithm, problem, actions, trace_payload, steps)
    if traced_response is not None:
        return traced_response

    state = problem.start
    visited = [state]
    trace = [
        TraceFrame(
            index=0,
            phase="submitted-code",
            message="Run the submitted Python3 code and visualize the returned action sequence.",
            current=State(row=state[0], col=state[1]),
            visited=_states(visited),
            plan_prefix=_states(visited),
        )
    ]

    for index, action in enumerate(actions, start=1):
        dr, dc = DIRECTIONS[action]  # type: ignore[index]
        state = (state[0] + dr, state[1] + dc)
        visited.append(state)
        trace.append(
            TraceFrame(
                index=index,
                phase="submitted-code",
                message=f"Submitted code step {index}: move {action} to ({state[0]}, {state[1]}).",
                current=State(row=state[0], col=state[1]),
                visited=_states(visited),
                discovered=[State(row=state[0], col=state[1])],
                plan_prefix=_states(visited),
            )
        )

    trace.append(
        TraceFrame(
            index=len(trace),
            phase="complete",
            message=f"Submitted code reached the goal in {len(actions)} step(s). Evaluation took {duration_ms} ms.",
            current=State(row=state[0], col=state[1]),
            visited=_states(visited),
            plan_prefix=_states(visited),
        )
    )

    return SearchResponse(
        algorithm=algorithm,
        status=SearchStatus.FOUND,
        start=State(row=problem.start[0], col=problem.start[1]),
        goal=State(row=problem.goal[0], col=problem.goal[1]),
        rows=problem.rows,
        cols=problem.cols,
        plan=steps,
        trace=trace,
        stats=SearchStats(
            expanded_count=len(actions),
            visited_count=len(set(visited)),
            max_frontier_size=0,
            path_length=len(actions),
            trace_length=len(trace),
        ),
    )


def _search_response_from_submitted_trace(
    algorithm: SearchAlgorithm,
    problem: GridProblem,
    actions: list[str],
    trace_payload: list[dict] | None,
    steps: list[PlanStep],
) -> SearchResponse | None:
    if not trace_payload:
        return None

    try:
        trace = [_trace_frame_from_payload(index, raw_frame) for index, raw_frame in enumerate(trace_payload)]
    except (TypeError, ValueError, KeyError):
        return None

    visited_states = {
        (state.row, state.col)
        for frame in trace
        for state in [*frame.visited, *frame.backward_visited]
    }
    max_frontier_size = max((len(frame.frontier) + len(frame.backward_frontier) for frame in trace), default=0)

    return SearchResponse(
        algorithm=algorithm,
        status=SearchStatus.FOUND,
        start=State(row=problem.start[0], col=problem.start[1]),
        goal=State(row=problem.goal[0], col=problem.goal[1]),
        rows=problem.rows,
        cols=problem.cols,
        plan=steps,
        trace=trace,
        stats=SearchStats(
            expanded_count=max(len(trace) - 1, len(actions)),
            visited_count=len(visited_states),
            max_frontier_size=max_frontier_size,
            path_length=len(actions),
            trace_length=len(trace),
        ),
    )


def _trace_frame_from_payload(index: int, raw_frame: dict) -> TraceFrame:
    return TraceFrame(
        index=index,
        phase=str(raw_frame.get("phase", "submitted-code")),
        message=str(raw_frame.get("message", "Submitted code trace frame.")),
        current=_state_from_payload(raw_frame.get("current")),
        frontier=_states_from_payload(raw_frame.get("frontier", [])),
        visited=_states_from_payload(raw_frame.get("visited", [])),
        backward_frontier=_states_from_payload(raw_frame.get("backward_frontier", [])),
        backward_visited=_states_from_payload(raw_frame.get("backward_visited", [])),
        forward_tree_edges=_tree_edges_from_payload(raw_frame.get("forward_tree_edges", [])),
        backward_tree_edges=_tree_edges_from_payload(raw_frame.get("backward_tree_edges", [])),
        discovered=_states_from_payload(raw_frame.get("discovered", [])),
        meeting_state=_state_from_payload(raw_frame.get("meeting_state")),
        plan_prefix=_states_from_payload(raw_frame.get("plan_prefix", [])),
    )


def _plan_steps_from_actions(problem: GridProblem, actions: list[str]) -> tuple[list[PlanStep], list[tuple[int, int]]]:
    state = problem.start
    states = [state]
    steps = []
    for index, action in enumerate(actions, start=1):
        previous = state
        dr, dc = DIRECTIONS[action]  # type: ignore[index]
        state = (state[0] + dr, state[1] + dc)
        states.append(state)
        steps.append(
            PlanStep(
                index=index,
                from_state=State(row=previous[0], col=previous[1]),
                to_state=State(row=state[0], col=state[1]),
                action=action,
            )
        )
    return steps, states


def _states(states: list[tuple[int, int]]) -> list[State]:
    return [State(row=row, col=col) for row, col in states]


def _state_from_payload(value: object) -> State | None:
    if value is None:
        return None
    if isinstance(value, dict):
        return State(row=int(value["row"]), col=int(value["col"]))
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return State(row=int(value[0]), col=int(value[1]))
    raise ValueError("State payload must be a row/col object or pair.")


def _states_from_payload(values: object) -> list[State]:
    if not isinstance(values, list):
        raise ValueError("State list payload must be a list.")
    states = []
    for value in values:
        state = _state_from_payload(value)
        if state is not None:
            states.append(state)
    return states


def _tree_edges_from_payload(values: object) -> list[SearchTreeEdge]:
    if not isinstance(values, list):
        raise ValueError("Tree edge payload must be a list.")

    edges = []
    for value in values:
        if isinstance(value, dict):
            start = _state_from_payload(value["from_state"])
            end = _state_from_payload(value["to_state"])
            action = str(value["action"])
        elif isinstance(value, (list, tuple)) and len(value) == 3:
            start = _state_from_payload(value[0])
            end = _state_from_payload(value[1])
            action = str(value[2])
        else:
            raise ValueError("Tree edge must be an object or (from, to, action) tuple.")
        if start is None or end is None:
            raise ValueError("Tree edge endpoints cannot be None.")
        edges.append(SearchTreeEdge(from_state=start, to_state=end, action=action))
    return edges


def _build_cases(
    algorithm: SearchAlgorithm,
    grid: list[str],
    start: State | None,
    goal: State | None,
) -> list[tuple[str, GridProblem, int | None]]:
    raw_cases = [
        ("Current grid", grid, start, goal),
        ("Straight path", ["S..G"], None, None),
        ("Blocked grid", ["S#G"], None, None),
        ("Turn around wall", ["S.#", "..G"], None, None),
    ]
    cases = []
    for name, raw_grid, raw_start, raw_goal in raw_cases:
        problem = parse_grid(raw_grid, raw_start, raw_goal)
        expected = run_search(problem, algorithm).stats.path_length
        cases.append((name, problem, expected))
    return cases


def _judge_case(
    name: str,
    problem: GridProblem,
    actions: list[str] | None,
    error: str | None,
    expected_length: int | None,
) -> JudgeCaseResult:
    if error:
        return JudgeCaseResult(name=name, passed=False, message=error.strip().splitlines()[-1], expected_length=expected_length)

    if expected_length is None:
        passed = actions is None
        return JudgeCaseResult(
            name=name,
            passed=passed,
            message="Correctly reported no plan." if passed else "Expected no plan, but the code returned actions.",
            expected_length=None,
            actual_length=len(actions) if actions is not None else None,
        )

    if actions is None:
        return JudgeCaseResult(name=name, passed=False, message="Expected a plan, but the code returned None.", expected_length=expected_length)

    state = problem.start
    for action in actions:
        if action not in DIRECTIONS:
            return JudgeCaseResult(
                name=name,
                passed=False,
                message=f"Invalid action {action!r}.",
                expected_length=expected_length,
                actual_length=len(actions),
            )
        dr, dc = DIRECTIONS[action]  # type: ignore[index]
        state = (state[0] + dr, state[1] + dc)
        if not problem.is_free(state):
            return JudgeCaseResult(
                name=name,
                passed=False,
                message=f"Action {action!r} moves into a wall or outside the grid.",
                expected_length=expected_length,
                actual_length=len(actions),
            )

    if state != problem.goal:
        return JudgeCaseResult(
            name=name,
            passed=False,
            message=f"Plan ended at {state}, not the goal {problem.goal}.",
            expected_length=expected_length,
            actual_length=len(actions),
        )

    if len(actions) != expected_length:
        return JudgeCaseResult(
            name=name,
            passed=False,
            message="Plan reaches the goal but is not shortest for this unweighted grid.",
            expected_length=expected_length,
            actual_length=len(actions),
        )

    return JudgeCaseResult(
        name=name,
        passed=True,
        message="Plan is valid and has the expected length.",
        expected_length=expected_length,
        actual_length=len(actions),
    )


def default_algorithm_code(algorithm: SearchAlgorithm) -> str:
    if algorithm == SearchAlgorithm.FORWARD:
        return textwrap.dedent(
            """
            from collections import deque


            def forward_search(x_init, is_goal, get_actions, transition):
                queue = deque([x_init])
                visited = {x_init}
                parent = {x_init: (None, None)}
                tree_edges = []
                trace = []

                append_frame(trace, "forward", "Initialize the frontier with the start state.", queue, visited, tree_edges)

                while queue:
                    state = queue.popleft()
                    if is_goal(state):
                        actions = extract_actions(parent, state)
                        append_frame(
                            trace,
                            "complete",
                            "Goal reached. Reconstruct the plan from parent pointers.",
                            queue,
                            visited,
                            tree_edges,
                            current=state,
                            plan_prefix=states_from_actions(x_init, actions, transition),
                        )
                        return {"actions": actions, "trace": trace}

                    discovered = []
                    for action in get_actions(state):
                        next_state = transition(state, action)
                        if next_state not in visited:
                            visited.add(next_state)
                            parent[next_state] = (state, action)
                            tree_edges.append((state, next_state, action))
                            queue.append(next_state)
                            discovered.append(next_state)

                    append_frame(
                        trace,
                        "forward",
                        f"Expand {state} and add {len(discovered)} unvisited successor state(s).",
                        queue,
                        visited,
                        tree_edges,
                        current=state,
                        discovered=discovered,
                    )

                return {"actions": None, "trace": trace}


            def extract_actions(parent, goal):
                actions = []
                state = goal
                while parent[state][0] is not None:
                    previous, action = parent[state]
                    actions.append(action)
                    state = previous
                actions.reverse()
                return actions


            def states_from_actions(start, actions, transition):
                states = [start]
                state = start
                for action in actions:
                    state = transition(state, action)
                    states.append(state)
                return states


            def append_frame(
                trace,
                phase,
                message,
                queue,
                visited,
                tree_edges,
                current=None,
                discovered=None,
                plan_prefix=None,
            ):
                trace.append(
                    {
                        "phase": phase,
                        "message": message,
                        "current": current,
                        "frontier": list(queue),
                        "visited": sorted(visited),
                        "forward_tree_edges": list(tree_edges),
                        "discovered": discovered or [],
                        "plan_prefix": plan_prefix or [],
                    }
                )
            """
        ).strip()
    if algorithm == SearchAlgorithm.BACKWARD:
        return textwrap.dedent(
            """
            from collections import deque


            def backward_search(x_init, x_goal, get_inverse_actions, inverse_transition):
                queue = deque([x_goal])
                visited = {x_goal}
                parent = {x_goal: (None, None)}
                tree_edges = []
                trace = []

                append_frame(trace, "backward", "Initialize the frontier with the goal state.", queue, visited, tree_edges)

                while queue:
                    state = queue.popleft()
                    if state == x_init:
                        actions = extract_actions(parent, x_init, x_goal)
                        append_frame(
                            trace,
                            "complete",
                            "Start reached by reverse expansion. Read stored forward actions.",
                            queue,
                            visited,
                            tree_edges,
                            current=state,
                            plan_prefix=states_from_actions(x_init, actions),
                        )
                        return {"actions": actions, "trace": trace}

                    discovered = []
                    for action in get_inverse_actions(state):
                        previous = inverse_transition(state, action)
                        if previous not in visited:
                            visited.add(previous)
                            parent[previous] = (state, action)
                            tree_edges.append((previous, state, action))
                            queue.append(previous)
                            discovered.append(previous)

                    append_frame(
                        trace,
                        "backward",
                        f"Reverse-expand {state} and add {len(discovered)} predecessor state(s).",
                        queue,
                        visited,
                        tree_edges,
                        current=state,
                        discovered=discovered,
                    )

                return {"actions": None, "trace": trace}


            def extract_actions(parent, start, goal):
                actions = []
                state = start
                while state != goal:
                    next_state, action = parent[state]
                    actions.append(action)
                    state = next_state
                return actions


            def states_from_actions(start, actions):
                deltas = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
                states = [start]
                state = start
                for action in actions:
                    dr, dc = deltas[action]
                    state = (state[0] + dr, state[1] + dc)
                    states.append(state)
                return states


            def append_frame(
                trace,
                phase,
                message,
                queue,
                visited,
                tree_edges,
                current=None,
                discovered=None,
                plan_prefix=None,
            ):
                trace.append(
                    {
                        "phase": phase,
                        "message": message,
                        "current": current,
                        "backward_frontier": list(queue),
                        "backward_visited": sorted(visited),
                        "backward_tree_edges": list(tree_edges),
                        "discovered": discovered or [],
                        "plan_prefix": plan_prefix or [],
                    }
                )
            """
        ).strip()
    return textwrap.dedent(
        """
        from collections import deque


        def bidirectional_search(
            x_init,
            x_goal,
            get_actions,
            transition,
            get_inverse_actions,
            inverse_transition,
        ):
            if x_init == x_goal:
                return []

            f_queue = deque([x_init])
            b_queue = deque([x_goal])
            f_seen = {x_init}
            b_seen = {x_goal}
            f_parent = {x_init: (None, None)}
            b_parent = {x_goal: (None, None)}
            f_edges = []
            b_edges = []
            trace = []

            append_frame(
                trace,
                "bidirectional",
                "Initialize one frontier at the start and one frontier at the goal.",
                f_queue,
                f_seen,
                b_queue,
                b_seen,
                f_edges,
                b_edges,
            )

            while f_queue or b_queue:
                if f_queue:
                    meeting = expand_forward(
                        f_queue,
                        f_seen,
                        f_parent,
                        b_seen,
                        f_edges,
                        trace,
                        b_queue,
                        b_seen,
                        b_edges,
                        get_actions,
                        transition,
                    )
                    if meeting is not None:
                        actions = join_plan(f_parent, b_parent, x_init, meeting, x_goal)
                        append_frame(
                            trace,
                            "complete",
                            f"Frontiers meet at {meeting}. Join both parent maps into one plan.",
                            f_queue,
                            f_seen,
                            b_queue,
                            b_seen,
                            f_edges,
                            b_edges,
                            meeting_state=meeting,
                            plan_prefix=states_from_actions(x_init, actions),
                        )
                        return {"actions": actions, "trace": trace}

                if b_queue:
                    meeting = expand_backward(
                        b_queue,
                        b_seen,
                        b_parent,
                        f_seen,
                        b_edges,
                        trace,
                        f_queue,
                        f_seen,
                        f_edges,
                        get_inverse_actions,
                        inverse_transition,
                    )
                    if meeting is not None:
                        actions = join_plan(f_parent, b_parent, x_init, meeting, x_goal)
                        append_frame(
                            trace,
                            "complete",
                            f"Frontiers meet at {meeting}. Join both parent maps into one plan.",
                            f_queue,
                            f_seen,
                            b_queue,
                            b_seen,
                            f_edges,
                            b_edges,
                            meeting_state=meeting,
                            plan_prefix=states_from_actions(x_init, actions),
                        )
                        return {"actions": actions, "trace": trace}

            return {"actions": None, "trace": trace}


        def expand_forward(
            queue,
            seen,
            parent,
            other_seen,
            tree_edges,
            trace,
            backward_queue,
            backward_seen,
            backward_edges,
            get_actions,
            transition,
        ):
            state = queue.popleft()
            discovered = []
            if state in other_seen:
                append_frame(
                    trace,
                    "forward",
                    f"Forward side expands {state}.",
                    queue,
                    seen,
                    backward_queue,
                    backward_seen,
                    tree_edges,
                    backward_edges,
                    current=state,
                    meeting_state=state,
                )
                return state
            for action in get_actions(state):
                next_state = transition(state, action)
                if next_state not in seen:
                    seen.add(next_state)
                    parent[next_state] = (state, action)
                    tree_edges.append((state, next_state, action))
                    queue.append(next_state)
                    discovered.append(next_state)
                    if next_state in other_seen:
                        append_frame(
                            trace,
                            "forward",
                            f"Forward side expands {state}.",
                            queue,
                            seen,
                            backward_queue,
                            backward_seen,
                            tree_edges,
                            backward_edges,
                            current=state,
                            discovered=discovered,
                            meeting_state=next_state,
                        )
                        return next_state
            append_frame(
                trace,
                "forward",
                f"Forward side expands {state}.",
                queue,
                seen,
                backward_queue,
                backward_seen,
                tree_edges,
                backward_edges,
                current=state,
                discovered=discovered,
            )
            return None


        def expand_backward(
            queue,
            seen,
            parent,
            other_seen,
            tree_edges,
            trace,
            forward_queue,
            forward_seen,
            forward_edges,
            get_inverse_actions,
            inverse_transition,
        ):
            state = queue.popleft()
            discovered = []
            if state in other_seen:
                append_frame(
                    trace,
                    "backward",
                    f"Backward side reverse-expands {state}.",
                    forward_queue,
                    forward_seen,
                    queue,
                    seen,
                    forward_edges,
                    tree_edges,
                    current=state,
                    meeting_state=state,
                )
                return state
            for action in get_inverse_actions(state):
                previous = inverse_transition(state, action)
                if previous not in seen:
                    seen.add(previous)
                    parent[previous] = (state, action)
                    tree_edges.append((previous, state, action))
                    queue.append(previous)
                    discovered.append(previous)
                    if previous in other_seen:
                        append_frame(
                            trace,
                            "backward",
                            f"Backward side reverse-expands {state}.",
                            forward_queue,
                            forward_seen,
                            queue,
                            seen,
                            forward_edges,
                            tree_edges,
                            current=state,
                            discovered=discovered,
                            meeting_state=previous,
                        )
                        return previous
            append_frame(
                trace,
                "backward",
                f"Backward side reverse-expands {state}.",
                forward_queue,
                forward_seen,
                queue,
                seen,
                forward_edges,
                tree_edges,
                current=state,
                discovered=discovered,
            )
            return None


        def actions_from_forward(parent, start, goal):
            actions = []
            state = goal
            while state != start:
                previous, action = parent[state]
                actions.append(action)
                state = previous
            actions.reverse()
            return actions


        def actions_from_backward(parent, start, goal):
            actions = []
            state = start
            while state != goal:
                next_state, action = parent[state]
                actions.append(action)
                state = next_state
            return actions


        def join_plan(f_parent, b_parent, start, meeting, goal):
            return actions_from_forward(f_parent, start, meeting) + actions_from_backward(b_parent, meeting, goal)


        def states_from_actions(start, actions):
            deltas = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
            states = [start]
            state = start
            for action in actions:
                dr, dc = deltas[action]
                state = (state[0] + dr, state[1] + dc)
                states.append(state)
            return states


        def append_frame(
            trace,
            phase,
            message,
            forward_queue,
            forward_seen,
            backward_queue,
            backward_seen,
            forward_edges,
            backward_edges,
            current=None,
            discovered=None,
            meeting_state=None,
            plan_prefix=None,
        ):
            trace.append(
                {
                    "phase": phase,
                    "message": message,
                    "current": current,
                    "frontier": list(forward_queue),
                    "visited": sorted(forward_seen),
                    "backward_frontier": list(backward_queue),
                    "backward_visited": sorted(backward_seen),
                    "forward_tree_edges": list(forward_edges),
                    "backward_tree_edges": list(backward_edges),
                    "discovered": discovered or [],
                    "meeting_state": meeting_state,
                    "plan_prefix": plan_prefix or [],
                }
            )
        """
    ).strip()

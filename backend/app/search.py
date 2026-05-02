from collections import deque
from collections.abc import Iterable

from app.grid import Action, GridProblem, GridState
from app.models import (
    PlanStep,
    SearchAlgorithm,
    SearchResponse,
    SearchStats,
    SearchStatus,
    State,
    TraceFrame,
)

ParentMap = dict[GridState, tuple[GridState | None, Action | None]]


def run_search(problem: GridProblem, algorithm: SearchAlgorithm) -> SearchResponse:
    if algorithm == SearchAlgorithm.FORWARD:
        return _forward_search(problem)
    if algorithm == SearchAlgorithm.BACKWARD:
        return _backward_search(problem)
    return _bidirectional_search(problem)


def _forward_search(problem: GridProblem) -> SearchResponse:
    queue: deque[GridState] = deque([problem.start])
    visited: set[GridState] = {problem.start}
    parent: ParentMap = {problem.start: (None, None)}
    trace: list[TraceFrame] = []
    expanded_count = 0
    max_frontier = 1

    _append_frame(trace, "forward", "Initialize the frontier with the start state.", queue, visited)

    while queue:
        current = queue.popleft()
        expanded_count += 1
        discovered: list[GridState] = []

        if current == problem.goal:
            plan = _plan_from_parent(parent, problem.start, problem.goal)
            _append_frame(
                trace,
                "complete",
                "Goal reached. Reconstruct the plan by following parent pointers.",
                queue,
                visited,
                current=current,
                plan_prefix=_states_from_plan(problem.start, plan),
            )
            return _response(problem, SearchAlgorithm.FORWARD, plan, trace, expanded_count, len(visited), max_frontier)

        for action in problem.get_actions(current):
            next_state = problem.transition(current, action)
            if next_state not in visited:
                visited.add(next_state)
                parent[next_state] = (current, action)
                queue.append(next_state)
                discovered.append(next_state)

        max_frontier = max(max_frontier, len(queue))
        _append_frame(
            trace,
            "forward",
            f"Expand {format_state(current)} and add {len(discovered)} unvisited successor state(s).",
            queue,
            visited,
            current=current,
            discovered=discovered,
        )

    return _response(problem, SearchAlgorithm.FORWARD, [], trace, expanded_count, len(visited), max_frontier)


def _backward_search(problem: GridProblem) -> SearchResponse:
    queue: deque[GridState] = deque([problem.goal])
    visited: set[GridState] = {problem.goal}
    parent: ParentMap = {problem.goal: (None, None)}
    trace: list[TraceFrame] = []
    expanded_count = 0
    max_frontier = 1

    _append_frame(trace, "backward", "Initialize the frontier with the goal state.", queue, visited)

    while queue:
        current = queue.popleft()
        expanded_count += 1
        discovered: list[GridState] = []

        if current == problem.start:
            plan = _backward_plan_from_parent(parent, problem.start, problem.goal)
            _append_frame(
                trace,
                "complete",
                "Start reached by reverse expansion. Read the stored forward actions to form the plan.",
                queue,
                visited,
                current=current,
                plan_prefix=_states_from_plan(problem.start, plan),
            )
            return _response(problem, SearchAlgorithm.BACKWARD, plan, trace, expanded_count, len(visited), max_frontier)

        for action in problem.get_inverse_actions(current):
            previous = problem.inverse_transition(current, action)
            if previous not in visited:
                visited.add(previous)
                parent[previous] = (current, action)
                queue.append(previous)
                discovered.append(previous)

        max_frontier = max(max_frontier, len(queue))
        _append_frame(
            trace,
            "backward",
            f"Reverse-expand {format_state(current)} and add {len(discovered)} predecessor state(s).",
            queue,
            visited,
            current=current,
            discovered=discovered,
        )

    return _response(problem, SearchAlgorithm.BACKWARD, [], trace, expanded_count, len(visited), max_frontier)


def _bidirectional_search(problem: GridProblem) -> SearchResponse:
    if problem.start == problem.goal:
        trace: list[TraceFrame] = []
        _append_frame(
            trace,
            "complete",
            "Start and goal are the same state.",
            deque(),
            {problem.start},
            current=problem.start,
            meeting=problem.start,
            plan_prefix=[problem.start],
        )
        return _response(problem, SearchAlgorithm.BIDIRECTIONAL, [], trace, 0, 1, 0, meeting=problem.start)

    fwd_queue: deque[GridState] = deque([problem.start])
    bwd_queue: deque[GridState] = deque([problem.goal])
    fwd_visited: set[GridState] = {problem.start}
    bwd_visited: set[GridState] = {problem.goal}
    fwd_parent: ParentMap = {problem.start: (None, None)}
    bwd_parent: ParentMap = {problem.goal: (None, None)}
    trace: list[TraceFrame] = []
    expanded_count = 0
    max_frontier = 2

    _append_frame(
        trace,
        "bidirectional",
        "Initialize one frontier at the start and one frontier at the goal.",
        fwd_queue,
        fwd_visited,
        backward_frontier=bwd_queue,
        backward_visited=bwd_visited,
    )

    while fwd_queue or bwd_queue:
        if fwd_queue:
            meeting, expanded = _expand_forward_side(problem, fwd_queue, fwd_visited, fwd_parent, bwd_visited, trace)
            expanded_count += expanded
            max_frontier = max(max_frontier, len(fwd_queue) + len(bwd_queue))
            _mirror_backward_sets(trace[-1], bwd_queue, bwd_visited)
            if meeting is not None:
                plan = _join_bidirectional_plan(fwd_parent, bwd_parent, problem.start, meeting, problem.goal)
                _append_frame(
                    trace,
                    "complete",
                    f"Frontiers meet at {format_state(meeting)}. Join both parent maps into one plan.",
                    fwd_queue,
                    fwd_visited,
                    backward_frontier=bwd_queue,
                    backward_visited=bwd_visited,
                    meeting=meeting,
                    plan_prefix=_states_from_plan(problem.start, plan),
                )
                visited_count = len(fwd_visited | bwd_visited)
                return _response(
                    problem,
                    SearchAlgorithm.BIDIRECTIONAL,
                    plan,
                    trace,
                    expanded_count,
                    visited_count,
                    max_frontier,
                    meeting=meeting,
                )

        if bwd_queue:
            meeting, expanded = _expand_backward_side(problem, bwd_queue, bwd_visited, bwd_parent, fwd_visited, trace)
            expanded_count += expanded
            max_frontier = max(max_frontier, len(fwd_queue) + len(bwd_queue))
            _mirror_forward_sets(trace[-1], fwd_queue, fwd_visited)
            if meeting is not None:
                plan = _join_bidirectional_plan(fwd_parent, bwd_parent, problem.start, meeting, problem.goal)
                _append_frame(
                    trace,
                    "complete",
                    f"Frontiers meet at {format_state(meeting)}. Join both parent maps into one plan.",
                    fwd_queue,
                    fwd_visited,
                    backward_frontier=bwd_queue,
                    backward_visited=bwd_visited,
                    meeting=meeting,
                    plan_prefix=_states_from_plan(problem.start, plan),
                )
                visited_count = len(fwd_visited | bwd_visited)
                return _response(
                    problem,
                    SearchAlgorithm.BIDIRECTIONAL,
                    plan,
                    trace,
                    expanded_count,
                    visited_count,
                    max_frontier,
                    meeting=meeting,
                )

    visited_count = len(fwd_visited | bwd_visited)
    return _response(problem, SearchAlgorithm.BIDIRECTIONAL, [], trace, expanded_count, visited_count, max_frontier)


def _expand_forward_side(
    problem: GridProblem,
    queue: deque[GridState],
    visited: set[GridState],
    parent: ParentMap,
    other_visited: set[GridState],
    trace: list[TraceFrame],
) -> tuple[GridState | None, int]:
    current = queue.popleft()
    discovered: list[GridState] = []
    meeting = current if current in other_visited else None

    if meeting is None:
        for action in problem.get_actions(current):
            next_state = problem.transition(current, action)
            if next_state not in visited:
                visited.add(next_state)
                parent[next_state] = (current, action)
                queue.append(next_state)
                discovered.append(next_state)
                if next_state in other_visited:
                    meeting = next_state
                    break

    _append_frame(
        trace,
        "forward",
        f"Forward side expands {format_state(current)}.",
        queue,
        visited,
        current=current,
        discovered=discovered,
        meeting=meeting,
    )
    return meeting, 1


def _expand_backward_side(
    problem: GridProblem,
    queue: deque[GridState],
    visited: set[GridState],
    parent: ParentMap,
    other_visited: set[GridState],
    trace: list[TraceFrame],
) -> tuple[GridState | None, int]:
    current = queue.popleft()
    discovered: list[GridState] = []
    meeting = current if current in other_visited else None

    if meeting is None:
        for action in problem.get_inverse_actions(current):
            previous = problem.inverse_transition(current, action)
            if previous not in visited:
                visited.add(previous)
                parent[previous] = (current, action)
                queue.append(previous)
                discovered.append(previous)
                if previous in other_visited:
                    meeting = previous
                    break

    _append_frame(
        trace,
        "backward",
        f"Backward side reverse-expands {format_state(current)}.",
        deque(),
        set(),
        backward_frontier=queue,
        backward_visited=visited,
        current=current,
        discovered=discovered,
        meeting=meeting,
    )
    return meeting, 1


def _plan_from_parent(parent: ParentMap, start: GridState, goal: GridState) -> list[tuple[GridState, GridState, Action]]:
    if start == goal:
        return []
    steps: list[tuple[GridState, GridState, Action]] = []
    state = goal
    while state != start:
        previous, action = parent[state]
        if previous is None or action is None:
            raise ValueError("Broken parent map while reconstructing plan.")
        steps.append((previous, state, action))
        state = previous
    steps.reverse()
    return steps


def _backward_plan_from_parent(parent: ParentMap, start: GridState, goal: GridState) -> list[tuple[GridState, GridState, Action]]:
    steps: list[tuple[GridState, GridState, Action]] = []
    state = start
    while state != goal:
        next_state, action = parent[state]
        if next_state is None or action is None:
            raise ValueError("Broken backward parent map while reconstructing plan.")
        steps.append((state, next_state, action))
        state = next_state
    return steps


def _join_bidirectional_plan(
    fwd_parent: ParentMap,
    bwd_parent: ParentMap,
    start: GridState,
    meeting: GridState,
    goal: GridState,
) -> list[tuple[GridState, GridState, Action]]:
    fwd_half = _plan_from_parent(fwd_parent, start, meeting)
    bwd_half = _backward_plan_from_parent(bwd_parent, meeting, goal)
    return fwd_half + bwd_half


def _states_from_plan(start: GridState, plan: list[tuple[GridState, GridState, Action]]) -> list[GridState]:
    states = [start]
    states.extend(to_state for _, to_state, _ in plan)
    return states


def _append_frame(
    trace: list[TraceFrame],
    phase: str,
    message: str,
    frontier: Iterable[GridState],
    visited: Iterable[GridState],
    *,
    current: GridState | None = None,
    backward_frontier: Iterable[GridState] = (),
    backward_visited: Iterable[GridState] = (),
    discovered: Iterable[GridState] = (),
    meeting: GridState | None = None,
    plan_prefix: Iterable[GridState] = (),
) -> None:
    trace.append(
        TraceFrame(
            index=len(trace),
            phase=phase,
            message=message,
            current=_state(current),
            frontier=_states(frontier),
            visited=_states(visited),
            backward_frontier=_states(backward_frontier),
            backward_visited=_states(backward_visited),
            discovered=_states(discovered),
            meeting_state=_state(meeting),
            plan_prefix=_states(plan_prefix),
        )
    )


def _response(
    problem: GridProblem,
    algorithm: SearchAlgorithm,
    plan: list[tuple[GridState, GridState, Action]],
    trace: list[TraceFrame],
    expanded_count: int,
    visited_count: int,
    max_frontier_size: int,
    *,
    meeting: GridState | None = None,
) -> SearchResponse:
    if meeting is not None and trace:
        trace[-1].meeting_state = _state(meeting)

    status = SearchStatus.FOUND if plan or problem.start == problem.goal else SearchStatus.NOT_FOUND
    plan_steps = [
        PlanStep(index=index, from_state=_state_or_raise(start), to_state=_state_or_raise(end), action=action)
        for index, (start, end, action) in enumerate(plan, start=1)
    ]
    return SearchResponse(
        algorithm=algorithm,
        status=status,
        start=_state_or_raise(problem.start),
        goal=_state_or_raise(problem.goal),
        rows=problem.rows,
        cols=problem.cols,
        plan=plan_steps,
        trace=trace,
        stats=SearchStats(
            expanded_count=expanded_count,
            visited_count=visited_count,
            max_frontier_size=max_frontier_size,
            path_length=len(plan) if status == SearchStatus.FOUND else None,
            trace_length=len(trace),
        ),
    )


def _mirror_backward_sets(frame: TraceFrame, frontier: Iterable[GridState], visited: Iterable[GridState]) -> None:
    frame.backward_frontier = _states(frontier)
    frame.backward_visited = _states(visited)


def _mirror_forward_sets(frame: TraceFrame, frontier: Iterable[GridState], visited: Iterable[GridState]) -> None:
    frame.frontier = _states(frontier)
    frame.visited = _states(visited)


def _states(states: Iterable[GridState]) -> list[State]:
    return [_state_or_raise(state) for state in sorted(states)]


def _state(state: GridState | None) -> State | None:
    if state is None:
        return None
    return _state_or_raise(state)


def _state_or_raise(state: GridState) -> State:
    return State(row=state[0], col=state[1])


def format_state(state: GridState) -> str:
    return f"({state[0]}, {state[1]})"


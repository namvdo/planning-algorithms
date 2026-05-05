from __future__ import annotations

import heapq
import math
from collections.abc import Iterable

from fastapi import HTTPException

from app.models import (
    GraphNode,
    GraphNodeLabel,
    GraphTraceEdge,
    QueueItem,
    RelaxationEvent,
    SearchAlgorithm,
    SearchResponse,
    SearchStats,
    SearchStatus,
    State,
    TraceFrame,
    WeightedGraphEdge,
    WeightedGraphProblem,
)

NodeId = str
INF = float("inf")


def run_weighted_graph_search(graph: WeightedGraphProblem, algorithm: SearchAlgorithm) -> SearchResponse:
    problem = normalize_weighted_graph(graph)
    if algorithm == SearchAlgorithm.DIJKSTRA:
        return _dijkstra(problem)
    if algorithm == SearchAlgorithm.ASTAR:
        return _astar(problem)
    if algorithm == SearchAlgorithm.FORWARD_VALUE_ITERATION:
        return _forward_value_iteration(problem)
    if algorithm == SearchAlgorithm.BACKWARD_VALUE_ITERATION:
        return _backward_value_iteration(problem)
    raise HTTPException(status_code=422, detail=f"{algorithm.value} is not a weighted graph algorithm.")


def normalize_weighted_graph(graph: WeightedGraphProblem) -> WeightedGraphProblem:
    ids = [node.id for node in graph.nodes]
    if len(set(ids)) != len(ids):
        raise HTTPException(status_code=422, detail="Graph node ids must be unique.")
    if graph.start not in ids:
        raise HTTPException(status_code=422, detail="Graph start node must exist.")
    if graph.goal not in ids:
        raise HTTPException(status_code=422, detail="Graph goal node must exist.")

    id_set = set(ids)
    for edge in graph.edges:
        if edge.source not in id_set or edge.target not in id_set:
            raise HTTPException(status_code=422, detail="Every graph edge must reference existing nodes.")

    positioned_nodes = _with_positions(graph.nodes)
    return WeightedGraphProblem(nodes=positioned_nodes, edges=graph.edges, start=graph.start, goal=graph.goal)


def _dijkstra(graph: WeightedGraphProblem) -> SearchResponse:
    nodes = _node_ids(graph)
    adjacency = _adjacency(graph)
    g = {node: INF for node in nodes}
    g[graph.start] = 0.0
    parent: dict[NodeId, NodeId | None] = {graph.start: None}
    settled: set[NodeId] = set()
    heap: list[tuple[float, NodeId]] = [(0.0, graph.start)]
    trace: list[TraceFrame] = []
    expanded = 0
    relaxation_count = 0
    max_frontier = 1

    _append_graph_frame(
        trace,
        graph,
        "initialize",
        "Initialize Dijkstra with g(start) = 0 and all other costs unknown.",
        g=g,
        settled=settled,
        frontier=_heap_nodes(heap, settled),
        queue=_queue_items(heap, settled, g),
        parent=parent,
    )

    while heap:
        cost, node = heapq.heappop(heap)
        if node in settled:
            continue
        settled.add(node)
        expanded += 1

        _append_graph_frame(
            trace,
            graph,
            "settle",
            f"Settle {node}; its shortest cost-to-come is now fixed at {cost:g}.",
            current=node,
            g=g,
            settled=settled,
            frontier=_heap_nodes(heap, settled),
            queue=_queue_items(heap, settled, g),
            parent=parent,
        )

        if node == graph.goal:
            break

        for edge in adjacency[node]:
            if edge.target in settled:
                continue
            previous = g[edge.target]
            candidate = g[node] + edge.cost
            improved = candidate < previous
            if improved:
                g[edge.target] = candidate
                parent[edge.target] = node
                heapq.heappush(heap, (candidate, edge.target))
                relaxation_count += 1
            max_frontier = max(max_frontier, len(_heap_nodes(heap, settled)))
            _append_graph_frame(
                trace,
                graph,
                "relax",
                _relax_message(node, edge.target, edge.cost, previous, candidate, improved),
                current=node,
                g=g,
                settled=settled,
                frontier=_heap_nodes(heap, settled),
                updated=[edge.target] if improved else [],
                active_edge=edge,
                relaxation=RelaxationEvent(
                    source=edge.source,
                    target=edge.target,
                    cost=edge.cost,
                    previous=_finite(previous),
                    updated=_finite(candidate),
                    improved=improved,
                ),
                queue=_queue_items(heap, settled, g),
                parent=parent,
            )

    path = _path_from_parent(parent, graph.start, graph.goal)
    return _graph_response(graph, SearchAlgorithm.DIJKSTRA, path, g.get(graph.goal, INF), trace, expanded, len(settled), max_frontier, relaxation_count)


def _astar(graph: WeightedGraphProblem) -> SearchResponse:
    nodes = _node_ids(graph)
    adjacency = _adjacency(graph)
    h = {node.id: node.heuristic for node in graph.nodes}
    g = {node: INF for node in nodes}
    g[graph.start] = 0.0
    parent: dict[NodeId, NodeId | None] = {graph.start: None}
    settled: set[NodeId] = set()
    heap: list[tuple[float, float, NodeId]] = [(h[graph.start], 0.0, graph.start)]
    trace: list[TraceFrame] = []
    expanded = 0
    relaxation_count = 0
    max_frontier = 1

    _append_graph_frame(
        trace,
        graph,
        "initialize",
        "Initialize A* with f(start) = g(start) + h(start).",
        g=g,
        h=h,
        settled=settled,
        frontier=_astar_heap_nodes(heap, settled),
        queue=_astar_queue_items(heap, settled, g, h),
        parent=parent,
    )

    while heap:
        _, cost, node = heapq.heappop(heap)
        if node in settled:
            continue
        settled.add(node)
        expanded += 1

        _append_graph_frame(
            trace,
            graph,
            "settle",
            f"Expand {node}; it has the smallest f = g + h among open nodes.",
            current=node,
            g=g,
            h=h,
            settled=settled,
            frontier=_astar_heap_nodes(heap, settled),
            queue=_astar_queue_items(heap, settled, g, h),
            parent=parent,
        )

        if node == graph.goal:
            break

        for edge in adjacency[node]:
            if edge.target in settled:
                continue
            previous = g[edge.target]
            candidate = cost + edge.cost
            improved = candidate < previous
            if improved:
                g[edge.target] = candidate
                parent[edge.target] = node
                heapq.heappush(heap, (candidate + h[edge.target], candidate, edge.target))
                relaxation_count += 1
            max_frontier = max(max_frontier, len(_astar_heap_nodes(heap, settled)))
            _append_graph_frame(
                trace,
                graph,
                "relax",
                _relax_message(node, edge.target, edge.cost, previous, candidate, improved, label="g"),
                current=node,
                g=g,
                h=h,
                settled=settled,
                frontier=_astar_heap_nodes(heap, settled),
                updated=[edge.target] if improved else [],
                active_edge=edge,
                relaxation=RelaxationEvent(
                    source=edge.source,
                    target=edge.target,
                    cost=edge.cost,
                    previous=_finite(previous),
                    updated=_finite(candidate),
                    improved=improved,
                ),
                queue=_astar_queue_items(heap, settled, g, h),
                parent=parent,
            )

    path = _path_from_parent(parent, graph.start, graph.goal)
    return _graph_response(graph, SearchAlgorithm.ASTAR, path, g.get(graph.goal, INF), trace, expanded, len(settled), max_frontier, relaxation_count)


def _forward_value_iteration(graph: WeightedGraphProblem) -> SearchResponse:
    nodes = _node_ids(graph)
    reverse = _reverse_adjacency(graph)
    g = {node: INF for node in nodes}
    g[graph.start] = 0.0
    parent: dict[NodeId, NodeId | None] = {node: None for node in nodes}
    trace: list[TraceFrame] = []
    relaxation_count = 0
    sweeps = 0

    _append_graph_frame(
        trace,
        graph,
        "initialize",
        "Anchor the forward value iteration with g(start) = 0.",
        g=g,
        parent=parent,
    )

    while sweeps <= len(nodes):
        sweeps += 1
        changed = False
        for target in nodes:
            if target == graph.start:
                continue
            for source, cost in reverse[target]:
                if g[source] == INF:
                    continue
                previous = g[target]
                candidate = g[source] + cost
                improved = candidate < previous
                if improved:
                    g[target] = candidate
                    parent[target] = source
                    changed = True
                    relaxation_count += 1
                _append_graph_frame(
                    trace,
                    graph,
                    "sweep",
                    _relax_message(source, target, cost, previous, candidate, improved, label="g"),
                    current=target,
                    g=g,
                    updated=[target] if improved else [],
                    active_edge=WeightedGraphEdge(source=source, target=target, cost=cost),
                    relaxation=RelaxationEvent(source=source, target=target, cost=cost, previous=_finite(previous), updated=_finite(candidate), improved=improved),
                    parent=parent,
                )
        if not changed:
            break

    path = _path_from_parent(parent, graph.start, graph.goal)
    return _graph_response(graph, SearchAlgorithm.FORWARD_VALUE_ITERATION, path, g.get(graph.goal, INF), trace, sweeps, len([v for v in g.values() if v < INF]), 0, relaxation_count, sweeps)


def _backward_value_iteration(graph: WeightedGraphProblem) -> SearchResponse:
    nodes = _node_ids(graph)
    adjacency = _adjacency(graph)
    value = {node: INF for node in nodes}
    value[graph.goal] = 0.0
    policy: dict[NodeId, NodeId | None] = {node: None for node in nodes}
    trace: list[TraceFrame] = []
    relaxation_count = 0
    sweeps = 0

    _append_graph_frame(
        trace,
        graph,
        "initialize",
        "Anchor the backward value iteration with V(goal) = 0.",
        value=value,
        policy=policy,
    )

    while sweeps <= len(nodes):
        sweeps += 1
        changed = False
        for source in nodes:
            if source == graph.goal:
                continue
            for edge in adjacency[source]:
                if value[edge.target] == INF:
                    continue
                previous = value[source]
                candidate = edge.cost + value[edge.target]
                improved = candidate < previous
                if improved:
                    value[source] = candidate
                    policy[source] = edge.target
                    changed = True
                    relaxation_count += 1
                _append_graph_frame(
                    trace,
                    graph,
                    "sweep",
                    _relax_message(source, edge.target, edge.cost, previous, candidate, improved, label="V"),
                    current=source,
                    value=value,
                    updated=[source] if improved else [],
                    active_edge=edge,
                    relaxation=RelaxationEvent(source=edge.source, target=edge.target, cost=edge.cost, previous=_finite(previous), updated=_finite(candidate), improved=improved),
                    policy=policy,
                )
        if not changed:
            break

    path = _path_from_policy(policy, graph.start, graph.goal)
    return _graph_response(graph, SearchAlgorithm.BACKWARD_VALUE_ITERATION, path, value.get(graph.start, INF), trace, sweeps, len([v for v in value.values() if v < INF]), 0, relaxation_count, sweeps, policy=policy, value=value)


def _append_graph_frame(
    trace: list[TraceFrame],
    graph: WeightedGraphProblem,
    phase: str,
    message: str,
    *,
    current: NodeId | None = None,
    g: dict[NodeId, float] | None = None,
    h: dict[NodeId, float] | None = None,
    value: dict[NodeId, float] | None = None,
    settled: Iterable[NodeId] = (),
    frontier: Iterable[NodeId] = (),
    updated: Iterable[NodeId] = (),
    active_edge: WeightedGraphEdge | None = None,
    relaxation: RelaxationEvent | None = None,
    queue: list[QueueItem] | None = None,
    parent: dict[NodeId, NodeId | None] | None = None,
    policy: dict[NodeId, NodeId | None] | None = None,
) -> None:
    parent_edges = _parent_edges(parent or {}, graph)
    policy_edges = _policy_edges(policy or {}, graph)
    trace.append(
        TraceFrame(
            index=len(trace),
            phase=phase,
            message=message,
            current_node=current,
            frontier_nodes=sorted(set(frontier)),
            visited_nodes=sorted(set(settled)),
            settled_nodes=sorted(set(settled)),
            updated_nodes=sorted(set(updated)),
            node_labels=_node_labels(graph, g=g, h=h, value=value),
            active_edge=_trace_edge(active_edge) if active_edge else None,
            parent_edges=parent_edges,
            policy_edges=policy_edges,
            relaxation=relaxation,
            priority_queue=queue or [],
        )
    )


def _graph_response(
    graph: WeightedGraphProblem,
    algorithm: SearchAlgorithm,
    path: list[NodeId],
    total_cost: float,
    trace: list[TraceFrame],
    expanded_count: int,
    visited_count: int,
    max_frontier: int,
    relaxation_count: int,
    sweep_count: int = 0,
    *,
    policy: dict[NodeId, NodeId | None] | None = None,
    value: dict[NodeId, float] | None = None,
) -> SearchResponse:
    found = bool(path) and total_cost < INF
    if found and trace:
        if policy:
            trace[-1].policy_edges = _policy_edges(policy, graph)
        if value:
            trace[-1].node_labels = _node_labels(graph, value=value)
        trace[-1].phase = "complete"
        trace[-1].message = f"Optimal path {' -> '.join(path)} has total cost {total_cost:g}."

    return SearchResponse(
        algorithm=algorithm,
        status=SearchStatus.FOUND if found else SearchStatus.NOT_FOUND,
        start=State(row=0, col=0),
        goal=State(row=0, col=0),
        rows=0,
        cols=0,
        plan=[],
        graph=graph,
        graph_path=path if found else [],
        trace=trace,
        stats=SearchStats(
            expanded_count=expanded_count,
            visited_count=visited_count,
            max_frontier_size=max_frontier,
            path_length=max(len(path) - 1, 0) if found else None,
            trace_length=len(trace),
            total_cost=_finite(total_cost),
            relaxation_count=relaxation_count,
            sweep_count=sweep_count,
        ),
    )


def _node_ids(graph: WeightedGraphProblem) -> list[NodeId]:
    return [node.id for node in graph.nodes]


def _adjacency(graph: WeightedGraphProblem) -> dict[NodeId, list[WeightedGraphEdge]]:
    adjacency = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.source].append(edge)
    for edges in adjacency.values():
        edges.sort(key=lambda edge: (edge.cost, edge.target))
    return adjacency


def _reverse_adjacency(graph: WeightedGraphProblem) -> dict[NodeId, list[tuple[NodeId, float]]]:
    reverse = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        reverse[edge.target].append((edge.source, edge.cost))
    for predecessors in reverse.values():
        predecessors.sort(key=lambda item: (item[1], item[0]))
    return reverse


def _with_positions(nodes: list[GraphNode]) -> list[GraphNode]:
    if all(node.x is not None and node.y is not None for node in nodes):
        return nodes

    count = len(nodes)
    radius = 170
    center = 220
    positioned = []
    for index, node in enumerate(nodes):
        if node.x is not None and node.y is not None:
            positioned.append(node)
            continue
        angle = -math.pi / 2 + (2 * math.pi * index / max(count, 1))
        positioned.append(
            GraphNode(
                id=node.id,
                label=node.label,
                x=center + radius * math.cos(angle),
                y=center + radius * math.sin(angle),
                heuristic=node.heuristic,
            )
        )
    return positioned


def _node_labels(
    graph: WeightedGraphProblem,
    *,
    g: dict[NodeId, float] | None = None,
    h: dict[NodeId, float] | None = None,
    value: dict[NodeId, float] | None = None,
) -> list[GraphNodeLabel]:
    labels = []
    for node in graph.nodes:
        gv = g.get(node.id, INF) if g else None
        hv = h.get(node.id, node.heuristic) if h else None
        vv = value.get(node.id, INF) if value else None
        labels.append(
            GraphNodeLabel(
                node_id=node.id,
                g=_finite(gv) if gv is not None else None,
                h=_finite(hv) if hv is not None else None,
                f=_finite(gv + hv) if gv is not None and hv is not None and gv < INF else None,
                value=_finite(vv) if vv is not None else None,
            )
        )
    return labels


def _trace_edge(edge: WeightedGraphEdge) -> GraphTraceEdge:
    return GraphTraceEdge(source=edge.source, target=edge.target, cost=edge.cost)


def _parent_edges(parent: dict[NodeId, NodeId | None], graph: WeightedGraphProblem) -> list[GraphTraceEdge]:
    cost_by_edge = {(edge.source, edge.target): edge.cost for edge in graph.edges}
    edges = []
    for target, source in parent.items():
        if source is not None:
            edges.append(GraphTraceEdge(source=source, target=target, cost=cost_by_edge[(source, target)]))
    return edges


def _policy_edges(policy: dict[NodeId, NodeId | None], graph: WeightedGraphProblem) -> list[GraphTraceEdge]:
    cost_by_edge = {(edge.source, edge.target): edge.cost for edge in graph.edges}
    edges = []
    for source, target in policy.items():
        if target is not None:
            edges.append(GraphTraceEdge(source=source, target=target, cost=cost_by_edge[(source, target)]))
    return edges


def _path_from_parent(parent: dict[NodeId, NodeId | None], start: NodeId, goal: NodeId) -> list[NodeId]:
    if goal not in parent:
        return []
    path = []
    node: NodeId | None = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    path.reverse()
    return path if path and path[0] == start else []


def _path_from_policy(policy: dict[NodeId, NodeId | None], start: NodeId, goal: NodeId) -> list[NodeId]:
    path = [start]
    seen = {start}
    node = start
    while node != goal:
        next_node = policy.get(node)
        if next_node is None or next_node in seen:
            return []
        path.append(next_node)
        seen.add(next_node)
        node = next_node
    return path


def _heap_nodes(heap: list[tuple[float, NodeId]], settled: set[NodeId]) -> list[NodeId]:
    return sorted({node for _, node in heap if node not in settled})


def _astar_heap_nodes(heap: list[tuple[float, float, NodeId]], settled: set[NodeId]) -> list[NodeId]:
    return sorted({node for _, _, node in heap if node not in settled})


def _queue_items(heap: list[tuple[float, NodeId]], settled: set[NodeId], g: dict[NodeId, float]) -> list[QueueItem]:
    best: dict[NodeId, float] = {}
    for priority, node in heap:
        if node in settled:
            continue
        best[node] = min(priority, best.get(node, INF))
    return [QueueItem(node_id=node, priority=priority, g=_finite(g[node])) for node, priority in sorted(best.items(), key=lambda item: (item[1], item[0]))]


def _astar_queue_items(heap: list[tuple[float, float, NodeId]], settled: set[NodeId], g: dict[NodeId, float], h: dict[NodeId, float]) -> list[QueueItem]:
    best: dict[NodeId, tuple[float, float]] = {}
    for priority, cost, node in heap:
        if node in settled:
            continue
        if node not in best or priority < best[node][0]:
            best[node] = (priority, cost)
    return [
        QueueItem(node_id=node, priority=priority, g=_finite(g[node]), h=_finite(h[node]))
        for node, (priority, _) in sorted(best.items(), key=lambda item: (item[1][0], item[0]))
    ]


def _relax_message(source: NodeId, target: NodeId, cost: float, previous: float, candidate: float, improved: bool, label: str = "cost") -> str:
    old = "unknown" if previous == INF else f"{previous:g}"
    if improved:
        return f"Relax {source} -> {target}: {label} improves from {old} to {candidate:g} using edge cost {cost:g}."
    return f"Check {source} -> {target}: candidate {candidate:g} does not improve current {label} {old}."


def _finite(value: float | None) -> float | None:
    if value is None or math.isinf(value):
        return None
    return value

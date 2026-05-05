import heapq
import heapq
from copy import deepcopy
from typing import TypeAlias, Callable
 
 
Node: TypeAlias = str
Cost: TypeAlias = float
Edge: TypeAlias = tuple[Node, Cost]          # (neighbor, cost)
Graph: TypeAlias = dict[Node, list[Edge]]    # adjacency list (forward edges)
CostMap: TypeAlias = dict[Node, Cost]        # V*(x) or g*(x) for every node
Parent: TypeAlias = dict[Node, Node | None]  # for path reconstruction
Heuristic: TypeAlias = Callable[[Node], Cost]


INF: Cost = float("inf")


def astar(
    graph: Graph, start: Node, goal: Node, h: Heuristic = lambda _: 0.0, 
) -> tuple[CostMap, Parent, int]: 
    """
    Find the optimal path from start to goal with A*

    A* maintains: 
        g(x) - exact cost-to-come - cost paying from start to x 
        h(x) - estimated cost-to-go: remaining cost from x to the goal (heuristics)
        f(x) = g(x) + h(x) - estimated total path cost through x 


    The priority queue is ordered by f(x). The node with the smallest total cost is always 
    expanded first, biasing the search toward the goal. This is the key difference compared to 
    Dijkstra's, which orders by g(x) alone and expands uniformly in all directions.

    Admissibility requirement:
        h(x) <= V*(x) for all x (never overestimate the true cost-to-go)

    If h is admissible, A* is guaranteed to find the optimal path
    If h = 0 everywhere, A* degenerates exactly into Dijkstra's algorithm.
    if h = V* exactly, A* expands only nodes on the optimal path - zero waste.


    Retturns:
        g: optimal cost-to-come for nodes that were visited
        parent: predecessor map for path reconstruction
        expanded: number of nodes expanded ( popped from the priority queue)
    """
    g: CostMap = dict.fromkeys(graph, INF)
    g[start] = 0.0 
    parent: Parent = {start: None}

    # (f, p, node) - store g as tiebreaker to keep comparison stable
    pq: list[tuple[Cost, Cost, Node]] = [(h(start), 0.0, start)]
    visited: set[Node] = set() 
    expanded = 0

    while pq: 
        f, cost, x = heapq.heappop(pq)

        if x in visited: 
            continue
        visited.add(x) 
        expanded += 1 

        if x == goal: 
            break # optimal path found - stop early

        for neighbor, edge_cost in graph[x]: 
            new_g = g[x] + edge_cost
            if new_g < g[neighbor]:
                g[neighbor] = new_g 
                parent[neighbor] = x 
                f_val = new_g + h(neighbor)
                heapq.heappush(pq, (f_val, new_g, neighbor))
    
    return g, parent, expanded



def reconstruct_path(parent: Parent, goal: Node) -> list[Node]:
    """Trace parent pointers from goal back to start, then reverse."""
    path: list[Node] = []
    node: Node | None = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    return list(reversed(path))


graph: Graph = {
    "S": [("A", 4.0), ("B", 2.0)],
    "A": [("C", 3.0), ("G", 10.0)],
    "B": [("A", 1.0), ("C", 8.0)],
    "C": [("G", 2.0)],
    "G": []
}

# admissible heuristic : rough underestimates true cost-to-go V*(x)
known_h: dict[Node, Cost] = {"S": 7.0, "A": 5.0, "B": 6.0, "C": 2.0, "G": 0.0}
h: Heuristic = lambda x: known_h.get(x, 0.0) 

START, GOAL = "S", "G"
print("Graph edges")
for node, edges in graph.items(): 
    for nb, cost, in edges: 
        print(f"{node} --{cost:.0f}--> {nb}")
    
g, parent, expanded = astar(graph, START, GOAL, h) 
apath = reconstruct_path(parent, GOAL)

for node in graph: 
    gv = g.get(node, INF)
    hv = known_h.get(node, 0.0)
    fv = gv + hv if gv != INF else INF 
    print(f"{node}: g={gv:.1f}  h={hv:.1f}  f={fv:.1f}")

print(f"Optimal path  : {'->'.join(apath)}")
print(f"Total cost    : {g[GOAL]:.1f}")










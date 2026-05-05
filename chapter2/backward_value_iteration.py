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



# helpers 
def build_reverse_graph(graph: Graph) -> Graph: 
    """
    Flip all the edges to get the predecessor graph.

    Forward edge x --cost--> x' 
    Backward edge x' --cost--> x 

    Used by forward value iteration, which sweeps forward but needs to know which predecessors 
    can reach each state. 
    """ 
    rev: Graph = {node: [] for node in graph}
    for x, edges in graph.items(): 
        for neighbor, cost in edges: 
            rev[neighbor].append((x, cost)) 
    return rev 

def reconstruct_path(parent: Parent, goal: Node) -> list[Node]:
    """Trace parent pointers from goal back to start, then reverse."""
    path: list[Node] = []
    node: Node | None = goal
    while node is not None:
        path.append(node)
        node = parent.get(node)
    return list(reversed(path))


def backward_value_iteration(
    graph: Graph, goal: Node, tol: float = 1e-9 
) -> tuple[CostMap, Parent, int]: 
    """
    Compute V*(x) = optimal cost-to-go from every state x to the goal. 

    Bellman equation (backward): 
        V(x) = min over all outgoing edges (x, x') of (l(x, x') + V(x'))
    
    The anchor is V(goal) = 0. The dependency chain runs: 
        goal(known) -> neighbors of goal -> the neighbors of the neighbors 
        and so on -> start
    
    Each sweep applies Bellman update to every state. Value only ever decrease (costs improve)
    The algorithm terminates when no value changed by more than tol in a full sweep --
    convergence is guaranteed for finite graph with non-negative costs. 

    Returns: 
        V: optimal cost-to-go from every state to goal 
        parent: predecessor map for path reconstruction 
        sweeps: number of sweeps until convergence
    """

    V: CostMap = dict.fromkeys(graph, INF)
    V[goal] = 0.0 

    parent: Parent = dict.fromkeys(graph, None)
    sweeps = 0

    while True: 
        sweeps += 1 
        changed = False 

        for x, edges in graph.items(): 
            if x == goal: 
                continue  # anchor, we don't have to update the goal

            for neighbor, cost in edges: 
                if V[neighbor] == INF: 
                    continue # neighbor not yet reached - skip

                candidate = cost + V[neighbor]

                if candidate < V[x] - tol: 
                    V[x] = candidate
                    parent[x] = neighbor
                    changed = True
        if not changed: 
            break
    return V, parent, sweeps
    


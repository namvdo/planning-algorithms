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

def forward_value_iteration(
    graph: Graph, start: Node, tol: float = 1e-9
) -> tuple[CostMap, Parent, int]: 
    """
    Compute g*(x) = optimal cost-to-come from x_start to every state x 

    Bellman equation (forward): 
        g(x') = min over all incoming edges (x, x') of [g(x) + l(x, x')] 

    The anchor is g(x_start) = 0. The dependency chain runs: 
        start (known) -> neighbor of start -> their neighbor -> ... -> goal 
    
    We build the reverse graph so we can iterate over predecessor of each node 

    Returns: 
        g: optimal cost-to-come for every node
        parent: predecessor map for path reconstruction
        sweeps: number of sweeps until convergence
    """


    rev = build_reverse_graph(graph)
    g: CostMap = dict.fromkeys(graph, INF) 
    g[start] = 0.0 
    parent: Parent = dict.fromkeys(graph)

    sweeps = 0 
    while True: 
        sweeps += 1
        changed = False 

        for x_prime, predecessors in rev.items(): 
            if x_prime == start: 
                continue # dont update the anchor
            
            for x, cost in predecessors: 
                if g[x] == INF: 
                    continue 

                candidate = g[x] + cost 
                if candidate < g[x_prime] - tol:
                    g[x_prime] = candidate
                    parent[x_prime] = x 
                    changed = True 
        if not changed: 
            break # fixed point reached - g*(x) is optimal everywhere
    
    return g, parent, sweeps






import heapq 

from collections import deque
from typing import TypeAlias


Node: TypeAlias = str 
Cost: TypeAlias = float  
Edge: TypeAlias = tuple[Node, Cost]
Graph: TypeAlias = dict[Node, list[Edge]]
GValues: TypeAlias = dict[Node, Cost]
Parent: TypeAlias = dict[Node, Node | None]


SAMPLE_GRAPH = {
    'S': [('A', 4), ('B', 2)],
    'A': [('C', 3), ('G', 10)],
    'B': [('A', 1), ('C', 8)],
    'C': [('G', 2)],
    'G': [],
}

def label_correcting(graph: Graph, start: Node) -> tuple[GValues, Parent]:
    g: GValues = {node: float("inf") for node in graph}
    g[start] = 0 
    parent: Parent = {start: None}
    in_queue: set[Node] = set([start])

    queue: deque[Node] = deque([start])
    while queue: 
        x = queue.popleft() 
        in_queue.discard(x) 

        for neighbor, edge_cost in graph[x]:
            new_cost = g[x] + edge_cost
            if new_cost < g[neighbor]:
                g[neighbor] = new_cost 
                parent[neighbor] = x 
                if neighbor not in in_queue:
                    queue.append(neighbor)
                    in_queue.add(neighbor)
    
    return g, parent



def reconstruct_path(parent: Parent, goal: Node) -> list[Node]: 
    path: list[Node] = [] 
    node: Node | None = goal 
    while node is not None: 
        path.append(node) 
        node = parent.get(node) 
    
    return list(reversed(path))
    

print("Label correcting: ")
g, parent = label_correcting(SAMPLE_GRAPH, "S")
path = reconstruct_path(parent, "G")
print(f"costs : {dict(g.items())}")
print(f"path  : {' → '.join(path)}")
print(f"total : {g['G']}\n")

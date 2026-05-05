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


# Chapter 2: Discrete Planning Notes

Chapter 2 of LaValle's _Planning Algorithms_ introduces planning in discrete state spaces. This is the right starting point because the state space can be represented as a graph, and the main question is clear: how can an algorithm find a sequence of actions from an initial state to a goal state?

## Core Model

A discrete planning problem has:

- a state space `S`
- an initial state `x_init`
- a goal state or goal test
- an action set
- a transition function that maps a state and action to a next state

For the first version of this project, a grid world is used as the state space. Each free cell is a state. The actions are `up`, `down`, `left`, and `right`. Walls remove states from the graph.

This is simple, but it is still useful. It makes the search frontier, visited set, parent pointers, and final plan visible.

## Forward Search

Forward search starts at the initial state and expands reachable states. With a FIFO queue, it becomes breadth-first search. On an unweighted graph, breadth-first search returns a shortest path in number of actions.

Important learning points:

- the frontier contains states discovered but not expanded
- the visited set prevents repeated work
- parent pointers reconstruct the final plan
- the worst case can grow quickly when the branching factor is high

## Backward Search

Backward search starts from the goal and expands predecessor states. It is useful when reverse actions are easy to compute and when the goal side of the problem is smaller than the initial side.

The returned plan must still be executable forward from the initial state. This is why the backend stores the forward action while expanding backward.

## Bidirectional Search

Bidirectional search grows two frontiers: one from the initial state and one from the goal. When the frontiers meet, the algorithm joins the two partial plans.

The usual intuition is that two searches of depth `d / 2` may be much smaller than one search of depth `d`. This advantage depends on the problem. Bidirectional search needs a useful way to expand backward and a cheap way to detect when the frontiers meet.

## Metrics To Show

The first MVP reports:

- expanded states
- visited states
- maximum frontier size
- path length
- trace length

These metrics are good for learning because they connect the visual behavior to computational cost. Later versions can add runtime, memory estimates, weighted costs, and comparisons across algorithms.

## References

- Steven M. LaValle, _Planning Algorithms_, Chapter 2: Discrete Planning, Cambridge University Press, 2006.
- Official book page: https://lavalle.pl/planning/web.html
- Chapter 2 PDF: https://lavalle.pl/planning/ch2.pdf
- Cambridge University Press chapter page: https://www.cambridge.org/core/books/planning-algorithms/discrete-planning/D5B4A1A618C89DDB2E0D5C55A6060F30

## Live Coding Notes

The live editor uses Python3 because it matches the early Chapter 2 notes and is easy to read while studying algorithms. The default code is correct and executable. A learner can change it, run the visualization with that exact code, and run the judge to see whether the submitted code still returns valid plans.

The judge checks action sequences, not only whether a function returns something. This matters because a planning algorithm is correct only if its returned plan can actually be executed from the initial state to the goal.

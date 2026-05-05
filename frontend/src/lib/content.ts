import type { ProblemKind, SearchAlgorithm } from "./types";

export interface AlgorithmContent {
  id: SearchAlgorithm;
  title: string;
  shortName: string;
  problemKind: ProblemKind;
  liveCode: boolean;
  summary: string;
  complexity: string;
  citation: string;
  pseudocodeLatex: string;
}

export const algorithms: AlgorithmContent[] = [
  {
    id: "forward",
    title: "Forward Search",
    shortName: "Forward",
    problemKind: "grid",
    liveCode: true,
    summary:
      "Forward search grows a reachable set from the initial state until it reaches the goal. With a FIFO frontier, this is breadth-first search on an unweighted graph.",
    complexity: "Time O(|S| + |E|), space O(|S|). In a tree with branching factor b and solution depth d, the common bound is O(b^d).",
    citation: "LaValle, Planning Algorithms, Chapter 2, Section 2.2.",
    pseudocodeLatex: String.raw`\begin{array}{l}
\textbf{ForwardSearch}(x_I)\\
Q \leftarrow [x_I],\quad V \leftarrow \{x_I\}\\
\textbf{while } Q \ne \emptyset \textbf{ do}\\
\quad x \leftarrow \operatorname{pop\_front}(Q)\\
\quad \textbf{if } x \in X_G \textbf{ then return } \operatorname{Plan}(x)\\
\quad \textbf{for each } u \in U(x) \textbf{ do}\\
\quad\quad x' \leftarrow f(x,u)\\
\quad\quad \textbf{if } x' \notin V \textbf{ then}\\
\quad\quad\quad V \leftarrow V \cup \{x'\}\\
\quad\quad\quad \operatorname{parent}(x') \leftarrow (x,u)\\
\quad\quad\quad \operatorname{push\_back}(Q,x')\\
\textbf{return } \varnothing
\end{array}`,
  },
  {
    id: "backward",
    title: "Backward Search",
    shortName: "Backward",
    problemKind: "grid",
    liveCode: true,
    summary:
      "Backward search grows from the goal through predecessor states. It is useful when the goal is compact and inverse actions are easier than exploring many forward branches.",
    complexity: "Time O(|S| + |E|), space O(|S|). It can be much smaller than forward search when the reverse branching factor is lower.",
    citation: "LaValle, Planning Algorithms, Chapter 2, Section 2.2.",
    pseudocodeLatex: String.raw`\begin{array}{l}
\textbf{BackwardSearch}(x_G)\\
Q \leftarrow [x_G],\quad V \leftarrow \{x_G\}\\
\textbf{while } Q \ne \emptyset \textbf{ do}\\
\quad x \leftarrow \operatorname{pop\_front}(Q)\\
\quad \textbf{if } x = x_I \textbf{ then return } \operatorname{ForwardPlan}(x_I)\\
\quad \textbf{for each predecessor action } u \textbf{ do}\\
\quad\quad x^- \leftarrow f^{-1}(x,u)\\
\quad\quad \textbf{if } x^- \notin V \textbf{ then}\\
\quad\quad\quad V \leftarrow V \cup \{x^-\}\\
\quad\quad\quad \operatorname{parent}(x^-) \leftarrow (x,u)\\
\quad\quad\quad \operatorname{push\_back}(Q,x^-)\\
\textbf{return } \varnothing
\end{array}`,
  },
  {
    id: "bidirectional",
    title: "Bidirectional Search",
    shortName: "Bidirectional",
    problemKind: "grid",
    liveCode: true,
    summary:
      "Bidirectional search grows one frontier from the start and one from the goal. The plan is found when the two explored regions meet.",
    complexity:
      "For balanced trees this is often described as O(b^(d/2)) space and time per side, instead of O(b^d), but it requires useful reverse expansion.",
    citation: "LaValle, Planning Algorithms, Chapter 2, Section 2.2.",
    pseudocodeLatex: String.raw`\begin{array}{l}
\textbf{BidirectionalSearch}(x_I,x_G)\\
Q_F \leftarrow [x_I],\quad Q_B \leftarrow [x_G]\\
V_F \leftarrow \{x_I\},\quad V_B \leftarrow \{x_G\}\\
\textbf{while } Q_F \ne \emptyset \textbf{ or } Q_B \ne \emptyset \textbf{ do}\\
\quad \operatorname{ExpandForward}(Q_F,V_F)\\
\quad \textbf{if } V_F \cap V_B \ne \emptyset \textbf{ then return } \operatorname{JoinPlans}\\
\quad \operatorname{ExpandBackward}(Q_B,V_B)\\
\quad \textbf{if } V_F \cap V_B \ne \emptyset \textbf{ then return } \operatorname{JoinPlans}\\
\textbf{return } \varnothing
\end{array}`,
  },
  {
    id: "dijkstra",
    title: "Dijkstra's Algorithm",
    shortName: "Dijkstra",
    problemKind: "weighted_graph",
    liveCode: false,
    summary:
      "Dijkstra's algorithm computes optimal cost-to-come values on a graph with positive edge costs. The priority queue is ordered by the current best g value.",
    complexity: "Time O((|S| + |E|) log |S|) with a binary heap, space O(|S| + |E|).",
    citation: "LaValle, Planning Algorithms, Chapter 2, weighted discrete planning.",
    pseudocodeLatex: String.raw`\begin{array}{l}
\textbf{Dijkstra}(x_I)\\
g(x_I) \leftarrow 0,\quad g(x) \leftarrow \infty \text{ otherwise}\\
Q \leftarrow \{x_I\}\\
\textbf{while } Q \ne \emptyset \textbf{ do}\\
\quad x \leftarrow \operatorname{pop\_min}_g(Q)\\
\quad \textbf{for each } (x,x') \in E \textbf{ do}\\
\quad\quad \textbf{if } g(x)+l(x,x') < g(x') \textbf{ then}\\
\quad\quad\quad g(x') \leftarrow g(x)+l(x,x')\\
\quad\quad\quad parent(x') \leftarrow x\\
\quad\quad\quad \operatorname{push}(Q,x')
\end{array}`,
  },
  {
    id: "astar",
    title: "A* Search",
    shortName: "A*",
    problemKind: "weighted_graph",
    liveCode: false,
    summary:
      "A* orders the open set by f(x) = g(x) + h(x). A good admissible heuristic guides the search toward the goal while preserving optimality.",
    complexity: "Worst-case exponential in solution depth, but often expands far fewer states than Dijkstra when h is informative.",
    citation: "LaValle, Planning Algorithms, Chapter 2, cost-to-go and heuristic search.",
    pseudocodeLatex: String.raw`\begin{array}{l}
\textbf{A*}(x_I,x_G,h)\\
g(x_I) \leftarrow 0,\quad Q \leftarrow \{x_I\}\\
\textbf{while } Q \ne \emptyset \textbf{ do}\\
\quad x \leftarrow \operatorname{pop\_min}_{g+h}(Q)\\
\quad \textbf{if } x = x_G \textbf{ then return } \operatorname{Plan}(x)\\
\quad \textbf{for each } (x,x') \in E \textbf{ do}\\
\quad\quad c \leftarrow g(x)+l(x,x')\\
\quad\quad \textbf{if } c < g(x') \textbf{ then}\\
\quad\quad\quad g(x') \leftarrow c,\quad parent(x') \leftarrow x
\end{array}`,
  },
  {
    id: "forward_value_iteration",
    title: "Forward Value Iteration",
    shortName: "Forward VI",
    problemKind: "weighted_graph",
    liveCode: false,
    summary:
      "Forward value iteration repeatedly applies Bellman updates to compute optimal cost-to-come values g*(x) from the start.",
    complexity: "For this finite positive-cost graph demo, each sweep scans edges; convergence takes at most about |S| sweeps on simple shortest-path instances.",
    citation: "LaValle, Planning Algorithms, Chapter 2, dynamic programming over discrete states.",
    pseudocodeLatex: String.raw`\begin{array}{l}
\textbf{ForwardVI}(x_I)\\
g(x_I) \leftarrow 0,\quad g(x) \leftarrow \infty\\
\textbf{repeat}\\
\quad changed \leftarrow false\\
\quad \textbf{for each } x' \in S \textbf{ do}\\
\quad\quad g(x') \leftarrow \min_{(x,x') \in E}\ g(x)+l(x,x')\\
\quad\quad \text{record parent if value improves}\\
\textbf{until not } changed
\end{array}`,
  },
  {
    id: "backward_value_iteration",
    title: "Backward Value Iteration",
    shortName: "Backward VI",
    problemKind: "weighted_graph",
    liveCode: false,
    summary:
      "Backward value iteration computes cost-to-go values V*(x) by anchoring the goal at zero and choosing the best outgoing successor for each state.",
    complexity: "Each sweep scans outgoing edges; the policy arrows become stable once the Bellman fixed point is reached.",
    citation: "LaValle, Planning Algorithms, Chapter 2, value functions and optimal plans.",
    pseudocodeLatex: String.raw`\begin{array}{l}
\textbf{BackwardVI}(x_G)\\
V(x_G) \leftarrow 0,\quad V(x) \leftarrow \infty\\
\textbf{repeat}\\
\quad changed \leftarrow false\\
\quad \textbf{for each } x \in S \textbf{ do}\\
\quad\quad V(x) \leftarrow \min_{(x,x') \in E}\ l(x,x')+V(x')\\
\quad\quad \pi(x) \leftarrow \arg\min_{x'} l(x,x')+V(x')\\
\textbf{until not } changed
\end{array}`,
  },
];

export const plannedTopics = ["STRIPS", "Planning graph", "SAT planning"];

export const defaultGrid = `S.....#......
.####....#...
....#....#..G
..#..........`;

export const defaultWeightedGraph = JSON.stringify(
  {
    nodes: [
      { id: "S", x: 48, y: 170, heuristic: 7 },
      { id: "A", x: 220, y: 74, heuristic: 5 },
      { id: "B", x: 220, y: 270, heuristic: 6 },
      { id: "C", x: 390, y: 170, heuristic: 2 },
      { id: "G", x: 560, y: 170, heuristic: 0 },
    ],
    edges: [
      { source: "S", target: "A", cost: 4 },
      { source: "S", target: "B", cost: 2 },
      { source: "B", target: "A", cost: 1 },
      { source: "A", target: "C", cost: 3 },
      { source: "B", target: "C", cost: 8 },
      { source: "A", target: "G", cost: 10 },
      { source: "C", target: "G", cost: 2 },
    ],
    start: "S",
    goal: "G",
  },
  null,
  2,
);

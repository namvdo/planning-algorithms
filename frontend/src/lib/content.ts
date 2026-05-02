import type { SearchAlgorithm } from "./types";

export interface AlgorithmContent {
  id: SearchAlgorithm;
  title: string;
  shortName: string;
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
];

export const plannedTopics = ["Dijkstra", "A*", "Value iteration", "STRIPS", "Planning graph", "SAT planning"];

export const defaultGrid = `S.....#.
.####...
....#..G
..#.....`;

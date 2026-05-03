# Architecture

## Overview

The explorer is a two-part application. The frontend gives the learner an interactive workbench. The backend owns the planning algorithms and returns a trace that can be visualized one frame at a time.

## Backend

The backend is a FastAPI application in `backend/app`.

Main components:

- `grid.py`: parses and validates grid worlds, defines actions, transitions, and inverse transitions
- `models.py`: Pydantic request and response models shared by the API
- `search.py`: forward, backward, and bidirectional search implementations
- `code_judge.py`: live Python3 code execution and correctness evaluation
- `main.py`: FastAPI routes and CORS configuration

The main endpoint is:

```text
POST /api/chapter2/search/trace
```

The request includes an algorithm name and a grid. The response includes:

- status: found or not found
- plan: executable forward action sequence
- trace: ordered frames for visualization
- stats: expanded count, visited count, maximum frontier size, path length, trace length

The live-code endpoints are:

```text
GET  /api/chapter2/code/default/{algorithm}
POST /api/chapter2/code/evaluate
POST /api/chapter2/code/visualize
```

The default-code endpoint returns the editable Python3 implementation for the selected algorithm. The visualization endpoint executes the submitted code, validates the current-grid action sequence, and returns a trace for the frontend. The evaluation endpoint runs the same submitted code against the current grid plus fixed judge cases.

The current judge is appropriate for local educational use. It is not a security boundary for arbitrary public users.

## Frontend

The frontend is a Vite React TypeScript app in `frontend/src`.

Main components:

- `App.tsx`: application state and layout
- `AlgorithmSelector.tsx`: Chapter 2 algorithm selection
- `GridEditor.tsx`: editable grid input
- `GridVisualization.tsx`: SVG visualization of trace frames
- `TraceControls.tsx`: run, reset, step, and play controls
- `InspectorPanel.tsx`: explanation, complexity, stats, pseudocode, and trace messages
- `LiveCodeEditor.tsx`: Python3 editor, light/dark mode, exact-code evaluation, and judge results
- `LatexBlock.tsx`: KaTeX rendering for pseudocode

The visualization is SVG-based because the state space is a grid and the visual state is easy to inspect, test, and scale.

## Data Flow

1. The learner edits the grid, selects an algorithm, and edits the Python3 code.
2. The frontend validates simple grid shape errors.
3. The frontend posts the grid, algorithm, and exact editor code to the backend.
4. The backend executes the submitted code with a timeout and validates the returned action sequence.
5. The backend returns a trace generated from the submitted code's returned actions.
6. The frontend renders any trace frame without rerunning the algorithm.

For live coding:

1. The frontend loads the default Python3 code for the selected algorithm.
2. The learner edits the code and submits it through `Run Code`.
3. The backend runs that exact code in the judge process.
4. The judge checks whether the returned actions are valid, shortest for the unweighted cases, and correct on no-path cases.
5. The frontend shows per-case pass/fail feedback.

## Development Workflow

When adding a new algorithm, implement it first in the backend with tests. Then add the frontend content, controls, and visualization states needed to teach it.

For a new Chapter 2 algorithm, add:

- backend implementation and response trace
- backend correctness tests and trace invariant tests
- frontend algorithm metadata and pseudocode
- UI tests for selection, controls, and rendered stats
- live-code default implementation and judge cases when learners should edit it
- documentation notes in `docs/chapter-2-discrete-planning.md`

## Deployment Shape

The default production target is Vercel:

- `frontend/` is built into static files served from Vercel's CDN.
- `api/index.py` exposes the existing FastAPI app as a Vercel Python Function.
- `vercel.json` rewrites `/api/*` to the Python Function and keeps the React single-page app fallback at `/index.html`.

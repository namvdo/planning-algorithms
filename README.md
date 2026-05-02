# Planning Algorithms Explorer

An interactive web application for learning and visualizing algorithms from Steven M. LaValle's *Planning Algorithms*. The first milestone focuses on Chapter 2, discrete planning, with forward search, backward search, and bidirectional search on editable grid worlds.

The project is intentionally small and direct:

- `backend/`: Python FastAPI service and tested search algorithms
- `frontend/`: Vite, React, and TypeScript learning interface
- `docs/`: architecture notes, development workflow, and Chapter 2 learning notes
- `chapter2/`: early Python learning notes and prototypes

## Run Locally

Install backend dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Install frontend dependencies:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend at `http://127.0.0.1:5173`.

## Test

Backend:

```bash
cd backend
pytest
```

Frontend unit tests:

```bash
cd frontend
npm test
```

Frontend smoke test:

```bash
cd frontend
npx playwright test
```

## Deploy

The default deployment target is Vercel. The repository includes `vercel.json`, a Python Function entrypoint in `api/index.py`, and a root `requirements.txt` that points to the FastAPI backend dependencies.

Deploy from the repository root:

```bash
vercel
vercel --prod
```

Vercel builds `frontend/dist` and routes `/api/*` to the FastAPI app. See `docs/deployment.md` for setup notes, limitations, and the live-code execution safety warning.

## Current MVP

The current application implements a Chapter 2 workbench:

- choose forward, backward, or bidirectional search
- edit a grid with `S`, `G`, `.`, and `#`
- run the exact Python3 code currently in the live editor
- inspect the returned trace frame by frame
- compare visited sets, frontier states, current expansion, meeting state, and final plan
- read short explanations, complexity notes, LaTeX-rendered pseudocode, and source citations
- edit the selected Python3 algorithm implementation and run it through the local judge

The Python backend is the source of truth for execution and judging. The frontend edits examples, submits the current Python3 code, and renders the trace produced from that submitted code.

## Live Code Evaluation

The live editor sends the exact Python3 code in the editor to the backend. The visualization run uses that code, validates the returned action sequence, and renders the resulting path. The separate judge button evaluates the same code on the current grid plus fixed cases.

If an edit breaks the algorithm, the visualization run reports the failure and keeps the previous trace. Use `Reset code` to restore the default implementation, then run the visualization again.

This is designed for local learning, not for running untrusted public submissions. Do not expose the judge endpoint on the public internet without a stronger sandbox such as a container, seccomp profile, network isolation, and per-run filesystem limits.

## References

- Steven M. LaValle, [Planning Algorithms](https://lavalle.pl/planning/web.html)
- Steven M. LaValle, [Chapter 2: Discrete Planning](https://lavalle.pl/planning/ch2.pdf)
- Cambridge University Press, [2 - Discrete Planning](https://www.cambridge.org/core/books/planning-algorithms/discrete-planning/D5B4A1A618C89DDB2E0D5C55A6060F30)

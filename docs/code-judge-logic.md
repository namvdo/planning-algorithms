# Code Judge Overview

The `code_judge.py` module is the evaluation engine that runs and validates user-submitted Python implementations of search algorithms. It ensures that user code is executed safely, measured for performance, and verified for correctness.

## System Architecture

The judge follows a **subprocess-based execution model** to isolate user code from the main backend process.

### 1. Execution Sandbox

To prevent security risks and process interference, the judge implements a basic sandboxing strategy:

- **Temporary Isolation**: For every evaluation request, a unique `tempfile.TemporaryDirectory` is created.
- **Isolated Python Process**: User code is executed using `subprocess.run` with the `-I` (isolated) flag. This ensures the script doesn't inherit the backend's environment or external site-packages.
- **Resource Constraints**: A `TIMEOUT_SECONDS` (2.0s) limit is enforced to prevent infinite loops or CPU exhaustion.

### 2. The Runner Component

The system uses a predefined `RUNNER` script (stored as a string in `code_judge.py`) that acts as the entry point for the subprocess:

- **Dynamic Loading**: It uses `importlib` to dynamically load the specific search function (e.g., `forward_search`) from the user's uploaded file.
- **Problem Injection**: It converts the raw grid data into a high-level API (providing `get_actions`, `transition`, etc.) that matches the formal definitions in planning literature.
- **Standardized Output**: It captures all results, errors, and tracebacks, returning them to the main backend via JSON printed to `stdout`.

## Evaluation Workflow

### Step 1: Payload Preparation

The backend builds a set of test cases:

- **Current Grid**: The user's active configuration in the UI.
- **Standard Benchmarks**: Straight paths, blocked grids, and wall-turning scenarios.

### Step 2: Subprocess Execution

Files are written to the temp directory:

- `user_solution.py`: The user's algorithm code.
- `payload.json`: The test case definitions.
- `runner.py`: The executor script.

### Step 3: Judging Logic

The backend parses the runner's output and validates the plan for each case:

- **Validity**: Are the actions strings (e.g., `"up"`)?
- **Feasibility**: Does the robot stay within bounds and avoid walls (`#`)?
- **Correctness**: Does the robot end up at the Goal (`G`)?
- **Optimality**: For these unweighted grids, is the path length equal to the BFS-calculated shortest path?

## Visualization Integration

When "visualizing" a solution, the judge:

1. Runs the algorithm on the current grid.
2. Expands the returned list of actions into a sequence of `TraceFrame` objects.
3. Each frame contains the `(row, col)` state, visited set, and current plan prefix.
4. The frontend iterates through these frames to provide the step-by-step animation.

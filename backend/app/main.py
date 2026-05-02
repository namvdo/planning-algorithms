from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.code_judge import default_algorithm_code, evaluate_code, visualize_code
from app.grid import parse_grid
from app.models import CodeEvaluationRequest, CodeEvaluationResponse, CodeVisualizationRequest, SearchAlgorithm, SearchRequest, SearchResponse
from app.search import run_search

app = FastAPI(title="Planning Algorithms Explorer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chapter2/search/trace", response_model=SearchResponse)
def chapter2_search_trace(request: SearchRequest) -> SearchResponse:
    problem = parse_grid(request.grid, request.start, request.goal)
    return run_search(problem, request.algorithm)


@app.post("/api/chapter2/code/evaluate", response_model=CodeEvaluationResponse)
def chapter2_code_evaluate(request: CodeEvaluationRequest) -> CodeEvaluationResponse:
    return evaluate_code(request.algorithm, request.grid, request.code, request.start, request.goal)


@app.post("/api/chapter2/code/visualize", response_model=SearchResponse)
def chapter2_code_visualize(request: CodeVisualizationRequest) -> SearchResponse:
    return visualize_code(request.algorithm, request.grid, request.code, request.start, request.goal)


@app.get("/api/chapter2/code/default/{algorithm}")
def chapter2_default_code(algorithm: SearchAlgorithm) -> dict[str, str]:
    return {"language": "python3", "code": default_algorithm_code(algorithm)}

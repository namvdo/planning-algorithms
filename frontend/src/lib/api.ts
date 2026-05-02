import type { CodeEvaluationResponse, SearchAlgorithm, SearchResponse } from "./types";

const API_BASE = import.meta.env.VITE_API_URL ?? "";

export async function fetchSearchTrace(algorithm: SearchAlgorithm, gridText: string): Promise<SearchResponse> {
  const grid = gridText.split("\n").filter((row) => row.length > 0);
  const response = await fetch(`${API_BASE}/api/chapter2/search/trace`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ algorithm, grid }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    const message = detail?.detail ?? `Request failed with status ${response.status}`;
    throw new Error(Array.isArray(message) ? message.map((item) => item.msg).join("; ") : message);
  }

  return response.json();
}

export async function fetchDefaultCode(algorithm: SearchAlgorithm): Promise<string> {
  const response = await fetch(`${API_BASE}/api/chapter2/code/default/${algorithm}`);
  if (!response.ok) {
    throw new Error(`Unable to load default ${algorithm} code.`);
  }
  const payload = await response.json();
  return payload.code;
}

export async function evaluateCode(
  algorithm: SearchAlgorithm,
  gridText: string,
  code: string,
): Promise<CodeEvaluationResponse> {
  const grid = gridText.split("\n").filter((row) => row.length > 0);
  const response = await fetch(`${API_BASE}/api/chapter2/code/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ algorithm, grid, code }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Code evaluation failed with status ${response.status}`);
  }

  return response.json();
}

export async function visualizeCode(
  algorithm: SearchAlgorithm,
  gridText: string,
  code: string,
): Promise<SearchResponse> {
  const grid = gridText.split("\n").filter((row) => row.length > 0);
  const response = await fetch(`${API_BASE}/api/chapter2/code/visualize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ algorithm, grid, code }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => null);
    throw new Error(detail?.detail ?? `Code visualization failed with status ${response.status}`);
  }

  return response.json();
}

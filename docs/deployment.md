# Deployment

## Vercel Deployment

The current deployment target is Vercel. This repository is configured as one Vercel project:

- `frontend/` builds the Vite React app into static files.
- `api/index.py` exposes the existing FastAPI backend as a Vercel Python Function.
- `vercel.json` builds `frontend/dist`, serves the app, and rewrites `/api/*` requests to the Python Function.
- `requirements.txt` at the repository root installs the backend dependencies for Vercel.

This follows Vercel's documented FastAPI support, where a FastAPI `app` instance can be exported from an entrypoint such as `index.py`, and Vercel rewrites can route browser requests to functions without changing the URL.

Deploy from the repository root:

```bash
vercel
vercel --prod
```

The deployed application should use same-origin API calls:

```text
https://<your-project>.vercel.app/api/health
```

No `VITE_API_URL` is needed for the normal Vercel deployment because the frontend calls `/api/...` on the same domain.

## Vercel Project Settings

The repository-level `vercel.json` defines the important settings:

- Build command: `cd frontend && npm ci && npm run build`
- Output directory: `frontend/dist`
- Python Function: `api/index.py`
- API rewrite: `/api/:path*` to `/api/index.py`
- SPA fallback rewrite: `/:path*` to `/index.html`

If you configure the project through the Vercel dashboard, keep the project root as the repository root. Do not set the Vercel root directory to `frontend/`, because that would hide the FastAPI function and root Python requirements.

## Live-Code Safety

The backend executes learner-submitted Python code. This is useful for an educational MVP, but it is still arbitrary code execution.

Vercel Functions give an isolated serverless runtime, request time limits, and a temporary filesystem, but this should not be treated as a complete public judge sandbox. Before opening the live editor to untrusted traffic, add stronger protection such as authentication, rate limiting, narrower code capabilities, or a separate hardened execution service with per-run containers and network-disabled execution.

## References

- Vercel, [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- Vercel, [Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- Vercel, [Rewrites](https://vercel.com/docs/rewrites)

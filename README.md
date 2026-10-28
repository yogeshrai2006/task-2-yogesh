# Tasks REST API
Stdlib-only Python API. Run: `python app.py` (uses `PORT`, default 8000).

| Method | Path | Notes |
|---|---|---|
| GET | /health | liveness |
| GET/POST | /tasks | list / create `{title, done?}` |
| GET/PUT/PATCH/DELETE | /tasks/{id} | 404 if missing, 400 on bad input |

Tests: `python -m unittest -v` (also run in CI via .github/workflows/ci.yml).
Deploy: `docker build -t tasks-api . && docker run -p 8000:8000 tasks-api`,
or push to GitHub and create a Render/Railway "Web Service" (start command `python app.py`).

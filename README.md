# Trip Planner API

## Run the server

```bash
# Dev: auto-reload, only your machine (127.0.0.1:8000)
uv run fastapi dev app/main.py
uv run uvicorn app.main:app --reload

# Production: no reload, reachable from the network (0.0.0.0:8000)
uv run fastapi run app/main.py
uv run uvicorn app.main:app --host 0.0.0.0
```

Docs: http://127.0.0.1:8000/docs

## Run the tests

```bash
uv run pytest
```

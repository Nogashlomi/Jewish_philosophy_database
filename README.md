# Medieval Jewish Philosophy - RDF Explorer

A research-oriented web application for mapping and studying medieval Jewish philosophy.

## Setup

### Backend
Make sure you have `uv` installed.

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

To run tests:

```shell
PYTHONPATH=. uv run --with pytest --with pytest-asyncio --with httpx pytest tests
```

### Frontend

```shell
yarn install
yarn dev
```

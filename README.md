# Medieval Jewish Philosophy - RDF Explorer

A research-oriented web application for mapping and studying medieval Jewish philosophy.

Deployed at [https://jephy-index.web.app](https://jephy-index.web.app).

## Backend

### Local run

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

Or to run in Docker:

```shell
docker build -t jephy-backend .
docker run -p 8000:8000 jephy-backend
```

### Deploy

Deployed to Google Cloud Run. Make sure you have the `gcloud` CLI installed and configured.

```shell
export PROJECT_ID=jephy-510614
export REGION=europe-west1
gcloud run deploy jephy-backend \
  --source . \
  --project ${PROJECT_ID} --region ${REGION} \
  --allow-unauthenticated
```

### Frontend

```shell
yarn install
yarn dev
```

### Frontend deploy

Deployed to Firebase Hosting at https://jephy-index.web.app. Run from `frontend/`. The Firebase Hosting target is explicitly mapped to the `jephy-index` site, so `firebase deploy` deploys there while retaining the `jephy-db` Firebase project. The command first runs `yarn build` (the `predeploy` hook in `firebase.json`), which uses the production API URL from `.env.production`:

```shell
yarn firebase login
yarn firebase deploy
```

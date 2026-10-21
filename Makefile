PROJECT_ID ?= jephy-510614
REGION ?= europe-west1
SERVICE ?= jephy-backend
ENV_FILE ?= backend/.env

.PHONY: server-deploy server-dev frontend-deploy frontend-dev frontend-dev-remote

server-deploy:
	@MONGODB_URI="$$(grep -E '^MONGODB_URI=' $(ENV_FILE) | head -n1 | cut -d= -f2-)"; \
	if [ -z "$$MONGODB_URI" ]; then echo "MONGODB_URI not found in $(ENV_FILE)"; exit 1; fi; \
	gcloud run deploy $(SERVICE) \
		--source . \
		--project $(PROJECT_ID) --region $(REGION) \
		--allow-unauthenticated \
		--set-env-vars "^@@^MONGODB_URI=$$MONGODB_URI"

server-dev:
	cd backend && uv sync && uv run uvicorn app.main:app --reload

frontend-deploy:
	cd frontend && yarn firebase deploy

frontend-dev:
	cd frontend && yarn dev

frontend-dev-remote:
	cd frontend && yarn dev:remote

run:
	@export $$(cat .env | xargs) && uvicorn app.api.main:app --reload

test:
	@export $$(cat .env.test | xargs) && pytest -q

db-reset:
	@docker compose down -v && docker compose up -d

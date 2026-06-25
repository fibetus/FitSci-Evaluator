.PHONY: up down logs migrate pull-model status test integration app

up:
	@./scripts/dev.sh up

down:
	@./scripts/dev.sh down

logs:
	@./scripts/dev.sh logs

migrate:
	@./scripts/dev.sh migrate

pull-model:
	@./scripts/dev.sh pull-model

status:
	@./scripts/dev.sh status

test:
	cd backend && python -m pytest --cov --cov-report=term-missing -m "not integration"

integration:
	cd backend && FITSCI_INTEGRATION=1 python -m pytest -m integration

app:
	docker compose --profile app up -d --build

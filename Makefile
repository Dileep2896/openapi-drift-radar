.PHONY: install dev api web test lint build metrics serve

install:
	uv sync
	cd web && npm install

api:
	uv run python -m server.app

web:
	cd web && npm run dev

dev:
	@echo "API on http://127.0.0.1:5001 · UI on http://localhost:5173 (and /story)"
	@trap 'kill 0' INT TERM; uv run python -m server.app & (cd web && npm run dev) & wait

metrics:
	uv run python -m radar.metrics

test:
	uv run pytest --cov=radar --cov=server --cov-report=term-missing
	cd web && npm test

lint:
	uv run ruff check .
	cd web && npm run lint

build: metrics
	cd web && npm run build

serve: build
	uv run python -m server.app

DOCKER_COMPOSE_SERVER=./docker-compose.yml
DOCKER_COMPOSE_LOCAL=./docker-compose.local.yml
ENV_LOCAL=.env.local

.PHONY: remove-volumes
remove-volumes:
	@echo "Removing all Docker volumes..."
	docker compose -f $(DOCKER_COMPOSE_LOCAL) down --volumes

up-local:
	docker compose --env-file $(ENV_LOCAL) -f $(DOCKER_COMPOSE_LOCAL) up -d --build

up-local-app:
	docker compose --env-file $(ENV_LOCAL) -f $(DOCKER_COMPOSE_LOCAL) up -d --build steganography_api

up-local-db:
	docker compose --env-file $(ENV_LOCAL) -f $(DOCKER_COMPOSE_LOCAL) up -d --build steganography_postgres

down-local:
	docker compose --env-file $(ENV_LOCAL) -f $(DOCKER_COMPOSE_LOCAL) down

build-local:
	docker compose --env-file $(ENV_LOCAL) -f $(DOCKER_COMPOSE_LOCAL) build

format:
	ruff format --config=./pyproject.toml
	ruff check --fix --preview --unsafe-fixes --config=./pyproject.toml

migrations:
	docker compose -f $(DOCKER_COMPOSE_LOCAL) exec steganography_api alembic revision --autogenerate -m "$(m)"

migrate:
	docker compose -f $(DOCKER_COMPOSE_LOCAL) exec steganography_api alembic upgrade head

logs:
	docker compose -f $(DOCKER_COMPOSE_LOCAL) logs -f

shell:
	docker compose -f $(DOCKER_COMPOSE_LOCAL) exec steganography_api /bin/bash

psql:
	docker compose -f $(DOCKER_COMPOSE_LOCAL) exec steganography_postgres psql -U $$POSTGRES_USER -d $$POSTGRES_DB

test:
	docker compose -f $(DOCKER_COMPOSE_LOCAL) exec steganography_api pytest

status:
	docker compose -f $(DOCKER_COMPOSE_LOCAL) ps

CHANGED_PY_FILES = $(shell git diff --name-only --diff-filter=ACM HEAD | findstr /R "\.py")

format_and_check_code_changed_win:
	@for %%f in ($(CHANGED_PY_FILES)) do (\
	@echo %%f && \
	ruff check --fix --preview --unsafe-fixes --fix %%f && \
	ruff format %%f \
	)
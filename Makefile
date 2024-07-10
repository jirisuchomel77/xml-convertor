DOCKER_COMPOSE=docker-compose

lint: ruff black

fixlint:
	"$(DOCKER_COMPOSE)" run --rm poetry run ruff --fix rossum || exit 0
	"$(DOCKER_COMPOSE)" run --rm poetry run black rossum || exit 0

local:
	# poetry run mypy rossum || exit 0
	poetry run ruff rossum || exit 0
	poetry run black --diff rossum || exit 0

build:
	"$(DOCKER_COMPOSE)" build rossum || exit 0

ruff:
	"$(DOCKER_COMPOSE)" run --rm poetry run ruff rossum || exit 0

black:
	"$(DOCKER_COMPOSE)" run --rm poetry run black --diff rossum || exit 0

test:
	"$(DOCKER_COMPOSE)" run --rm test

api:
	"$(DOCKER_COMPOSE)" up rossum

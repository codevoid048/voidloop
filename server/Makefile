.PHONY: run migrate makemigrations shell check format init venv

run:
	uv run python src/manage.py runserver

migrate:
	uv run python src/manage.py migrate

makemigrations:
	uv run python src/manage.py makemigrations

shell:
	uv run python src/manage.py shell

check:
	uv run python src/manage.py check

format:
	uv run ruff check src --fix
	uv run ruff format src

venv:
	source .venv/bin/activate
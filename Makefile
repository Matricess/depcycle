.PHONY: install format lint typecheck test coverage check build clean

install:
	uv sync --group dev

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run pyright src/

test:
	uv run pytest -q

coverage:
	uv run pytest --cov=depcycle --cov-branch --cov-report=term-missing

check: 
	lint typecheck test

build:
	uv build

clean:
	find . -type d \( -name "dist" -o -name ".ruff_cache" -o -name ".pytest_cache" -o -name ".pyright_cache" -o -name "htmlcov" -o -name "__pycache__" -o -name "*.egg-info" \) -prune -exec rm -rf {} +
	find . -type f \( -name ".coverage" -o -name ".coverage.*" \) -exec rm -f {} +

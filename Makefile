# Update version ONLY here
VERSION := 0.2.4
SHELL := /bin/bash
# Makefile for project
VENV := ~/.venv/bin/activate
UNAME_S := $(shell uname -s)

# ----------------------------------------------------------------------------
# Documentation
# ----------------------------------------------------------------------------

# Build documentation using Sphinx and zip it
build-docs:
	uv run sphinx-build -n -b text docs builddocs
	uv run sphinx-build -n -a -b html docs builddocs
	cd builddocs && zip -r ../builddocs.zip . -x ".*" && cd ..

rebuild-docs:
	uv run sphinx-apidoc . --full -o docs -H 'fake-py-mcp' -A 'Artur Barseghyan <artur.barseghyan@gmail.com>' -f -d 20
	cp docs/conf.py.distrib docs/conf.py
	cp docs/index.rst.distrib docs/index.rst

build-docs-epub:
	$(MAKE) -C docs/ epub

build-docs-pdf:
	$(MAKE) -C docs/ latexpdf

auto-build-docs:
	uv run sphinx-autobuild docs docs/_build/html

# Serve the built docs on port 5001
serve-docs:
	source $(VENV) && cd builddocs && python -m http.server 5001

# ----------------------------------------------------------------------------
# Pre-commit
# ----------------------------------------------------------------------------

pre-commit-install:
	pre-commit install

pre-commit:
	pre-commit run --all-files

# ----------------------------------------------------------------------------
# Linting
# ----------------------------------------------------------------------------

doc8:
	uv run doc8

# Run ruff on the codebase
ruff:
	uv run ruff check .

# ----------------------------------------------------------------------------
# Installation
# ----------------------------------------------------------------------------

create-venv:
	uv venv

# Install the project
install: create-venv
	uv sync --all-extras

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

test: clean
	uv run pytest -vrx -s

test-integration: test

install-all: install

test-all: test

# ----------------------------------------------------------------------------
# Security
# ----------------------------------------------------------------------------

create-secrets:
	uv run detect-secrets scan > .secrets.baseline

detect-secrets:
	uv run detect-secrets scan --baseline .secrets.baseline

# ----------------------------------------------------------------------------
# Development
# ----------------------------------------------------------------------------

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -exec rm -f {} \;
	find . -type f -name "builddocs.zip" -exec rm -f {} \;
	find . -type f -name "*.py,cover" -exec rm -f {} \;
	find . -type f -name "*.orig" -exec rm -f {} \;
	find . -type f -name "*.coverage" -exec rm -f {} \;
	find . -type f -name "*.db" -exec rm -f {} \;
	find . -type d -name "__pycache__" -exec rm -rf {} \; -prune
	rm -rf build/
	rm -rf dist/
	rm -rf .cache/
	rm -rf htmlcov/
	rm -rf builddocs/
	rm -rf testdocs/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf fake.py.egg-info/

mcpo:
	uv run mcpo --port 8006 -- fake-py-mcp --storage-root=/Users/me/repos/fake-py-mcp/tmp_root

mcpo-dev:
	uv run mcpo --hot-reload --port 8006 -- /Users/me/repos/fake-py-mcp/.venv/bin/python /Users/me/repos/fake-py-mcp/fakepy_mcp.py --storage-root=/Users/me/repos/fake-py-mcp/tmp_root

mcp-inspector:
	DANGEROUSLY_OMIT_AUTH=true CLIENT_PORT=8006 uv run mcp-inspector fake-py-mcp --storage-root=/Users/me/repos/fake-py-mcp/tmp_root

mcp-inspector-dev:
	DANGEROUSLY_OMIT_AUTH=true CLIENT_PORT=8006 uv run mcp-inspector /Users/me/repos/fake-py-mcp/.venv/bin/python /Users/me/repos/fake-py-mcp/fakepy_mcp.py --storage-root=/Users/me/repos/fake-py-mcp/tmp_root

shell:
	uv run ipython

compile-requirements:
	source $(VENV) && uv pip compile --all-extras -o docs/requirements.txt pyproject.toml

compile-requirements-upgrade:
	source $(VENV) && uv pip compile --all-extras -o docs/requirements.txt pyproject.toml --upgrade

# ----------------------------------------------------------------------------
# Release
# ----------------------------------------------------------------------------

update-version:
	@echo "Updating version in pyproject.toml and fakepy_mcp.py"
	@if [ "$(UNAME_S)" = "Darwin" ]; then \
		gsed -i 's/version = "[0-9.]\+"/version = "$(VERSION)"/' pyproject.toml; \
		gsed -i 's/__version__ = "[0-9.]\+"/__version__ = "$(VERSION)"/' fakepy_mcp.py; \
	else \
		sed -i 's/version = "[0-9.]\+"/version = "$(VERSION)"/' pyproject.toml; \
		sed -i 's/__version__ = "[0-9.]\+"/__version__ = "$(VERSION)"/' fakepy_mcp.py; \
	fi

build:
	uv run python -m build .

check-build:
	uv run twine check dist/*

release:
	uv run twine upload dist/* --verbose

test-release:
	uv run twine upload --repository testpypi dist/*

mypy:
	uv run mypy fake.py

# ----------------------------------------------------------------------------
# Other
# ----------------------------------------------------------------------------

%:
	@:

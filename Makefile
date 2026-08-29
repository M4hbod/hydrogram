PYTHON = python
SPHINX_BUILD = sphinx-build
SPHINX_AUTOBUILD = sphinx-autobuild
TOWNCRIER = towncrier

PYROGRAM_DIR = pyrogram
DOCS_DIR = docs
DOCS_SOURCE = $(DOCS_DIR)/source
DOCS_BUILD = $(DOCS_DIR)/build
API_DIRS = $(PYROGRAM_DIR)/errors/exceptions $(PYROGRAM_DIR)/raw/all.py $(PYROGRAM_DIR)/raw/base $(PYROGRAM_DIR)/raw/functions $(PYROGRAM_DIR)/raw/types
DOCS_API_DIRS = $(DOCS_SOURCE)/api/bound-methods $(DOCS_SOURCE)/api/methods $(DOCS_SOURCE)/api/types $(DOCS_SOURCE)/telegram

.PHONY: types all clean clean-api clean-docs api api-raw api-errors docs docs-compile docs-serve live-docs towncrier towncrier-draft dev-tools dev-setup test test-cov check-api-schema generate-docs-json compare-bot-api cherry-pick-pyro sync-upstream sync-upstream-check help

all: api docs

dev-setup:
	@echo "Installing dependencies..."
	@uv sync --all-extras --dev
	@echo "Installing git hooks..."
	@uv run pre-commit install
	@uv run pre-commit install --hook-type pre-push
	@echo "Ready. Style runs on commit, tests run on push."

test:
	@uv run pytest -q -m "not integration"

test-cov:
	@uv run pytest -m "not integration" --cov --cov-report=term-missing --cov-report=xml

clean: clean-api clean-docs
	@echo "All directories cleaned successfully"

clean-api:
	@echo "Cleaning generated API files..."
	@rm -rf $(API_DIRS)

clean-docs:
	@echo "Cleaning generated documentation..."
	@rm -rf $(DOCS_BUILD) $(DOCS_API_DIRS)

api: api-raw api-errors
	@echo "API compilation finished"

api-raw:
	@echo "Compiling raw API..."
	@$(PYTHON) -c "from compiler.api.compiler import start; start()"

api-errors:
	@echo "Compiling API errors..."
	@$(PYTHON) -c "from compiler.errors.compiler import start; start()"

docs: docs-compile docs-serve

docs-compile:
	@echo "Compiling documentation..."
	@$(PYTHON) -c "from compiler.docs.compiler import start; start()"

docs-serve:
	@echo "Building and serving documentation..."
	@$(SPHINX_BUILD) -b html $(DOCS_SOURCE) $(DOCS_BUILD)/html -j auto

live-docs:
	@echo "Starting documentation server with live reload..."
	@$(SPHINX_AUTOBUILD) $(DOCS_SOURCE) $(DOCS_BUILD)/html -j auto --watch $(PYROGRAM_DIR)

towncrier:
	@echo "Generating release notes..."
	@$(TOWNCRIER) build --yes

towncrier-draft:
	@echo "Generating draft release notes..."
	@$(TOWNCRIER) build --draft

check-api-schema:
	@echo "Checking Telegram API schema for updates..."
	@$(PYTHON) dev_tools/check_api_schema_updates.py

sync-upstream:
	@echo "Replaying unsynced upstream commits with the namespace rename applied..."
	@$(PYTHON) dev_tools/sync_upstream.py

sync-upstream-check:
	@echo "Checking upstream for unsynced commits..."
	@$(PYTHON) dev_tools/sync_upstream.py --check

generate-docs-json:
	@echo "Generating API documentation JSON..."
	@$(PYTHON) dev_tools/generate_docs_json.py

compare-bot-api:
	@echo "Comparing implementation against Bot API..."
	@$(PYTHON) dev_tools/compare_to_bot_api.py

cherry-pick-pyro:
	@echo "Usage: make cherry-pick-pyro TYPE=<pr|branch|commit> ID=<number|name|hash>"
	@[ "$(TYPE)" ] && [ "$(ID)" ] && $(PYTHON) dev_tools/cherry_pick_pyro.py $(TYPE) $(ID) || echo "Please provide TYPE and ID parameters"

help:
	@echo "Available targets:"
	@echo "  dev-setup      : Install dependencies and git hooks (run this first)"
	@echo "  test           : Run unit + contract tests"
	@echo "  test-cov       : Run tests with a coverage report"
	@echo "  all            : Compile API and documentation"
	@echo "  clean          : Remove all generated files"
	@echo "  api            : Compile all API components"
	@echo "  docs           : Compile and serve documentation"
	@echo "  live-docs      : Start documentation server with live reload"
	@echo "  towncrier      : Generate release notes"
	@echo "  towncrier-draft: Generate draft release notes"
	@echo "  check-api-schema: Check Telegram API schema for updates"
	@echo "  sync-upstream  : Replay upstream commits onto dev with the rename applied"
	@echo "  sync-upstream-check: Report unsynced upstream commits without applying them"
	@echo "  generate-docs-json: Generate API documentation JSON"
	@echo "  compare-bot-api: Compare implementation against Bot API"
	@echo "  cherry-pick-pyro: Cherry-pick code from Pyrogram (usage: make cherry-pick-pyro TYPE=<pr|branch|commit> ID=<number|name|hash>)"

types:
	@echo "Running the type ratchet..."
	@$(PYTHON) dev_tools/type_ratchet.py

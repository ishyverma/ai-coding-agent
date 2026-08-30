# ── Paths ─────────────────────────────────────────────────────────────────────
PYTHON   := backend/venv/bin/python
PYTEST   := backend/venv/bin/pytest
RUFF     := backend/venv/bin/ruff
NPM      := $(shell command -v npm 2>/dev/null || echo "npm-not-found")

# ── Default target ────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  make test              Run all tests (backend + frontend build check)"
	@echo "  make test-backend      Run backend unit tests"
	@echo "  make test-frontend     Run frontend build check"
	@echo "  make lint              Lint + format check (ruff)"
	@echo "  make install           Install all dependencies"
	@echo "  make install-backend   Install backend Python deps into venv"
	@echo "  make install-frontend  Install frontend npm deps"
	@echo ""

# ── Install ───────────────────────────────────────────────────────────────────
.PHONY: install
install: install-backend install-frontend

.PHONY: install-backend
install-backend:
	@if [ ! -f backend/venv/bin/python ]; then \
	    echo "Creating virtualenv with python3.11..."; \
	    python3.11 -m venv backend/venv; \
	fi
	backend/venv/bin/pip install -q -r backend/requirements.txt
	@echo "Backend dependencies installed."

.PHONY: install-frontend
install-frontend:
	@if [ "$(NPM)" = "npm-not-found" ]; then \
	    echo "ERROR: npm not found. Install Node.js from https://nodejs.org"; exit 1; \
	fi
	cd frontend && $(NPM) ci
	@echo "Frontend dependencies installed."

# ── Tests ─────────────────────────────────────────────────────────────────────
.PHONY: test
test: test-backend test-frontend

.PHONY: test-backend
test-backend:
	@echo "==> Running backend tests..."
	cd backend && \
	  GROQ_API_KEY=test-key-for-ci \
	  SECRET_KEY=test-secret-for-ci \
	  DATABASE_URL=sqlite:///./test.db \
	  LANGSMITH_TRACING=false \
	  ../$(PYTEST) tests/ -v -m "not integration" --cov=app

.PHONY: test-frontend
test-frontend:
	@if [ "$(NPM)" = "npm-not-found" ]; then \
	    echo "ERROR: npm not found. Install Node.js from https://nodejs.org"; exit 1; \
	fi
	@echo "==> Running frontend build check..."
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:8000 $(NPM) run build

# ── Lint ──────────────────────────────────────────────────────────────────────
.PHONY: lint
lint:
	@echo "==> Linting backend..."
	$(RUFF) check backend/app/
	$(RUFF) format --check backend/app/
	@echo "Lint passed."

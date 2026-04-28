import os

ROOT = "codeagent"

files = {
    ".clinerules": "# Cline Rules\n# Global rules that apply to all packages\n",

    ".clinerules-ignore": "# Files/folders to ignore for clinerules\nnode_modules/\n__pycache__/\n.env\n*.pyc\n",

    ".clinerules.d/python-standards.md": """# Python Standards

## Style
- Follow PEP 8
- Use type hints for all function signatures
- Max line length: 88 (Black formatter)

## Tools
- Formatter: black
- Linter: ruff
- Type checker: mypy

## Naming
- snake_case for variables and functions
- PascalCase for classes
- UPPER_SNAKE_CASE for constants
""",

    ".clinerules.d/typescript-standards.md": """# TypeScript Standards

## Style
- Use strict mode
- Prefer interfaces over types for object shapes
- No `any` — use `unknown` if type is truly unknown

## Tools
- Formatter: prettier
- Linter: eslint
- Compiler: tsc --strict

## Naming
- camelCase for variables and functions
- PascalCase for components and classes
- UPPER_SNAKE_CASE for constants
""",

    ".clinerules.d/architecture.md": """# Architecture

## Overview
Monorepo with three packages:
- `agent-core` — Python backend / AI agent logic
- `web-ui` — Frontend interface
- `worker` — Background job processor

## Communication
- agent-core exposes a REST API
- web-ui calls agent-core API
- worker consumes tasks via queue

## Principles
- Each package is independently deployable
- Shared config via root docker-compose.yml
- Secrets via .env files (never committed)
""",

    ".clinerules.d/security.md": """# Security Rules

## Secrets
- Never commit .env files
- Use .env.example with placeholder values only
- Rotate keys if accidentally exposed

## Dependencies
- Pin all dependency versions
- Run `pip audit` / `npm audit` regularly

## API
- Validate all inputs
- Use parameterised queries — no raw SQL
- Rate-limit all public endpoints
""",

    # ── agent-core ──────────────────────────────────────────────
    "packages/agent-core/CONTEXT.md": """# agent-core — Context

## Purpose
Core AI agent logic and REST API backend.

## Stack
- Python 3.11+
- FastAPI
- Anthropic SDK

## Structure
- `api/` — route handlers and schemas
- `core/` — agent logic and tools
- `tests/` — pytest test suite

## Run
```bash
pip install -r requirements.txt
cp .env.example .env
python main.py
```
""",

    "packages/agent-core/main.py": """import uvicorn
from fastapi import FastAPI

app = FastAPI(title="CodeAgent API", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
""",

    "packages/agent-core/requirements.txt": """fastapi>=0.111.0
uvicorn[standard]>=0.29.0
anthropic>=0.25.0
python-dotenv>=1.0.0
pydantic>=2.7.0
httpx>=0.27.0
pytest>=8.2.0
pytest-asyncio>=0.23.0
""",

    "packages/agent-core/.env.example": """# Copy this file to .env and fill in real values
ANTHROPIC_API_KEY=your_anthropic_api_key_here
APP_ENV=development
PORT=8000
""",

    "packages/agent-core/api/__init__.py": "",
    "packages/agent-core/api/routes.py": """from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")


@router.get("/ping")
def ping():
    return {"message": "pong"}
""",

    "packages/agent-core/core/__init__.py": "",
    "packages/agent-core/core/agent.py": """class Agent:
    \"\"\"Main agent orchestrator.\"\"\"

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.model = model

    async def run(self, task: str) -> str:
        raise NotImplementedError
""",

    "packages/agent-core/tests/__init__.py": "",
    "packages/agent-core/tests/test_health.py": """from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
""",

    # ── web-ui ──────────────────────────────────────────────────
    "packages/web-ui/CONTEXT.md": """# web-ui — Context

## Purpose
Frontend interface for the CodeAgent.

## Stack
- Node.js 20+
- (Add your framework here: Next.js / Vite / etc.)

## Run
```bash
npm install
cp .env.example .env
npm run dev
```
""",

    "packages/web-ui/package.json": """{
  "name": "web-ui",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "echo 'Add your dev command here'",
    "build": "echo 'Add your build command here'",
    "lint": "eslint ."
  },
  "dependencies": {},
  "devDependencies": {}
}
""",

    "packages/web-ui/.env.example": """# Copy this file to .env and fill in real values
NEXT_PUBLIC_API_URL=http://localhost:8000
""",

    # ── worker ──────────────────────────────────────────────────
    "packages/worker/CONTEXT.md": """# worker — Context

## Purpose
Background job processor for async agent tasks.

## Stack
- Python 3.11+
- (Add queue: Celery / RQ / ARQ / etc.)

## Run
```bash
pip install -r requirements.txt
cp .env.example .env
python worker.py
```
""",

    # ── root files ──────────────────────────────────────────────
    "docker-compose.yml": """version: "3.9"

services:
  agent-core:
    build: ./packages/agent-core
    ports:
      - "8000:8000"
    env_file: ./packages/agent-core/.env
    volumes:
      - ./packages/agent-core:/app
    command: python main.py

  web-ui:
    build: ./packages/web-ui
    ports:
      - "3000:3000"
    env_file: ./packages/web-ui/.env
    depends_on:
      - agent-core

  worker:
    build: ./packages/worker
    env_file: ./packages/worker/.env
    depends_on:
      - agent-core
""",

    "PLAN.md": """# CodeAgent — Project Plan

## Goal
Build an AI-powered code agent with a web UI and background worker.

## Milestones
- [ ] 1. Scaffold monorepo structure
- [ ] 2. agent-core: basic FastAPI + Anthropic integration
- [ ] 3. web-ui: connect to agent-core API
- [ ] 4. worker: async task queue
- [ ] 5. Docker Compose — all services running together
- [ ] 6. Deploy

## Notes
""",

    "README.md": """# CodeAgent

AI-powered code agent — monorepo.

## Packages
| Package | Description |
|---|---|
| `packages/agent-core` | Python backend / AI agent logic |
| `packages/web-ui` | Frontend interface |
| `packages/worker` | Background job processor |

## Quick Start

```bash
# 1. Clone
git clone <repo-url>
cd codeagent

# 2. Copy env files
cp packages/agent-core/.env.example packages/agent-core/.env
cp packages/web-ui/.env.example packages/web-ui/.env

# 3. Run with Docker
docker-compose up --build
```

## Development
See each package's `CONTEXT.md` for per-package setup instructions.
""",

    ".gitignore": """# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
.venv/
venv/
env/
*.egg-info/
dist/
build/
.mypy_cache/
.ruff_cache/
.pytest_cache/

# Node
node_modules/
.next/
dist/
build/
*.tsbuildinfo

# Env
.env
.env.local
.env.*.local

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
*.log
""",
}


def create_project(root: str, files: dict) -> None:
    created_dirs = set()
    created_files = 0

    for rel_path, content in files.items():
        full_path = os.path.join(root, rel_path)
        dir_path = os.path.dirname(full_path)

        if dir_path and dir_path not in created_dirs:
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.add(dir_path)

        if not os.path.exists(full_path):
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_files += 1
        else:
            print(f"  ⚠️  Skipped (exists): {full_path}")

    print(f"\n✅ Done!  {len(created_dirs)} folders · {created_files} files created")
    print(f"📂 Project root: {os.path.abspath(root)}\n")


if __name__ == "__main__":
    create_project(ROOT, files)
# Python Coding Standards

## 🎯 Core Principles

1. **Type hints are mandatory** - Every function parameter and return value
2. **Async by default** - All I/O operations must be async
3. **Explicit over implicit** - No magic, clear code
4. **Fail fast** - Validate inputs immediately
5. **Test everything** - 80%+ coverage required

---

## 📝 File Template

```python
"""
Module: packages/agent_core/nodes/planning.py

Task planning and decomposition for coding agents.

This module handles breaking down user tasks into actionable steps
that the coding node can execute sequentially.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from anthropic import Anthropic
import asyncio
import logging

logger = logging.getLogger(__name__)


class PlanStep(BaseModel):
    """Single step in execution plan."""
    
    step_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    estimated_time_seconds: int = Field(default=60, ge=1)


class PlanningInput(BaseModel):
    """Input for planning node."""
    
    task_description: str
    language: str
    context: Optional[Dict[str, Any]] = None


async def create_plan(
    input_data: PlanningInput,
    client: Anthropic
) -> List[PlanStep]:
    """
    Create execution plan from task description.
    
    Args:
        input_data: Task description and context
        client: Anthropic API client
        
    Returns:
        List of actionable steps
        
    Raises:
        ValueError: If task description is too vague
        APIError: If LLM call fails
        
    Example:
        >>> input_data = PlanningInput(
        ...     task_description="Create REST API for todos",
        ...     language="python"
        ... )
        >>> plan = await create_plan(input_data, client)
        >>> len(plan) >= 1
        True
    """
    try:
        # Implementation here
        pass
        
    except Exception as e:
        logger.error(f"Planning failed: {e}", exc_info=True)
        raise


# Always have __main__ for testing
if __name__ == "__main__":
    # Quick test
    import os
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    input_data = PlanningInput(
        task_description="Write fibonacci function",
        language="python"
    )
    
    plan = asyncio.run(create_plan(input_data, client))
    print(f"Generated {len(plan)} steps")
```

---

## 🏗️ Project Structure

packages/agent-core/
├── main.py                 # FastAPI app entry
├── api/
│   ├── init.py
│   ├── routes/
│   │   ├── init.py
│   │   ├── generate.py     # POST /generate
│   │   ├── tasks.py        # CRUD for tasks
│   │   └── health.py       # GET /health
│   └── models.py           # Pydantic request/response models
├── core/
│   ├── init.py
│   ├── agent.py            # Main agent orchestrator
│   ├── executor.py         # Docker code execution
│   ├── github_mgr.py       # GitHub API wrapper
│   └── model_router.py     # LLM selection logic
├── nodes/                  # LangGraph nodes
│   ├── init.py
│   ├── planning.py
│   ├── coding.py
│   ├── testing.py
│   └── review.py
├── tests/
│   ├── test_agent.py
│   ├── test_executor.py
│   └── conftest.py         # Pytest fixtures
├── requirements.txt
└── .env.example

---

## 📦 Dependencies (requirements.txt)

```txt
# Core
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# AI/ML
anthropic==0.18.1
google-generativeai==0.3.2
openai==1.12.0
langgraph==0.0.20
langchain==0.1.6

# Database
supabase==2.3.4
redis[hiredis]==5.0.1

# GitHub
PyGithub==2.1.1
gitpython==3.1.41

# Docker
docker==7.0.0

# Utils
python-dotenv==1.0.1
httpx==0.26.0

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
pylint==3.0.3
mypy==1.8.0
black==24.1.1
bandit==1.7.6
```

---

## 🎨 Code Style

### Formatting
```python
# Use Black (line length 100)
# Run: black . --line-length 100

# Good ✅
def function_name(
    param1: str,
    param2: int,
    param3: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Docstring here."""
    pass

# Bad ❌
def function_name(param1: str, param2: int, param3: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    pass
```

### Import Order
```python
# 1. Standard library
import os
import sys
from typing import Dict, Any, List

# 2. Third-party
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import anthropic

# 3. Local
from core.agent import Agent
from api.models import TaskRequest
```

### Naming Conventions
```python
# Classes: PascalCase
class CodeExecutor:
    pass

# Functions/variables: snake_case
def execute_code():
    pass

result_data = {}

# Constants: UPPER_SNAKE_CASE
MAX_RETRIES = 3
API_TIMEOUT = 30

# Private: leading underscore
def _internal_helper():
    pass

_cache = {}
```

---

## 🔒 Type Hints

```python
from typing import Dict, Any, List, Optional, Union, Callable, TypedDict

# Function signatures (REQUIRED)
async def fetch_user(user_id: str) -> Dict[str, Any]:
    """Every param and return must have type."""
    return {"id": user_id, "name": "Alice"}

# Optional parameters
def create_task(
    prompt: str,
    language: str = "python",
    timeout: Optional[int] = None
) -> Task:
    pass

# Complex types
def process_batch(
    items: List[Dict[str, Any]],
    callback: Optional[Callable[[str], None]] = None
) -> List[str]:
    pass

# TypedDict for structured data
class UserData(TypedDict):
    id: str
    email: str
    created_at: int

def get_user() -> UserData:
    return {"id": "123", "email": "a@b.com", "created_at": 1234567890}
```

---

## ⚡ Async/Await

```python
import asyncio
import httpx

# ALWAYS use async for I/O
async def fetch_data(url: str) -> Dict[str, Any]:
    """Network call = async."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# Database queries = async
async def save_task(task: Task) -> None:
    """DB write = async."""
    await supabase.table("tasks").insert(task.dict()).execute()

# LLM calls = async
async def generate_code(prompt: str) -> str:
    """LLM call = async."""
    client = Anthropic()
    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# Gather multiple async tasks
async def parallel_operations():
    """Run multiple I/O operations concurrently."""
    results = await asyncio.gather(
        fetch_data("https://api1.com"),
        fetch_data("https://api2.com"),
        save_task(task),
        return_exceptions=True  # Don't fail all if one fails
    )
    return results
```

---

## 🧪 Testing with Pytest

```python
# tests/test_executor.py

import pytest
from core.executor import CodeExecutor

# Fixtures
@pytest.fixture
def executor():
    """Create executor instance for tests."""
    return CodeExecutor()

# Test function naming: test_<what>_<scenario>
@pytest.mark.asyncio
async def test_executor_runs_valid_python():
    """Valid Python code should execute successfully."""
    executor = CodeExecutor()
    
    code = "print('Hello, World!')"
    result = await executor.run_python(code)
    
    assert result["success"] is True
    assert "Hello, World!" in result["output"]

@pytest.mark.asyncio
async def test_executor_fails_on_syntax_error():
    """Invalid syntax should return error."""
    executor = CodeExecutor()
    
    code = "print('unclosed string"
    result = await executor.run_python(code)
    
    assert result["success"] is False
    assert "SyntaxError" in result["error"]

# Parameterized tests
@pytest.mark.parametrize("code,expected", [
    ("1 + 1", "2"),
    ("'hello'.upper()", "HELLO"),
    ("len([1, 2, 3])", "3"),
])
async def test_executor_expressions(code, expected):
    """Test various Python expressions."""
    executor = CodeExecutor()
    result = await executor.run_python(f"print({code})")
    assert expected in result["output"]

# Mocking external dependencies
@pytest.mark.asyncio
async def test_llm_call_mocked(mocker):
    """Test LLM call with mocked response."""
    mock_response = mocker.Mock()
    mock_response.content = [mocker.Mock(text="def hello(): pass")]
    
    mocker.patch(
        "anthropic.Anthropic.messages.create",
        return_value=mock_response
    )
    
    result = await generate_code("write hello function")
    assert "def hello()" in result
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/test_executor.py

# Run specific test
pytest tests/test_executor.py::test_executor_runs_valid_python

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## 🔍 Code Quality

### Pylint (Score > 8.0 required)
```bash
# Run Pylint
pylint packages/agent-core/**/*.py --fail-under=8.0

# Disable specific warnings (sparingly)
# pylint: disable=line-too-long
long_variable_name_that_exceeds_limit = "value"
```

### MyPy (Strict mode)
```bash
# mypy.ini
[mypy]
python_version = 3.12
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

```bash
# Run MyPy
mypy packages/agent-core --strict
```

### Bandit (Security)
```bash
# Run security scan
bandit -r packages/agent-core -f json -o security-report.json
```

---

## 📋 Error Handling

```python
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

# Custom exceptions
class CodeExecutionError(Exception):
    """Raised when code execution fails."""
    pass

class LLMAPIError(Exception):
    """Raised when LLM API call fails."""
    pass

# Error handling pattern
async def generate_code(prompt: str) -> str:
    """
    Generate code with proper error handling.
    
    Raises:
        ValueError: If prompt is empty
        LLMAPIError: If API call fails
    """
    # Validate input
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    try:
        # Call LLM
        response = await llm_client.generate(prompt)
        return response.code
        
    except httpx.TimeoutError as e:
        logger.error(f"LLM API timeout: {e}")
        raise LLMAPIError("Request timed out") from e
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise LLMAPIError(f"Code generation failed: {str(e)}") from e

# FastAPI error handling
@app.post("/generate")
async def generate_endpoint(request: GenerateRequest):
    try:
        code = await generate_code(request.prompt)
        return {"code": code}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    except LLMAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🪵 Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Usage
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred", exc_info=True)  # Include traceback
logger.critical("Critical error")

# Structured logging (production)
import json

logger.info(json.dumps({
    "event": "task_completed",
    "task_id": "123",
    "duration_ms": 4500,
    "tokens_used": 1200
}))
```

---

## 🎯 FastAPI Best Practices

```python
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

app = FastAPI(title="CodeAgent API", version="0.1.0")

# Request/Response models
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="python", pattern="^(python|typescript|rust)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Create a function to calculate fibonacci",
                "language": "python"
            }
        }

class GenerateResponse(BaseModel):
    code: str
    explanation: str
    quality_score: float = Field(..., ge=0, le=10)

# Dependency injection
async def get_llm_client():
    """Provide LLM client instance."""
    return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Endpoint with all features
@app.post(
    "/generate",
    response_model=GenerateResponse,
    tags=["code-generation"],
    summary="Generate code from prompt",
    description="Uses AI to generate code based on natural language description"
)
async def generate(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    client: Anthropic = Depends(get_llm_client)
) -> GenerateResponse:
    """
    Generate code endpoint.
    
    - **prompt**: What you want the code to do
    - **language**: Target programming language
    """
    try:
        code = await generate_code_logic(request.prompt, client)
        
        # Background task (doesn't block response)
        background_tasks.add_task(save_to_db, code)
        
        return GenerateResponse(
            code=code,
            explanation="Generated successfully",
            quality_score=8.5
        )
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🚫 Anti-Patterns (AVOID)

```python
# ❌ NO type hints
def process(data):
    return data

# ✅ YES type hints
def process(data: Dict[str, Any]) -> Dict[str, Any]:
    return data

# ❌ NO sync I/O in async function
async def fetch_data():
    response = requests.get(url)  # BLOCKS!
    return response.json()

# ✅ YES async I/O
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ❌ NO bare except
try:
    risky_operation()
except:
    pass  # Silently swallows ALL errors

# ✅ YES specific exceptions
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    raise

# ❌ NO mutable default arguments
def add_item(item, items=[]):
    items.append(item)
    return items

# ✅ YES None + in-function init
def add_item(item: str, items: Optional[List[str]] = None) -> List[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

---

## ✅ Pre-Commit Checklist

Before committing Python code:

```bash
# 1. Format with Black
black . --line-length 100

# 2. Sort imports
isort .

# 3. Type check
mypy packages/agent-core --strict

# 4. Lint
pylint packages/agent-core/**/*.py --fail-under=8.0

# 5. Security scan
bandit -r packages/agent-core

# 6. Run tests
pytest --cov=. --cov-fail-under=80

# 7. Check coverage
# Must be > 80%
```

---

**Questions? Check the code examples in this file first. They are authoritative.**
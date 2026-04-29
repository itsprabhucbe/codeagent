import logging
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.agent import Agent
from core.executor import CodeExecutor, DockerUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

_agent: Agent | None = None
_executor: CodeExecutor | None = None


def get_agent() -> Agent:
    global _agent
    if _agent is None:
        _agent = Agent()
    return _agent


def get_executor() -> CodeExecutor:
    global _executor
    if _executor is None:
        _executor = CodeExecutor()
    return _executor


class GenerateRequest(BaseModel):
    task: str
    language: str = "python"


class GenerateResponse(BaseModel):
    code: str
    language: str
    model: str


class ExecuteRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50_000)
    language: Literal["python"] = "python"
    timeout: Optional[int] = Field(default=None, ge=1, le=300)


class ExecuteResponse(BaseModel):
    success: bool
    output: Optional[str]
    error: Optional[str]
    exit_code: int


@router.post("/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest):
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty")
    agent = get_agent()
    code = await agent.run(req.task, req.language)
    return GenerateResponse(code=code, language=req.language, model=agent.model)


@router.post("/execute", response_model=ExecuteResponse)
async def execute(req: ExecuteRequest) -> ExecuteResponse:
    """Execute Python code in a secure Docker sandbox."""
    logger.info(
        "Execution attempt: language=%s code_bytes=%d timeout=%s",
        req.language,
        len(req.code.encode()),
        req.timeout,
    )

    try:
        executor = get_executor()
    except DockerUnavailableError as exc:
        logger.error("Docker unavailable: %s", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "Code execution is unavailable — Docker is not running. "
                "Start Docker Desktop and retry."
            ),
        ) from exc

    timeout = req.timeout if req.timeout is not None else CodeExecutor.TIMEOUT_SECONDS
    result = await executor.run_python(req.code, timeout=timeout)

    logger.info(
        "Execution complete: success=%s exit_code=%d",
        result["success"],
        result["exit_code"],
    )

    return ExecuteResponse(
        success=result["success"],
        output=result["output"] if result["output"] else None,
        error=result["error"],
        exit_code=result["exit_code"],
    )


@router.get("/ping")
def ping():
    return {"message": "pong"}

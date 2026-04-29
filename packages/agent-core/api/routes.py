import logging
import secrets
from typing import Literal, Optional

from fastapi import APIRouter, Cookie, HTTPException, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from core.agent import Agent
from core.executor import CodeExecutor, DockerUnavailableError
from core.github_manager import GitHubManager
from core.oauth_manager import GitHubOAuthManager

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


oauth_manager = GitHubOAuthManager()

# Store state tokens temporarily (in production, use Redis)
pending_states = {}


@router.get("/auth/github")
async def github_auth():
    """
    Initiate GitHub OAuth flow.

    Returns:
        Redirect to GitHub authorization page
    """
    state = secrets.token_urlsafe(32)
    pending_states[state] = True
    auth_url = oauth_manager.get_authorization_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/auth/github/callback")
async def github_callback(code: str, state: str, response: Response):
    """
    Handle GitHub OAuth callback.

    Args:
        code: Authorization code from GitHub
        state: State token for CSRF protection
        response: FastAPI response object

    Returns:
        Redirect to frontend with session token
    """
    if state not in pending_states:
        logger.warning(f"Invalid state token: {state}")
        return RedirectResponse(url="http://localhost:3000?error=invalid_state")

    del pending_states[state]

    access_token = await oauth_manager.exchange_code_for_token(code)
    if not access_token:
        logger.error("Failed to get access token")
        return RedirectResponse(url="http://localhost:3000?error=auth_failed")

    user_data = await oauth_manager.get_github_user(access_token)
    if not user_data:
        logger.error("Failed to get user data")
        return RedirectResponse(url="http://localhost:3000?error=user_data_failed")

    session_token = oauth_manager.create_session_token(access_token, user_data)
    redirect_url = (
        f"http://localhost:3000?github_connected=true"
        f"&session_token={session_token}"
        f"&github_user={user_data['login']}"
    )
    return RedirectResponse(url=redirect_url)


@router.get("/auth/github/status")
async def github_status(session_token: Optional[str] = Cookie(default=None)):
    """
    Check GitHub connection status.

    Args:
        session_token: Session token from cookie

    Returns:
        Connection status and user info
    """
    if not session_token:
        return {"connected": False, "user": None}

    payload = oauth_manager.decode_session_token(session_token)
    if not payload:
        return {"connected": False, "user": None}

    return {
        "connected": True,
        "user": payload.get("github_user"),
        "github_id": payload.get("github_id"),
    }


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


class CreatePRRequest(BaseModel):
    session_token: str
    repo_url: str
    file_path: str
    code: str
    commit_message: str
    branch_name: str
    pr_title: str
    pr_body: Optional[str] = ""


@router.post("/create-pr")
async def create_pull_request(request: CreatePRRequest):
    """Create GitHub PR using stored OAuth token."""
    payload = oauth_manager.decode_session_token(request.session_token)
    if not payload:
        return {"success": False, "error": "Invalid or expired session"}

    github_token = payload.get("github_token")
    github_manager = GitHubManager(github_token)

    if not github_manager.validate_token():
        return {"success": False, "error": "GitHub token invalid"}

    return await github_manager.create_pull_request(
        repo_url=request.repo_url,
        file_path=request.file_path,
        code=request.code,
        commit_message=request.commit_message,
        branch_name=request.branch_name,
        pr_title=request.pr_title,
        pr_body=request.pr_body
    )


@router.get("/ping")
def ping():
    return {"message": "pong"}

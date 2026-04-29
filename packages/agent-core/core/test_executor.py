"""
Tests for packages/agent-core/core/executor.py

Integration tests (test_executor_*) require a running Docker daemon and the
python:3.12-slim image pulled locally. Mocked tests run without Docker.
"""
import docker.errors
import pytest
from requests.exceptions import ReadTimeout
from unittest.mock import MagicMock, patch

from core.executor import CodeExecutor, DockerUnavailableError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def executor() -> CodeExecutor:
    """Real CodeExecutor — requires Docker daemon to be running."""
    return CodeExecutor()


# ---------------------------------------------------------------------------
# Integration tests — require Docker + python:3.12-slim image
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_executor_runs_valid_python(executor: CodeExecutor) -> None:
    """Valid Python code should execute successfully and capture stdout."""
    result = await executor.run_python("print('Hello, World!')")

    assert result["success"] is True
    assert "Hello, World!" in result["output"]
    assert result["exit_code"] == 0
    assert result["error"] is None


@pytest.mark.asyncio
async def test_executor_handles_syntax_error(executor: CodeExecutor) -> None:
    """Malformed Python should exit non-zero and report SyntaxError."""
    result = await executor.run_python("print('unclosed string")

    assert result["success"] is False
    assert result["exit_code"] != 0
    assert "SyntaxError" in result["output"]


@pytest.mark.asyncio
async def test_executor_enforces_timeout(executor: CodeExecutor) -> None:
    """An infinite loop must be killed after the timeout expires."""
    result = await executor.run_python("while True: pass", timeout=5)

    assert result["success"] is False
    assert result["error"] is not None
    assert "timeout" in result["error"].lower()


@pytest.mark.asyncio
async def test_executor_network_disabled(executor: CodeExecutor) -> None:
    """Container must not be able to open any network connection."""
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('8.8.8.8', 53), timeout=2)\n"
        "    print('NETWORK_OK')\n"
        "except Exception:\n"
        "    print('NETWORK_BLOCKED')\n"
    )
    result = await executor.run_python(code)

    assert "NETWORK_OK" not in result["output"]
    assert "NETWORK_BLOCKED" in result["output"]


@pytest.mark.asyncio
async def test_executor_ram_limit(executor: CodeExecutor) -> None:
    """Allocating 600 MB must be killed by the OOM killer (limit is 256 MB)."""
    # Touch every 4 KB page to force the kernel to commit the pages.
    code = (
        "data = bytearray(600 * 1024 * 1024)\n"
        "for i in range(0, len(data), 4096):\n"
        "    data[i] = 1\n"
        "print('done')\n"
    )
    result = await executor.run_python(code)

    assert result["success"] is False


# ---------------------------------------------------------------------------
# Mocked tests — no Docker required
# ---------------------------------------------------------------------------


def test_executor_raises_when_docker_unavailable() -> None:
    """CodeExecutor.__init__ must raise DockerUnavailableError when the daemon is down."""
    with patch("core.executor.docker.from_env") as mock_docker:
        mock_docker.return_value.ping.side_effect = docker.errors.DockerException(
            "daemon not running"
        )
        with pytest.raises(DockerUnavailableError):
            CodeExecutor()


@pytest.mark.asyncio
async def test_executor_handles_docker_api_error() -> None:
    """A Docker API error during container creation must return a safe error dict."""
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.containers.run.side_effect = docker.errors.APIError("internal error")

    with patch("core.executor.docker.from_env", return_value=mock_client):
        exc = CodeExecutor()
        result = await exc.run_python("print('test')")

    assert result["success"] is False
    assert result["exit_code"] == -1
    assert result["error"] is not None


@pytest.mark.asyncio
async def test_executor_handles_container_timeout() -> None:
    """A ReadTimeout from container.wait() must surface as a timeout error."""
    mock_container = MagicMock()
    mock_container.wait.side_effect = ReadTimeout("timed out waiting for container")

    mock_client = MagicMock()
    mock_client.ping.return_value = True
    mock_client.containers.run.return_value = mock_container

    with patch("core.executor.docker.from_env", return_value=mock_client):
        exc = CodeExecutor()
        result = await exc.run_python("while True: pass", timeout=1)

    assert result["success"] is False
    assert "timeout" in result["error"].lower()
    # Verify the container was force-removed despite the timeout
    mock_container.remove.assert_called_once_with(force=True)

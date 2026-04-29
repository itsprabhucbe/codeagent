"""
Module: packages/agent-core/core/executor.py

Secure Docker-based Python code execution sandbox.

SECURITY CRITICAL: Executes untrusted user-submitted code inside an isolated
Docker container. Every security constraint below is mandatory and must never
be removed or weakened without a documented security review.
"""
import asyncio
import logging
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional

import docker
import docker.errors
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout

logger = logging.getLogger(__name__)

_thread_pool = ThreadPoolExecutor(max_workers=4)

_IMAGE = "python:3.12-slim"


class DockerUnavailableError(Exception):
    """Raised when the Docker daemon cannot be reached."""


class CodeExecutor:
    """
    Executes Python code in an isolated Docker container.

    SECURITY CRITICAL — this class runs untrusted user code. All constraints
    listed below are active simultaneously (defense-in-depth):

    1. Network disabled       — container cannot reach the internet or LAN
    2. RAM limited to 256 MB  — prevents memory exhaustion attacks
    3. CPU limited to 50%     — prevents CPU starvation of the host
    4. Timeout enforced       — kills containers that run forever
    5. Read-only root fs      — code cannot persist malicious files
    6. /tmp writable (100 MB) — grants just enough writable space
    7. Non-root user          — limits blast radius if container is escaped
    8. No privileged mode     — prevents host kernel access
    9. All capabilities dropped — removes every Linux capability by default
    10. Auto-cleanup           — container and temp file removed after each run
    """

    MAX_RAM_MB: int = 256
    MAX_CPU_PERCENT: int = 50
    TIMEOUT_SECONDS: int = 30

    def __init__(self) -> None:
        try:
            self._client = docker.from_env()
            self._client.ping()
        except docker.errors.DockerException as exc:
            raise DockerUnavailableError(
                "Docker daemon is not running. Start Docker Desktop and retry."
            ) from exc

    async def run_python(
        self,
        code: str,
        timeout: int = TIMEOUT_SECONDS,
    ) -> Dict[str, Any]:
        """
        Execute Python code and return the result.

        SECURITY CHECKLIST (all enforced):
        ✅ Network disabled      (network_disabled=True)
        ✅ RAM limit 256 MB      (mem_limit="256m")
        ✅ CPU limit 50%         (cpu_quota=50000)
        ✅ Timeout enforced      (container.wait timeout)
        ✅ Non-root user         (user="nobody")
        ✅ Read-only filesystem  (read_only=True)
        ✅ /tmp writable 100 MB  (tmpfs={'/tmp': 'size=100M'})
        ✅ No privileged mode    (privileged=False)
        ✅ All caps dropped      (cap_drop=["ALL"])
        ✅ Auto-cleanup          (remove=True in finally)

        Args:
            code: Python source to execute. Treat as HOSTILE — never trust it.
            timeout: Maximum wall-clock seconds before the container is killed.

        Returns:
            {
                "success":   bool          — True when exit code is 0,
                "output":    str           — combined stdout + stderr,
                "error":     Optional[str] — human-readable failure reason,
                "exit_code": int           — process exit code from container,
            }
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _thread_pool,
            self._run_sync,
            code,
            timeout,
        )

    def _run_sync(self, code: str, timeout: int) -> Dict[str, Any]:
        """Blocking execution — must be called only via run_in_executor."""
        temp_file: Optional[str] = None
        container = None

        try:
            temp_file = _write_temp_file(code)
            temp_dir = os.path.dirname(temp_file)
            filename = os.path.basename(temp_file)

            container = self._client.containers.run(
                _IMAGE,
                command=["python", f"/code/{filename}"],
                # SECURITY: no network access whatsoever
                network_disabled=True,
                # SECURITY: resource limits
                mem_limit=f"{self.MAX_RAM_MB}m",
                cpu_quota=self.MAX_CPU_PERCENT * 1000,
                # SECURITY: drop all privilege
                user="nobody",
                privileged=False,
                cap_drop=["ALL"],
                # SECURITY: read-only root fs; /tmp is the only writable location
                read_only=True,
                tmpfs={"/tmp": "size=100M"},
                # Code mounted read-only so the guest cannot modify it
                volumes={temp_dir: {"bind": "/code", "mode": "ro"}},
                detach=True,
                remove=False,
            )

            wait_result = container.wait(timeout=timeout)
            exit_code: int = wait_result["StatusCode"]
            output = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
            success = exit_code == 0

            return {
                "success": success,
                "output": output,
                "error": None if success else f"Process exited with code {exit_code}",
                "exit_code": exit_code,
            }

        except docker.errors.ImageNotFound:
            logger.error("Docker image %s not found. Run: docker pull %s", _IMAGE, _IMAGE)
            return {
                "success": False,
                "output": "",
                "error": f"Image {_IMAGE} not found locally. Run: docker pull {_IMAGE}",
                "exit_code": -1,
            }

        except docker.errors.APIError as exc:
            logger.error("Docker API error during execution: %s", exc)
            return {
                "success": False,
                "output": "",
                "error": "Execution environment error — Docker API failure.",
                "exit_code": -1,
            }

        except (ReadTimeout, RequestsConnectionError) as exc:
            logger.warning("Container execution timed out after %ds: %s", timeout, exc)
            return {
                "success": False,
                "output": "",
                "error": f"Timeout — execution exceeded {timeout} seconds.",
                "exit_code": -1,
            }

        except Exception as exc:
            logger.error("Unexpected error during code execution: %s", exc, exc_info=True)
            return {
                "success": False,
                "output": "",
                "error": "Unexpected execution error.",
                "exit_code": -1,
            }

        finally:
            if container is not None:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
            if temp_file and os.path.exists(temp_file):
                os.unlink(temp_file)


def _write_temp_file(code: str) -> str:
    """Write code to a temporary file and return its absolute path."""
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".py",
        delete=False,
        encoding="utf-8",
    ) as f:
        f.write(code)
        return f.name

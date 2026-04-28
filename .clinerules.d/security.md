# Security Standards

## 🔐 Security First Principles

**CRITICAL: Every feature must be secure by default, not secure by configuration.**

### Core Rules (NEVER VIOLATE)

1. **Never trust user input** - Validate everything
2. **Principle of least privilege** - Minimum permissions always
3. **Defense in depth** - Multiple security layers
4. **Fail securely** - Errors must not leak sensitive data
5. **Audit everything** - Log all security-relevant events

---

## 🛡️ Code Execution Sandbox (CRITICAL)

```python
# File: packages/agent-core/core/executor.py

import docker
from typing import Dict, Any

class CodeExecutor:
    """
    SECURITY CRITICAL: This executes untrusted user code.
    
    Security layers:
    1. Docker container isolation
    2. Network disabled
    3. Resource limits (CPU, RAM)
    4. Read-only filesystem
    5. Non-root user
    6. Timeout enforcement
    """
    
    def __init__(self):
        self.client = docker.from_env()
        
        # Security configuration
        self.MAX_RAM_MB = 256
        self.MAX_CPU_PERCENT = 50
        self.TIMEOUT_SECONDS = 30
    
    async def run_python(
        self,
        code: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute Python code in isolated container.
        
        SECURITY CHECKLIST:
        ✅ Network disabled
        ✅ RAM limited to 256MB
        ✅ CPU limited to 50%
        ✅ Timeout enforced
        ✅ Non-root user
        ✅ Read-only filesystem
        ✅ No privileged mode
        
        Args:
            code: Python code to execute (UNTRUSTED)
            timeout: Max execution time in seconds
            
        Returns:
            {"success": bool, "output": str, "error": str}
        """
        try:
            # Create temp file with code
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute in Docker (SECURE)
            container = self.client.containers.run(
                "python:3.12-slim",
                command=f"python {os.path.basename(temp_file)}",
                
                # SECURITY: No network access
                network_disabled=True,
                
                # SECURITY: Resource limits
                mem_limit=f"{self.MAX_RAM_MB}m",
                cpu_quota=self.MAX_CPU_PERCENT * 1000,
                
                # SECURITY: Non-root user
                user="nobody",
                
                # SECURITY: Read-only filesystem
                read_only=True,
                tmpfs={'/tmp': 'size=100M'},  # Only /tmp is writable
                
                # SECURITY: No privileged access
                privileged=False,
                cap_drop=["ALL"],  # Drop all Linux capabilities
                
                # Execution settings
                detach=False,
                remove=True,  # Auto-cleanup
                timeout=timeout,
                
                # Volume mount (read-only)
                volumes={
                    os.path.dirname(temp_file): {
                        'bind': '/code',
                        'mode': 'ro'  # Read-only
                    }
                }
            )
            
            return {
                "success": True,
                "output": container.decode('utf-8'),
                "error": None
            }
            
        except docker.errors.ContainerError as e:
            # Code execution failed
            return {
                "success": False,
                "output": None,
                "error": str(e)
            }
            
        except docker.errors.APIError as e:
            # Docker API error
            logger.error(f"Docker API error: {e}")
            return {
                "success": False,
                "output": None,
                "error": "Execution environment error"
            }
            
        finally:
            # SECURITY: Always cleanup
            if os.path.exists(temp_file):
                os.unlink(temp_file)
```

### Additional Sandbox Security

```python
# Dockerfile for execution environment
FROM python:3.12-slim

# SECURITY: Create non-root user
RUN useradd -m -u 1000 agent && \
    chown -R agent:agent /home/agent

# SECURITY: Install only what's needed (minimal attack surface)
RUN pip install --no-cache-dir \
    pytest==8.0.0 \
    requests==2.31.0

# SECURITY: Switch to non-root user
USER agent

WORKDIR /home/agent

# SECURITY: No shell access
CMD ["python"]
```

---

## 🔑 API Key Management

```python
# ❌ NEVER DO THIS
api_key = "sk-ant-1234567890"  # Hardcoded
print(f"Using key: {api_key}")  # Logged

# ✅ ALWAYS DO THIS
import os
from typing import Optional

def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key from environment.
    
    SECURITY: Never log the actual key value.
    """
    key = os.getenv(f"{provider.upper()}_API_KEY")
    
    if not key:
        logger.warning(f"Missing API key for {provider}")
        return None
    
    # SECURITY: Log only that key exists, not the value
    logger.info(f"API key found for {provider}")
    
    return key

# Usage
anthropic_key = get_api_key("anthropic")
if not anthropic_key:
    raise ValueError("ANTHROPIC_API_KEY not set")

client = Anthropic(api_key=anthropic_key)
```

### Environment Variable Security

```bash
# .env (NEVER commit this file)
ANTHROPIC_API_KEY=sk-ant-***
GOOGLE_API_KEY=***
OPENAI_API_KEY=sk-***

# Database passwords
DATABASE_URL=postgresql://user:SECURE_PASSWORD@host:5432/db

# JWT secrets (generate with: openssl rand -hex 32)
JWT_SECRET=a1b2c3d4e5f6...

# GitHub tokens
GITHUB_TOKEN=ghp_***
```

```python
# Loading environment variables
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application settings from environment.
    
    SECURITY: Pydantic validates and type-checks all values.
    """
    anthropic_api_key: str
    google_api_key: str
    database_url: str
    jwt_secret: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # SECURITY: Don't expose secrets in error messages
        case_sensitive = True

# Usage
settings = Settings()

# SECURITY: Never print settings
# print(settings)  # ❌ Would expose secrets
```

---

## 🔒 Authentication & Authorization

```python
from fastapi import Depends, HTTPException, Header
from supabase import Client
import jwt

# JWT verification
async def verify_token(authorization: str = Header(...)) -> Dict[str, Any]:
    """
    Verify JWT token from Authorization header.
    
    SECURITY: Validates token signature and expiration.
    
    Args:
        authorization: "Bearer <token>"
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Extract token
        scheme, token = authorization.split(" ")
        
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme"
            )
        
        # Verify JWT
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"]
        )
        
        # Check expiration
        if payload.get("exp", 0) < time.time():
            raise HTTPException(
                status_code=401,
                detail="Token expired"
            )
        
        return payload
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )

# Protected endpoint
@app.get("/tasks")
async def get_tasks(user: Dict = Depends(verify_token)):
    """
    Get user's tasks.
    
    SECURITY: Only returns tasks owned by authenticated user.
    """
    user_id = user["sub"]
    
    # SECURITY: Row-level security via user_id filter
    tasks = await supabase.table("tasks")\
        .select("*")\
        .eq("user_id", user_id)\
        .execute()
    
    return tasks.data
```

### Row-Level Security (Supabase)

```sql
-- SECURITY: Enable RLS on all tables
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_artifacts ENABLE ROW LEVEL SECURITY;

-- SECURITY: Users can only see their own tasks
CREATE POLICY "Users see own tasks"
ON tasks
FOR SELECT
USING (auth.uid() = user_id);

-- SECURITY: Users can only insert their own tasks
CREATE POLICY "Users insert own tasks"
ON tasks
FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- SECURITY: Users can only update their own tasks
CREATE POLICY "Users update own tasks"
ON tasks
FOR UPDATE
USING (auth.uid() = user_id);

-- SECURITY: Users can only delete their own tasks
CREATE POLICY "Users delete own tasks"
ON tasks
FOR DELETE
USING (auth.uid() = user_id);
```

---

## 🛡️ Input Validation

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
import re

class GenerateRequest(BaseModel):
    """
    Code generation request.
    
    SECURITY: All inputs validated before processing.
    """
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=5000,  # SECURITY: Prevent abuse
        description="Task description"
    )
    
    language: str = Field(
        default="python",
        pattern="^(python|typescript|javascript|rust|go)$"  # SECURITY: Whitelist
    )
    
    timeout: Optional[int] = Field(
        default=30,
        ge=1,  # SECURITY: Minimum 1 second
        le=300  # SECURITY: Maximum 5 minutes
    )
    
    @validator("prompt")
    def validate_prompt(cls, v):
        """
        SECURITY: Sanitize prompt.
        
        - Block SQL injection attempts
        - Block command injection attempts
        - Block XXE attacks
        """
        # Check for suspicious patterns
        dangerous_patterns = [
            r"<\?xml",  # XML injection
            r"<!DOCTYPE",  # XXE
            r"UNION\s+SELECT",  # SQL injection
            r"\$\(.*\)",  # Command substitution
            r"`.*`",  # Backtick execution
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Suspicious content detected")
        
        return v
    
    @validator("language")
    def validate_language(cls, v):
        """SECURITY: Only allow supported languages."""
        allowed = {"python", "typescript", "javascript", "rust", "go"}
        
        if v not in allowed:
            raise ValueError(f"Unsupported language: {v}")
        
        return v
```

### SQL Injection Prevention

```python
# ❌ NEVER concatenate SQL
user_id = request.user_id
query = f"SELECT * FROM users WHERE id = {user_id}"  # VULNERABLE

# ✅ ALWAYS use parameterization
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))

# ✅ With Supabase (safe by default)
result = await supabase.table("users")\
    .select("*")\
    .eq("id", user_id)\  # Parameterized automatically
    .execute()
```

---

## 🚫 Secrets in Logs

```python
import logging
import re

class SecureFormatter(logging.Formatter):
    """
    SECURITY: Redact secrets from log messages.
    """
    
    PATTERNS = [
        (re.compile(r'(sk-ant-)[a-zA-Z0-9]{20,}'), r'\1***'),  # Anthropic keys
        (re.compile(r'(ghp_)[a-zA-Z0-9]{20,}'), r'\1***'),  # GitHub tokens
        (re.compile(r'(Bearer\s+)[a-zA-Z0-9._-]+'), r'\1***'),  # JWT tokens
        (re.compile(r'(password["\s:=]+)[^"\s]+'), r'\1***'),  # Passwords
    ]
    
    def format(self, record):
        message = super().format(record)
        
        # Redact all patterns
        for pattern, replacement in self.PATTERNS:
            message = pattern.sub(replacement, message)
        
        return message

# Usage
handler = logging.StreamHandler()
handler.setFormatter(SecureFormatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger(__name__)
logger.addHandler(handler)

# Now safe to log
logger.info(f"Using API key: {api_key}")  # Logged as "Using API key: sk-ant-***"
```

---

## 🔐 HTTPS & TLS

```python
# FastAPI HTTPS redirect middleware
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    SECURITY: Redirect HTTP to HTTPS in production.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Only in production
        if settings.environment == "production":
            if request.url.scheme != "https":
                url = request.url.replace(scheme="https")
                return RedirectResponse(url, status_code=301)
        
        response = await call_next(request)
        
        # SECURITY: Add security headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        return response

app.add_middleware(HTTPSRedirectMiddleware)
```

---

## 🚨 Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply rate limits
@app.post("/generate")
@limiter.limit("10/minute")  # SECURITY: Max 10 requests per minute
async def generate(request: Request, data: GenerateRequest):
    """Rate limited endpoint."""
    pass

@app.get("/tasks")
@limiter.limit("100/minute")  # Higher limit for read operations
async def get_tasks(request: Request):
    """Get tasks."""
    pass
```

---

## 🔍 Security Scanning

### Pre-Commit Checks

```bash
# 1. Bandit (Python security linter)
bandit -r packages/agent-core -f json -o security-report.json

# Critical issues to fix:
# - Hardcoded passwords
# - SQL injection vulnerabilities
# - Command injection
# - Insecure temp file usage

# 2. Safety (dependency vulnerabilities)
safety check

# 3. Secrets scanning
gitleaks detect --source .

# 4. Docker image scanning
docker scan codeagent-api:latest
```

---

## 📋 Security Checklist

**Before deploying to production:**

- [ ] All API keys in environment variables (not code)
- [ ] Database has row-level security policies
- [ ] All endpoints have authentication
- [ ] Rate limiting configured
- [ ] HTTPS enforced (no HTTP)
- [ ] Security headers added
- [ ] Docker containers run as non-root
- [ ] Network disabled for code execution
- [ ] Resource limits on containers
- [ ] Logging doesn't expose secrets
- [ ] Input validation on all endpoints
- [ ] SQL queries use parameterization
- [ ] Bandit scan passes
- [ ] No hardcoded credentials
- [ ] CORS configured (not wildcard in production)

---

## 🚨 Incident Response

```python
# Security incident logging
async def log_security_event(
    event_type: str,
    details: Dict[str, Any],
    severity: str = "medium"
):
    """
    Log security-relevant events.
    
    Event types:
    - failed_auth: Failed authentication attempt
    - suspicious_input: Potentially malicious input detected
    - rate_limit_exceeded: User hitting rate limits
    - privilege_escalation: Unauthorized access attempt
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "source_ip": details.get("ip"),
        "user_id": details.get("user_id")
    }
    
    # Log to security channel
    logger.warning(json.dumps(log_entry))
    
    # Alert on critical events
    if severity == "critical":
        await send_alert_to_slack(log_entry)

# Usage
await log_security_event(
    event_type="failed_auth",
    details={"ip": "1.2.3.4", "attempts": 5},
    severity="high"
)
```

---

**REMEMBER: Security is not optional. Every violation of these rules is a potential breach.**
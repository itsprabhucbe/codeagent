# CodeAgent - System Architecture

## 🎯 Overview

CodeAgent is a microservices-based autonomous coding agent with three main components:
1. **Agent Core** (Python/FastAPI) - Brain of the system
2. **Web UI** (Next.js) - User interface
3. **Worker** (BullMQ) - Background job processor

---

## 🏗️ System Diagram

┌─────────────────────────────────────────────────────────┐
│                       USER                              │
└────────────┬────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│              WEB UI (Next.js 15)                        │
│  - Task submission form                                 │
│  - Real-time progress display (SSE)                     │
│  - Code preview (Monaco Editor)                         │
│  - Project management                                   │
└────────────┬────────────────────────────────────────────┘
│ HTTP/REST + WebSocket
▼
┌─────────────────────────────────────────────────────────┐
│           AGENT API (FastAPI/Python)                    │
│                                                         │
│  ┌─────────────────────────────────────────────┐       │
│  │  API Layer                                  │       │
│  │  - /generate (code generation)              │       │
│  │  - /tasks (CRUD operations)                 │       │
│  │  - /github (repo integration)               │       │
│  │  - /stream (SSE for real-time updates)      │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
│  ┌─────────────────────────────────────────────┐       │
│  │  LangGraph Agent Orchestrator               │       │
│  │                                             │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │       │
│  │  │ Planning │→ │  Coding  │→ │ Testing  │ │       │
│  │  │   Node   │  │   Node   │  │   Node   │ │       │
│  │  └──────────┘  └──────────┘  └──────────┘ │       │
│  │       ↓              ↓              ↓      │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │       │
│  │  │ Review   │  │ Debug    │  │ Commit   │ │       │
│  │  │  Node    │  │  Node    │  │  Node    │ │       │
│  │  └──────────┘  └──────────┘  └──────────┘ │       │
│  │                                             │       │
│  │  State Management: StateGraph              │       │
│  │  Self-Correction: Max 3 loops               │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
│  ┌─────────────────────────────────────────────┐       │
│  │  Model Router                               │       │
│  │  - Fast tasks → Gemini Flash                │       │
│  │  - Complex reasoning → Claude Sonnet 4      │       │
│  │  - Privacy mode → Ollama (local)            │       │
│  └─────────────────────────────────────────────┘       │
│                                                         │
└────────┬───────────────────────┬──────────────────┬────┘
│                       │                  │
▼                       ▼                  ▼
┌─────────────────┐    ┌──────────────────┐   ┌─────────────┐
│  Docker Sandbox │    │   GitHub API     │   │   Supabase  │
│                 │    │                  │   │             │
│ - Isolated env  │    │ - Clone repo     │   │ - Auth      │
│ - Network off   │    │ - Create branch  │   │ - Database  │
│ - RAM limit     │    │ - Commit         │   │ - Storage   │
│ - CPU limit     │    │ - Create PR      │   │ - Realtime  │
│ - Auto cleanup  │    │                  │   │             │
└─────────────────┘    └──────────────────┘   └─────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│              Background Worker (BullMQ)                 │
│                                                         │
│  - Long-running tasks (multi-file projects)            │
│  - Scheduled jobs (periodic testing)                   │
│  - Email notifications                                 │
│  - Project archiving                                   │
└─────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────┐
│                    Redis                                │
│  - Cache (LLM responses, 24h TTL)                      │
│  - Queue (BullMQ job storage)                          │
│  - Session store                                       │
└─────────────────────────────────────────────────────────┘
---

## 📊 Data Flow

### Code Generation Flow

User Input
└─→ Web UI: User types prompt "Create a REST API for todos"
API Request
└─→ POST /generate
Body: { prompt: "...", language: "python" }
Task Creation
└─→ Create task record in Supabase
Status: "pending" → "running"
Agent Orchestration (LangGraph)
┌─→ Planning Node
│   ├─ Analyze prompt
│   ├─ Break into steps
│   └─ Output: ["Create FastAPI app", "Add GET /todos", "Add POST /todos", ...]
│
├─→ Coding Node
│   ├─ Context: Plan + codebase (if exists)
│   ├─ LLM Call: Claude Sonnet 4
│   └─ Output: main.py content
│
├─→ Testing Node
│   ├─ Generate tests (pytest)
│   ├─ Execute in Docker
│   └─ Output: { passed: 5, failed: 0 }
│
├─→ Review Node
│   ├─ Check: Tests passed? Quality score > 8.0?
│   ├─ Decision:
│   │   ✅ Pass → Commit Node
│   │   ❌ Fail → Debug Node → Back to Coding (max 3 loops)
│   └─ Output: approval or retry
│
└─→ Commit Node
├─ Git add, commit, push
├─ Create PR on GitHub
└─ Output: PR URL
Response to User
└─→ SSE stream: Real-time updates at each node
Final: { code, pr_url, tests_passed: true }

---

## 🔄 Agent State Machine

```python
# LangGraph State Schema

class AgentState(TypedDict):
    """State passed between nodes"""
    
    # Input
    task_id: str
    prompt: str
    language: str
    repo_url: Optional[str]
    
    # Planning
    plan: List[str]
    
    # Coding
    code_files: Dict[str, str]  # filename -> content
    dependencies: List[str]
    
    # Testing
    test_code: str
    test_results: Dict[str, Any]
    
    # Review
    quality_score: float
    issues: List[str]
    iteration: int  # Self-correction counter
    
    # Output
    pr_url: Optional[str]
    error: Optional[str]
```

### State Transitions

START
↓
PLANNING (always executes)
↓
CODING (always executes)
↓
TESTING (always executes)
↓
REVIEW (conditional logic)
├─→ Tests passed + Quality > 8.0 → COMMIT → END
├─→ Tests failed + iteration < 3 → DEBUG → CODING (loop)
└─→ iteration >= 3 → FAIL → END (return error)

---

## 🗄️ Database Schema (Supabase/PostgreSQL)

```sql
-- Users (handled by Supabase Auth)

-- Projects
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  repo_url TEXT,
  tech_stack JSONB,  -- ["python", "fastapi"]
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks (individual agent executions)
CREATE TABLE tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects,
  user_id UUID REFERENCES auth.users NOT NULL,
  
  -- Input
  prompt TEXT NOT NULL,
  language TEXT NOT NULL,
  
  -- Status
  status TEXT NOT NULL,  -- 'pending', 'running', 'completed', 'failed'
  progress_percent INTEGER DEFAULT 0,
  current_step TEXT,
  
  -- Output
  code_files JSONB,  -- {filename: content}
  pr_url TEXT,
  error_message TEXT,
  
  -- Metrics
  tokens_used INTEGER,
  execution_time_ms INTEGER,
  quality_score FLOAT,
  
  -- LLM details
  model_used TEXT,
  iterations_count INTEGER DEFAULT 1,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

-- Code Artifacts (version history)
CREATE TABLE code_artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES tasks NOT NULL,
  file_path TEXT NOT NULL,
  content TEXT NOT NULL,
  language TEXT NOT NULL,
  quality_score FLOAT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Agent Conversations (audit trail)
CREATE TABLE conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id UUID REFERENCES tasks NOT NULL,
  role TEXT NOT NULL,  -- 'user', 'assistant', 'system'
  content TEXT NOT NULL,
  tokens_used INTEGER,
  model TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_tasks_user ON tasks(user_id, created_at DESC);
CREATE INDEX idx_tasks_status ON tasks(status, created_at DESC);
CREATE INDEX idx_projects_user ON projects(user_id, created_at DESC);
```

---

## 🔐 Security Architecture

### Defense in Depth

Layer 1: Network Security
├─ Docker network isolation (containers can't talk to internet)
├─ CORS (strict origin whitelisting)
└─ Rate limiting (100 req/min per IP)
Layer 2: Authentication & Authorization
├─ Supabase Auth (JWT tokens)
├─ Row-level security (RLS) on all tables
└─ API key rotation (30-day expiry)
Layer 3: Code Execution Sandbox
├─ Docker containers (isolated per task)
├─ No network access (network_disabled=true)
├─ Resource limits (256MB RAM, 50% CPU)
├─ Read-only filesystem (except /tmp)
├─ Non-root user
└─ Auto-cleanup after 30 seconds
Layer 4: Data Protection
├─ Encryption at rest (Supabase default)
├─ Encryption in transit (TLS 1.3)
├─ API keys in environment variables (never in code)
├─ No logging of user code content
└─ GDPR compliance (right to delete)
Layer 5: Input Validation
├─ Pydantic models (type validation)
├─ SQL parameterization (no SQL injection)
├─ File upload size limits (10MB max)
└─ Content sanitization

---

## ⚡ Performance Optimization

### Caching Strategy

```python
# Redis cache layers

# Layer 1: LLM Response Cache (24h TTL)
Key: f"llm:{hash(prompt)}:{model}"
Value: {"code": "...", "explanation": "..."}
Hit rate target: >60%

# Layer 2: GitHub Repo Metadata (1h TTL)
Key: f"gh:repo:{owner}/{name}"
Value: {"default_branch": "main", "languages": [...]}

# Layer 3: Code Quality Results (permanent)
Key: f"quality:{hash(code)}"
Value: {"pylint": 8.5, "mypy": "passed"}

# Layer 4: User Session (30min TTL)
Key: f"session:{user_id}"
Value: {"preferences": {...}, "api_keys": {...}}
```

### Database Query Optimization

```sql
-- Use materialized views for dashboards
CREATE MATERIALIZED VIEW user_stats AS
SELECT 
  user_id,
  COUNT(*) as total_tasks,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
  AVG(quality_score) as avg_quality,
  SUM(tokens_used) as total_tokens
FROM tasks
GROUP BY user_id;

-- Refresh every hour
REFRESH MATERIALIZED VIEW user_stats;
```

### API Response Time Targets

Health check: < 50ms (p95)
Code generation: < 5s (p95)
Task list: < 200ms (p95)
Real-time updates (SSE): < 100ms latency

---

## 📈 Scalability Plan

### Horizontal Scaling

Current (MVP):

1 API server
1 Worker process
1 Redis instance
1 PostgreSQL instance

Target: 10,000 concurrent users

10 API servers (load balanced)
20 Worker processes (BullMQ concurrency)
Redis cluster (3 nodes)
PostgreSQL read replicas (2)

Target: 100,000 concurrent users

100 API servers
200 Workers
Redis cluster (6 nodes)
PostgreSQL sharding

---

## 🔌 Integration Points

### External APIs

LLM Providers
├─ Anthropic (Claude)
├─ Google (Gemini)
├─ OpenAI (GPT-4)
└─ Ollama (local models)
GitHub API
├─ Repository operations
├─ Pull request creation
└─ Webhook listeners
Supabase
├─ Authentication
├─ Database
├─ Storage
└─ Realtime subscriptions
Monitoring
├─ Sentry (error tracking)
├─ Grafana (metrics)
└─ LogTail (log aggregation)

---

## 🧪 Testing Strategy

Unit Tests (70% coverage target)
└─ Test each function/class independently
Files: tests/test_*.py
Integration Tests (20% coverage)
└─ Test API endpoints with real database
Files: tests/integration/test_*.py
E2E Tests (10% coverage)
└─ Test full workflow: UI → API → Agent → PR
Files: tests/e2e/test_*.py
Load Tests
└─ Simulate 1000 concurrent users
Tool: Locust

---

## 🚀 Deployment Architecture

### Production Setup (Railway)

┌─────────────────────────────────────────┐
│         Cloudflare (CDN + DDoS)         │
└────────────┬────────────────────────────┘
│
▼
┌─────────────────────────────────────────┐
│      Railway Load Balancer              │
└────┬────────────────────────────────┬───┘
│                                │
▼                                ▼
┌──────────┐                    ┌──────────┐
│ API Pod 1│                    │ API Pod 2│
│ (Python) │                    │ (Python) │
└────┬─────┘                    └────┬─────┘
│                                │
└────────────┬───────────────────┘
▼
┌────────────────┐
│  Supabase DB   │
│  (PostgreSQL)  │
└────────────────┘
│
┌────────────────┐
│  Redis Cloud   │
│  (Managed)     │
└────────────────┘

### Environment Variables

```bash
# Production .env template
NODE_ENV=production
API_URL=https://api.codeagent.dev

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://user:pass@host:6379

# AI Providers
ANTHROPIC_API_KEY=sk-ant-***
GOOGLE_API_KEY=***
OPENAI_API_KEY=sk-***

# GitHub
GITHUB_TOKEN=ghp_***
GITHUB_WEBHOOK_SECRET=***

# Monitoring
SENTRY_DSN=https://***
```

---

## 📊 Monitoring & Observability

```python
# Key metrics to track

# Performance
- API latency (p50, p95, p99)
- LLM response time
- Database query time
- Cache hit rate

# Business
- Tasks created per day
- Completion rate
- Average quality score
- User retention (DAU/MAU)

# Infrastructure
- CPU/RAM usage
- Docker container count
- Queue depth (BullMQ)
- Error rate (5xx responses)

# Cost
- LLM API costs (by model)
- Database storage growth
- Bandwidth usage
```

---

## 🔄 CI/CD Pipeline

```yaml
# GitHub Actions workflow

on: [push]

jobs:
  test:
    - Run pytest (backend)
    - Run npm test (frontend)
    - Check coverage > 80%
    
  lint:
    - Pylint (Python)
    - ESLint (TypeScript)
    - MyPy strict mode
    
  security:
    - Bandit (Python security)
    - npm audit
    - Snyk scan
    
  deploy:
    if: branch == main
    - Build Docker images
    - Push to Railway
    - Run smoke tests
    - Rollback if failed
```

---

## 🎯 Architecture Decision Records (ADRs)

### ADR-001: Why LangGraph over LangChain?
**Decision:** Use LangGraph for agent orchestration  
**Rationale:** 
- Graph-based = easier debugging
- State management built-in
- Better for complex workflows with loops
- Production-ready (used by Anthropic internally)

### ADR-002: Why Supabase over AWS RDS?
**Decision:** Use Supabase for database + auth  
**Rationale:**
- Open source (can self-host later)
- Auth built-in (no need for separate service)
- Realtime subscriptions out of box
- Better DX than AWS

### ADR-003: Why Docker for code execution?
**Decision:** Sandbox all code in Docker containers  
**Rationale:**
- Security: isolated environment
- Consistency: same env for all languages
- Resource limits: prevent abuse
- Industry standard (Replit, CodeSandbox use this)

---

**This architecture is optimized for:**
- ✅ Speed (< 5s code generation)
- ✅ Security (multi-layer defense)
- ✅ Scalability (horizontal scaling ready)
- ✅ Cost efficiency (caching, model routing)
- ✅ Developer experience (clear separation of concerns)

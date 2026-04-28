# 🤖 CodeAgent - Open Source Autonomous Coding Agent

**The self-hostable alternative to Google Jules and Cursor.**

[![GitHub stars](https://img.shields.io/github/stars/yourusername/codeagent?style=social)](https://github.com/yourusername/codeagent)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()

> ⚠️ **Early Development**: This project is in active development. Star & watch for updates!

---

## 🎯 Why CodeAgent?

**Google Jules** and **Cursor** (recently valued at $60B by SpaceX) are amazing, but they have fundamental limitations:

❌ Closed source (black box algorithms)  
❌ Vendor lock-in (Google/Anthropic only)  
❌ Privacy concerns (your code on their servers)  
❌ Expensive ($20-125/month)

**CodeAgent solves this:**

✅ **100% Open Source** - Audit every line of code  
✅ **Self-Hostable** - Run on your infrastructure  
✅ **Multi-Model** - Use Claude, Gemini, GPT-4, or local models  
✅ **Privacy First** - Your code never leaves your servers  
✅ **Free Forever** - Self-host at zero cost

---

## 🚀 Features

### Current (MVP - Week 1)
- ✅ Autonomous code generation (Python, TypeScript)
- ✅ GitHub integration (clone, commit, create PR)
- ✅ Docker sandbox execution (secure, isolated)
- ✅ Multi-model support (Claude/Gemini/GPT-4)
- ✅ Real-time progress tracking
- ✅ Web UI (task submission + monitoring)

### Coming Soon (Week 2-4)
- 🚧 Self-correction loops (agent debugs its own code)
- 🚧 Test generation & execution
- 🚧 Multi-file project generation
- 🚧 Team collaboration features
- 🚧 VS Code extension
- 🚧 CLI tool

### Roadmap (Week 5-12)
- 📅 Advanced scheduling (cron-like automation)
- 📅 Plugin system (extend with custom tools)
- 📅 Enterprise features (SSO, audit logs)
- 📅 Mobile app

---

## 📦 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/codeagent.git
cd codeagent

# Copy environment file
cp .env.example .env

# Add your API keys to .env
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_API_KEY=...

# Start all services
docker-compose up -d

# Open in browser
# Web UI: http://localhost:3000
# API: http://localhost:8000/docs
```

### Option 2: Manual Setup

```bash
# Backend (Python)
cd packages/agent-core
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend (Node.js)
cd packages/web-ui
npm install
npm run dev
```

---

## 🎨 Screenshots

### Dashboard
![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Screenshot)

### Code Generation
![Code Generation](https://via.placeholder.com/800x400?text=Code+Generation+Screenshot)

### Real-time Progress
![Progress](https://via.placeholder.com/800x400?text=Progress+Screenshot)

---

## 🏗️ Architecture
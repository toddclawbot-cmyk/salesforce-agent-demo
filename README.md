# Genie — AI Agent Demo

> _"You won't bring your resume to a new job. You'll bring your agent."_

An AI agent built for a Salesforce Developer persona, demonstrating:
- **Reasoning** — chain-of-thought traces visible to the user
- **Memory** — Obsidian vault retrieval for personal context
- **Tools** — Salesforce REST API + web search
- **MCP architecture** — the foundation for portable agent identity

Built with **LangGraph** + **Flask** + **Claude Sonnet** (demo mode works without API key).

## Quick Start

```bash
cd salesforce-agent-demo
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://localhost:5051
```

## Architecture

```
┌─────────────────────────────────────┐
│     EMPLOYEE'S AGENT (Genie)        │  ← Personality, memory, skills
├─────────────────────────────────────┤
│     LANGGRAPH FRAMEWORK             │  ← Reasoning, state, routing
├─────────────────────────────────────┤
│     TOOL LAYER (MCP)               │  ← Vault, Salesforce, Web
├─────────────────────────────────────┤
│     COMPANY INFRASTRUCTURE          │  ← Salesforce, Slack, etc.
└─────────────────────────────────────┘
```

## Tools

| Tool | What it does |
|------|-------------|
| `search_vault` | Semantic search over Obsidian vault notes |
| `sf_query` | SOQL queries against Salesforce REST API |
| `sf_create_task` | Create follow-up tasks in Salesforce |
| `web_search` | DuckDuckGo real-time search |

## The Vision

The demo is anchored on the **headless organization** concept:

> In the future, every employee will have their own agent — with skills, personality, and memory that travel with them from job to job. Companies will expose their systems via MCP (Model Context Protocol), and your agent will plug right in on day one. You won't interview with a resume. You'll be judged on the strength of your agent.

## Salesforce Integration

To connect to a real Salesforce org:

```bash
export SF_INSTANCE_URL=https://yourorg.my.salesforce.com
export SF_ACCESS_TOKEN=your_oauth_access_token
python app.py
```

Without credentials, the agent runs in **demo mode** with realistic mock data.

## Built By

This agent was built by Todd Ghidaleson using **Chaz** (OpenClaw agent) — demonstrating that the builder already lives in the agentic enterprise era.

---

_Built at the intersection of storytelling and technical architecture — for the Principal Technical Architect interview at Salesforce._

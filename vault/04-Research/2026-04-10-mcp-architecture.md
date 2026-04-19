---
type: research
date: 2026-04-10
tags: [mcp, architecture, model-context-protocol, anthropic]
related: [[2026-04-15-agentforce-adoption]], [[2026-04-12-vault-kb-retrieval]], [[2026-04-18-sfdc-rest-api-notes]]
---

# MCP Architecture Deep Dive

## What is MCP?
Model Context Protocol (MCP) is an open standard developed by Anthropic that enables AI agents to connect to external tools and data sources using a standardized interface — analogous to USB-C for AI toolchains.

**Key insight:** MCP isn't just for Salesforce. It's a universal protocol. Any system can expose an MCP server and become "agent-compatible."

## MCP in the Salesforce Context
Salesforce's Headless 360 exposes 60+ MCP tools:
- Object CRUD (Account, Contact, Opportunity, Case, Lead, etc.)
- Workflow execution
- SOQL query execution
- Apex class invocation
- Flow triggering
- Permission analysis

## Architecture Pattern
```
┌──────────────┐     MCP      ┌─────────────────┐
│  AI Agent    │◄────────────►│  MCP Server     │
│  (Claude,    │   std JSON   │  (Salesforce,   │
│  GPT, etc.)  │              │   Slack, etc.)  │
└──────────────┘              └─────────────────┘
```

## Why This Matters for Our Org
If every employee has an agent, and every company exposes MCP servers, then the agent ecosystem becomes the new integration layer. No more "it doesn't connect to our system" — if you have an MCP server, any agent can work with you.

## Risks to Consider
- Security: agents accessing sensitive data via MCP
- Governance: audit trails for agent actions
- Lock-in: MCP is nascent, standards still evolving

## References
- Anthropic MCP docs: modelcontextprotocol.io
- Salesforce Headless 360 announcement at TDX 2026

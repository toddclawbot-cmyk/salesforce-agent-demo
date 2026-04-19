---
type: project
date: 2026-04-15
tags: [agentforce, mcp, headless-360, tdx2026]
related: [[2026-04-10-mcp-architecture]], [[2026-04-12-vault-kb-retrieval]], [[2026-04-18-sfdc-rest-api-notes]]
---

# Agentforce Adoption Project

## Overview
Lead the adoption of Salesforce Agentforce 2.0 across our enterprise org. This involves setting up MCP tools, configuring the VS Code IDE agent harness, and training the dev team on new patterns.

## Key Decisions Made
- **Default model:** Claude Sonnet 4.5 (can switch to GPT-5 per project)
- **MCP registry:** Self-hosted on internal infra, mirrors AgentExchange
- **Agent persona guidelines:** Every agent must have documented values, boundaries, and escalation paths

## Current Status
✅ Phase 1 complete (MCP server setup, dev org configured)
🔄 Phase 2 in progress (team training, prompt engineering standards)
⏳ Phase 3 planned (production org rollout, governance board)

## Open Questions
- How do we handle agent actions that span multiple clouds (Salesforce + Slack)?
- What's our rollback strategy if an agent goes off-policy?
- How do we measure ROI of agent adoption?

## Notes
See [[2026-04-18-sfdc-rest-api-notes]] for API details.
See [[2026-04-12-vault-kb-retrieval]] for retrieval architecture.

---
type: research
date: 2026-04-12
tags: [retrieval, vector, RAG, knowledge-base, obsidian]
related: [[2026-04-10-mcp-architecture]], [[2026-04-15-agentforce-adoption]], [[2026-04-18-sfdc-rest-api-notes]]
---

# Vault Knowledge Base & Retrieval Architecture

## Concept
Personal knowledge management system built on Obsidian, with an agent that can retrieve relevant context from my vault at query time.

## How It Works
1. User asks a question
2. Agent embeds the question (using OpenAI text-embedding-3-small or similar)
3. Semantic search over vault notes
4. Top-k results retrieved, injected into LLM context
5. LLM answers with full knowledge of my notes

## Vault Structure
```
vault/
  03-Projects/    — Active work projects
  04-Research/   — Technical deep dives
  05-Meetings/   — Meeting notes, 1:1s
  06-References/ — Quick references, cheatsheets
```

## Retrieval Config
- Embedding model: text-embedding-3-small
- Chunk size: 500 tokens (semantic boundaries)
- Overlap: 50 tokens
- Top-k: 5 most relevant notes
- Similarity threshold: 0.7

## Why This Matters for the Agent Demo
The agent isn't just a chatbot — it has *persistent memory* and *context* from my actual work life. When I ask it about an account, it can pull my notes. When I ask about a technical decision, it retrieves my research.

This is what "bring your agent to every job" means in practice.

## Next Steps
- Add more meeting notes from Q1 2026
- Integrate with Salesforce to auto-pull account context
- Build an "insights" feature that surfaces patterns across notes

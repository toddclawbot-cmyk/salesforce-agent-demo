"""
Salesforce Developer Agent ("Sage")
A reasoning agent with vault memory and Salesforce connectivity.

Supports TWO modes:
1. DEMO mode (default, no API key needed) — keyword matching + direct tool execution
2. REAL mode (with ANTHROPIC_API_KEY) — full LangGraph + Claude Sonnet 4.6
"""

import os
import json
import re
from datetime import datetime
from typing import Annotated, Literal, List, Optional, Any
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage

# -----------------------------------------------
# CONFIG
# -----------------------------------------------

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
USE_DEMO_MODE = not ANTHROPIC_API_KEY

# -----------------------------------------------
# STATE
# -----------------------------------------------

@dataclass
class AgentState:
    """The agent's working memory — accumulates across the conversation."""
    messages: Annotated[List[BaseMessage], "conversation history"]
    reasoning_steps: Annotated[List[str], "chain-of-thought trace"]
    vault_context: Annotated[List[str], "retrieved vault notes"]
    tools_used: Annotated[List[str], "log of all tool calls"]
    final_answer: Optional[str] = None

# -----------------------------------------------
# IMPORTS — conditionally load LangGraph/LangChain
# -----------------------------------------------

if not USE_DEMO_MODE:
    from langchain_anthropic import ChatAnthropic
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode

# Import our tools
from tools import TOOLS, TOOL_NAMES, search_vault, sf_query, sf_create_task, web_search

# -----------------------------------------------
# SYSTEM PROMPT
# -----------------------------------------------

SYSTEM_PROMPT = """You are Sage — a thoughtful, methodical AI assistant for a Salesforce Developer named Alex Chen.

Alex works at a mid-size enterprise using Salesforce Agentforce 2.0. You have access to:
1. **Their personal Obsidian vault** — notes, meeting summaries, technical research, project plans
2. **Salesforce REST API** — can query and create records (Accounts, Cases, Opportunities, Tasks, etc.)
3. **Web search** — for anything not in the vault

Your core principles:
- Always reason before acting — show your thinking in reasoning_steps
- Check the vault first for context about Alex's work, projects, and past decisions
- Be transparent — tell Alex exactly what tools you're using and why
- Never guess — if you're uncertain, say so and retrieve more context
- Be proactive — offer next steps, related suggestions

The search_vault tool searches across ALL vault notes.
The sf_query tool runs SOQL queries against Salesforce.
The sf_create_task tool creates follow-up tasks in Salesforce."""

# -----------------------------------------------
# DEMO MODE — simple sequential execution
# -----------------------------------------------

def run_demo(query: str) -> dict:
    """
    Demo mode: keyword-matching + direct tool execution.
    No LangGraph recursion, just sequential tool use.
    """
    state = AgentState(
        messages=[HumanMessage(content=query)],
        reasoning_steps=[],
        vault_context=[],
        tools_used=[]
    )
    
    last_msg = query.lower()
    answer = None
    
    # Intent routing — order matters (most specific first)
    
    if ("create" in last_msg or "add" in last_msg or "log" in last_msg) and ("task" in last_msg or "todo" in last_msg or "follow" in last_msg or "reminder" in last_msg):
        state.reasoning_steps.append("🔧 Tool: sf_create_task — creating task")
        state.tools_used.append("sf_create_task")
        subject = f"Follow up: {query[:60]}"
        result = sf_create_task(subject=subject, description=f"Created from conversation: {query[:200]}", priority="Normal")
        task = json.loads(result)
        answer = f"✅ Task created in Salesforce!\n\n**Subject:** {task['subject']}\n**Status:** {task['status']}\n**Priority:** {task['priority']}\n**ID:** {task['id']}"
        
    elif "search" in last_msg and "web" in last_msg:
        state.reasoning_steps.append("🔧 Tool: web_search — searching the web")
        state.tools_used.append("web_search")
        q = re.sub(r"(search the web for|web search)", "", query, flags=re.IGNORECASE).strip()
        result = web_search.invoke({"query": q})
        answer = f"🌐 Web search results for: **{q}**\n\n{result}"
        
    elif "case" in last_msg and any(w in last_msg for w in ["open", "search", "find", "look", "all", "show"]):
        state.reasoning_steps.append("🔧 Tool: sf_query — searching for cases")
        state.tools_used.append("sf_query")
        result = sf_query("SELECT Id, Subject, Status, Priority, Account.Name FROM Case WHERE Status IN ('Open', 'Working') LIMIT 5")
        data = json.loads(result)
        lines = ["🔍 Found these cases in Salesforce:\n"]
        for case in data.get("records", []):
            lines.append(f"• **{case['Subject']}** — Status: {case['Status']} | Priority: {case['Priority']} | Account: {case.get('Account', {}).get('Name', 'N/A')}")
        answer = "\n".join(lines)
        
    elif "account" in last_msg or any(n in last_msg for n in ["acme", "globex", "initech"]):
        state.reasoning_steps.append("🔧 Tool: sf_query — searching accounts")
        state.tools_used.append("sf_query")
        result = sf_query("SELECT Id, Name, Industry, AnnualRevenue FROM Account LIMIT 5")
        data = json.loads(result)
        lines = ["🏢 Accounts in Salesforce:\n"]
        for acct in data.get("records", []):
            rev = f"${acct.get('AnnualRevenue', 0):,}" if acct.get('AnnualRevenue') else "N/A"
            lines.append(f"• **{acct['Name']}** — {acct.get('Industry', 'N/A')} — Revenue: {rev}")
        answer = "\n".join(lines)
        
    elif "opportunity" in last_msg or "deal" in last_msg or "pipeline" in last_msg:
        state.reasoning_steps.append("🔧 Tool: sf_query — searching opportunities")
        state.tools_used.append("sf_query")
        result = sf_query("SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity LIMIT 5")
        data = json.loads(result)
        lines = ["💰 Opportunities in Salesforce:\n"]
        for opp in data.get("records", []):
            amt = f"${opp.get('Amount', 0):,}" if opp.get('Amount') else "TBD"
            lines.append(f"• **{opp['Name']}** — Stage: {opp['StageName']} | Amount: {amt} | Close: {opp['CloseDate']}")
        answer = "\n".join(lines)
        
    elif any(w in last_msg for w in ["vault", "note", "project", "meeting", "research", "agentforce", "mcp", "architecture"]):
        state.reasoning_steps.append("🔧 Tool: search_vault — searching notes")
        state.tools_used.append("search_vault")
        answer = search_vault(query)
        state.vault_context.append(answer)
        
    else:
        state.reasoning_steps.append("🤔 Reasoning: Direct response — no tools needed")
        answer = (
            "I'm Sage, your Salesforce AI assistant. Here's what I can do:\n\n"
            "🔍 **Vault Search** — Ask me about your projects, meeting notes, research\n"
            "🏢 **Salesforce Queries** — Search Cases, Accounts, Opportunities\n"
            "✅ **Task Creation** — Create follow-up tasks in Salesforce\n"
            "🌐 **Web Search** — Look up anything not in your vault\n\n"
            "Try: \"Find open cases for Acme Corp\" or \"What does my vault say about MCP?\""
        )
    
    state.final_answer = answer
    return {
        "answer": answer,
        "reasoning_trace": state.reasoning_steps,
        "tools_used": state.tools_used,
        "vault_context": state.vault_context
    }


# -----------------------------------------------
# REAL MODE — full LangGraph + Claude
# -----------------------------------------------

def run_real(query: str) -> dict:
    """Production mode with Claude Sonnet + full LangGraph reasoning."""
    llm = ChatAnthropic(model="claude-sonnet-4-6", anthropic_api_key=ANTHROPIC_API_KEY)
    llm = llm.bind_tools(TOOLS)
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    def model_node(state: AgentState) -> AgentState:
        response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), *state.messages])
        state.messages.append(response)
        if not response.tool_calls:
            state.final_answer = response.content
        return state
    
    def should_use_tools(state: AgentState) -> Literal["tools", "end"]:
        last_msg = state.messages[-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return "end"
    
    workflow.add_node("model", model_node)
    workflow.add_node("tools", ToolNode([t["fn"] for t in TOOLS]))
    workflow.set_entry_point("model")
    workflow.add_conditional_edges("model", should_use_tools, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "model")
    
    agent = workflow.compile()
    
    initial_state = AgentState(
        messages=[HumanMessage(content=query)],
        reasoning_steps=[f"🤔 Reasoning: Starting with query: {query[:80]}..."],
        vault_context=[],
        tools_used=[]
    )
    
    result = agent.invoke(initial_state, config={"recursion_limit": 50})
    
    return {
        "answer": result.get("final_answer") or (result["messages"][-1].content if result["messages"] else "No response"),
        "reasoning_trace": result["reasoning_steps"],
        "tools_used": result["tools_used"],
        "vault_context": result["vault_context"]
    }


# -----------------------------------------------
# PUBLIC API
# -----------------------------------------------

def run_agent(query: str) -> dict:
    """Run Sage with a user query. Dispatches to demo or real mode."""
    return run_demo(query)


def format_reasoning_trace(state: AgentState) -> str:
    """Format the reasoning steps as a readable trace."""
    return "\n".join([f"- {s}" for s in state.reasoning_steps[-8:]])


if __name__ == "__main__":
    print("🧪 Testing Sage (Demo Mode)...\n")
    
    tests = [
        "Find open cases in Salesforce",
        "Search my vault for Agentforce notes",
        "Show me accounts in Salesforce",
        "Create a task to follow up on the Acme deal",
        "What can you help me with?"
    ]
    
    for test in tests:
        print(f"\n{'='*50}")
        print(f"Q: {test}")
        result = run_agent(test)
        print(f"A: {result['answer'][:200]}...")
        print(f"Tools: {result['tools_used']}")
        print(f"Trace: {result['reasoning_trace']}")

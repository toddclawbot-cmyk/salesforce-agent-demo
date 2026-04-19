"""
Salesforce Developer Agent ("Genie") — Tool Definitions
LangGraph Agent with Vault Memory + Salesforce API + Web Search
"""

import os
import json
import re
from datetime import datetime
from typing import Annotated, List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.tools import WikipediaQueryRun, DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper

# -----------------------------------------------
# VAULT SEARCH TOOL
# -----------------------------------------------

VAULT_PATH = os.path.join(os.path.dirname(__file__), "vault")

def search_vault(query: str, top_k: int = 5) -> str:
    """
    Search the Obsidian vault for notes matching the query.
    Returns formatted markdown with relevant excerpts.
    """
    results = []
    query_terms = query.lower().split()
    
    for root, dirs, files in os.walk(VAULT_PATH):
        for filename in files:
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Simple keyword scoring
                content_lower = content.lower()
                score = sum(1 for term in query_terms if term in content_lower)
                
                if score > 0:
                    # Extract frontmatter
                    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                    frontmatter = frontmatter_match.group(1) if frontmatter_match else ""
                    
                    # Get relative path for display
                    rel_path = os.path.relpath(filepath, VAULT_PATH)
                    
                    # Find snippet around first match
                    lines = content.split('\n')
                    snippet_lines = []
                    in_content = False
                    for line in lines:
                        if line.startswith('---'):
                            in_content = True
                            continue
                        if in_content and any(term in line.lower() for term in query_terms):
                            snippet_lines.append(line.strip())
                        if len(snippet_lines) >= 3:
                            break
                    
                    snippet = '\n'.join(snippet_lines[:3]) if snippet_lines else content[:200] + "..."
                    
                    results.append({
                        "file": rel_path,
                        "score": score,
                        "snippet": snippet,
                        "frontmatter": frontmatter
                    })
            except Exception as e:
                continue
    
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:top_k]
    
    if not results:
        return "No vault results found."
    
    output = f"## 🔍 Vault Search: \"{query}\"\n\n"
    for i, r in enumerate(results, 1):
        output += f"**{i}. `{r['file']}`** (relevance: {r['score']})\n"
        output += f"> {r['snippet'][:200]}...\n\n"
    
    return output


def get_vault_note(filename: str) -> str:
    """Retrieve a specific vault note by filename."""
    # Find the file across all subdirectories
    for root, dirs, files in os.walk(VAULT_PATH):
        if filename in files:
            filepath = os.path.join(root, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            rel_path = os.path.relpath(filepath, VAULT_PATH)
            return f"## 📄 {rel_path}\n\n{content}"
    return f"Note '{filename}' not found in vault."


# -----------------------------------------------
# SALESFORCE TOOL (MOCK — real integration ready)
# -----------------------------------------------

SF_CONFIG = {
    "instance_url": os.environ.get("SF_INSTANCE_URL", "https://your-instance.salesforce.com"),
    "access_token": os.environ.get("SF_ACCESS_TOKEN", ""),
    "api_version": "v59.0"
}

def sf_query(soql: str) -> str:
    """
    Execute a SOQL query against Salesforce.
    Real integration: uses SF_REST_API env vars.
    Demo mode: returns mock data showing what real output would look like.
    """
    if not SF_CONFIG["access_token"]:
        # DEMO MODE — return realistic mock data
        return _sf_mock_query(soql)
    
    # REAL MODE — would call actual Salesforce REST API
    import requests
    headers = {
        "Authorization": f"Bearer {SF_CONFIG['access_token']}",
        "Content-Type": "application/json"
    }
    url = f"{SF_CONFIG['instance_url']}/services/data/{SF_CONFIG['api_version']}/query"
    params = {"q": soql}
    resp = requests.get(url, headers=headers, params=params)
    return json.dumps(resp.json(), indent=2)


def _sf_mock_query(soql: str) -> str:
    """Return realistic mock Salesforce data for demo purposes."""
    soql_lower = soql.lower()
    
    if "case" in soql_lower and "status" in soql_lower:
        return json.dumps({
            "totalSize": 3,
            "done": True,
            "records": [
                {"attributes": {"type": "Case", "url": "/services/data/v59.0/sobjects/Case/500Dn00000A3aY2IAJ"}, "Id": "500Dn00000A3aY2IAJ", "Subject": "Login issue for mobile app", "Status": "Open", "Priority": "High", "Account": {"Name": "Acme Corp"}},
                {"attributes": {"type": "Case", "url": "/services/data/v59.0/sobjects/Case/500Dn00000A3aY3IBK"}, "Id": "500Dn00000A3aY3IBK", "Subject": "API rate limit exceeded", "Status": "Working", "Priority": "Medium", "Account": {"Name": "Globex Industries"}},
                {"attributes": {"type": "Case", "url": "/services/data/v59.0/sobjects/Case/500Dn00000A3aY4ICL"}, "Id": "500Dn00000A3aY4ICL", "Subject": "Data export failing", "Status": "Open", "Priority": "Low", "Account": {"Name": "Initech"}},
            ]
        }, indent=2)
    elif "account" in soql_lower:
        return json.dumps({
            "totalSize": 2,
            "done": True,
            "records": [
                {"attributes": {"type": "Account", "url": "/services/data/v59.0/sobjects/Account/001Dn00000A2bX3IAZ"}, "Id": "001Dn00000A2bX3IAZ", "Name": "Acme Corp", "Industry": "Technology", "AnnualRevenue": 50000000},
                {"attributes": {"type": "Account", "url": "/services/data/v59.0/sobjects/Account/001Dn00000A2bX4IBA"}, "Id": "001Dn00000A2bX4IBA", "Name": "Globex Industries", "Industry": "Manufacturing", "AnnualRevenue": 120000000},
            ]
        }, indent=2)
    elif "opportunity" in soql_lower:
        return json.dumps({
            "totalSize": 2,
            "done": True,
            "records": [
                {"attributes": {"type": "Opportunity", "url": "/services/data/v59.0/sobjects/Opportunity/006Dn00000A3cY5ICA"}, "Id": "006Dn00000A3cY5ICA", "Name": "Acme Corp — Enterprise Deal", "StageName": "Proposal/Price Quote", "Amount": 150000, "CloseDate": "2026-05-15"},
                {"attributes": {"type": "Opportunity", "url": "/services/data/v59.0/sobjects/Opportunity/006Dn00000A3cY6IDA"}, "Id": "006Dn00000A3cY6IDA", "Name": "Globex — Platform Expansion", "StageName": "Negotiation/Review", "Amount": 85000, "CloseDate": "2026-04-30"},
            ]
        }, indent=2)
    else:
        return json.dumps({
            "totalSize": 0,
            "done": True,
            "records": []
        }, indent=2)


def sf_create_task(subject: str, description: str, priority: str = "Normal", what_id: str = None) -> str:
    """
    Create a Task in Salesforce.
    Real integration: uses SF_REST_API env vars.
    Demo mode: returns mock success response.
    """
    if not SF_CONFIG["access_token"]:
        task_id = f"00TDn00000{MOCK_ID_COUNTER.get_and_inc():08d}IAZ"
        return json.dumps({
            "id": task_id,
            "success": True,
            "errors": [],
            "subject": subject,
            "status": "Not Started",
            "priority": priority,
            "activityDate": (datetime.now().replace(hour=23, minute=59)).strftime("%Y-%m-%d"),
            "description": description,
            "whatId": what_id
        }, indent=2)
    
    import requests
    headers = {
        "Authorization": f"Bearer {SF_CONFIG['access_token']}",
        "Content-Type": "application/json"
    }
    url = f"{SF_CONFIG['instance_url']}/services/data/{SF_CONFIG['api_version']}/sobjects/Task"
    data = {"Subject": subject, "Description": description, "Priority": priority}
    if what_id:
        data["WhatId"] = what_id
    resp = requests.post(url, headers=headers, json=data)
    return json.dumps(resp.json(), indent=2)


# Simple mock counter for demo IDs
class MockCounter:
    def __init__(self):
        self.val = 1
    def get_and_inc(self):
        result = self.val
        self.val += 1
        return result

MOCK_ID_COUNTER = MockCounter()


# -----------------------------------------------
# WEB SEARCH TOOL
# -----------------------------------------------

web_search = DuckDuckGoSearchRun()

# -----------------------------------------------
# TOOLKIT REGISTRY
# -----------------------------------------------

TOOLS = [
    {
        "name": "search_vault",
        "description": "Search the Obsidian vault for notes matching a query. Use this to find project context, meeting notes, technical research, and reference materials.",
        "fn": search_vault,
        "params": {"query": "the search query"}
    },
    {
        "name": "get_vault_note", 
        "description": "Retrieve a specific vault note by its filename. Use when you know the exact filename you want.",
        "fn": get_vault_note,
        "params": {"filename": "e.g. 2026-04-15-agentforce-adoption.md"}
    },
    {
        "name": "sf_query",
        "description": "Execute a SOQL query against Salesforce to search for records (Accounts, Contacts, Cases, Opportunities, Leads, Tasks, etc.). Returns JSON with matching records.",
        "fn": sf_query,
        "params": {"soql": "e.g. SELECT Id, Subject, Status FROM Case WHERE Status = 'Open' LIMIT 5"}
    },
    {
        "name": "sf_create_task",
        "description": "Create a follow-up Task in Salesforce. Use when the user wants to log a to-do, reminder, or action item that should appear in Salesforce.",
        "fn": sf_create_task,
        "params": {
            "subject": "Task subject line",
            "description": "Task description/details",
            "priority": "High, Normal, or Low",
            "what_id": "Optional: Salesforce ID of related record (Account, Case, Opportunity)"
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for current information. Use for anything that requires up-to-date information not in the vault.",
        "fn": web_search,
        "params": {"query": "the search query"}
    }
]

TOOL_NAMES = [t["name"] for t in TOOLS]

print(f"✅ Loaded {len(TOOLS)} tools: {', '.join(TOOL_NAMES)}")

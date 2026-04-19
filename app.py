"""
Genie — Salesforce Developer Agent Demo
Flask web interface for demonstrating the agentic enterprise vision.
"""

import os
import json
import time
import threading
from datetime import datetime
from collections import deque
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
event_queue = deque(maxlen=100)  # Last 100 events

from agent import run_agent, format_reasoning_trace, AgentState, search_vault, sf_query, sf_create_task
from tools import TOOLS, TOOL_NAMES

app = Flask(__name__, template_folder="templates", static_folder="static")

# -----------------------------------------------
# ROUTES
# -----------------------------------------------

@app.route("/")
def index():
    """Main demo interface."""
    return render_template("index.html")

@app.route("/story")
def story():
    """The Genie origin story — Maya's journey."""
    return render_template("demo-story.html")

@app.route("/observer")
def observer():
    """Backend observer mode — live LangGraph reasoning visualization."""
    return render_template("observer.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """Process a message through Genie."""
    data = request.get_json()
    query = data.get("message", "")
    
    if not query:
        return jsonify({"error": "No message provided"}), 400
    
    start = time.time()
    
    # Emit request event
    def emit(etype, edata):
        event_queue.append({"type": etype, "data": edata, "timestamp": datetime.now().isoformat()})
    
    emit("request", {"query": query[:100]})
    
    # Determine intent by keyword matching (same logic as agent.py)
    q_lower = query.lower()
    if "case" in q_lower:
        intent = "sf_query_case"
        tool = "sf_query"
        emit("intent", {"intent": "Salesforce case search", "tool": tool})
        emit("node_active", {"node": "model"})
        emit("reasoning", {"step": f"Query: {query[:60]}"})
        emit("node_active", {"node": "tools"})
        emit("tool", {"tool": "sf_query", "params": {"soql": "SELECT Id, Subject, Status, Priority, Account.Name FROM Case WHERE Status IN ('Open', 'Working') LIMIT 5"}})
    elif "account" in q_lower or any(n in q_lower for n in ["acme", "globex", "initech"]):
        intent = "sf_query_account"
        tool = "sf_query"
        emit("intent", {"intent": "Salesforce account lookup", "tool": tool})
        emit("node_active", {"node": "model"})
        emit("reasoning", {"step": f"Query: {query[:60]}"})
        emit("node_active", {"node": "tools"})
        emit("tool", {"tool": "sf_query", "params": {"soql": "SELECT Id, Name, Industry, AnnualRevenue FROM Account LIMIT 5"}})
    elif ("create" in q_lower or "add" in q_lower) and ("task" in q_lower or "todo" in q_lower or "follow" in q_lower):
        intent = "sf_create_task"
        tool = "sf_create_task"
        emit("intent", {"intent": "Salesforce task creation", "tool": tool})
        emit("node_active", {"node": "model"})
        emit("node_active", {"node": "tools"})
        emit("tool", {"tool": "sf_create_task", "params": {"subject": query[:60], "priority": "Normal"}})
    elif any(w in q_lower for w in ["vault", "note", "project", "meeting", "research", "agentforce", "mcp"]):
        intent = "search_vault"
        tool = "search_vault"
        emit("intent", {"intent": "Vault semantic search", "tool": tool})
        emit("node_active", {"node": "model"})
        emit("node_active", {"node": "tools"})
        emit("tool", {"tool": "search_vault", "params": {"query": query}})
    elif "search" in q_lower and "web" in q_lower:
        intent = "web_search"
        tool = "web_search"
        emit("intent", {"intent": "Web search", "tool": tool})
        emit("node_active", {"node": "model"})
        emit("node_active", {"node": "tools"})
        emit("tool", {"tool": "web_search", "params": {"query": query}})
    else:
        intent = "direct_answer"
        tool = None
        emit("intent", {"intent": "General conversation", "tool": None})
        emit("node_active", {"node": "model"})
    
    result = run_agent(query)
    
    emit("response", {"answer": result["answer"][:200]})
    emit("node_active", {"node": "end"})
    
    latency_ms = int((time.time() - start) * 1000)
    emit("complete", {"steps": len(result["reasoning_trace"]) + 1, "tools_used": result["tools_used"], "latency_ms": latency_ms})
    
    return jsonify({
        "answer": result["answer"],
        "reasoning_trace": result["reasoning_trace"],
        "tools_used": result["tools_used"],
        "vault_context": result["vault_context"]
    })

@app.route("/api/tools", methods=["GET"])
def list_tools():
    """Return the agent's available tools."""
    return jsonify({
        "tools": [
            {"name": t["name"], "description": t["description"]} 
            for t in TOOLS
        ]
    })

@app.route("/api/vault/search", methods=["GET"])
def vault_search():
    """Direct vault search endpoint."""
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "No query provided"}), 400
    result = search_vault(query)
    return jsonify({"result": result})

@app.route("/api/sf/query", methods=["GET"])
def sf_query_endpoint():
    """Direct Salesforce SOQL query endpoint."""
    soql = request.args.get("q", "")
    if not soql:
        return jsonify({"error": "No SOQL query provided"}), 400
    result = sf_query(soql)
    try:
        return jsonify(json.loads(result))
    except:
        return jsonify({"raw": result})

@app.route("/api/sf/create_task", methods=["POST"])
def sf_create_task_endpoint():
    """Create a Salesforce task."""
    data = request.get_json()
    result = sf_create_task(
        subject=data.get("subject", ""),
        description=data.get("description", ""),
        priority=data.get("priority", "Normal"),
        what_id=data.get("what_id")
    )
    try:
        return jsonify(json.loads(result))
    except:
        return jsonify({"raw": result})

@app.route("/api/architecture", methods=["GET"])
def architecture():
    """Return the system architecture diagram data."""
    arch = {
        "title": "Genie — Portable AI Agent Architecture",
        "subtitle": "The employee brings their agent. The company provides the tools.",
        "layers": [
            {
                "name": "The Employee's Agent (Genie)",
                "color": "#6366f1",
                "components": [
                    {"name": "Memory", "desc": "Personal vault, preferences, history"},
                    {"name": "Reasoning", "desc": "Chain-of-thought, tool selection"},
                    {"name": "Personality", "desc": "Working style, values, boundaries"},
                    {"name": "Skills", "desc": "Capabilities, integrations learned"}
                ]
            },
            {
                "name": "The Agent Framework (LangGraph)",
                "color": "#8b5cf6",
                "components": [
                    {"name": "State Management", "desc": "Conversation context"},
                    {"name": "Tool Routing", "desc": "Conditional graph edges"},
                    {"name": "Memory Nodes", "desc": "Vault retrieval, long-term recall"},
                    {"name": "Reasoning Trace", "desc": "Visible thinking process"}
                ]
            },
            {
                "name": "Tool Layer (MCP — Model Context Protocol)",
                "color": "#06b6d4",
                "components": [
                    {"name": "Vault Tool", "desc": "Obsidian note retrieval"},
                    {"name": "Salesforce Tool", "desc": "SOQL, CRUD, Apex calls"},
                    {"name": "Web Search Tool", "desc": "Real-time information"},
                    {"name": "Task Tool", "desc": "Salesforce task creation"}
                ]
            },
            {
                "name": "Company Infrastructure",
                "color": "#10b981",
                "components": [
                    {"name": "Salesforce", "desc": "CRM, Cases, Accounts, Opps"},
                    {"name": "Slack", "desc": "Notifications, collaboration"},
                    {"name": "MCP Registry", "desc": "Company-specific tools"},
                    {"name": "Auth & Governance", "desc": "Security, audit, compliance"}
                ]
            }
        ],
        "vision": {
            "headline": "The Headless Organization",
            "points": [
                "Employees will bring their agent — not their resume",
                "Companies will compete on how well they connect to your agent",
                "Your knowledge, context, and preferences travel with you",
                "MCP is the USB-C of the AI era"
            ]
        }
    }
    return jsonify(arch)

@app.route("/api/events/stream")
def event_stream():
    """SSE stream of agent events for observer mode."""
    def generate():
        # Send initial ping
        yield "event: ping\ndata: {}\n\n"
        last_idx = 0
        while True:
            # Check for new events
            while len(event_queue) > last_idx:
                evt = event_queue[last_idx]
                last_idx += 1
                yield f"event: message\ndata: {json.dumps(evt)}\n\n"
            # Keep connection alive with periodic comment
            yield ": ping\n\n"
            time.sleep(0.5)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        }
    )

@app.route("/api/events/recent")
def event_recent():
    """Return recent events for polling fallback."""
    return jsonify(list(event_queue))

# -----------------------------------------------
# TEMPLATES
# -----------------------------------------------

# Create the templates directory
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Write the HTML template
INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Genie — AI Agent Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        :root {
            --bg-primary: #0f0f14;
            --bg-secondary: #1a1a24;
            --bg-tertiary: #24243a;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.3);
            --cyan: #06b6d4;
            --green: #10b981;
            --purple: #8b5cf6;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border: rgba(255,255,255,0.08);
        }
        
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }
        
        /* Animated background */
        .bg-grid {
            position: fixed;
            inset: 0;
            background-image: 
                linear-gradient(rgba(99,102,241,0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99,102,241,0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
            z-index: 0;
        }
        
        .container {
            max-width: 1100px;
            margin: 0 auto;
            padding: 40px 24px;
            position: relative;
            z-index: 1;
        }
        
        /* Header */
        header {
            text-align: center;
            margin-bottom: 48px;
        }
        
        .logo {
            display: inline-flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
        }
        
        .logo-icon {
            width: 56px;
            height: 56px;
            background: linear-gradient(135deg, var(--accent), var(--purple));
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            box-shadow: 0 0 40px var(--accent-glow);
        }
        
        .logo-text {
            font-size: 42px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--text-primary), var(--accent));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -1px;
        }
        
        .tagline {
            color: var(--text-secondary);
            font-size: 18px;
            font-weight: 400;
            margin-bottom: 8px;
        }
        
        .subtitle {
            color: var(--text-muted);
            font-size: 14px;
        }
        
        /* Vision Banner */
        .vision-banner {
            background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1));
            border: 1px solid var(--accent);
            border-radius: 20px;
            padding: 28px 32px;
            margin-bottom: 36px;
            text-align: center;
        }
        
        .vision-banner h2 {
            font-size: 20px;
            font-weight: 600;
            color: var(--accent);
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }
        
        .vision-banner p {
            color: var(--text-secondary);
            font-size: 15px;
            line-height: 1.7;
            max-width: 700px;
            margin: 0 auto;
        }
        
        /* Main Grid */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            margin-bottom: 32px;
        }
        
        @media (max-width: 768px) {
            .main-grid { grid-template-columns: 1fr; }
        }
        
        /* Panel */
        .panel {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 20px;
            overflow: hidden;
        }
        
        .panel-header {
            padding: 18px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .panel-icon {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }
        
        .panel-title {
            font-size: 15px;
            font-weight: 600;
        }
        
        /* Chat Panel */
        .chat-panel { grid-column: span 2; }
        
        @media (max-width: 768px) {
            .chat-panel { grid-column: span 1; }
        }
        
        .chat-messages {
            padding: 24px;
            height: 380px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .chat-messages::-webkit-scrollbar { width: 6px; }
        .chat-messages::-webkit-scrollbar-track { background: transparent; }
        .chat-messages::-webkit-scrollbar-thumb { background: var(--bg-tertiary); border-radius: 3px; }
        
        .genie {
            max-width: 85%;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .genie.user { align-self: flex-end; }
        .genie.genie { align-self: flex-start; }
        
        .genie-bubble {
            padding: 14px 18px;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.6;
        }
        
        .genie.user .genie-bubble {
            background: var(--accent);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .genie.genie .genie-bubble {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-bottom-left-radius: 4px;
        }
        
        .genie.genie .genie-bubble code {
            background: rgba(99,102,241,0.2);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
        }
        
        .genie.genie .genie-bubble strong {
            color: var(--cyan);
        }
        
        .genie.genie .genie-bubble em {
            color: var(--text-secondary);
            font-style: italic;
        }
        
        /* Thinking trace */
        .thinking-section {
            background: var(--bg-tertiary);
            border-top: 1px solid var(--border);
            padding: 18px 24px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--text-muted);
            max-height: 180px;
            overflow-y: auto;
        }
        
        .thinking-section::-webkit-scrollbar { width: 4px; }
        .thinking-section::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 2px; }
        
        .thinking-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
            color: var(--purple);
            font-weight: 500;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .thinking-step {
            padding: 4px 0;
            border-bottom: 1px solid var(--border);
        }
        
        .thinking-step:last-child { border-bottom: none; }
        
        /* Chat Input */
        .chat-input-area {
            padding: 18px 24px;
            border-top: 1px solid var(--border);
            display: flex;
            gap: 12px;
        }
        
        .chat-input {
            flex: 1;
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 12px 16px;
            color: var(--text-primary);
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
        }
        
        .chat-input:focus { border-color: var(--accent); }
        .chat-input::placeholder { color: var(--text-muted); }
        
        .send-btn {
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .send-btn:hover { background: var(--purple); transform: translateY(-1px); }
        .send-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        /* Tools Panel */
        .tools-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            padding: 20px;
        }
        
        .tool-card {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .tool-card:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
        }
        
        .tool-card.active {
            border-color: var(--green);
            background: rgba(16, 185, 129, 0.1);
        }
        
        .tool-name {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
            font-family: 'JetBrains Mono', monospace;
        }
        
        .tool-desc {
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.5;
        }
        
        /* Quick Actions */
        .quick-actions {
            padding: 16px 20px;
            border-top: 1px solid var(--border);
        }
        
        .quick-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 10px;
        }
        
        .quick-btns {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .quick-btn {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 12px;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .quick-btn:hover {
            border-color: var(--accent);
            color: var(--text-primary);
        }
        
        /* Loading */
        .loading {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: var(--text-muted);
            font-size: 14px;
        }
        
        .loading-dots {
            display: flex;
            gap: 4px;
        }
        
        .loading-dots span {
            width: 6px;
            height: 6px;
            background: var(--accent);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        /* Architecture Diagram */
        .arch-diagram {
            padding: 20px;
        }
        
        .arch-layer {
            margin-bottom: 16px;
        }
        
        .arch-layer-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .arch-layer-color {
            width: 12px;
            height: 12px;
            border-radius: 4px;
        }
        
        .arch-layer-name {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .arch-components {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding-left: 22px;
        }
        
        .arch-comp {
            background: var(--bg-tertiary);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 12px;
        }
        
        .arch-comp-name {
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 2px;
        }
        
        .arch-comp-desc {
            color: var(--text-muted);
            font-size: 11px;
        }
        
        /* Footer */
        footer {
            text-align: center;
            padding: 24px;
            color: var(--text-muted);
            font-size: 12px;
            border-top: 1px solid var(--border);
            margin-top: 16px;
        }
        
        footer a { color: var(--accent); text-decoration: none; }
    </style>
</head>
<body>
    <div class="bg-grid"></div>
    
    <div class="container">
        <header>
            <div class="logo">
                <div class="logo-icon">🧙</div>
                <div class="logo-text">Genie</div>
            </div>
            <p class="tagline">Your AI Agent for the Agentic Enterprise</p>
            <p class="subtitle">Built with LangGraph • Connected to Salesforce • Powered by Claude</p>
        </header>
        
        <div class="vision-banner">
            <h2>🌐 The Vision: Portable AI Agents</h2>
            <p>
                In the future, <strong>you won't bring your resume to a new job — you'll bring your agent</strong>. 
                Your agent carries your knowledge, context, working style, and memory. 
                Companies will expose their systems via MCP (Model Context Protocol), 
                and your agent will plug right in — ready to work on day one.
            </p>
        </div>
        
        <div class="main-grid">
            <!-- Chat Panel -->
            <div class="panel chat-panel">
                <div class="panel-header">
                    <div class="panel-icon" style="background: rgba(99,102,241,0.2);">💬</div>
                    <div class="panel-title">Chat with Genie</div>
                </div>
                
                <div class="chat-messages" id="chatGenies">
                    <div class="genie genie">
                        <div class="genie-bubble">
                            Hello! I'm <strong>Genie</strong>, your Salesforce development agent. 🧙‍♂️<br><br>
                            I have access to your Obsidian vault, Salesforce data, and web search. Try asking me about:<br><br>
                            • <code>Search for open cases in Salesforce</code><br>
                            • <code>What does my vault say about Agentforce?</code><br>
                            • <code>Create a follow-up task for the Acme account</code>
                        </div>
                    </div>
                </div>
                
                <div class="thinking-section" id="thinkingSection" style="display: none;">
                    <div class="thinking-header">🧠 Reasoning Trace</div>
                    <div id="thinkingSteps"></div>
                </div>
                
                <div class="chat-input-area">
                    <input type="text" class="chat-input" id="chatInput" placeholder="Ask Genie anything..." onkeypress="handleKeyPress(event)">
                    <button class="send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
                </div>
            </div>
            
            <!-- Tools Panel -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-icon" style="background: rgba(6,182,212,0.2);">🔧</div>
                    <div class="panel-title">Available Tools</div>
                </div>
                <div class="tools-grid" id="toolsGrid">
                    <div class="tool-card" onclick="insertQuery('search vault for ')">
                        <div class="tool-name">search_vault</div>
                        <div class="tool-desc">Find notes from Obsidian vault</div>
                    </div>
                    <div class="tool-card" onclick="insertQuery('query salesforce for ')">
                        <div class="tool-name">sf_query</div>
                        <div class="tool-desc">SOQL query Salesforce</div>
                    </div>
                    <div class="tool-card" onclick="insertQuery('create task in salesforce ')">
                        <div class="tool-name">sf_create_task</div>
                        <div class="tool-desc">Create a follow-up task</div>
                    </div>
                    <div class="tool-card" onclick="insertQuery('search the web for ')">
                        <div class="tool-name">web_search</div>
                        <div class="tool-desc">Search the internet</div>
                    </div>
                </div>
                
                <div class="quick-actions">
                    <div class="quick-label">Quick Actions</div>
                    <div class="quick-btns">
                        <button class="quick-btn" onclick="sendPreset('Find open cases for Acme Corp')">🔍 Open Cases</button>
                        <button class="quick-btn" onclick="sendPreset('Search my vault for Agentforce notes')">📚 Agentforce</button>
                        <button class="quick-btn" onclick="sendPreset('Show me accounts in Salesforce')">🏢 Accounts</button>
                        <button class="quick-btn" onclick="sendPreset('Create a task to follow up on the Acme deal')">✅ Task</button>
                    </div>
                </div>
            </div>
            
            <!-- Architecture Panel -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-icon" style="background: rgba(139,92,246,0.2);">🏗️</div>
                    <div class="panel-title">Architecture</div>
                </div>
                <div class="arch-diagram" id="archDiagram">
                    <!-- Loaded dynamically -->
                    <div class="loading">
                        <div class="loading-dots"><span></span><span></span><span></span></div>
                        Loading architecture...
                    </div>
                </div>
            </div>
        </div>
        
        <footer>
            Built with ❤️ using LangGraph, Flask, and Claude &nbsp;|&nbsp; 
            <a href="https://github.com/toddclawbot/salesforce-agent-demo">View on GitHub</a>
        </footer>
    </div>
    
    <script>
        // Load architecture diagram
        fetch('/api/architecture')
            .then(r => r.json())
            .then(data => {
                const container = document.getElementById('archDiagram');
                let html = '';
                data.layers.forEach(layer => {
                    html += `<div class="arch-layer">
                        <div class="arch-layer-header">
                            <div class="arch-layer-color" style="background: ${layer.color}"></div>
                            <div class="arch-layer-name">${layer.name}</div>
                        </div>
                        <div class="arch-components">`;
                    layer.components.forEach(comp => {
                        html += `<div class="arch-comp">
                            <div class="arch-comp-name">${comp.name}</div>
                            <div class="arch-comp-desc">${comp.desc}</div>
                        </div>`;
                    });
                    html += '</div></div>';
                });
                container.innerHTML = html;
            });
        
        // Chat functionality
        let isLoading = false;
        
        async function sendMessage() {
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            if (!genie || isLoading) return;
            
            isLoading = true;
            document.getElementById('sendBtn').disabled = true;
            
            // Add user genie
            addGenie('user', genie);
            input.value = '';
            
            // Show loading
            const loadingDiv = addGenie('genie', '<div class="loading"><div class="loading-dots"><span></span><span></span><span></span></div> Thinking...</div>');
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ genie })
                });
                
                const data = await response.json();
                
                // Remove loading genie
                loadingDiv.remove();
                
                // Add response
                addGenie('genie', data.answer);
                
                // Show thinking trace
                if (data.reasoning_trace && data.reasoning_trace.length > 0) {
                    showThinking(data.reasoning_trace);
                }
                
                // Highlight used tools
                if (data.tools_used && data.tools_used.length > 0) {
                    data.tools_used.forEach(tool => {
                        const cards = document.querySelectorAll('.tool-card');
                        cards.forEach(card => {
                            if (card.querySelector('.tool-name').textContent === tool) {
                                card.classList.add('active');
                                setTimeout(() => card.classList.remove('active'), 2000);
                            }
                        });
                    });
                }
            } catch (err) {
                loadingDiv.remove();
                addGenie('genie', 'Sorry, I encountered an error. Please try again.');
            }
            
            isLoading = false;
            document.getElementById('sendBtn').disabled = false;
        }
        
        function addGenie(type, content) {
            const container = document.getElementById('chatGenies');
            const div = document.createElement('div');
            div.className = `genie ${type}`;
            div.innerHTML = `<div class="genie-bubble">${content}</div>`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            return div;
        }
        
        function showThinking(steps) {
            const section = document.getElementById('thinkingSection');
            const stepsDiv = document.getElementById('thinkingSteps');
            section.style.display = 'block';
            stepsDiv.innerHTML = steps.map(step => `<div class="thinking-step">${step}</div>`).join('');
        }
        
        function handleKeyPress(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        }
        
        function sendPreset(genie) {
            document.getElementById('chatInput').value = genie;
            sendMessage();
        }
        
        function insertQuery(text) {
            document.getElementById('chatInput').value = text;
            document.getElementById('chatInput').focus();
        }
    </script>
</body>
</html>
"""

with open("templates/index.html", "w") as f:
    f.write(INDEX_HTML)

# -----------------------------------------------
# STATIC ASSETS
# -----------------------------------------------

# Create a simple static folder placeholder
with open("static/robots.txt", "w") as f:
    f.write("User-agent: *\nDisallow:")

# -----------------------------------------------
# RUN
# -----------------------------------------------

if __name__ == "__main__":
    print("🚀 Starting Genie — AI Agent Demo")
    print(f"📁 Vault path: {os.path.join(os.path.dirname(__file__), 'vault')}")
    print(f"🔧 Tools loaded: {', '.join(TOOL_NAMES)}")
    print("🌐 Open http://localhost:5051 in your browser")
    app.run(host="0.0.0.0", port=5051, debug=True)

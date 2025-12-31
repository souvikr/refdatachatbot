# Agentic Reference Data Chatbot

A sophisticated **Model Context Protocol (MCP)** agent designed for financial reference data. It uses large language models (LLMs) to answer queries about bonds, issuers, and credit ratings by dynamically querying a local SQLite database.

## 🚀 Features

- **Agentic Workflow**: Powered by **LangGraph** (ReAct architecture) to reason through complex queries.
- **MCP Integration**: Connects to a local MCP server (`server.py`) using `fastmcp` to securely access data.
- **Intent Guardrails**: Pre-validates user queries using an LLM to ensure they are relevant to finance/reference data.
- **Streaming UI**: **Gradio** interface that streams the agent's "thought process" (tool calls, arguments, and validation) in real-time.
- **Smart Search**: Supports lookup by both **Legal Name** and **LEI** (Legal Entity Identifier).

## 🛠️ Technology Stack

- **Language**: Python 3.12+
- **Management**: `uv` (Fast Python package installer)
- **Frontend**: Gradio (Streaming Chat Interface)
- **Orchestration**: LangChain & LangGraph
- **Backend Protocol**: Model Context Protocol (MCP) via `fastmcp`
- **Database**: SQLite
- **LLM**: OpenAI GPT-4o

---

## 🏃‍♂️ Step-by-Step Setup Guide

### 1. Prerequisites
- **Git** installed.
- **Python 3.10+** installed.
- **uv** installed (`pip install uv`).
- **OpenAI API Key**.

### 2. Clone the Repository
```bash
git clone https://github.com/souvikr/refdatachatbot.git
cd refdatachatbot/bond-mcp-agent
```

### 3. Initialize Environment
The project uses `uv` for ultra-fast dependency management.

```bash
# Create virtual environment and install dependencies
uv sync
```

### 4. Configure Secrets
Create a `.env` file in the `bond-mcp-agent` directory:

```bash
OPENAI_API_KEY=sk-proj-your-key-here
```

### 5. Initialize the Database
Run the database script to create `finance.db` and seed it with sample data (Apple, US Treasury, etc.):

```bash
uv run python database.py
```

### 6. Run the Application
Start the Agent App. This functionality acts as both the client (UI) and the orchestration layer, which automatically spins up the MCP server subprocess.

```bash
uv run python agent_app.py
```

Open your browser at the URL shown (usually `http://127.0.0.1:7860`).

---

## 🔮 Future Scope: Production Ready Architecture

The current implementation is a robust **Proof of Concept (PoC)** optimized for rapid development and local demonstration. For a high-scale, enterprise-grade production system, we recommend the following evolution:

### Current vs. Future Stack

| Component | Current Implementation | Recommended Production Stack | Benefits |
| :--- | :--- | :--- | :--- |
| **Database** | SQLite (Local File) | **PostgreSQL + pgvector** | Concurrency, Row-level security, Vector similarity search for RAG. |
| **Backend API** | `fastmcp` (Subprocess) | **FastAPI Microservices** | Horizontal scaling, proper API documentation (OpenAPI), non-blocking async at scale. |
| **Protocol** | Stdio (Local Pipes) | **MCP over SSE/WebSocket** | Separation of concerns; Agent and Tools can run on different servers/clusters. |
| **Frontend** | Gradio | **Next.js / React** | Full UI customization, better state management, faster rendering, whitelabeling. |
| **Orchestration**| LangGraph (In-Memory) | **LangGraph Cloud / Postgres Checkpointer** | Persistent conversational state (resume sessions days later), fault tolerance. |
| **Intent Check** | GPT-4o Call | **Semantic Router / Fine-tuned SLM** | Reduced latency (100ms vs 1s+) and significantly lower cost. |
| **LLM** | GPT-4o | **Hybrid (GPT-4o + Llama 3)** | Route simple queries to cheaper/faster local models; complex reasoning to SOTA models. |

### Architectural Improvements

1.  **Decoupled Architecture**:
    *   Separate the **Agent Service** (reasoning engine) from the **Tool Service** (data access). This allows independent scaling. If data lookup is heavy, scale the Tool Service API without duplicating the expensive Agent reasoning instances.

2.  **Observability & Tracing**:
    *   Integrate **LangSmith** or **Arize Phoenix** to trace every step of the agent's thought process in production. This is critical for debugging "why did the agent hallucinate?" issues.

3.  **Deployment**:
    *   Containerize the Agent and Server separately using **Docker**.
    *   Deploy on **Kubernetes (K8s)** with an Ingress Controller managing traffic.

4.  **Advanced RAG**:
    *   Currently, the search is strict SQL. In production, implement **Hybrid Search** (Keyword + Semantic). This allows users to ask "bonds for renewable energy companies" and match against sector descriptions rather than exact string matches.

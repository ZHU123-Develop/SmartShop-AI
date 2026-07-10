# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartShop-AI is a multi-model AI e-commerce customer service chatbot built with Python Flask. It supports function calling, RAG knowledge base retrieval, and provides a ChatGPT-style responsive UI.

## Quick Start

```bash
pip install -r requirements.txt          # Core dependencies
pip install chromadb python-docx PyMuPDF pdfplumber  # RAG knowledge base (optional)
python app.py                            # Start dev server on :5000
```

Configure API credentials in `settings.json` or via the UI settings panel.

## Architecture

### Core Flow

```
app.py (Flask routes)
  └── ai_client.py (OpenAI SDK client, system prompt, tool calling loop, streaming)
        ├── tools/registry.py (tool registration & execution center)
        │     └── tools/*.py (individual tool handlers)
        └── rag/ (knowledge base)
              ├── vector_store.py (ChromaDB wrapper)
              └── document_processor.py (PDF/DOCX/TXT parsing + chunking)
```

### Key Modules

- **`app.py`** — Flask entry point. Handles all HTTP routes: chat (SSE streaming), sessions CRUD, settings management, file upload. Uses SQLite (`chatbot.db`) for session/message persistence. Manages `active_streams` dict for aborting generation.
- **`ai_client.py`** — AI API client layer. Builds system prompt (customer service persona + RAG context), manages tool calling loop (up to 5 iterations), and handles streaming output. Two-phase flow: non-streaming tool resolution first, then streaming final response.
- **`tools/registry.py`** — Central tool registry. Tools register via `register(name, description, parameters, handler)`. `get_all_tools()` returns function definitions for the LLM API; `execute_tool()` dispatches to handlers.
- **`tools/__init__.py`** — Auto-imports all tool modules to trigger registration on startup.
- **`rag/vector_store.py`** — ChromaDB persistent client wrapper. Collection: `ecommerce_kb` with cosine similarity. Methods: `add_documents`, `query`, `delete_by_source`, `count`.
- **`rag/document_processor.py`** — Parses TXT/PDF/DOCX, splits into overlapping chunks (500 chars, 50 overlap) with paragraph-aware segmentation.

### Tool Catalog

| Tool | Module | Purpose |
|------|--------|---------|
| `calculator` | `calculator.py` | Safe math via AST parsing |
| `datetime` | `datetime_tool.py` | Current date/time |
| `weather` | `weather.py` | Weather via wttr.in |
| `bing_search` | `bing_search.py` | Web search via Bing |
| `duckduckgo_search` | `duckduckgo_search.py` | Web search via DuckDuckGo |
| `query_order` | `order_query.py` | Order status (mock) |
| `query_logistics` | `logistics_track.py` | Logistics tracking (mock) |
| `query_return_refund` | `return_refund.py` | Return/refund status (mock) |
| `query_member_info` | `member_info.py` | Member info (mock) |

Mock tools (order, logistics, return, member) use simulated data — replace with real DB queries for production.

### Frontend

Single-page app: `templates/index.html` + `static/app.js` + `static/style.css`. Vanilla JS with marked.js for Markdown rendering. Communicates via SSE for streaming chat and REST for sessions/settings/upload.

### Configuration

- **`settings.json`** — API key, base_url, model, search provider, KB settings, business hours. Not committed to git.
- **Env vars** override settings.json: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`.
- **`MODEL_PRESETS`** in `app.py` — predefined model provider configs (DeepSeek, Zhipu, Qwen, Moonshot, SiliconFlow, OpenAI, custom).

### Data Storage

- **SQLite** (`chatbot.db`) — Sessions and messages, created by `init_db()` on startup.
- **ChromaDB** (`rag_data/`) — Persistent vector store for RAG knowledge base.
- **`uploads/`** — Uploaded files storage.

## Development Notes

- Tools are self-registering: importing a module in `tools/__init__.py` triggers `register()` calls at module level.
- RAG is optional: `chromadb` import failure in `app.py` is silently handled — the app runs without knowledge base.
- Tool calling loop is non-streaming (max 5 turns) to resolve function calls before streaming the final answer.
- The system prompt is dynamically built from `settings.json` values (`customer_service_name`, `business_hours`).
- Models unsupported for tool calling (glm-4-flash, moonshot variants, qwen-long) are listed in `_supports_tool_calling()` and gracefully degrade to streaming.

# WhatsApp AI Chatbot (WhatsApp Web automation + LangGraph)

Backend demo project that combines:
- WhatsApp Web browser automation (`pyppeteer`) to read and send messages
- A LangGraph/LangChain agent that routes requests, asks clarifying questions, and can trigger tools (e.g. Zoom meeting creation)

## Important note
This project automates WhatsApp Web (not the official WhatsApp Business API). Using automation/scraping may violate WhatsApp terms of service. Use at your own risk and only on accounts you control.

## Key features
- Monitors unread WhatsApp chats and extracts recent chat history
- Detects non‑English messages, translates to English for processing, and can translate the response back
- Routes requests (handle directly, ask for more info, send a form, or escalate to admins)
- Can create Zoom meetings via Zoom API and return a shareable (optionally shortened) link
- Can reply with a file attachment (e.g. `.docx` forms under `forms/`)

## Repo layout
- `main.py` – main loop: fetch unread chats, invoke the graph, send responses
- `whatsapp_scraper.py` – WhatsApp Web automation (read messages, send messages/files)
- `graph/graph.py` – LangGraph state machine wiring
- `graph/nodes.py` – routing, translation, formatting, and tool-calling nodes
- `graph/tools/zoom_tool.py` – Zoom meeting tool (+ conflict detection)
- `forms/` – example `.docx` request forms sent to users when needed

## Prerequisites
- Windows + Google Chrome installed
- Python 3.13+
- A persistent Chrome profile directory so WhatsApp stays logged in (see `SELENIUM_PROFILE_PATH` below)

## Configuration
Update the following constants in `graph/constant.py`:
- `CHROME_PATH` – path to `chrome.exe`
- `SELENIUM_PROFILE_PATH` – folder used as Chrome user data dir (WhatsApp login is stored here)
- `ADMIN_GROUP_NAME` – the WhatsApp chat/group name used for escalations

## Environment variables
Create a local `.env` (do not commit it) and set what you need:
- `GOOGLE_API_KEY` – used by `langchain_google_genai.ChatGoogleGenerativeAI`
- `ZOOM_CLIENT_ID`, `ZOOM_CLIENT_SECRET`, `ZOOM_ACCOUNT_ID` – used by `graph/tools/zoom_tool.py`
- `TAVILY_API_KEY` – optional, only if you use `TavilySearchResults` (`graph/tools/tools.py`)

## Run
1. Install dependencies (this repo uses `pyproject.toml`):
   - `python -m venv .venv`
   - `.venv\\Scripts\\activate`
   - `pip install -U pip`
   - `pip install -e .`
2. Start the bot:
   - `python main.py`

The first run opens WhatsApp Web in Chrome. Scan the QR code once (or reuse your profile directory) so future runs stay authenticated.

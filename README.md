# WhatsApp AI Chatbot

A WhatsApp Web automation backend powered by LangGraph and LangChain. The bot reads unread WhatsApp chats, processes each client request through a controlled AI support workflow, uses tools when needed, and sends back a response, file, Zoom meeting details, or admin escalation message.

## Overview

This project is an AI-powered Tier-1 IT and network support assistant that works through WhatsApp. It can understand natural language requests, preserve chat history, ask for missing information, create Zoom meetings, send request forms, run safe read-only network diagnostics, and escalate privileged work to an admin group.

Technically, WhatsApp is only the transport layer: LangGraph coordinates translation, routing, safety checks, tool execution, response formatting, and escalation, while the ReAct agent is used as a controlled execution node for approved tools such as Zoom, Netmiko diagnostics, Genie parsing, Tavily search, and optional NetBox MCP context.

## Capabilities

### WhatsApp Automation

- Opens WhatsApp Web with a persistent Chrome profile.
- Reads unread chats and extracts recent conversation history.
- Sends text responses, single-bubble multiline responses, and file attachments.
- Sends admin escalation messages to a configured WhatsApp group.

### Parallel Agent Processing

- Processes multiple unread clients in the same scan cycle.
- Runs independent graph executions per chat.
- Limits concurrent agent work with a semaphore.
- Keeps WhatsApp sending sequential after processing to avoid Chrome profile conflicts.

### AI Support Workflow

- Detects the user's language.
- Translates non-English requests to English for consistent processing.
- Routes requests between direct answer, follow-up question, form delivery, tool execution, and admin escalation.
- Translates final responses back to the user's original language when needed.

### Tool Use

- Creates Zoom meetings with conflict detection.
- Sends hardware/account request forms from `forms/`.
- Uses Tavily search when external information is needed.
- Runs safe read-only network diagnostics.
- Optionally loads NetBox MCP tools for trusted network source-of-truth context.

## Network Diagnostics

Network diagnostic tools live in `graph/tools/network_diagnostics/`. They are designed for Tier-1 triage only and intentionally avoid configuration changes.

### Diagnostic Tools

- `ping_host`: checks host or IP reachability.
- `dns_lookup`: checks DNS resolution.
- `trace_route`: checks the network path to a host.
- `show_device_command`: connects to approved inventory devices with Netmiko and runs allowlisted show commands.
- `parse_show_output`: parses supported Cisco show output into structured data with Genie when available.

### Allowed Show Commands

- `show ip interface brief`
- `show interfaces`
- `show arp`
- `show ip route`
- `show mac address-table`
- `show mac-address table`
- `show version`
- `show logging`

### Safety Model

The diagnostics block arbitrary shell syntax and dangerous network actions, including:

- Configuration mode commands.
- Reloads, deletes, copies, writes, and erases.
- Interface shutdown/no shutdown.
- VLAN, firewall, routing, password, and permission changes.
- Commands against devices that are not in the approved inventory.

## Architecture Flow

1. `main.py` opens WhatsApp Web and collects unread chats.
2. Each chat becomes an independent graph state with `user_input`, `chat_history`, and `client_name`.
3. LangGraph processes multiple states concurrently.
4. The workflow translates, routes, checks safety, and calls the ReAct agent only when tools are appropriate.
5. Tools return results to the workflow.
6. The response is formatted, translated back if needed, and sent through WhatsApp Web.

## Project Layout

- `main.py`: WhatsApp scan loop, parallel graph processing, and sequential response sending.
- `whatsapp_scraper.py`: WhatsApp Web automation for reading chats and sending messages/files.
- `graph/graph.py`: LangGraph workflow wiring.
- `graph/nodes.py`: translation, routing, privilege checks, ReAct prompting, formatting, and response translation.
- `graph/tools/tools.py`: central tool registry used by the ReAct agent.
- `graph/tools/zoom_tool.py`: Zoom meeting creation and conflict detection.
- `graph/tools/network_diagnostics/`: read-only network diagnostics, inventory loading, and validation.
- `graph/tools/mcp_tools.py`: optional NetBox MCP loading.
- `forms/`: `.docx` request forms sent to users.
- `tests/`: pytest coverage for diagnostics, MCP defaults, and parallel processing.

## Configuration

Update these constants in `graph/constant.py`:

- `CHROME_PATH`: path to `chrome.exe`.
- `SELENIUM_PROFILE_PATH`: Chrome user data directory used to keep WhatsApp logged in.
- `ADMIN_GROUP_NAME`: WhatsApp chat/group name used for admin escalation.

Network device inventory can be configured in code through `DEVICE_INVENTORY` or through `.env` as JSON:

```text
NET_DIAGNOSTIC_DEVICE_INVENTORY={"core_switch":{"device_type":"cisco_ios","host":"10.0.0.10"}}
```

The Netmiko tool only connects to devices in the approved inventory.

## Environment Variables

Create a local `.env` file and do not commit real secrets.

### Core

- `GOOGLE_API_KEY`: used by `langchain_google_genai.ChatGoogleGenerativeAI`.
- `TAVILY_API_KEY`: optional web search support.

### Zoom

- `ZOOM_CLIENT_ID`
- `ZOOM_CLIENT_SECRET`
- `ZOOM_ACCOUNT_ID`

### Network Diagnostics

- `NET_DIAGNOSTIC_DEVICE_INVENTORY`
- `NETMIKO_USERNAME`
- `NETMIKO_PASSWORD`
- `NETMIKO_SECRET`

### Optional NetBox MCP

- `ENABLE_NETBOX_MCP=true`
- `NETBOX_MCP_COMMAND`
- `NETBOX_MCP_ARGS`

NetBox MCP is disabled by default. Enable it only after a NetBox MCP server and credentials are configured.

## Installation

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -U pip
pip install -e .
```

## Run

```powershell
python main.py
```

The first run opens WhatsApp Web in Chrome. Scan the QR code once, or reuse the configured Chrome profile directory to stay authenticated.

## Test

Run the non-WhatsApp test suite:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m pytest -q
```

The tests validate diagnostic command safety, public tool behavior, optional NetBox MCP default behavior, and parallel graph processing without opening WhatsApp Web.

## Important Note

This project automates WhatsApp Web, not the official WhatsApp Business API. Browser automation can be fragile and may violate WhatsApp terms of service. Use only on accounts you control and understand the operational risk.

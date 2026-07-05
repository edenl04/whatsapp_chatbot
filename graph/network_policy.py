from dataclasses import dataclass

from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain_core.messages import BaseMessage
from typing import Callable

ARMY_PRESERVED_NETWORK = "army.preserved"
NETWORK_TOOL_NAMES = {
    "ping_host",
    "trace_route",
    "dns_lookup",
    "show_device_command",
    "parse_show_output",
}
DIAGNOSTIC_KEYWORDS = {
    "ping",
    "dns",
    "nslookup",
    "traceroute",
    "trace route",
    "tracert",
    "route table",
    "show ip route",
    "arp",
    "mac address",
    "mac-address",
    "interface status",
    "show interfaces",
    "packet loss",
    "latency",
    "reachability",
    "reachable",
    "connectivity",
}


@dataclass
class AgentRuntimeContext:
    army_preserved_confirmed: bool
    client_name: str | None = None
    network_context: str | None = None


def _message_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, BaseMessage):
        return str(value.content)
    return str(value)


def is_army_preserved_confirmed(state: dict) -> bool:
    text_parts = [
        _message_text(state.get("translated_input")),
        _message_text(state.get("user_input")),
    ]

    for message in state.get("chat_history") or []:
        text_parts.append(_message_text(message))

    normalized_text = "\n".join(text_parts).lower()
    return ARMY_PRESERVED_NETWORK in normalized_text


def is_network_diagnostic_request(state: dict) -> bool:
    text_parts = [
        _message_text(state.get("translated_input")),
        _message_text(state.get("user_input")),
    ]

    for message in state.get("chat_history") or []:
        text_parts.append(_message_text(message))

    normalized_text = "\n".join(text_parts).lower()
    return any(keyword in normalized_text for keyword in DIAGNOSTIC_KEYWORDS)


def filter_tools_for_army_preserved(tools, army_preserved_confirmed: bool):
    if army_preserved_confirmed:
        return list(tools)
    return [
        tool
        for tool in tools
        if getattr(tool, "name", getattr(tool, "__name__", "")) not in NETWORK_TOOL_NAMES
    ]


@wrap_model_call
def filter_network_tools(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    context = request.runtime.context if request.runtime is not None else None
    if isinstance(context, dict):
        army_preserved_confirmed = bool(context.get("army_preserved_confirmed"))
    else:
        army_preserved_confirmed = bool(
            context is not None and context.army_preserved_confirmed
        )
    tools = filter_tools_for_army_preserved(request.tools or [], army_preserved_confirmed)
    return handler(request.override(tools=tools))

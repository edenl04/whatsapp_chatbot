from langchain_community.tools import TavilySearchResults

from .network_diagnostics import (
    dns_lookup,
    parse_show_output,
    ping_host,
    show_device_command,
    trace_route,
)
from .mcp_tools import load_optional_mcp_tools
from .zoom_tool import ZoomTool

zoom_tool = ZoomTool()


all_tools = [
    zoom_tool,
    ping_host,
    trace_route,
    dns_lookup,
    show_device_command,
    parse_show_output,
    TavilySearchResults(max_results=2),
] + load_optional_mcp_tools()


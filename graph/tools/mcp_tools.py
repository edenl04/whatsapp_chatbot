import asyncio
import os
import shlex


ENABLED_VALUES = {"1", "true", "yes", "on"}


def should_enable_netbox_mcp() -> bool:
    return os.getenv("ENABLE_NETBOX_MCP", "").strip().lower() in ENABLED_VALUES


async def _load_netbox_mcp_tools_async():
    from langchain_mcp_adapters.client import MultiServerMCPClient

    command = os.getenv("NETBOX_MCP_COMMAND", "netbox-mcp-server")
    args = shlex.split(os.getenv("NETBOX_MCP_ARGS", ""))
    client = MultiServerMCPClient(
        {
            "netbox": {
                "transport": "stdio",
                "command": command,
                "args": args,
            },
        }
    )
    return await client.get_tools()


def load_optional_mcp_tools():
    if not should_enable_netbox_mcp():
        return []

    try:
        return asyncio.run(_load_netbox_mcp_tools_async())
    except ImportError as error:
        print(f"NetBox MCP tools are disabled because MCP dependencies are missing: {error}")
    except Exception as error:
        print(f"NetBox MCP tools could not be loaded: {error}")

    return []

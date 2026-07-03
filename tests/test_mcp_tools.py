from graph.tools.mcp_tools import load_optional_mcp_tools, should_enable_netbox_mcp


def test_netbox_mcp_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_NETBOX_MCP", raising=False)

    assert should_enable_netbox_mcp() is False
    assert load_optional_mcp_tools() == []


def test_netbox_mcp_enable_flag(monkeypatch):
    monkeypatch.setenv("ENABLE_NETBOX_MCP", "true")

    assert should_enable_netbox_mcp() is True

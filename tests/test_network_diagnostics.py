from types import SimpleNamespace

from graph.tools.network_diagnostics.diagnostics import (
    dns_lookup,
    parse_show_output,
    ping_host,
    show_device_command,
    trace_route,
)
from graph.tools.network_diagnostics.device_inventory import get_device_inventory
from graph.tools.network_diagnostics.validators import validate_show_command


def invoke_tool(tool, **kwargs):
    if hasattr(tool, "invoke"):
        return tool.invoke(kwargs)
    return tool(**kwargs)


def test_validate_show_command_allows_switch_mac_table_commands():
    assert validate_show_command("show mac address-table") == "show mac address-table"
    assert validate_show_command("show mac-address table") == "show mac-address table"


def test_device_inventory_loads_json_from_environment(monkeypatch):
    monkeypatch.setenv(
        "NET_DIAGNOSTIC_DEVICE_INVENTORY",
        '{"core_switch": {"device_type": "cisco_ios", "host": "10.0.0.10"}}',
    )

    inventory = get_device_inventory()

    assert inventory["core_switch"]["host"] == "10.0.0.10"


def test_show_device_command_blocks_config_commands():
    result = invoke_tool(show_device_command, device_name="core_switch", command="configure terminal")

    assert "Device command failed" in result
    assert "not allowed" in result


def test_show_device_command_rejects_unknown_show_command():
    result = invoke_tool(show_device_command, device_name="core_switch", command="show running-config")

    assert "Device command failed" in result
    assert "Unsupported show command" in result


def test_ping_host_uses_safe_subprocess_args(monkeypatch):
    calls = []

    def fake_run(args, capture_output, text, timeout, check):
        calls.append(args)
        return SimpleNamespace(returncode=0, stdout="Reply from 8.8.8.8", stderr="")

    monkeypatch.setattr("graph.tools.network_diagnostics.diagnostics.subprocess.run", fake_run)

    result = invoke_tool(ping_host, host="8.8.8.8", count=2)

    assert "exit_code=0" in result
    assert "Reply from 8.8.8.8" in result
    assert calls[0][0] == "ping"
    assert calls[0][-2:] == ["2", "8.8.8.8"]


def test_ping_host_rejects_shell_control_input():
    result = invoke_tool(ping_host, host="8.8.8.8 && whoami")

    assert result.startswith("Ping failed")
    assert "unsafe shell control" in result


def test_trace_route_limits_hop_count():
    result = invoke_tool(trace_route, host="8.8.8.8", max_hops=99)

    assert result.startswith("Traceroute failed")
    assert "max_hops must be between" in result


def test_dns_lookup_rejects_unsafe_name():
    result = invoke_tool(dns_lookup, name="server.local;whoami")

    assert result.startswith("DNS lookup failed")
    assert "unsafe shell control" in result


def test_parse_show_output_reports_missing_genie_or_parser_result():
    result = invoke_tool(
        parse_show_output,
        command="show interfaces",
        raw_output="GigabitEthernet0/1 is up",
        os_type="iosxe",
    )

    assert "Genie parser dependencies are not installed" in result or "Failed to parse" in result

import json
import os
import subprocess

try:
    from langchain.tools import tool
except ImportError:
    def tool(func):
        return func


from .device_inventory import build_netmiko_device
from .validators import validate_count, validate_host, validate_show_command


def _run_subprocess(args: list[str], timeout: int) -> str:
    completed_process = subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    output = "\n".join(
        part.strip()
        for part in [completed_process.stdout, completed_process.stderr]
        if part and part.strip()
    )
    if not output:
        output = "Command completed without output."
    return f"exit_code={completed_process.returncode}\n{output}"


@tool
def ping_host(host: str, count: int = 4) -> str:
    """Ping a host or IP address for basic reachability diagnostics."""
    try:
        target = validate_host(host)
        safe_count = validate_count(count, 1, 10, "count")
        args = ["ping", "-n" if os.name == "nt" else "-c", str(safe_count), target]
        return _run_subprocess(args, 20)
    except (subprocess.TimeoutExpired, ValueError) as error:
        return f"Ping failed: {error}"


@tool
def trace_route(host: str, max_hops: int = 15) -> str:
    """Trace the network path to a host for latency or routing diagnostics."""
    try:
        target = validate_host(host)
        safe_hops = validate_count(max_hops, 1, 30, "max_hops")
        args = ["tracert", "-h", str(safe_hops), target] if os.name == "nt" else ["traceroute", "-m", str(safe_hops), target]
        return _run_subprocess(args, 60)
    except (subprocess.TimeoutExpired, ValueError) as error:
        return f"Traceroute failed: {error}"


@tool
def dns_lookup(name: str) -> str:
    """Resolve a hostname and inspect DNS lookup results."""
    try:
        target = validate_host(name)
        return _run_subprocess(["nslookup", target], 20)
    except (subprocess.TimeoutExpired, ValueError) as error:
        return f"DNS lookup failed: {error}"


@tool
def show_device_command(device_name: str, command: str) -> str:
    """Run an approved read-only show command on an inventory-approved network device."""
    try:
        safe_command = validate_show_command(command)
    except ValueError as error:
        return f"Device command failed: {error}"

    try:
        from netmiko import ConnectHandler
        from netmiko.exceptions import NetmikoAuthenticationException, NetmikoBaseException, NetmikoTimeoutException
    except ImportError as error:
        return f"Netmiko is not installed: {error}"

    try:
        device = build_netmiko_device(device_name)
        with ConnectHandler(**device) as connection:
            if device.get("secret"):
                connection.enable()
            output = connection.send_command(safe_command, read_timeout=60)
    except (KeyError, ValueError, NetmikoAuthenticationException, NetmikoTimeoutException, NetmikoBaseException) as error:
        return f"Device command failed: {error}"

    return f"device={device_name}\ncommand={safe_command}\n{output}"


@tool
def parse_show_output(command: str, raw_output: str, os_type: str = "iosxe") -> str:
    """Parse supported Cisco show command output into structured JSON-like data with Genie."""
    try:
        normalized_command = validate_show_command(command)
    except ValueError as error:
        return f"Show output parsing failed: {error}"

    platform = os_type.strip().lower()
    if not raw_output.strip():
        return "No command output was provided to parse."
    if platform != "iosxe":
        return f"Genie parsing is currently supported for iosxe only, not '{os_type}'."

    try:
        from genie.libs.parser.iosxe.show_arp import ShowArp
        from genie.libs.parser.iosxe.show_interface import ShowInterfaces, ShowIpInterfaceBrief
        from genie.libs.parser.iosxe.show_ip_route import ShowIpRoute
        from genie.libs.parser.iosxe.show_mac_address_table import ShowMacAddressTable
        from genie.libs.parser.iosxe.show_version import ShowVersion
        from unittest.mock import Mock
    except ImportError as error:
        return f"Genie parser dependencies are not installed: {error}"

    parser_map = {
        "show arp": lambda device: ShowArp(device=device).cli(output=raw_output),
        "show interfaces": lambda device: ShowInterfaces(device=device).cli(output=raw_output),
        "show ip interface brief": lambda device: ShowIpInterfaceBrief(device=device).cli(output=raw_output),
        "show ip route": lambda device: ShowIpRoute(device=device).cli(output=raw_output),
        "show mac address-table": lambda device: ShowMacAddressTable(device=device).cli(output=raw_output),
        "show mac-address table": lambda device: ShowMacAddressTable(device=device).cli(output=raw_output),
        "show version": lambda device: ShowVersion(device=device).cli(output=raw_output),
    }

    parser_factory = parser_map.get(normalized_command)
    if parser_factory is None:
        return f"No structured Genie parser is configured for '{normalized_command}'."

    try:
        parsed_output = parser_factory(Mock())
    except Exception as error:
        return f"Failed to parse '{normalized_command}' with Genie: {error}"

    return json.dumps(parsed_output, indent=2, sort_keys=True, default=str)

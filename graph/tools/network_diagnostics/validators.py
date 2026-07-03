import ipaddress
import re

HOSTNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,252}$")
SHELL_CONTROL_TOKENS = (";", "&&", "||", "|", ">", "<", "`", "$(", "\n", "\r")
FORBIDDEN_COMMAND_WORDS = (
    "configure",
    "conf",
    "reload",
    "delete",
    "erase",
    "copy",
    "write",
    "shutdown",
    "debug",
    "clear",
    "format",
)
SAFE_SHOW_COMMANDS = {
    "show ip interface brief",
    "show interfaces",
    "show arp",
    "show ip route",
    "show mac address-table",
    "show mac-address table",
    "show version",
    "show logging",
}


def normalize_show_command(command: str) -> str:
    return " ".join(command.strip().lower().split())


def validate_host(host: str) -> str:
    candidate = host.strip()
    if not candidate:
        raise ValueError("Host is required.")
    if any(token in candidate for token in SHELL_CONTROL_TOKENS):
        raise ValueError("Host contains unsafe shell control characters.")

    try:
        ipaddress.ip_address(candidate)
        return candidate
    except ValueError:
        pass

    if not HOSTNAME_PATTERN.fullmatch(candidate):
        raise ValueError("Host must be an IP address or hostname.")
    return candidate


def validate_count(value: int, minimum: int, maximum: int, name: str) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} must be a number.") from error

    if number < minimum or number > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return number


def validate_show_command(command: str) -> str:
    normalized = normalize_show_command(command)
    if not normalized:
        raise ValueError("Command is required.")
    if any(token in normalized for token in SHELL_CONTROL_TOKENS):
        raise ValueError("Command contains unsafe shell control characters.")
    if any(word in normalized.split() for word in FORBIDDEN_COMMAND_WORDS):
        raise ValueError("Command is not allowed for read-only diagnostics.")
    if normalized not in SAFE_SHOW_COMMANDS:
        raise ValueError(f"Unsupported show command: {command}")
    return normalized

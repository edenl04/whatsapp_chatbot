import json
import os
from copy import deepcopy

from dotenv import load_dotenv

load_dotenv()

DEVICE_INVENTORY = {}


def _load_env_inventory() -> dict:
    raw_inventory = os.getenv("NET_DIAGNOSTIC_DEVICE_INVENTORY")
    if not raw_inventory:
        return {}

    try:
        inventory = json.loads(raw_inventory)
    except json.JSONDecodeError:
        return {}

    if not isinstance(inventory, dict):
        return {}
    return inventory


def get_device_inventory() -> dict:
    inventory = deepcopy(DEVICE_INVENTORY)
    inventory.update(_load_env_inventory())
    return inventory


def get_device(device_name: str) -> dict:
    inventory = get_device_inventory()
    device = inventory.get(device_name)
    if device is None:
        raise KeyError(f"Unknown device '{device_name}'. Add it to the approved inventory first.")
    return deepcopy(device)


def build_netmiko_device(device_name: str) -> dict:
    device = get_device(device_name)
    username = os.getenv(device.get("username_env", "NETMIKO_USERNAME"))
    password = os.getenv(device.get("password_env", "NETMIKO_PASSWORD"))
    secret_env = device.get("secret_env", "NETMIKO_SECRET")
    secret = os.getenv(secret_env) if secret_env else None

    if not username or not password:
        raise ValueError(f"Missing Netmiko credentials for '{device_name}'.")

    netmiko_device = {
        "device_type": device["device_type"],
        "host": device["host"],
        "username": username,
        "password": password,
        "conn_timeout": int(device.get("conn_timeout", 10)),
        "auth_timeout": int(device.get("auth_timeout", 20)),
        "banner_timeout": int(device.get("banner_timeout", 15)),
    }

    if "port" in device:
        netmiko_device["port"] = int(device["port"])
    if secret:
        netmiko_device["secret"] = secret

    return netmiko_device

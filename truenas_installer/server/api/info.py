from dataclasses import asdict

from truenas_installer.disks import list_disks as _list_disks
from truenas_installer.network_interfaces import (
    list_network_interfaces as _list_network_interfaces,
    get_available_ip_addresses as _get_available_ip_addresses
)
from truenas_installer.lock import installation_lock
from truenas_installer.server.method import method

__all__ = ["system_info", "list_disks", "list_network_interfaces", "get_available_ip_addresses"]


@method(None, {
    "type": "object",
    "properties": {
        "installation_running": {"type": "boolean"},
        "installation_completed": {"type": "boolean"},
        "installation_error": {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        "version": {"type": "string"},
        "efi": {"type": "boolean"},
    },
})
async def system_info(context):
    """
    Provides auxiliary system information.
    """
    return {
        "installation_running": installation_lock.locked(),
        "installation_completed": context.server.installation_completed,
        "installation_error": context.server.installation_error,
        "version": context.server.installer.version,
        "efi": context.server.installer.efi,
    }


@method(None, {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "size": {"type": "number"},
            "model": {"type": "string"},
            "label": {"type": "string"},
            "zfs_members": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "pool": {"type": "string"},
                    },
                },
            },
            "removable": {"type": "boolean"},
        },
    },
})
async def list_disks(context):
    """
    Provides list of available disks.
    """
    return [asdict(disk) for disk in await _list_disks()]


@method(None, {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
    },
})
async def list_network_interfaces(context):
    """
    Provides list of available network interfaces.
    """
    return [asdict(interface) for interface in await _list_network_interfaces()]


@method(None, {
    "type": "object",
    "properties": {
        "ipv4": {
            "type": "array",
            "items": {"type": "string"},
        },
        "ipv6": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
})
async def get_available_ip_addresses(context):
    """
    Provides available IP addresses on the system that can be used to connect from another machine.
    Excludes loopback, link-local, and wildcard addresses.
    """
    return await _get_available_ip_addresses()

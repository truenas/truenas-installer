from dataclasses import asdict

from truenas_installer.disks import list_disks as _list_disks
from truenas_installer.network_interfaces import list_network_interfaces as _list_network_interfaces
from truenas_installer.lock import installation_lock
from truenas_installer.server.method import method

__all__ = ["system_info", "list_disks", "list_network_interfaces"]


@method(None, {
    "type": "object",
    "properties": {
        "installation_running": {"type": "boolean"},
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

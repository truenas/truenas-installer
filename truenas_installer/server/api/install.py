import asyncio
import errno
import functools

from aiohttp_rpc.protocol import JsonRpcRequest

from truenas_installer.disks import list_disks
from truenas_installer.exception import InstallError
from truenas_installer.install import install as install_
from truenas_installer.serial import serial_sql
from truenas_installer.server.error import Error
from truenas_installer.server.method import method

__all__ = ["install"]


@method({
    "type": "object",
    "required": ["disks", "set_pmbr", "authentication"],
    "additionalProperties": False,
    "properties": {
        "wipe_disks": {
            "type": "array",
            "items": {"type": "string"},
        },
        "disks": {
            "type": "array",
            "items": {"type": "string"},
        },
        "set_pmbr": {"type": "boolean"},
        "authentication": {
            "type": ["object", "null"],
            "required": ["username", "password"],
            "additionalProperties": False,
            "properties": {
                "username": {
                    "type": "string",
                    "enum": ["truenas_admin", "root"],
                },
                "password": {
                    "type": "string",
                    "minLength": 6,
                },
            },
        },
        "post_install": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "network_interfaces": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name"],
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "aliases": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["type", "address", "netmask"],
                                    "additionalProperties": False,
                                    "properties": {
                                        "type": {"type": "string"},
                                        "address": {"type": "string"},
                                        "netmask": {"type": "integer"},
                                    },
                                },
                            },
                            "ipv4_dhcp": {"type": "boolean"},
                            "ipv6_auto": {"type": "boolean"},
                        },
                    },
                },
            },
        },
    },
}, None)
async def install(context, params):
    """
    Performs system installation.
    """
    disks = {disk.name: disk for disk in await list_disks()}

    try:
        destination_disks = [disks[disk_name] for disk_name in params["disks"]]
    except KeyError as e:
        raise Error(f"Disk {e.args[0]!r} does not exist", errno.EFAULT)

    try:
        wipe_disks = [disks[disk_name] for disk_name in params.get("wipe_disks", [])]
    except KeyError as e:
        raise Error(f"Disk {e.args[0]!r} does not exist", errno.EFAULT)

    try:
        await install_(
            destination_disks,
            wipe_disks,
            params["set_pmbr"],
            params["authentication"],
            params.get("post_install", None),
            await serial_sql(),
            functools.partial(callback, context.server),
        )
    except InstallError as e:
        raise Error(e.message, errno.EFAULT)


def callback(server, progress, message):
    request = server.json_serialize(
        JsonRpcRequest(
            "installation_progress",
            params=[{"progress": progress, "message": message}]
        ).dump()
    )

    for other in server.rcp_websockets:
        asyncio.ensure_future(other.send_str(request))

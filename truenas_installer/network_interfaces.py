from dataclasses import dataclass

from pyroute2 import IPRoute, NetlinkDumpInterrupted

__all__ = ["list_network_interfaces"]


@dataclass
class NetworkInterface:
    name: str


async def list_network_interfaces():
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            with IPRoute() as ipr:
                interfaces = [NetworkInterface(dev.get_attr("IFLA_IFNAME")) for dev in ipr.get_links()]
        except NetlinkDumpInterrupted:
            if attempt < max_retries:
                # When the kernel is producing a dump of a kernel structure
                # over multiple netlink messages, and the structure changes
                # mid-way, NLM_F_DUMP_INTR is added to the header flags.
                # This an indication that the requested dump contains
                # inconsistent data and must be re-requested. See function
                # nl_dump_check_consistent() in include/net/netlink.h. The
                # pyroute2 library raises this specific exception for this
                # scenario, so we'll try again (up to a max of 3 times).
                continue
            else:
                raise

    return [
        interface for interface in interfaces
        if interface.name not in ["lo"]
    ]

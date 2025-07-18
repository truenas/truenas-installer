from dataclasses import dataclass
import ipaddress
import logging

from pyroute2 import IPRoute, NetlinkDumpInterrupted

logger = logging.getLogger(__name__)


__all__ = ["list_network_interfaces", "get_available_ip_addresses", "get_interface_ips"]


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


def _is_valid_ip_for_connection(ip_obj):
    """
    Check if an IP address is valid for external connections.
    Excludes loopback, link-local, wildcard, and multicast addresses.
    """
    # Skip loopback addresses
    if ip_obj.is_loopback:
        return False

    # Skip link-local addresses
    if ip_obj.is_link_local:
        return False

    # Skip wildcard addresses
    if ip_obj == ipaddress.ip_address("0.0.0.0") or ip_obj == ipaddress.ip_address("::"):
        return False

    # Skip multicast addresses
    if ip_obj.is_multicast:
        return False

    return True


async def _get_ip_addresses_with_filter(interface_filter=None):
    """
    Get IP addresses with optional interface filtering.

    Args:
        interface_filter: None to get all interfaces, or a list of interface names to filter

    Returns:
        dict: {"ipv4": [...], "ipv6": [...]}
    """
    result = {"ipv4": [], "ipv6": []}

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            with IPRoute() as ipr:
                # Get all addresses
                addresses = ipr.get_addr()

                for addr in addresses:
                    # Get the IP address
                    ip_str = addr.get_attr("IFA_ADDRESS")
                    if not ip_str:
                        continue

                    # Get the interface index and name
                    if_index = addr["index"]
                    try:
                        link = ipr.get_links(if_index)[0]
                        if_name = link.get_attr("IFLA_IFNAME")

                        # Apply interface filter
                        if interface_filter is None:
                            # Skip loopback for "all interfaces" mode
                            if if_name == "lo":
                                continue
                        else:
                            # Check if interface is in the filter list
                            if if_name not in interface_filter:
                                continue
                    except (IndexError, KeyError):
                        continue

                    try:
                        ip_obj = ipaddress.ip_address(ip_str)

                        # Check if IP is valid for connections
                        if not _is_valid_ip_for_connection(ip_obj):
                            continue

                        # Add to appropriate list
                        if isinstance(ip_obj, ipaddress.IPv4Address):
                            if ip_str not in result["ipv4"]:
                                result["ipv4"].append(ip_str)
                        elif isinstance(ip_obj, ipaddress.IPv6Address):
                            if ip_str not in result["ipv6"]:
                                result["ipv6"].append(ip_str)

                    except ValueError:
                        # Invalid IP address, skip
                        continue

            # Success, break out of retry loop
            break

        except NetlinkDumpInterrupted:
            if attempt < max_retries:
                continue
            else:
                logger.error("Failed to get IP addresses after %d retries due to NetlinkDumpInterrupted", max_retries)
                return result
        except Exception as e:
            if interface_filter:
                logger.error("Error getting IP addresses for interfaces %s: %s", interface_filter, e, exc_info=True)
            else:
                logger.error("Error getting IP addresses: %s", e, exc_info=True)
            return result

    return result


async def get_available_ip_addresses():
    """
    Get all available IP addresses on the system that can be used to connect from another machine.
    Excludes loopback, link-local, and wildcard addresses.

    Returns:
        dict: {"ipv4": [...], "ipv6": [...]}
    """
    return await _get_ip_addresses_with_filter(interface_filter=None)


async def get_interface_ips(interface_names):
    """
    Get IP addresses from specific network interfaces.

    Args:
        interface_names: List of interface names (e.g., ["em0", "em1"])

    Returns:
        dict: {"ipv4": [...], "ipv6": [...]}
    """
    # First validate that all requested interfaces exist
    available_interfaces = await list_network_interfaces()
    available_names = [iface.name for iface in available_interfaces]

    for name in interface_names:
        if name not in available_names:
            raise ValueError(f"Interface '{name}' not found")

    return await _get_ip_addresses_with_filter(interface_filter=interface_names)

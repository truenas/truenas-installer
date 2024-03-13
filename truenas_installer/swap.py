from .disks import Disk
from .utils import GiB

MIN_SWAPSAFE_MEDIASIZE = 60 * GiB

__all__ = ["is_swap_safe"]


def is_swap_safe(disk: Disk):
    return disk.size >= MIN_SWAPSAFE_MEDIASIZE and not disk.removable

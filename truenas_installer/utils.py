import asyncio
import os
import subprocess

__all__ = ["GiB", "get_partitions", "run"]

GiB = 1024 ** 3
MAX_PARTITION_WAIT_TIME_SECS = 300


async def get_partitions(
    device: str,
    partitions: list[int],
    tries: None | int = None
) -> dict:
    """
    `device`: str (i.e. /dev/sda, /dev/nvme0n1)
    `partitions`: list of integers (i.e. [1, 2, 3])
    `tries`: None or int, defaults to None, if provided, will
        sleep up to that time waiting on all `partitions` for `device`
        to appear in sysfs. Maximum of `MAX_PARTITION_WAIT_TIME_SECS`.
    """
    if not isinstance(tries, int) or tries < 2:
        tries = 1
    else:
        tries = min(tries, MAX_PARTITION_WAIT_TIME_SECS)

    # by the time this function is called, partitions should have been
    # written to the disk. However, it doesn't mean the kernel/udev has
    # updated the various symlinks in sysfs. We'll open the block device
    # in write mode. This should send a kernel and udev change event for
    # the device and any partitions as well. Ideally, this will help bubble
    # up the events so sysfs is populated before the logic below kicks in
    with open(device, 'w'):
        pass

    disk_partitions = {i: None for i in partitions}
    device = device.removeprefix('/dev/')
    for _try in range(tries):
        if all((disk_partitions[i] is not None for i in disk_partitions)):
            # all partitions were found on disk
            return disk_partitions

        try:
            with os.scandir(f"/sys/block/{device}") as dir_contents:
                for partdir in filter(lambda x: x.is_dir() and x.name.startswith(device), dir_contents):
                    with open(os.path.join(partdir.path, 'partition')) as f:
                        try:
                            _part = int(f.read().strip())
                            if _part in partitions:
                                # looks like {1: '/dev/sda1', 2: '/dev/nvme0n1p2'}
                                disk_partitions[_part] = f'/dev/{partdir.name}'
                        except (OSError, ValueError):
                            # OSError: [Errno 19] No such device was seen on
                            # our internal CI/CD infrastructure for reasons
                            # not understood...
                            continue
        except FileNotFoundError:
            continue

        await asyncio.sleep(1)

    empty_parts = {k: v for k, v in disk_partitions.items() if v is None}
    if empty_parts:
        # sysfs is unpredictable AT BEST when expecting it to reliably populate
        # symlinks for the block devices after a partition has been written
        # to it. We're seeing our CI/CD randomly "fail" because sysfs hasn't
        # been populated after partition creation. As a last resort, we'll just
        # haphazardly check to see if the disk partitions block device exists
        with os.scandir('/dev/') as dir_contents:
            for dev in filter(lambda x: x.name.startswith(device), dir_contents):
                for partnum in empty_parts:
                    part_str = str(partnum)
                    if dev.name[-len(part_str):] == part_str:
                        disk_partitions[partnum] = f'/dev/{dev.name}'

    return disk_partitions


async def run(args, check=True):
    process = await asyncio.create_subprocess_exec(*args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()

    stdout = stdout.decode("utf-8", "ignore")
    stderr = stderr.decode("utf-8", "ignore")

    if check:
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, args, stdout, stderr)

    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)

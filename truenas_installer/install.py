import os.path

import asyncio
import json
import pathlib
import subprocess
import tempfile

from .utils import get_partition, run

__all__ = ["InstallError", "install"]

BOOT_POOL = "boot-pool"


class InstallError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


async def install(disks, create_swap, set_pmbr, authentication, sql, callback):
    try:
        if not os.path.exists("/etc/hostid"):
            await run(["zgenhostid"])

        for disk in disks:
            callback(0, f"Formatting disk {disk}")
            await format_disk(f"/dev/{disk}", create_swap, set_pmbr, callback)

        callback(0, "Creating boot pool")
        await create_boot_pool([get_partition(disk, 3) for disk in disks])
        try:
            await run_installer(disks, authentication, sql, callback)
        finally:
            await run(["zpool", "export", "-f", BOOT_POOL])
    except subprocess.CalledProcessError as e:
        raise InstallError(f"Command {' '.join(e.cmd)} failed:\n{e.stderr.rstrip()}")


async def format_disk(device, create_swap, set_pmbr, callback):
    if (result := await run(["wipefs", "-a", device], check=False)).returncode != 0:
        callback(0, f"Warning: unable to wipe partition table for {device}: {result.stderr.rstrip()}")

    # Erase both typical metadata area.
    await run(["sgdisk", "-Z", device], check=False)
    await run(["sgdisk", "-Z", device], check=False)

    # Create BIOS boot partition
    await run(["sgdisk", "-a4096", "-n1:0:+1024K", "-t1:EF02", "-A1:set:2", device])

    # Create EFI partition (Even if not used, allows user to switch to UEFI later)
    await run(["sgdisk", "-n2:0:+524288K", "-t2:EF00", device])

    if create_swap:
        await run(["sgdisk", "-n4:0:+16777216K", "-t4:8200", device])
        await run(["wipefs", "-a", "-t", "zfs_member", get_partition(device, 4)], check=False)

    # Create data partition
    await run(["sgdisk", "-n3:0:0", "-t3:BF01", device])

    # Bad hardware is bad, but we've seen a few users
    # state that by the time we run `parted` command
    # down below OR the caller of this function tries
    # to do something with the partition(s), they won't
    # be present. This is almost _exclusively_ related
    # to bad hardware, but we add this here as a compromise.
    await wait_on_partitions(device, [1, 2, 3, 4] if create_swap else [1, 2, 3])

    if set_pmbr:
        await run(["parted", "-s", device, "disk_set", "pmbr_boot", "on"], check=False)


async def wait_on_partitions(device, partitions):
    if not pathlib.Path(device).is_block_device():
        raise InstallError(f"{device} was not found or is not a block device")

    partitions = [get_partition(device, partition) for partition in partitions]

    for i in range(30):
        if all(pathlib.Path(partition).is_block_device() for partition in partitions):
            return

        await asyncio.sleep(1)

    for partition in partitions:
        if not pathlib.Path(partition).is_block_device():
            raise InstallError(f"Could not find {partition}")


async def create_boot_pool(devices):
    await run(
        [
            "zpool", "create", "-f",
            "-o", "ashift=12",
            "-o", "cachefile=none",
            "-o", "compatibility=grub2",
            "-O", "acltype=off",
            "-O", "canmount=off",
            "-O", "compression=on",
            "-O", "devices=off",
            "-O", "mountpoint=none",
            "-O", "normalization=formD",
            "-O", "relatime=on",
            "-O", "xattr=sa",
            BOOT_POOL,
        ] +
        (["mirror"] if len(devices) > 1 else []) +
        devices
    )
    await run(["zfs", "create", "-o", "canmount=off", f"{BOOT_POOL}/ROOT"])
    await run(["zfs", "create", "-o", "canmount=off", "-o", "mountpoint=legacy", f"{BOOT_POOL}/grub"])


async def run_installer(disks, authentication, sql, callback):
    with tempfile.TemporaryDirectory() as src:
        await run(["mount", "/cdrom/TrueNAS-SCALE.update", src, "-t", "squashfs", "-o", "loop"])
        try:
            params = {
                "authentication_method": authentication,
                "disks": disks,
                "json": True,
                "pool_name": BOOT_POOL,
                "sql": sql,
                "src": src,
            }
            process = await asyncio.create_subprocess_exec(
                "python3", "-m", "truenas_install",
                cwd=src,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            process.stdin.write(json.dumps(params).encode("utf-8"))
            process.stdin.close()
            error = None
            stderr = ""
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                line = line.decode("utf-8", "ignore")

                try:
                    data = json.loads(line)
                except ValueError:
                    stderr += line
                else:
                    if "progress" in data and "message" in data:
                        callback(data["progress"], data["message"])
                    elif "error" in data:
                        error = data["error"]
                    else:
                        raise ValueError(f"Invalid truenas_install JSON: {data!r}")
            await process.wait()

            if error is not None:
                result = error
            else:
                result = stderr

            if process.returncode != 0:
                raise InstallError(result or f"Abnormal installer process termination with code {process.returncode}")
        finally:
            await run(["umount", "-f", src])

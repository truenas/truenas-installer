import asyncio
import json
import os
import subprocess
import tempfile

from .exception import InstallError
from .lock import installation_lock
from .utils import get_partitions, run

__all__ = ["InstallError", "install"]

BOOT_POOL = "boot-pool"


async def install(disks, set_pmbr, authentication, post_install, sql, callback):
    with installation_lock:
        try:
            if not os.path.exists("/etc/hostid"):
                await run(["zgenhostid"])

            for disk in disks:
                callback(0, f"Formatting disk {disk}")
                await format_disk(f"/dev/{disk}", set_pmbr, callback)

            disk_parts = list()
            part_num = 3
            for disk in disks:
                found = (await get_partitions(disk, [part_num]))[part_num]
                if found is None:
                    raise InstallError(f"Failed to find data partition on {disk!r}")
                else:
                    disk_parts.append(found)

            callback(0, "Creating boot pool")
            await create_boot_pool(disk_parts)
            try:
                await run_installer(disks, authentication, post_install, sql, callback)
            finally:
                await run(["zpool", "export", "-f", BOOT_POOL])
        except subprocess.CalledProcessError as e:
            raise InstallError(f"Command {' '.join(e.cmd)} failed:\n{e.stderr.rstrip()}")


async def format_disk(device, set_pmbr, callback):
    if (result := await run(["wipefs", "-a", device], check=False)).returncode != 0:
        callback(0, f"Warning: unable to wipe partition table for {device}: {result.stderr.rstrip()}")

    # Erase both typical metadata area.
    await run(["sgdisk", "-Z", device], check=False)
    await run(["sgdisk", "-Z", device], check=False)

    # Create BIOS boot partition
    await run(["sgdisk", "-a4096", "-n1:0:+1024K", "-t1:EF02", "-A1:set:2", device])

    # Create EFI partition (Even if not used, allows user to switch to UEFI later)
    await run(["sgdisk", "-n2:0:+524288K", "-t2:EF00", device])

    # Create data partition
    await run(["sgdisk", "-n3:0:0", "-t3:BF01", device])

    # Bad hardware is bad, but we've seen a few users
    # state that by the time we run `parted` command
    # down below OR the caller of this function tries
    # to do something with the partition(s), they won't
    # be present. This is almost _exclusively_ related
    # to bad hardware, but we will wait up to 30 seconds
    # for the partitions to show up in sysfs.
    disk_parts = await get_partitions(device, [1, 2, 3], tries=30)
    for partnum, part_device in disk_parts.items():
        if part_device is None:
            raise InstallError(f"Failed to find partition number {partnum} on {device!r}")

    if set_pmbr:
        await run(["parted", "-s", device, "disk_set", "pmbr_boot", "on"], check=False)


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


async def run_installer(disks, authentication, post_install, sql, callback):
    with tempfile.TemporaryDirectory() as src:
        await run(["mount", "/cdrom/TrueNAS-SCALE.update", src, "-t", "squashfs", "-o", "loop"])
        try:
            params = {
                "authentication_method": authentication,
                "disks": disks,
                "json": True,
                "pool_name": BOOT_POOL,
                "post_install": post_install,
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

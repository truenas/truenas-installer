from dataclasses import dataclass
import json
import re

from .utils import run

__all__ = ["list_disks"]

MIN_DISK_SIZE = 8_000_000_000


@dataclass
class ZFSMember:
    name: str
    pool: str


@dataclass
class Disk:
    name: str
    size: int
    model: str
    label: str
    zfs_members: list[ZFSMember]
    removable: bool

    @property
    def device(self):
        return f"/dev/{self.name}"


async def list_disks():
    # need to settle so that lsblk output is stable
    await run(["udevadm", "settle"])

    with open("/etc/mtab") as f:
        mtab = f.read()

    disks = []
    for disk in json.loads(
        (await run(["lsblk", "-b", "-fJ", "-o", "name,fstype,label,rm,size,model"])).stdout
    )["blockdevices"]:
        if disk["name"].startswith(("dm", "loop", "md", "sr", "st")):
            continue
        elif disk["size"] < MIN_DISK_SIZE:
            continue
        elif re.search(fr"/dev/{disk["model"]}p?[0-9]+", mtab):
            continue

        zfs_members = []
        if disk["fstype"] is not None:
            label = disk["fstype"]
        else:
            children = disk.get("children", [])
            if zfs_members := [ZFSMember(child["name"], child["label"])
                               for child in children
                               if child["fstype"] == "zfs_member"]:
                label = ", ".join([f"zfs-\"{zfs_member.pool}\"" for zfs_member in zfs_members])
            else:
                for fstype in ["ext4", "xfs"]:
                    if labels := [child for child in children if child["fstype"] == fstype]:
                        label = f"{fstype}-{labels[0]['label']}"
                        break
                else:
                    if labels := [child for child in children if child["fstype"] is not None]:
                        label = "-".join(filter(None, [labels[0]["fstype"], labels[0]["label"]]))
                    else:
                        label = ""

        disks.append(
            Disk(
                disk["name"],
                disk["size"],
                disk["model"] or "Unknown Model",
                label,
                zfs_members,
                disk["rm"]
            )
        )

    return disks

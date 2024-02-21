import asyncio
import subprocess

__all__ = ["GiB", "get_partition", "run"]

GiB = 1024 ** 3


def get_partition(device, partition):
    if device[-1].isdigit():
        return f"{device}n{partition}"
    else:
        return f"{device}{partition}"


async def run(args, check=True):
    process = await asyncio.create_subprocess_exec(*args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = await process.communicate()

    stdout = stdout.decode("utf-8", "ignore")
    stderr = stderr.decode("utf-8", "ignore")

    if check:
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, args, stdout, stderr)

    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)

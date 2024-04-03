import re

from .utils import run


async def serial_sql():
    with open("/proc/cmdline") as f:
        if "console=ttyS" not in f.read():
            return ""

    result = "update system_advanced set adv_serialconsole = 1;"

    if m := re.search("(ttyS[0-9]) at I/O", (await run(["dmesg"])).stdout):
        tty = m.group(1)
        result += f"update system_advanced set adv_serialport = '{tty}';"

        try:
            serial_speed = int((await run(["setserial", "-G", f"/dev/{tty}"], check=False)).stdout.split()[8])
        except (IndexError, ValueError):
            pass
        else:
            result += f"update system_advanced set adv_serialspeed = {serial_speed};"

    return result

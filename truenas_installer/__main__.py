import os
import pathlib
import sys

import psutil

from ixhardware import parse_dmi

from .installer import Installer


if __name__ == "__main__":
    pidfile = pathlib.Path("/run/truenas_installer.pid")
    try:
        pid = int(pidfile.read_text().strip())
    except (FileNotFoundError, UnicodeDecodeError, ValueError):
        pass
    else:
        try:
            process = psutil.Process(pid)
        except psutil.NoSuchProcess:
            pass
        else:
            if "truenas_installer" in process.cmdline():
                print(f"Installer is already running (pid={pid})", file=sys.stderr)
                sys.exit(1)

    pidfile.write_text(str(os.getpid()))
    try:
        with open("/etc/version") as f:
            version = f.read().strip()

        dmi = parse_dmi()

        installer = Installer(version, dmi)
        installer.run()
    finally:
        pidfile.unlink(missing_ok=True)

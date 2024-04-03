from ixhardware import parse_dmi

from .installer import Installer


if __name__ == "__main__":
    with open("/etc/version") as f:
        version = f.read().strip()

    dmi = parse_dmi()

    installer = Installer(version, dmi)
    installer.run()

import os


class Installer:
    def __init__(self, version, dmi, vendor=None):
        self.version = version
        self.dmi = dmi
        self.efi = os.path.exists("/sys/firmware/efi")
        self.vendor = vendor

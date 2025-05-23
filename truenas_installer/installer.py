import os


class Installer:
    def __init__(self, version, dmi, vendor, tn_model):
        self.version = version
        self.dmi = dmi
        self.efi = os.path.exists("/sys/firmware/efi")
        self.vendor = vendor
        self.tn_model = tn_model

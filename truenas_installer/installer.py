import os


class Installer:
    def __init__(self, version, vendor, tn_model):
        self.version = version
        self.efi = os.path.exists("/sys/firmware/efi")
        self.dtb = os.path.exists("/sys/firmware/devicetree/base")
        self.vendor = vendor
        self.tn_model = tn_model

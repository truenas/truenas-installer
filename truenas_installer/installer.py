import asyncio

from .installer_menu import InstallerMenu


class Installer:
    def __init__(self, version, dmi):
        self.version = version
        self.dmi = dmi

    def run(self):
        loop = asyncio.get_event_loop()

        loop.create_task(InstallerMenu(self).run())

        loop.run_forever()

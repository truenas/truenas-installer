import asyncio
import os
import sys

import humanfriendly

from .dialog import dialog_checklist, dialog_menu, dialog_msgbox, dialog_password, dialog_yesno
from .disks import list_disks
from .exception import InstallError
from .install import install
from .serial import serial_sql
from .swap import is_swap_safe


class InstallerMenu:
    def __init__(self, installer):
        self.installer = installer

    async def run(self):
        await self._main_menu()

    async def _main_menu(self):
        await dialog_menu(
            f"TrueNAS {self.installer.version} Console Setup",
            {
                "Install/Upgrade": self._install_upgrade,
                "Shell": self._shell,
                "Reboot System": self._reboot,
                "Shutdown System": self._shutdown,
            }
        )

    async def _install_upgrade(self):
        while True:
            await self._install_upgrade_internal()
            await self._main_menu()

    async def _install_upgrade_internal(self):
        disks = await list_disks()

        if not disks:
            await dialog_msgbox("Choose Destination Media", "No drives available")
            return False

        while True:
            destination_disks = await dialog_checklist(
                "Choose Destination Media",
                (
                    "Install TrueNAS to a drive. If desired, select multiple drives to provide redundancy. TrueNAS "
                    "installation drive(s) are not available for use in storage pools. Use arrow keys to navigate "
                    "options. Press spacebar to select."
                ),
                {
                    disk.name: " ".join([
                        disk.model[:15].ljust(15, " "),
                        disk.label[:15].ljust(15, " "),
                        "--",
                        humanfriendly.format_size(disk.size, binary=True)
                    ])
                    for disk in disks
                }
            )

            if destination_disks is None:
                # Installation cancelled
                return False

            if not destination_disks:
                await dialog_msgbox(
                    "Choose Destination Media",
                    "Select at least one disk to proceed with the installation.",
                )
                continue

            break

        text = "\n".join([
            "WARNING:",
            f"- This erases ALL partitions and data on {', '.join(destination_disks)}.",
            f"- {', '.join(destination_disks)} will be unavailable for use in storage pools.",
            "",
            "NOTE:",
            "- Installing on SATA, SAS, or NVMe flash media is recommended.",
            "  USB flash sticks are discouraged.",
            "",
            "Proceed with the installation?"
        ])
        if not await dialog_yesno("TrueNAS Installation", text):
            return False

        authentication_method = await dialog_menu(
            "Web UI Authentication Method",
            {
                "Administrative user (admin)": self._authentication_admin,
                "Configure using Web UI": self._authentication_webui,
            }
        )
        if authentication_method is False:
            return False

        create_swap = False
        if all(is_swap_safe([disk for disk in disks if disk.name == destination_disk][0])
               for destination_disk in destination_disks):
            create_swap = await dialog_yesno("Swap", "Create 16GB swap partition on boot devices?")

        set_pmbr = False
        if not self.installer.efi:
            set_pmbr = await dialog_yesno(
                "Legacy Boot",
                (
                    "Allow EFI boot? Enter Yes for systems with newer components such as NVMe devices. Enter No when "
                    "system hardware requires legacy BIOS boot workaround."
                ),
            )

        # If the installer was booted with serial mode enabled, we should save these values to the installed system
        sql = await serial_sql()

        try:
            await install(destination_disks, create_swap, set_pmbr, authentication_method, None, sql, self._callback)
        except InstallError as e:
            await dialog_msgbox("Installation Error", e.message)
            return False

        await dialog_msgbox(
            "Installation Succeeded",
            (
                f"The TrueNAS installation on {', '.join(destination_disks)} succeeded!\n"
                "Please reboot and remove the installation media."
            ),
        )
        return True

    async def _authentication_admin(self):
        return await self._authentication_password(
            "admin",
            "Enter your \"admin\" user password. Root password login will be disabled.",
        )

    async def _authentication_password(self, username, title):
        password = await dialog_password(title)
        if password is None:
            return False

        return {"username": username, "password": password}

    async def _authentication_webui(self):
        return None

    async def _shell(self):
        os._exit(1)

    async def _reboot(self):
        process = await asyncio.create_subprocess_exec("reboot")
        await process.communicate()

    async def _shutdown(self):
        process = await asyncio.create_subprocess_exec("shutdown", "now")
        await process.communicate()

    def _callback(self, progress, message):
        sys.stdout.write(f"[{int(progress * 100)}%] {message}\n")
        sys.stdout.flush()

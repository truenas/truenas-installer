import pathlib

from .exception import InstallError

__all__ = ["installation_lock"]


class InstallationLock:
    def __init__(self):
        self.path = pathlib.Path("/run/truenas_installer.lock")

    def locked(self):
        return self.path.exists()

    def __enter__(self):
        if self.locked():
            raise InstallError("Installation is already in progress")

        self.path.write_text("")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.path.unlink(missing_ok=True)


installation_lock = InstallationLock()

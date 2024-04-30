import asyncio

from truenas_installer.server.method import method

__all__ = ["reboot", "shutdown"]


@method(None, None)
async def reboot(context):
    """
    Performs system reboot.
    """
    process = await asyncio.create_subprocess_exec("reboot")
    await process.communicate()


@method(None, None)
async def shutdown(context):
    """
    Performs system shutdown.
    """
    process = await asyncio.create_subprocess_exec("shutdown", "now")
    await process.communicate()

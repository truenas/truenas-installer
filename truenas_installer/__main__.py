import argparse
import asyncio

from aiohttp import web

from ixhardware import parse_dmi

from .installer import Installer
from .installer_menu import InstallerMenu
from .server import InstallerRPCServer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()

    with open("/etc/version") as f:
        version = f.read().strip()

    dmi = parse_dmi()

    installer = Installer(version, dmi)

    if args.server:
        rpc_server = InstallerRPCServer(installer)
        app = web.Application()
        app.router.add_routes([
            web.get("/", rpc_server.handle_http_request),
        ])
        app.on_shutdown.append(rpc_server.on_shutdown)
        web.run_app(app, port=80)
    else:
        loop = asyncio.get_event_loop()
        loop.create_task(InstallerMenu(installer).run())
        loop.run_forever()


if __name__ == "__main__":
    main()

import argparse
import asyncio
import json

from aiohttp import web

from ixhardware import parse_dmi

from .installer import Installer
from .installer_menu import InstallerMenu
from .server import InstallerRPCServer
from .server.doc import generate_api_doc


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", action="store_true")
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()

    with open("/etc/version") as f:
        version = f.read().strip()
    
    try:
        with open("/data/.vendor") as f:
            vendor = json.loads(f.read()).get("vendor")
    except FileNotFoundError:
        vendor = None
        
    dmi = parse_dmi()

    installer = Installer(version, dmi, vendor)

    if args.doc:
        generate_api_doc()
    elif args.server:
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

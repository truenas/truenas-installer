import aiohttp_rpc

import truenas_installer.server.api  # noqa
from truenas_installer.server.api.adoption import adoption_middleware
from .error import exception_middleware
from .method import methods

__all__ = ["InstallerRPCServer"]


class InstallerRPCServer(aiohttp_rpc.WsJsonRpcServer):
    def __init__(self, installer):
        self.installer = installer
        self.configured_tnc = False
        self.installation_completed = False
        super().__init__(
            middlewares=(
                adoption_middleware,
                exception_middleware,
                aiohttp_rpc.middlewares.extra_args_middleware,
            ),
        )

        for method in methods.values():
            method.server = self
            self.add_method(aiohttp_rpc.protocol.JsonRpcMethod(method.call, name=method.name))

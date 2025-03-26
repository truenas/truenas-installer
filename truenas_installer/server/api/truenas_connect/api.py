from truenas_installer.server.method import method

from .cache import get_tnc_config
from .schema import TNC_CONFIG_SCHEMA


__all__ = ['tnc_config']


@method(None, TNC_CONFIG_SCHEMA)
async def tnc_config(context):
    """
    Get TrueNAS Connect configuration.
    """
    return get_tnc_config()

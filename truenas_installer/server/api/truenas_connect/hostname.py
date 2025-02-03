from .cache import tnc_config
from .urls import get_hostname_url
from .utils import auth_headers, call, get_account_id_and_system_id


async def register_update_ips() -> dict:
    config = tnc_config()
    creds = get_account_id_and_system_id(config)
    return await call(
        get_hostname_url(config).format(**creds), 'put', payload={'ips': config['ips']}, headers=auth_headers(config),
    )

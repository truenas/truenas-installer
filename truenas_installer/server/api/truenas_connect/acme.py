from .acme_utils import normalize_acme_config
from .cache import tnc_config, update_tnc_config
from .crypto.cert_utils import get_hostnames_from_hostname_config
from .hostname import hostname_config, register_update_ips
from .urls import get_acme_config_url
from .utils import auth_headers, call, get_account_id_and_system_id


async def acme_config() -> dict:
    config = tnc_config()
    creds = get_account_id_and_system_id(config)
    if not config['enabled'] or creds is None:
        return {
            'error': 'TrueNAS Connect is not enabled or not configured properly',
            'tnc_configured': False,
            'acme_details': {},
        }

    resp = await call(
        get_acme_config_url(config).format(account_id=creds['account_id']), 'get', headers=auth_headers(config)
    )
    resp['acme_details'] = resp.pop('response')
    if resp['error'] is None:
        resp = normalize_acme_config(resp)

    return resp | {'tnc_configured': True}

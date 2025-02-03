from .cache import tnc_config
from .urls import get_hostname_url
from .utils import auth_headers, call, get_account_id_and_system_id


async def register_update_ips() -> dict:
    config = tnc_config()
    creds = get_account_id_and_system_id(config)
    return await call(
        get_hostname_url(config).format(**creds), 'put', payload={'ips': config['ips']}, headers=auth_headers(config),
    )


async def hostname_config() -> dict:
    config = tnc_config()
    creds = get_account_id_and_system_id(config)
    if not config['enabled'] or creds is None:
        return {
            'error': 'TrueNAS Connect is not enabled or not configured properly',
            'tnc_configured': False,
            'hostname_details': {},
            'base_domain': None,
            'hostname_configured': False,
        }

    resp = (
        await call(get_hostname_url(config).format(**creds), 'get', headers=auth_headers(config))
    ) | {'base_domain': None}
    resp['hostname_details'] = resp.pop('response')
    for domain in resp['hostname_details']:
        if len(domain.rsplit('.', maxsplit=4)) == 5 and domain.startswith('*.'):
            resp['base_domain'] = domain.split('.', maxsplit=1)[-1]
            break

    return resp | {
        'tnc_configured': True,
        'hostname_configured': bool(resp['hostname_details']),
    }

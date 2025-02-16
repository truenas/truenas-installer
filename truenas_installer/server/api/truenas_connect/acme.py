from acme_utils.issue_cert import issue_certificate

from .cache import tnc_config, update_tnc_config
from .cert_utils import generate_csr, get_hostnames_from_hostname_config
from .hostname import hostname_config, register_update_ips
from .tnc_acme_utils import normalize_acme_config
from .tnc_authenticator import TrueNASConnectAuthenticator
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


async def create_cert() -> dict:
    await register_update_ips()
    tnc_hostname_config = await hostname_config()
    if tnc_hostname_config['error']:
        raise Exception(f'Failed to fetch TN Connect hostname config: {tnc_hostname_config["error"]}')

    tnc_acme_config = await acme_config()
    if tnc_acme_config['error']:
        raise Exception(f'Failed to fetch TN Connect ACME config: {tnc_acme_config["error"]}')

    hostnames = get_hostnames_from_hostname_config(tnc_hostname_config)
    csr, private_key = generate_csr(hostnames)
    authenticator_mapping = {f'DNS:{hostname}': TrueNASConnectAuthenticator() for hostname in hostnames}
    final_order = issue_certificate(tnc_acme_config['acme_details'], csr, authenticator_mapping)
    return update_tnc_config({
        'csr_public_key': csr,
        'certificate_public_key': final_order.fullchain_pem,
        'certificate_private_key': private_key,
        'initialization_completed': True,
        'initialization_in_progress': False,
    })

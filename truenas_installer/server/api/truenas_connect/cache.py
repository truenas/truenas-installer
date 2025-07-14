import json


CACHE_FILE = '/tmp/tnc.cache'


def default_tnc_config() -> dict:
    return {
        'jwt_token': None,
        'registration_details': {},
        'ips': [],
        'csr_public_key': None,
        'certificate_public_key': None,
        'certificate_private_key': None,
        'account_service_base_url': 'https://account-service.staging.truenasconnect.net/',
        'leca_service_base_url': 'https://dns-service.staging.truenasconnect.net/',
        'heartbeat_service_base_url': 'https://heartbeat-service.staging.truenasconnect.net/',
        'tnc_base_url': 'https://web.staging.truenasconnect.net/',
        'claim_token': None,
        'initialization_in_progress': False,
        'initialization_completed': False,
        'initialization_error': None,
        'system_id': None,
        'truenas_version': None,
        'enabled': False,
    }


def get_tnc_config() -> dict:
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.loads(f.read())
    except FileNotFoundError:
        return default_tnc_config()


def update_tnc_config(data: dict) -> dict:
    config = get_tnc_config() | data
    with open(CACHE_FILE, 'w') as f:
        f.write(json.dumps(config))

    return config

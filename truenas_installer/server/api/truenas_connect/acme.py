from truenas_connect_utils.acme import create_cert
from truenas_connect_utils.hostname import register_update_ips

from truenas_installer.network_interfaces import get_available_ip_addresses

from .cache import get_tnc_config, update_tnc_config


async def finalize_steps_after_registration() -> dict:
    # We would be doing the following here:
    # 1. Making sure we register/update ips with TNC so domains can point to that
    # 2. Initiate cert generation process and complete it
    tnc_config = get_tnc_config()
    detected_ips = await get_available_ip_addresses()
    all_ips = detected_ips['ipv4'] + detected_ips['ipv6']
    resp = await register_update_ips(tnc_config, all_ips, True)
    cert_details = await create_cert(tnc_config, resp['response'] or {})
    return update_tnc_config({
        'csr_public_key': cert_details['csr'],
        'certificate_public_key': cert_details['cert'],
        'certificate_private_key': cert_details['private_key'],
        'initialization_completed': True,
        'initialization_in_progress': False,
    })

from truenas_connect_utils.acme import create_cert
from truenas_connect_utils.hostname import register_update_ips, register_system_config

from .cache import get_tnc_config, update_tnc_config


async def finalize_steps_after_registration() -> dict:
    # We would be doing the following here:
    # 1. Register system configuration (including websocket port) with TNC
    # 2. Making sure we register/update ips with TNC so domains can point to that
    # 3. Initiate cert generation process and complete it
    tnc_config = get_tnc_config()

    # Register system configuration with TNC (use default HTTPS port 443 during installation)
    await register_system_config(tnc_config, 443)

    await register_update_ips(tnc_config, tnc_config['ips'] + tnc_config['interfaces_ips'], True)
    cert_details = await create_cert(tnc_config)
    return update_tnc_config({
        'csr_public_key': cert_details['csr'],
        'certificate_public_key': cert_details['cert'],
        'certificate_private_key': cert_details['private_key'],
        'initialization_completed': True,
        'initialization_in_progress': False,
    })

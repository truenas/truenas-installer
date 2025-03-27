import asyncio
import time

import jwt
from truenas_connect_utils.request import call
from truenas_connect_utils.urls import get_registration_finalization_uri

from .acme import finalize_steps_after_registration
from .cache import get_tnc_config, update_tnc_config


async def poll_once(config: dict) -> dict:
    return await call(
        get_registration_finalization_uri(config), 'post',
        payload={'system_id': config['system_id'], 'claim_token': config['claim_token']},
    )


async def finalize_registration():
    config = get_tnc_config()
    while time.time() < config['claim_token_expiration']:
        error = None
        status = await poll_once(config)
        if status['error'] is None:
            # We have got the key now and the registration has been finalized
            if 'token' not in status['response']:
                error = ('Registration finalization failed for TNC as token not '
                         f'found in response: {status["response"]}'),
            else:
                token = status['response']['token']
                decoded_token = {}
                try:
                    decoded_token = jwt.decode(token, options={'verify_signature': False})
                except jwt.exceptions.DecodeError:
                    error = 'Invalid JWT token received from TNC'
                else:
                    if diff := {'account_id', 'system_id'} - set(decoded_token):
                        error = f'JWT token does not contain required fields: {diff!r}'

            if error:
                config.update({
                    'initialization_completed': True,
                    'initialization_in_progress': False,
                    'initialization_error': error,
                })
                update_tnc_config(config)
            else:
                config.update({
                    'jwt_token': token,
                    'registration_details': decoded_token,
                })
                update_tnc_config(config)
                await finalize_steps_after_registration()

            # We either got the cert created or we errored out above
            return

        await asyncio.sleep(60)
    else:
        update_tnc_config(config | {
            'initialization_completed': True,
            'initialization_in_progress': False,
            'initialization_error': 'Timed out while waiting for finalizing registration',
        })

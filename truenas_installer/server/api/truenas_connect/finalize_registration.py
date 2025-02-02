import asyncio
import time

import jwt  # FIXME: Bring in jwt package dep

from .cache import tnc_config, update_tnc_config
from .urls import get_registration_finalization_uri
from .utils import call as tnc_call


async def poll_once(config: dict) -> dict:
    return await tnc_call(
        get_registration_finalization_uri(config), 'post',
        payload={'system_id': config['system_id'], 'claim_token': config['claim_token']},
    )


async def finalize_registration():
    config = tnc_config()
    while time.time() < config['registration_finalization_expiration']:
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
                        'initialization_in_progress': False,
                        'initialization_error': error,
                    })
                else:
                    config.update({
                        'jwt_token': token,
                        'registration_details': decoded_token,
                    })
                    # TODO: Trigger acme task

                update_tnc_config(config)
                return

        await asyncio.sleep(60)
    else:
        config.update({
            'initialization_in_progress': False,
            'initialization_error': 'Timed out while waiting for finalizing registration',
        })
        update_tnc_config(config)

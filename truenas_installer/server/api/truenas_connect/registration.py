import asyncio
import time

import jwt
from truenas_connect_utils.exceptions import CallError
from truenas_connect_utils.finalize import FinalizeResult, classify_finalize_response
from truenas_connect_utils.request import call
from truenas_connect_utils.urls import get_registration_finalization_uri

from .acme import finalize_steps_after_registration
from .cache import get_tnc_config, update_tnc_config
from .nginx import update_nginx_conf


async def poll_once(config: dict) -> dict:
    return await call(
        get_registration_finalization_uri(config), 'post',
        payload={'system_id': config['system_id'], 'claim_token': config['claim_token']},
    )


async def finalize_registration():
    config = get_tnc_config()
    while time.time() < config['claim_token_expiration']:
        status = await poll_once(config)
        result, description = classify_finalize_response(status)

        if result is FinalizeResult.RETRY:
            await asyncio.sleep(60)
            continue

        if result is FinalizeResult.TERMINAL:
            update_tnc_config({
                'initialization_completed': True,
                'initialization_in_progress': False,
                'initialization_error': f'Registration failed: {description}',
            })
            return

        # SUCCESS - decode token and run post-registration steps
        error = None
        token = status['response']['token']
        decoded_token: dict = {}
        try:
            decoded_token = jwt.decode(token, options={'verify_signature': False})
        except jwt.exceptions.DecodeError:
            error = 'Invalid JWT token received from TNC'
        else:
            if diff := {'account_id', 'system_id'} - set(decoded_token):
                error = f'JWT token does not contain required fields: {diff!r}'

        if error:
            update_tnc_config(config | {
                'initialization_completed': True,
                'initialization_in_progress': False,
                'initialization_error': error,
            })
            return

        update_tnc_config(config | {
            'jwt_token': token,
            'registration_details': decoded_token,
        })
        try:
            await finalize_steps_after_registration()
        except CallError as e:
            update_tnc_config({
                'initialization_completed': True,
                'initialization_in_progress': False,
                'initialization_error': f'Failed to generate certificate: {e}',
            })
        else:
            try:
                await asyncio.to_thread(update_nginx_conf)
            except Exception as e:
                update_tnc_config({
                    'initialization_completed': True,
                    'initialization_in_progress': False,
                    'initialization_error': f'Failed to update nginx config: {e}',
                })
        return
    else:
        update_tnc_config(config | {
            'initialization_completed': True,
            'initialization_in_progress': False,
            'initialization_error': 'Timed out while waiting for finalizing registration',
        })

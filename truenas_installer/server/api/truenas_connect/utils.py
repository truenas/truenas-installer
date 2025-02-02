import asyncio
import json

import aiohttp


def auth_headers(config: dict) -> dict:
    return {'Authorization': f'Bearer {config["jwt_token"]}'}


async def call(
    endpoint: str, mode: str, *, options: dict | None = None, payload: dict | None = None,
    headers: dict | None = None, json_response: bool = True,
) -> dict:
    options = options or {}
    timeout = options.get('timeout', 15)
    response = {'error': None, 'response': {}}
    if payload and (headers is None or 'Content-Type' not in headers):
        headers = headers or {}
        headers['Content-Type'] = 'application/json'
    try:
        async with asyncio.timeout(timeout):
            async with aiohttp.ClientSession(raise_for_status=True, trust_env=True) as session:
                req = await getattr(session, mode)(
                    endpoint,
                    data=json.dumps(payload) if payload else payload,
                    headers=headers,
                )
    except asyncio.TimeoutError:
        response['error'] = f'Unable to connect with TNC in {timeout} seconds.'
    except aiohttp.ClientResponseError as e:
        response['error'] = str(e)
    except aiohttp.ClientConnectorError as e:
        response['error'] = f'Failed to connect to TNC: {e}'
    else:
        response['response'] = await req.json() if json_response else await req.text()
    return response

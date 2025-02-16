import asyncio
import os
import textwrap

from .cache import tnc_config


CERT_DIR = '/etc/certificates'
CERT_PRIVATE_KEY = 'tn_connect_crt.key'
CERT_PUBLIC_KEY = 'tn_connect_crt.crt'
NGINX_CERT_CONF = '/etc/nginx/conf.d/cert.conf'


def generate_cert_files(crt: str, key: str):
    os.makedirs(CERT_DIR, exist_ok=True)
    for path, data in (
        (os.path.join(CERT_DIR, CERT_PUBLIC_KEY), crt),
        (os.path.join(CERT_DIR, CERT_PRIVATE_KEY), key),
    ):
        with open(path, 'w') as f:
            f.write(data)


async def update_nginx_conf():
    config = tnc_config()
    generate_cert_files(config['certificate_public_key'], config['certificate_private_key'])
    with open(NGINX_CERT_CONF, 'w') as f:
        f.write(textwrap.dedent(f'''
        listen                 0.0.0.0:443 default_server ssl http2;
        ssl_certificate        "{os.path.join(CERT_DIR, CERT_PUBLIC_KEY)}";
        ssl_certificate_key    "{os.path.join(CERT_DIR, CERT_PRIVATE_KEY)}";
        '''))
    await reload_nginx()


async def reload_nginx():
    process = await asyncio.create_subprocess_exec("systemctl", "restart", "nginx")
    await process.communicate()

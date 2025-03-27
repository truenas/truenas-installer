import os
import subprocess
import textwrap

from .cache import get_tnc_config


CERT_DIR = '/etc/certificates'
CERT_PRIVATE_KEY = 'tn_connect_crt.key'
CERT_PUBLIC_KEY = 'tn_connect_crt.crt'
NGINX_CERT_CONF = '/etc/nginx/conf.d/cert.conf'


def generate_cert_files(crt: str, key: str):
    os.makedirs(CERT_DIR, exist_ok=True)
    for path, data, perms in (
        (os.path.join(CERT_DIR, CERT_PUBLIC_KEY), crt, None),
        (os.path.join(CERT_DIR, CERT_PRIVATE_KEY), key, 0o400),
    ):
        with open(path, 'w') as f:
            if perms is not None:
                os.fchmod(f.fileno(), perms)
            f.write(data)


def update_nginx_conf():
    config = get_tnc_config()
    generate_cert_files(config['certificate_public_key'], config['certificate_private_key'])
    with open(NGINX_CERT_CONF, 'w') as f:
        f.write(textwrap.dedent(f'''
        listen                 0.0.0.0:443 default_server ssl http2;
        ssl_certificate        "{os.path.join(CERT_DIR, CERT_PUBLIC_KEY)}";
        ssl_certificate_key    "{os.path.join(CERT_DIR, CERT_PRIVATE_KEY)}";
        '''))
    reload_nginx()


def reload_nginx():
    subprocess.run(['systemctl', 'restart', 'nginx'], check=True)

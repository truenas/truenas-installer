import ipaddress

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID

from .cert_extensions_util import add_extensions


CERT_BACKEND_MAPPINGS = {
    'common_name': 'common',
    'country_name': 'country',
    'state_or_province_name': 'state',
    'locality_name': 'city',
    'organization_name': 'organization',
    'organizational_unit_name': 'organizational_unit',
    'email_address': 'email'
}


def normalize_san(san_list: list) -> list:
    # TODO: ADD MORE TYPES WRT RFC'S
    normalized = []

    for san in san_list or []:
        # Check if SAN is already prefixed
        if ':' in san:
            san_type, san_value = san.split(':', 1)
        else:
            # Determine if it's an IP or DNS entry
            try:
                ipaddress.ip_address(san)  # Validate as an IP address
                san_type = 'IP'
            except ValueError:
                san_type = 'DNS'
            san_value = san

        normalized.append([san_type, san_value])

    return normalized


def retrieve_signing_algorithm(data: dict):
    return getattr(hashes, data.get('digest_algorithm') or 'SHA256')()


def generate_private_key(options: dict) ->  str | rsa.RSAPrivateKey:
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=options.get('key_length'),
        backend=default_backend()
    )


def export_private_key_object(key: rsa.RSAPrivateKey) -> str:
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()


def generate_csr_builder(options: dict) -> x509.CertificateSigningRequestBuilder:
    """
    Generates a Certificate Signing Request (CSR) builder based on the provided options.
    """
    # Extract and normalize subject name
    subject_name = x509.Name([
        x509.NameAttribute(getattr(NameOID, k.upper()), v)
        for k, v in (options.get('crypto_subject_name') or {}).items() if v
    ])

    # Normalize `san`
    san_list = [
        x509.IPAddress(ipaddress.ip_address(value)) if kind == 'IP' else x509.DNSName(value)
        for kind, value in options.get('san') or []
    ]
    san_extension = x509.SubjectAlternativeName(san_list) if san_list else None

    # Create CSR builder
    csr_builder = x509.CertificateSigningRequestBuilder().subject_name(subject_name)

    # Add SAN extension if present
    if san_extension:
        csr_builder = csr_builder.add_extension(san_extension, critical=False)

    return csr_builder


def generate_certificate_signing_request(data: dict) -> tuple[str, str]:
    key = generate_private_key({
        'key_length': 2048,
    })

    csr = generate_csr_builder({
        'crypto_subject_name': {
            k: data.get(v) for k, v in CERT_BACKEND_MAPPINGS.items()
        },
        'san': normalize_san(data.get('san') or []),
        'serial': data.get('serial'),
        'lifetime': data.get('lifetime'),
        'csr': True
    })

    csr = add_extensions(csr, data.get('cert_extensions', {}), key, None)
    csr = csr.sign(key, retrieve_signing_algorithm(data), default_backend())

    return csr.public_bytes(serialization.Encoding.PEM).decode(), export_private_key_object(key)

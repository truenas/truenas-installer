TNC_CONFIG_SCHEMA = {
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'type': 'object',
    'properties': {
        'jwt_token': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'registration_details': {'type': 'object', 'additionalProperties': True},
        'ips': {'type': 'array', 'items': {'type': 'string'}},
        'csr_public_key': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'certificate_public_key': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'certificate_private_key': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'account_service_base_url': {'type': 'string'},
        'leca_service_base_url': {'type': 'string'},
        'tnc_base_url': {'type': 'string'},
        'claim_token': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'claim_token_expiration': {'oneOf': [{'type': 'null'}, {'type': 'number'}]},
        'registration_finalization_expiration': {'oneOf': [{'type': 'null'}, {'type': 'number'}]},
        'system_id': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'truenas_version': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'initialization_in_progress': {'enabled': {'type': 'boolean'},},
        'initialization_completed': {'enabled': {'type': 'boolean'},},
        'initialization_error': {'oneOf': [{'type': 'null'}, {'type': 'string'}]},
        'enabled': {'type': 'boolean'},
    },
    'required': [
        'jwt_token', 'registration_details', 'ips', 'certificate_public_key', 'certificate_private_key',
        'csr_public_key', 'account_service_base_url', 'leca_service_base_url', 'tnc_base_url', 'claim_token',
        'registration_finalization_expiration', 'enabled', 'systemd_id', 'truenas_version',
        'initialization_in_progress', 'initialization_completed', 'initialization_error',
    ],
}

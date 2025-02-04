import json
import logging
import requests
import time

from .cache import tnc_config as retrieve_tnc_config
from .urls import get_leca_cleanup_url, get_leca_dns_url
from .utils import auth_headers


logger = logging.getLogger()


class TrueNASConnectAuthenticator:

    NAME = 'tn_connect'
    PROPAGATION_DELAY = 20

    def perform(self, domain, validation_name, validation_content):
        try:
            perform_ret = self._perform(domain, validation_name, validation_content)
        except Exception as e:
            raise Exception(f'Failed to perform {self.NAME} challenge for {domain!r} domain: {e}')
        else:
            self.wait_for_records_to_propagate(perform_ret)

    def wait_for_records_to_propagate(self, perform_ret):
        time.sleep(self.PROPAGATION_DELAY)

    def cleanup(self, domain, validation_name, validation_content):
        try:
            self._cleanup(domain, validation_name, validation_content)
        except Exception as e:
            raise Exception(f'Failed to cleanup {self.NAME} challenge for {domain!r} domain: {e}')

    def _perform(self, domain, validation_name, validation_content):
        try:
            self._perform_internal(domain, validation_name, validation_content)
        except Exception as e:
            raise Exception(f'Failed to perform {self.NAME} challenge for {domain!r} domain: {e}')

    def _perform_internal(self, domain, validation_name, validation_content):
        logger.debug(
            'Performing %r challenge for %r domain with %r validation name and %r validation content',
            self.NAME, domain, validation_name, validation_content,
        )
        tnc_config = retrieve_tnc_config()
        try:
            response = requests.post(get_leca_dns_url(tnc_config), data=json.dumps({
                'token': validation_content,
                'hostnames': [domain],  # We should be using validation name here
            }), headers=auth_headers(tnc_config), timeout=30)
        except requests.Timeout:
            raise Exception(f'Timeout while performing {self.NAME} challenge for {domain!r} domain')

        if response.status_code != 201:
            raise Exception(
                f'Failed to perform {self.NAME} challenge for {domain!r} domain with '
                f'{response.status_code!r} status code: {response.text}'
            )

        logger.debug('Successfully performed %r challenge for %r domain', self.NAME, domain)

    def _cleanup(self, domain, validation_name, validation_content):
        logger.debug('Cleaning up %r challenge for %r domain', self.NAME, domain)
        tnc_config = retrieve_tnc_config()
        try:
            requests.delete(
                get_leca_cleanup_url(tnc_config), headers=auth_headers(tnc_config), timeout=30, data=json.dumps({
                    'hostnames': [validation_name],  # We use validation name here instead of domain as Zack advised
                })
            )
        except Exception:
            # We do not make this fatal as it does not matter if we fail to clean-up
            logger.debug('Failed to cleanup %r challenge for %r domain', self.NAME, domain, exc_info=True)

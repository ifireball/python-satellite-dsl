#!/usr/bin/env python
"""foreman-ans-to-nailgun-conf.py - Create Nailgun default configuration from
the foreman answer file.

This script assumes it is running from the Foreman machine after a fresh
Foreman install, from a user that has full sudo access
"""
import sys
import yaml
import logging
from subprocess import check_output
from os.path import exists

import nailgun.config

FOREMAN_ANS_FILE = '/etc/foreman-installer/scenarios.d/foreman-answers.yaml'
KATELLO_ANS_FILE = '/etc/katello-installer/answers.katello-installer.yaml'


def main():
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    foreman_answers_yaml = next((
        check_output(('sudo', 'cat', ans_file))
        for ans_file in (FOREMAN_ANS_FILE, KATELLO_ANS_FILE)
        if exists(ans_file)
    ), None)
    if foreman_answers_yaml is None:
        raise RuntimeError('Foreman/Katello answer file not found')
    foreman_answers = yaml.load(foreman_answers_yaml)

    foreman_credentials = dict(
        url=foreman_answers['foreman']['foreman_url'],
        auth=(
            foreman_answers['foreman']['admin_username'],
            foreman_answers['foreman']['admin_password']
        ),
    )
    logger.debug('Details detected from Foreman answer file:')
    logger.debug('  URL: %s', foreman_credentials['url'])
    logger.debug('  Admin user: %s', foreman_credentials['auth'][0])
    logger.debug('  Admin password: %s', foreman_credentials['auth'][1])

    satellite = nailgun.config.ServerConfig(
        verify=False,
        **foreman_credentials
    )
    logger.info('Writing naigun default configuration')
    satellite.save()


if __name__ == '__main__':
    sys.exit(main() or 0)

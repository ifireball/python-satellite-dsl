#!/usr/bin/env python
"""satellite6/configuration.py - Automate configuration of Satellite 6

To use this script you need to configure the default connection parameters for
NailGun. You can do this with something like the following:

    import nailgun.config

    satellite = nailgun.config.ServerConfig(
        url='https://satellite6-ops.rhev-ci-vms.eng.rdu2.redhat.com',
        auth=('YOURUSER', 'PASSWORD'),
        verify=False,
    )
    satellite.save()

"""
import sys
import logging

import satellite_dsl
from satellite_dsl import ensure

from nailgun.entities import (
    Location,
    Organization,
    HostGroup,
    OperatingSystem,
    Architecture,
    Media,
    PartitionTable,
)


def main():
    """The main body of work, this is where the actual Satellite configutration
    resides, there rest is just the DSL implementation
    """
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    satellite_dsl.LOGGER.setLevel(logging.INFO)

    logger.info("Beginning Katello configuration")

    # We 'ensure' pre-created objects to gain access to them so we can refernece
    # them in objects we create
    main_org = ensure(Organization, name='Default Organization')
    locations = [ensure(Location, name='Default Location')]
    organizations = [main_org]

    x86_64 = ensure(Architecture, name='x86_64')
    centos_mirror = ensure(Media, name='CentOS mirror')
    centos7_2 = ensure(
        OperatingSystem,
        name='CentOS', major=7, minor=2,
        medium=[centos_mirror],
    )
    ksd_ptable = ensure(PartitionTable, name='Kickstart default')

    ensure(
        HostGroup,
        name='test_hg',
        location=locations,
        organization=organizations,
        architecture=x86_64,
        operatingsystem=centos7_2,
        medium=centos_mirror,
        ptable=ksd_ptable,
    )

    logger.info("Katello configuration complete")


if __name__ == '__main__':
    sys.exit(main() or 0)

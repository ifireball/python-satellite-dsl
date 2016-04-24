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

import satellite_ensurer
from satellite_ensurer import ensure

from nailgun.entities import (
    Location,
    Organization,
    HostGroup,
    OperatingSystem,
    LifecycleEnvironment,
    Subscription,
    Architecture,
    Media,
    PartitionTable,
    Domain,
    Subnet,
    SmartProxy,
)


def main():
    """The main body of work, this is where the actual Satellite configutration
    resides, there rest is just the DSL implementation
    """
    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    satellite_ensurer.LOGGER.setLevel(logging.INFO)

    logger.info("Beginning Satellite configuration")

    # TODO: create some kind of context to not need variables for things that
    # everyting will reference like organization and location
    main_org = ensure(Organization, name='RHEVM-DEV-CI')
    locations = [ensure(Location, name='TLV')]
    organizations = [main_org]

    # TODO: Somehow make capsole detection less instance-specific
    boot_capsule = ensure(
        SmartProxy,
        name='capsule-ops.qa.lab.tlv.redhat.com',
    )
    puppet_capsule = ensure(
        SmartProxy,
        name='capsule-rhevm-ci-puppet.eng.lab.tlv.redhat.com',
    )

    employee_sku = ensure(
        Subscription,
        product_name='Employee SKU',
        organization=main_org
    )
    assert employee_sku  # Make pyflakes not warn about unused variable

    # TODO: use employee_sku to ensure Red Hat products are synced and assign
    # them into content views

    library_env = ensure(
        LifecycleEnvironment,
        name='Library',
        organization=main_org,
    )
    pre_prod_env = ensure(
        LifecycleEnvironment,
        name='PreProd',
        organization=main_org,
        prior=library_env,
    )
    prod_env = ensure(
        LifecycleEnvironment,
        name='Production',
        organization=main_org,
        prior=pre_prod_env,
    )

    ci_dom = ensure(
        Domain,
        name='ci.lab.tlv.redhat.com',
        location=locations,
        organization=organizations,
    )
    ensure(
        Subnet,
        name='10.35.148.x',
        network='10.35.148.0',
        mask='255.255.252.0',
        gateway='10.35.151.254',
        dns_primary='10.35.28.28',
        dns_secondary='10.35.28.1',
        ipam='DHCP',
        boot_mode='DHCP',
        domain=[ci_dom],
        location=locations,
        organization=organizations,
        tftp=boot_capsule,
    )
    ensure(
        Subnet,
        name='10.35.32.x',
        network='10.35.32.0',
        mask='255.255.240.0',
        gateway='10.35.47.254',
        dns_primary='10.35.28.28',
        dns_secondary='10.35.28.1',
        ipam='DHCP',
        boot_mode='DHCP',
        domain=[ci_dom],
        location=locations,
        organization=organizations,
        tftp=boot_capsule,
    )

    x86_64 = ensure(Architecture, name='x86_64')
    rhel71 = ensure(OperatingSystem, name='RedHat', major=7, minor=1)
    rhel71_medium = ensure(
        Media,
        name='RHEVM/Library/Red_Hat_7_Server_Kickstart_x86_64_7_1'
    )
    ksd_ptable = ensure(PartitionTable, name='Kickstart default')

    ensure(
        HostGroup,
        name='test_hg',
        location=locations,
        organization=organizations,
        lifecycle_environment=prod_env,
        architecture=x86_64,
        operatingsystem=rhel71,
        medium=rhel71_medium,
        ptable=ksd_ptable,
        domain=ci_dom,
    )

    logger.info("Satellite configuration complete")


if __name__ == '__main__':
    sys.exit(main() or 0)

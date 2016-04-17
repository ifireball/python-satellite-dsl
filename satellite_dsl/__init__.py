#!/usr/bin/env python
"""A Mini-DSL for doing puppet-like declerative configuration of Satellite 6
"""
from logger import LOGGER

from entity_ensurer import EntityEnsurer
import life_cycle_environment_ensurer
import operating_system_ensurer
import product_ensurer
import subscription_ensurer

# to make pyflakes happy
assert LOGGER
assert life_cycle_environment_ensurer
assert operating_system_ensurer
assert product_ensurer
assert subscription_ensurer


def ensure(entity_cls, **attrs):
    """Ensures that a Satellite entity of the given class exists and has its
    attributes set to the given values.

    :param type entity_cls: The (nailgun) class of the Satellte entity to be
                            managed
    :param str name: The name of the entity to be managed

    Other named parameters are taken as attributes for the manage entity.

    :returns: A pointer to the entity that was created that can be assigned to
              other entities` link attributes (Please do no assume that is an
              entity object - this is subject to change)
    """
    # TODO: Do not ensure directly instead create an object to be
    #       used later when ensuring in bulk
    # TODO: Ensure things that are not NailGun classes
    ensurer = EntityEnsurer(entity_cls)
    return ensurer.ensure(entity_cls, **attrs)

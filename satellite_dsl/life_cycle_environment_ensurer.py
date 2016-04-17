#!/usr/bin/env python
"""A class fo ensuring existance of nailgun LifeCycleEnvironment entities
"""
import nailgun.entities

from type_handler import type_handler

from entity_ensurer import EntityEnsurer
from org_context_entity_ensurer import OrgContextEntityEnsurer


@type_handler(
    fortype=nailgun.entities.LifecycleEnvironment,
    incls=EntityEnsurer
)
class LifecycleEnvironmentEnsurer(OrgContextEntityEnsurer):
    """Ensurer class for LifecycleEnvironment entities
    """

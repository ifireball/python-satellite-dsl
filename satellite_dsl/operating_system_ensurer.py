#!/usr/bin/env python
"""A class fo ensuring existance of nailgun OperatingSystem entities
"""
import nailgun.entities

from type_handler import type_handler

from entity_ensurer import EntityEnsurer


@type_handler(fortype=nailgun.entities.OperatingSystem, incls=EntityEnsurer)
class OperatingSystemEnsurer(EntityEnsurer):
    """Ensurer class for OperatingSystem entities
    """
    def _format_self_entity(self, entity):
        """Format an OperatingSystem entity for dispaly

        :param nailgun.entities.OperatingSystem entity: The entity to format
        :returns: A string represenation of the entity
        :rtype: str
        """
        try:
            key = self.extract_key_attrs(entity.get_values())
            key_str = '"{name} {major}.{minor}"'.format(**key)
        except TypeError:
            key_str = '#{}'.format(entity.id)
        return '{} {}'.format(entity.__class__.__name__, key_str)

    def extract_key_attrs(self, attrs):
        """Extract and validate the existace of the entity key attributes
        from the given attribute dictionary

        :param dict attrs: The attribute dictionary in which to search key
                        attributes
        :returns: A dictionary of key attribute
        :rtype: dict
        """
        try:
            key = dict(
                (attr, attrs[attr])
                for attr in ('name', 'major', 'minor')
            )
            return key
        except KeyError as kerr:
            raise TypeError(
                "Missing entity key attibute: {}".format(kerr.args[0])
            )

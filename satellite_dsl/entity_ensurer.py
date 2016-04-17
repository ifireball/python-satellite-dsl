#!/usr/bin/env python
"""A class fo ensuring existance of nailgun entities
"""
from pprint import pformat
from requests import HTTPError
from itertools import izip_longest
import nailgun.entities

from type_handler import type_handler
from nailgun_hacks import entity_search_by_attrs

from logger import LOGGER


@type_handler(fortype=nailgun.entities.Entity)
class EntityEnsurer(object):
    """Class for encupsulating code that ensures that a Satellite entity of a
    given type and properties exists
    """
    def ensure(self, entity_cls, **attrs):
        """Ensures that a Satellite entity of the given class exists and has
        its attributes set to the given values.

        :param type entity_cls: The (nailgun) class of the Satellte entity to
                                be managed

        Other named parameters are taken as attributes for the manage entity.

        :returns: A pointer to the entity that was created that can be assigned
                  to other entities` link attributes (Please do no assume that
                  is an entity object - this is subject to change)
        """
        template = self.entity_from_attrs(entity_cls, attrs)
        LOGGER.debug('template: %s', pformat(template.get_values()))
        existing = self.find_by_key(entity_cls, **attrs)
        if existing:
            existing_data = existing[0].read()
            LOGGER.debug('existing: %s', pformat(existing_data.get_values()))
            template.id = existing_data.id
            if self.similar_entities(existing_data, template):
                LOGGER.info(
                    'Unchanged entitiy: %s',
                    self.format_entity(existing_data)
                )
                return existing_data
            else:
                self.log_entity_diff(existing_data, template)
        return self.update_or_create(template)

    def entity_from_attrs(self, entity_cls, attrs):
        """Create and entity from the given class and attributes while
        validating the given attributes should really exist for that entity
        class

        :param type entity_cls: The class of the entity to create
        :param str name: The name of the entity to be created
        :param dict attrs: The attributes to be assigned to the entity
        :returns: The created entity
        :rtype nailgun.entities.Entity
        """
        entity = entity_cls()
        fields = entity.get_fields()
        for attr, value in attrs.iteritems():
            if attr not in fields:
                raise AttributeError(
                    "Entities of type '{}' do not have an '{}' attribute"
                    .format(entity_cls.__name__, attr)
                )
            # TODO: Validate value type
            setattr(entity, attr, value)
        return entity

    def find_by_key(self, entity_cls, **attrs):
        """Find an entity by its key attributes

        :param type entity_cls: The class of entity to look for

        The rest of the keyword arguments are the attributes comprising the
        entity key

        :returns: The found entity
        :rtype nailgun.entities.Entity
        """
        key = self.extract_key_attrs(attrs)
        context = self.extract_context(attrs)
        return entity_search_by_attrs(
            entity_cls,
            context=context,
            **key
        )

    def update_or_create(self, entity):
        """If the given entity has the 'id' attribute set, try to update it.
        If not, or if the update failes because the entity doesn't exist, try
        to creat it instead.

        :param nailgun.entities.Entity entity: The entity to create
        :returns: The entity object that was created
        :rtype nailgun.entities.Entity
        """
        if hasattr(entity, 'id') and entity.id is not None:
            try:
                updated = entity.update()
                LOGGER.info('Updated entity: %s', self.format_entity(updated))
                return updated
            except HTTPError as httpe:
                if httpe.response.status_code != 404:
                    raise
        created = entity.create()
        LOGGER.info('Created entity: %s', self.format_entity(created))
        return created

    def similar_entities(self, entity_a, entity_b):
        """Compares two entities. Entities are considered similar if all common
        attributes have the same valus.

        :param nailgun.entities.Entity entity_a: 1st entity to be compared
        :param nailgun.entities.Entity entity_b: 2nd entity to be compared

        :retrurns: Wither the entities are similar or not
        :rtype: bool
        """
        if type(entity_a) != type(entity_b):
            raise TypeError(
                "Entities passed to 'similar_entities' must be of the same " +
                "type"
            )
        cmn_attrs = \
            set(entity_a.get_values()).intersection(set(entity_b.get_values()))
        return next(
            (
                False for attr in cmn_attrs
                if not
                self.similar_values(
                    getattr(entity_a, attr),
                    getattr(entity_b, attr)
                )
            ),
            True
        )

    def similar_values(self, value_a, value_b):
        """Compare entity values, returns if tye are to be considered equivalent
        (Same value or pointing to same entity)

        :param object entity_a: 1st value to be compared
        :param object entity_b: 2nd value to be compared

        :returns: Wither the values are similar or not
        :rtype: bool
        """
        if value_a is None and value_b is not None:
            return False
        elif value_a is not None and value_b is None:
            return False
        elif hasattr(value_a, 'id') and hasattr(value_b, 'id'):
            return value_a.id == value_b.id
        elif hasattr(value_a, '__iter__') and hasattr(value_b, '__iter__'):
            return next(
                (
                    False for sva, svb in izip_longest(value_a, value_b)
                    if not self.similar_values(sva, svb)
                ),
                True
            )
        else:
            try:
                value_a = int(value_a)
            except (TypeError, ValueError):
                value_a = str(value_a)
            try:
                value_b = int(value_b)
            except (TypeError, ValueError):
                value_b = str(value_b)
            return value_a == value_b

    def log_entity_diff(self, existing, wanted):
        """Log the needed chjanges to an entity

        :param nailgun.entities.Entity existing: The esiting state of the
                                                 entity
        :param nailgun.entities.Entity wanted: The wanted state of the entity
        """
        if type(existing) != type(wanted):
            raise TypeError(
                "Entities passed to 'similar_entities' must be of the same " +
                "type"
            )
        cmn_attrs = \
            set(existing.get_values()).intersection(set(wanted.get_values()))
        for attr in cmn_attrs:
            existing_val = getattr(existing, attr)
            wanted_val = getattr(wanted, attr)
            if not self.similar_values(existing_val, wanted_val):
                LOGGER.info(
                    '%s %s attribute is %s, should be %s',
                    self.format_entity(existing),
                    attr,
                    self.format_attr(existing_val),
                    self.format_attr(wanted_val)
                )

    def format_entity(self, entity):
        """Format an entity for dispaly

        :param nailgun.entities.Entity entity: The entity to format
        :returns: A string represenation of the entity
        :rtype: str
        """
        return EntityEnsurer(type(entity))._format_self_entity(entity)

    def _format_self_entity(self, entity):
        """Format an entity for dispaly while assuming the entity is of a type
        handled by this class

        :param nailgun.entities.Entity entity: The entity to format
        :returns: A string represenation of the entity
        :rtype: str
        """
        try:
            key_str = '"{}"'.format(entity.name)
        except AttributeError:
            key_str = '#{}'.format(entity.id)
        return '{} {}'.format(entity.__class__.__name__, key_str)

    def format_attr(self, value):
        """Format an entity attribute value for display

        :param object value: The value to format
        :returns: If the value is an Entity reference, return the entity name,
                otherwise just call 'str'
        :rtype: str
        """
        if isinstance(value, nailgun.entities.Entity):
            return self.format_entity(value)
        elif hasattr(value, '__iter__'):
            return pformat([self.format_attr(aval) for aval in value])
        else:
            return str(value)

    def extract_key_attrs(self, attrs):
        """Extract and validate the existace of the entity key attributes
        from the given attribute dictionary

        :param dict attrs: The attribute dictionary in which to search key
                        attributes
        :returns: A dictionary of key attribute
        :rtype: dict
        """
        try:
            key = {'name': attrs['name']}
            return key
        except KeyError as kerr:
            raise TypeError(
                "Missing entity key attibute: {}".format(kerr.args[0])
            )

    def extract_context(self, attrs):
        """Extract and validate the existace of the search context for the given
        entity class from the given attribute dictionary

        :param dict attrs: The attribute dictionary in which to search context
                           attributes
        :returns: A search context
        :rtype: dict
        """
        return {}

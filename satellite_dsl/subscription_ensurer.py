#!/usr/bin/env python
"""A class fo ensuring existance of nailgun Subscription entities
"""
import nailgun.entities

from type_handler import type_handler
from nailgun_hacks import (
    build_entity_attr_query,
    satellite_get_entities,
)

from logger import LOGGER
from entity_ensurer import EntityEnsurer


@type_handler(fortype=nailgun.entities.Subscription, incls=EntityEnsurer)
class SubscriptionEnsurer(EntityEnsurer):
    """Ensurer class for Subscription entities

    This class cannot catually create subscriptions, only verify their
    existance within a given organisation
    """
    def ensure(self, entity_cls, product_name, organization):
        """Verify that a Subscription with the given product name exists for
        the given organization

        :param type entity_cls: Expected to be Subscription, only included for
                                method signiture compatibility.
        :param str product_name: The product name for the subscription
        :param nailgun.entities.Organization organization: The organization
                                                           entity
        :rturns: An entity representing the subscription (an exception is
                 raised if no matching subscription is found)
        :rtype: nailgun.entities.Subscription
        """
        entities = self.find_by_key(
            entity_cls=entity_cls,
            product_name=product_name,
            organization=organization
        )
        if not entities:
            raise KeyError(
                'Subscription with product: {} and org: {} not found'
                .format(product_name, self.format_entity(organization))
            )
        LOGGER.info('Unchanged entitiy: %s', self.format_entity(entities[0]))
        return entities[0]

    def find_by_key(self, entity_cls, product_name, organization):
        """Find a Subscription for given organization and product

        :param type entity_cls: The class of entity to look for
        :param str product_name: The product name for the subscription
        :param nailgun.entities.Organization organization: The organization

        :returns: The found Subscription
        :rtype nailgun.entities.Subscription
        """
        path = 'katello/api/v2/organizations/{}/subscriptions'.format(
            organization.id
        )
        data = dict(search=build_entity_attr_query(product_name=product_name))
        entities = satellite_get_entities(
            entity_cls=nailgun.entities.Subscription,
            query_path=path,
            query_data=data,
        )
        return entities

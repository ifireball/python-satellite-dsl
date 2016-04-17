#!/usr/bin/env python
"""A class fo ensuring existance of nailgun Product entities
"""
import nailgun.entities

from type_handler import type_handler
from nailgun_hacks import (
    satellite_get_response,
    satellite_json_to_entity,
)

from entity_ensurer import EntityEnsurer
from org_context_entity_ensurer import OrgContextEntityEnsurer


# The code in the class below is mostly ment as a workaround for:
# - https://bugzilla.redhat.com/show_bug.cgi?id=1256645
# - https://bugzilla.redhat.com/show_bug.cgi?id=1256717
# But the workaround does not work yet, therefor the ensurer cannot be
# properly used with non-custom products (E.g. the 'subscription' propery
# should never be specified for an ensured product)
@type_handler(fortype=nailgun.entities.Product, incls=EntityEnsurer)
class ProductEnsurer(OrgContextEntityEnsurer):
    """Ensurer class for Product entities

    Product entities can either be custom products that always belong to
    organizations and can be handled just like any other entity that requires
    organization_id as search context, or products that are provided by
    subscriptions which can not be searched or created.

    The way this ensurer behaves is that is subscription is provided as a
    product propery, the product will simply be searched by name on the given
    subscription and never created.
    """
    def ensure(self, entity_cls, **attrs):
        """Verify that a product with the given properties can be found under
        the specified subscription or exists as a custom product with the given
        attributes if subscription unspecified

        :param type entity_cls: The (nailgun) class of the Satellte entity to
                                be managed

        :returns: A pointer to the entity that was created that can be assigned
                  to other entities` link attributes (Please do no assume that
                  is an entity object - this is subject to change)
        """
        if 'subscription' in attrs:
            return self.ensure_in_context(self, **attrs)
        else:
            return super(type(self), self).ensure(entity_cls, **attrs)

    def ensure_in_context(self, subscription, name):
        """Ensure that a Product with the given name exists in the given
        subscription

        :param str name: The product name
        :param nailgun.entities.Subscription subscription: The subscription for
                                                           the product
        :rturns: An entity representing the product (an exception is raised
                 if no matching product is found)
        :rtype: nailgun.entities.Product
        """
        try:
            self._products_in_subscriptions
        except AttributeError:
            self._products_in_subscriptions = {}
        try:
            return self._products_in_subscriptions.setdefault(
                subscription.id,
                self._get_products_in_subscription(subscription)
            )[name]
        except KeyError:
            raise KeyError(
                'Product in: {} with name: {} not found'
                .format(self.format_entity(subscription, name))
            )

    def _get_products_in_subscription(self, subscription):
        """Returns a dictionariy mapping product names to Product entities for
        the products in the given subscription

        :param nailgun.entities.Subscription subscription: The subscription
        :rtype: dict
        """
        path = 'katello/api/v2/subscriptions/{}'.format(subscription.id)
        subscription_json = satellite_get_response(path)
        name_dict = dict(
            (
                prod_json['name'],
                satellite_json_to_entity(prod_json, nailgun.entities.Product)
            )
            for prod_json in subscription_json['provided_products']
        )
        return name_dict

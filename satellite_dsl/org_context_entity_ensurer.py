#!/usr/bin/env python
from entity_ensurer import EntityEnsurer


class OrgContextEntityEnsurer(EntityEnsurer):
    """Ensurer base class for entities for which organization_id must be
    specified as a search context
    """
    def extract_context(self, attrs):
        """Extract and validate the existace of the search context for the given
        entity class from the given attribute dictionary

        :param dict attrs: The attribute dictionary in which to search context
                           attributes
        :returns: A search context
        :rtype: dict
        """
        try:
            return {'organization_id': attrs['organization'].id}
        except KeyError as kerr:
            raise TypeError(
                "Missing entity search context attibute: {}"
                .format(kerr.args[0])
            )

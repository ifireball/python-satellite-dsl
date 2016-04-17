#!/usr/bin/env python
"""Some supplements to the NailGun library

Mostly to enable searching and querying agains Satellite
"""
from re import match

import nailgun.config
import nailgun.client
import nailgun.entities

try:
    # Hide ugly warning about no ssl cert verification
    nailgun.client.requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass


def entity_index(
    entity_cls,
    context={},
    server_config=nailgun.config.ServerConfig.get()
):
    """Returns all visible entities of the given entity class

    :param type entity_cls: The class of the entity to be listed
    :param str context: Addtional context parameters for the query (some
                        classes require these in order to be queried)
    :param nailgun.config.ServerConfig server_config: Connection information
    :returns: A list of objects of type 'entity_cls' ready to be read()
    """
    entities = satellite_get_entities(
        entity_cls=entity_cls,
        query_path=entity_cls().path(),
        query_data=context,
        server_config=server_config
    )
    return entities


def entity_search_by_attrs(
    entity_cls,
    server_config=nailgun.config.ServerConfig.get(),
    context={},
    **attrs
):
    """Search satellite for entities of the given class by the given attributs
    and values

    :param type entity_cls: The class of the entity to be searched
    :param nailgun.config.ServerConfig server_config: Connection information
    :param str context: Addtional context parametes for the query (some classes
                        require these in order to be queried)

    All other keyword params are taken to be entity attributes and values to
    compare against

    :returns: A list of objects of type 'entity_cls' ready to be read()
    """
    # TODO: Validate attrs against entity_cls
    return entity_search(
        entity_cls=entity_cls,
        query=build_entity_attr_query(**attrs),
        context=context,
        server_config=server_config
    )


def build_entity_attr_query(**attrs):
    """Build a foreman query from the given attribute name and value pairs
    """
    query = ' and '.join(
        '{} = {}'.format(attr, format_entity_query_value(value))
        for attr, value in attrs.iteritems()
    )
    return query


def format_entity_query_value(value):
    """Format and if needed, quote a value to be place in an entity search query
    """
    value_s = str(value)
    if len(value_s.split()) > 1:
        return '"{}"'.format(value_s.replace('"', '\\"'))
    else:
        return value_s


def entity_search(
    entity_cls,
    query,
    context={},
    server_config=nailgun.config.ServerConfig.get()
):
    """Search satellite for entities of the given class

    :param type entity_cls: The class of the entity to be searched
    :param str query: The query string to filter entites by
    :param str context: Addtional context parameters for the query (some
                        classes require these in order to be queried)
    :param nailgun.config.ServerConfig server_config: Connection information
    :returns: A list of objects of type 'entity_cls' ready to be read()
    """
    data = {}
    data.update(search=query)
    data.update(context)
    entities = satellite_get_entities(
        entity_cls=entity_cls,
        query_path=entity_cls().path(),
        query_data=data,
        server_config=server_config
    )
    return entities


def satellite_get_entities(
    entity_cls,
    query_path,
    query_data,
    server_config=nailgun.config.ServerConfig.get()
):
    """Run HTTP query against Satellite 6 and return Nailgun entities

    :param type entity_cls: The class of the entity to be returned (Not actual
                            type matching of the query results and the class is
                            done, this is up to the user)
    :param str query_path: The API path to query against
    :param str query_data: The HTTP GET parameters to send woth the query
    :param nailgun.config.ServerConfig server_config: Connection information
    :returns: A list on Nailgun entities
    :rtype: list
    """
    json = satellite_get_response(query_path, query_data, server_config)
    entities = satellite_json_to_entities(
        json=json['results'],
        entity_cls=entity_cls,
        server_config=server_config,
    )
    return entities


def satellite_json_to_entities(
    json,
    entity_cls,
    server_config=nailgun.config.ServerConfig.get()
):
    """Convert JSON data returned from satellite into Nailgun entities

    :param type entity_cls: The class of the entity to be returned (Not actual
                            type matching of the json data and the class is
                            done, this is up to the user)
    :param list json: A JSON list containing entities returned from Satellite
    :param nailgun.config.ServerConfig server_config: Connection information
    :returns: A list on Nailgun entities
    :rtype: list
    """
    entities = [
        satellite_json_to_entity(ent_json, entity_cls, server_config)
        for ent_json in json
    ]
    return entities


def satellite_json_to_entity(
    json,
    entity_cls,
    server_config=nailgun.config.ServerConfig.get()
):
    """Convert JSON data returned from satellite into Nailgun entity

    :param type entity_cls: The class of the entity to be returned (Not actual
                            type matching of the json data and the class is
                            done, this is up to the user)
    :param dict json: A JSON dict returned from Satellite
    :param nailgun.config.ServerConfig server_config: Connection information
    :returns: A Nailgun entity (of type entity_cls)
    :rtype: nailgun.entities.Entity
    """
    entity = entity_cls(server_config, id=json['id'])
    return entity


def satellite_get_response(
    query_path,
    query_data={},
    server_config=nailgun.config.ServerConfig.get()
):
    """Run HTTP query against Satellite 6

    :param str query_path: The API path to query against
    :param str query_data: The HTTP GET parameters to send woth the query
    :param nailgun.config.ServerConfig server_config: Connection information
    :returns: A parsed json response data structure
    :rtype: dict
    """
    if not match('https?://', query_path):
        query_path = server_config.url + '/' + query_path.strip('/')
    response = nailgun.client.get(
        query_path,
        data=query_data,
        **server_config.get_client_kwargs()
    )
    response.raise_for_status()
    return response.json()

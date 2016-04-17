#!/usr/bin/env python
"""This module provides a decorator that can be used to create type handler
singleton classes

Type handlers are classes that can be called with a type and always return a
specific instance meant to handle that type. Different classes can be
registered into the same class to handle different types. Inheritance rules
apply so that if class B is subclass of B, a handler for A will be returned
unless a handler for B was registered
"""


class TypeHandler(type):
    """A metaclass for creating classes which instances are handlers for given
    types so that the same handler instance is always returned for the same
    type unless a new handler was registered (enssentially these are
    singletones looked up by type, with the lookup supporting inheritance)
    """
    _handlers = {}

    def __call__(cls, handled_type):
        for parent in handled_type.__mro__:
            try:
                return cls._handlers[parent]
            except KeyError:
                pass
        raise TypeError(
            'Class {} has no handler in {}'.format(str(handled_type), str(cls))
        )
        pass

    def register_handler(cls, handled_type, handler_cls):
        """Registers a class as the handler for a given type

        :param type cls: The class to register the handler into
        :param type handled_type: The type the handler is for
        :param type handler_cls: The handler class being registered
        :returns: handler_cls
        :rtype: type
        """
        cls._handlers[handled_type] = \
            super(TypeHandler, handler_cls).__call__()
        return handler_cls


def type_handler(fortype, incls=None):
    """A decorator to create and register type handler classes

    :param type fortype: The type for which the decoratede class is a handler
    :param TypeHandler incls: The class in which the handler class is to be
                              registered if not given then the handler class is
                              registered in itself
    """
    if incls:
        def register_handler(cls):
            return incls.register_handler(fortype, cls)
    else:
        def register_handler(cls):
            cls = TypeHandler(cls.__name__, cls.__bases__, cls.__dict__.copy())
            return cls.register_handler(fortype, cls)
    return register_handler

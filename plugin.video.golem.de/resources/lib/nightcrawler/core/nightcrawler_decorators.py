__author__ = 'bromix'


import re
import json

from ..exception import ProviderException


def _string_to_type(value, value_type):
    if value_type == bool:
        return value.lower() == 'true' or value == '1'

    if value_type == dict:
        return json.loads(value)

    return value_type(value)


class register_path(object):
    def __init__(self, path):
        """
        :param path: path for navigation
        """
        self._path = path

        # we want to match the complete path, not part of it
        if not self._path.startswith('^'):
            self._path = '^%s' % self._path
            pass
        if not self._path.endswith('$'):
            self._path = '%s$' % self._path
            pass
        pass

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # first argument is the provider (self)
            context = args[1]
            path = context.get_path()
            re_match = re.match(self._path, path)
            if re_match:
                context.set_path_match(re_match)
                return func(*args, **kwargs)

            return None

        # flag this method so we can filter this method later while navigating
        wrapper.nightcrawler_registered_path = True
        return wrapper


class register_path_value(object):
    def __init__(self, name, value_type, alias=None):
        """
        :param name: name of the matched group
        :param value_type: type of the value (int, str, bool, ...)
        :param alias: [optional] provide an alternative name for the parameter of the method
        """
        self._name = name
        self._value_type = value_type
        self._alias = alias
        if not self._alias:
            self._alias = self._name
            pass
        pass

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # first argument is the provider (self)
            context = args[1]

            # validate if the name of the value is one of the groups in the match
            re_match = context.get_path_match()
            if re_match and self._name in re_match.groupdict():
                # update the parameters with the value
                value = re_match.group(self._name)
                kwargs[self._alias] = _string_to_type(value, self._value_type)
                pass

            return func(*args, **kwargs)

        return wrapper


class register_context_value(object):
    def __init__(self, name, value_type, alias=None, default=None, required=False):
        """
        :param name: name of the matched group
        :param value_type: type of the value (int, str, bool, ...)
        :param alias: [optional] provide an alternative name for the parameter of the method
        :param default: [optional] provide a value for fallback reasons
        :param required: [optional] set True if this value is required
        :return:
        """
        self._name = name
        self._value_type = value_type
        self._required = required
        self._default = default
        self._alias = alias
        if not self._alias:
            self._alias = self._name
            pass
        pass

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            context = args[1]

            # validate if the name of the value is in the parameters of the context
            if self._name in context.get_params():
                # update the parameters with the value
                value = context.get_params()[self._name]
                kwargs[self._alias] = _string_to_type(value, self._value_type)
                pass
            else:
                # if required raise an exception!
                if self._required:
                    raise ProviderException(
                        'Context value "%s" required for path "%s"' % (self._name, context.get_path()))

                # at this point we can set the default (fallback) value
                kwargs[self._alias] = self._default
                pass

            return func(*args, **kwargs)

        return wrapper

    pass

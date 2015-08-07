__author__ = 'bromix'

import urlparse
import urllib

from . import strings


def normalize(path):
    return path.replace('\\', '/').replace('//', '/').strip('/')


def from_uri(uri):
    """
    Return only the path and query params as dict
    :param uri:
    :return: path and params
    """
    uri_comps = urlparse.urlparse(uri)
    path = uri_comps.path
    params = dict(urlparse.parse_qsl(uri_comps.query))
    return path, params


def to_uri(path):
    """
    Creates a valid uri from the given path
    :param path:
    :return:
    """
    path = normalize(path)

    path_components = path.split('/')
    for i in range(0, len(path_components)):
        path_components[i] = strings.to_utf8(path_components[i])
        pass
    path = '/'.join(path_components)

    if not path:
        return '/'

    return urllib.quote('/%s/' % path)

__author__ = 'bromix'

from .api import get, post, put, options, head, delete


class HttpClient(object):
    def __init__(self, default_header=None):
        if not default_header:
            default_header = {}
            pass

        self._default_header = default_header
        self._verify = False

    def _request(self, url, method='GET', headers=None, post_data=None, params=None, allow_redirects=True):
        if not params:
            params = {}
            pass

        # create headers based on default values
        _headers = self._default_header
        if not headers:
            headers = {}
            pass
        # update headers with possible new valus
        _headers.update(headers)

        result = None

        if method == 'GET':
            result = get(url, params=params, headers=_headers, verify=self._verify, allow_redirects=allow_redirects)
            pass
        elif method == 'POST':
            result = post(url, data=post_data, params=params, headers=_headers, verify=False,
                          allow_redirects=allow_redirects)
            pass
        elif method == 'PUT':
            result = put(url, data=post_data, params=params, headers=_headers, verify=False,
                         allow_redirects=allow_redirects)
            pass
        elif method == 'DELETE':
            result = delete(url, data=post_data, params=params, headers=_headers, verify=False,
                            allow_redirects=allow_redirects)
            pass
        elif method == 'OPTIONS':
            result = options(url, data=post_data, params=params, headers=_headers, verify=False,
                             allow_redirects=allow_redirects)
            pass
        elif method == 'HEAD':
            result = head(url, params=params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            pass

        return result

    pass

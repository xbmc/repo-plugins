# -*- encoding: utf-8 -*-
import sys
import requests
# import six
from six.moves.urllib.error import URLError
from six.moves.urllib.parse import quote_plus  # NOQA
from six.moves.urllib.parse import urlencode
# from six.moves.urllib.request import Request, urlopen

from twitch.keys import USER_AGENT, USER_AGENT_STRING
from twitch.logging import log
import methods

try:
    import json
except:
    import simplejson as json  # @UnresolvedImport

SSL_VERIFICATION = True
if sys.version_info <= (2, 7, 9):
    SSL_VERIFICATION = False

MAX_RETRIES = 5


def get_json(baseurl, parameters={}, headers={}, data={}, method=methods.GET):
    '''Download Data from an URL and returns it as JSON
    @param url Url to download from
    @param parameters Parameter dict to be encoded with url
    @param headers Headers dict to pass with Request
    @param data Request body
    @param method Request method
    @returns JSON Object with data from URL
    '''
    method = methods.validate(method)
    jsonString = download(baseurl, parameters, headers, data, method)
    jsonDict = json.loads(jsonString)
    log.debug(json.dumps(jsonDict, indent=4, sort_keys=True))
    return jsonDict


def download(baseurl, parameters={}, headers={}, data={}, method=methods.GET):
    '''Download Data from an url and returns it as a String
    @param method Request method
    @param baseurl Url to download from (e.g. http://www.google.com)
    @param parameters Parameter dict to be encoded with url
    @param headers Headers dict to pass with Request
    @param data Request body
    @param method Request method
    @returns String of data from URL
    '''
    method = methods.validate(method)
    url = '?'.join([baseurl, urlencode(parameters)])
    log.debug('Downloading: ' + url)
    content = ""
    for _ in range(MAX_RETRIES):
        try:
            headers.update({USER_AGENT: USER_AGENT_STRING})
            response = requests.request(method=method, url=url, headers=headers, data=data, verify=SSL_VERIFICATION)
            content = response.content
            if not content:
                content = '{"status": %d}' % response.status_code
            break
        except Exception as err:
            if not isinstance(err, URLError):
                log.debug("Error %s during HTTP Request, abort", repr(err))
                raise  # propagate non-URLError
            log.debug("Error %s during HTTP Request, retrying", repr(err))
    else:
        raise
    return content

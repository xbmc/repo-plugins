# ===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
# ===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
# ===============================================================================

import requests
from requests.adapters import HTTPAdapter, DEFAULT_POOLSIZE, DEFAULT_RETRIES, DEFAULT_POOLBLOCK

from .dnsresolver import DnsResolver


class DnsResolverHTTPAdapter(HTTPAdapter):
    """ DNS resolver class that can be used for `urllib3` and `requests` modules. """
    __dns_cache = {}        # A cache object to keep DNS requests per server

    def __init__(self, url, dns_server, logger, pool_connections=DEFAULT_POOLSIZE,
                 pool_maxsize=DEFAULT_POOLSIZE, max_retries=DEFAULT_RETRIES,
                 pool_block=DEFAULT_POOLBLOCK):

        self.__dns_server = dns_server
        logger.debug("Creating %s", self)
        if dns_server not in DnsResolverHTTPAdapter.__dns_cache:
            logger.trace("Creating a DNS Cache object for server %s", dns_server)
            DnsResolverHTTPAdapter.__dns_cache[dns_server] = {}

        # <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        # Return a 6-tuple: (scheme, netloc, path, params, query, fragment).
        self.__url_parts = list(requests.utils.urlparse(url))
        self.__original_host_name = self.__url_parts[1]

        # resolve the DNS
        resolved_ip = DnsResolverHTTPAdapter.__dns_cache[dns_server].get(self.__original_host_name)
        if resolved_ip is None:
            self.__dns_resolver = DnsResolver(self.__dns_server)
            resolved_ips = self.__dns_resolver.resolve_address(self.__original_host_name)
            logger.debug("Resolved DNS %s to %s", self.__original_host_name, resolved_ips)
            resolved_ip = resolved_ips[0][-1]
            DnsResolverHTTPAdapter.__dns_cache[dns_server][self.__original_host_name] = resolved_ip
        else:
            logger.debug("Resolved DNS %s to %s (via cache)", self.__original_host_name, resolved_ip)
        self.__url_parts[1] = resolved_ip
        self.__resolved_url = requests.utils.urlunparse(self.__url_parts)

        super(DnsResolverHTTPAdapter, self).__init__(pool_connections, pool_maxsize, max_retries,
                                                     pool_block)

    def get_connection(self, url, proxies=None):

        conn = super(DnsResolverHTTPAdapter, self).get_connection(self.__resolved_url, proxies=proxies)
        return conn

    def request_url(self, request, proxies):
        requests.url = self.__resolved_url
        return super(DnsResolverHTTPAdapter, self).request_url(request, proxies)

    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK, **pool_kwargs):
        # Add the original host to make SSL verification pass
        if self.__url_parts[0] == "https":
            pool_kwargs['assert_hostname'] = self.__original_host_name
        super(DnsResolverHTTPAdapter, self).init_poolmanager(connections, maxsize, block,
                                                             **pool_kwargs)

    def __str__(self):
        return "DNS Resolving HTTP Adapter for dns://{0}".format(self.__dns_server)

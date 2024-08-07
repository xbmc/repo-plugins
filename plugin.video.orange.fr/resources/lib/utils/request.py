"""Request utils."""

from random import randint
from urllib.parse import urlparse
from urllib.request import Request

# from socks import SOCKS5
# from sockshandler import SocksiPyHandler
from lib.utils.kodi import get_addon_setting

_USER_AGENTS = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.3",  # noqa: E501
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.3",  # noqa: E501
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.3",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0",  # noqa: E501
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.",
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 OPR/108.0.0.",  # noqa: E501
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.1",  # noqa: E501
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.1",  # noqa: E501
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.1",  # noqa: E501
]


def get_random_ua() -> str:
    """Get a randomised user agent."""
    return _USER_AGENTS[randint(0, len(_USER_AGENTS) - 1)]


def build_request(url: str, additional_headers: dict = None) -> Request:
    """Build HTTP request."""
    if additional_headers is None:
        additional_headers = {}

    install_proxy()

    return Request(url, headers={"User-Agent": get_random_ua(), "Host": urlparse(url).netloc, **additional_headers})


def install_proxy() -> None:
    """Install proxy server for the next requests."""
    if get_addon_setting("proxy.enabled") != "true":
        return

    ip = get_addon_setting("proxy.ip")
    port = get_addon_setting("proxy.port")

    if ip == "" or port == "":
        return

    # protocol = get_addon_setting('proxy.protocol')

    # if protocol == 'HTTP':
    #     proxies = {
    #         'https': f"http://{ip}:{port}",
    #         'http': f"http://{ip}:{port}"
    #     }
    #     log(proxies, xbmc.LOGDEBUG)
    #     proxy_support = ProxyHandler(proxies)

    # elif protocol == 'Socks5 Local DNS':
    #     proxy_support = SocksiPyHandler(SOCKS5, ip, int(port), False)

    # elif protocol == 'Socks5 Remote DNS':
    #     proxy_support = SocksiPyHandler(SOCKS5, ip, int(port), True)

    # opener = build_opener(proxy_support)
    # install_opener(opener)

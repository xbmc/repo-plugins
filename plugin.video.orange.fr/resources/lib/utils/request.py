"""Request utils."""

from random import randint
from typing import Mapping, Union

import xbmc
from requests import Response, Session
from requests.exceptions import JSONDecodeError, RequestException

# from socks import SOCKS5
# from sockshandler import SocksiPyHandler
from lib.utils.kodi import get_addon_setting, log

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


def request(method: str, url: str, headers: Mapping[str, str] = None, data=None, s: Session = None) -> Response:
    """Send HTTP request using requests."""
    if headers is None:
        headers = {}

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "*",
        "Sec-Fetch-Mode": "cors",
        "User-Agent": get_random_ua(),
        **headers,
    }

    s = s if s is not None else Session()

    log(f"Fetching {url}", xbmc.LOGDEBUG)
    res = s.request(method, url, headers=headers, data=data)
    res.raise_for_status()
    log(f" -> {res.status_code}", xbmc.LOGDEBUG)
    return res


def request_json(url: str, headers: Mapping[str, str] = None, default: Union[dict, list] = None) -> Union[dict, list]:
    """Send HTTP request and load json response."""
    try:
        res = request("GET", url, headers=headers)
        res.raise_for_status()
    except RequestException as e:
        log(e, xbmc.LOGWARNING)
        return default

    try:
        content = res.json()
    except JSONDecodeError:
        log("Cannot load json content", xbmc.LOGWARNING)
        log(res.text, xbmc.LOGDEBUG)
        return default

    return content


def to_cookie_string(cookies: dict, pick: list = None) -> str:
    """Convert cookies to cookie string."""
    if pick is None:
        pick = cookies.keys()

    cookies = {key: value for key, value in cookies.items() if key in pick}

    return "; ".join([f"{key}={value}" for key, value in cookies.items()])


def install_proxy() -> None:
    """Install proxy server for the next requests."""
    if get_addon_setting("proxy.enabled", bool):
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

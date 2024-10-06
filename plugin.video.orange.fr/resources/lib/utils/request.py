"""Request utils."""

import gzip
import json
from http.client import HTTPConnection, HTTPResponse, HTTPSConnection
from http.cookies import SimpleCookie
from random import randint
from socket import gaierror
from typing import Mapping, TypeVar, Union
from urllib.error import URLError
from urllib.parse import unquote_plus, urlparse

import xbmc

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


C = TypeVar("C", HTTPConnection, HTTPSConnection)


def get_cookies(response: HTTPResponse) -> dict:
    """Get cookies from HTTP response."""
    cookies = {}
    for header in response.getheaders():
        if header[0] == "Set-Cookie":
            cookie = header[1].split(";")[0]
            cookies[cookie.split("=")[0]] = cookie.split("=")[1]
    return cookies


def get_random_ua() -> str:
    """Get a randomised user agent."""
    return _USER_AGENTS[randint(0, len(_USER_AGENTS) - 1)]


def parse_cookies(cookie_strings: list) -> dict:
    """Parse cookie strings."""
    cookies = {}

    for cookie_string in cookie_strings:
        simple_cookie = SimpleCookie(cookie_string)
        for key, item in simple_cookie.items():
            cookies[key] = unquote_plus(item.value)

    return cookies


def request(conn: C, url: str, method: str = "GET", headers: Mapping[str, str] = None, body=None) -> C:
    """Send HTTP request."""
    if headers is None:
        headers = {}

    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "br, gzip, deflate",
        "Accept-Language": "*",
        "Sec-Fetch-Mode": "cors",
        "User-Agent": get_random_ua(),
        **headers,
    }

    try:
        log(f"Fetching {url}", xbmc.LOGDEBUG)
        conn.request(method, url, headers=headers, body=body)
    except gaierror as e:
        log(e, xbmc.LOGERROR)
        return None
    except URLError as e:
        log(f"{e.reason}", xbmc.LOGERROR)
        return None

    res = conn.getresponse()

    if res.status != 200:
        log(f"Error while fetching: {res.status} {res.reason}", xbmc.LOGERROR)
        log(res.read(), xbmc.LOGDEBUG)
        return None

    return res


def request_json(url: str, headers: Mapping[str, str] = None, default=None) -> Union[dict, list]:
    """Send HTTP request and load json response."""
    url = urlparse(url)
    conn = HTTPConnection(url.netloc) if url.scheme == "http" else HTTPSConnection(url.netloc)
    res = request(conn, url.geturl(), headers=headers)

    if res is None:
        conn.close()
        return default

    content = res.read()
    conn.close()

    if res.headers.get("Content-Encoding") == "gzip":
        content = gzip.decompress(content)

    try:
        content = json.loads(content)
    except json.decoder.JSONDecodeError:
        log("Cannot load json content", xbmc.LOGWARNING)
        return default

    return content


def request_text(url: str, headers: Mapping[str, str] = None) -> str:
    """Send HTTP request and load text response."""
    url = urlparse(url)
    conn = HTTPConnection(url.netloc) if url.scheme == "http" else HTTPSConnection(url.netloc)
    res = request(conn, url.geturl(), headers=headers)

    if res is None:
        conn.close()
        return None

    content = res.read()
    conn.close()

    if res.headers.get("Content-Encoding") == "gzip":
        content = gzip.decompress(content)

    return content.decode("utf-8")


def to_cookie_string(cookies: dict, pick: list = None) -> str:
    """Convert cookies to cookie string."""
    if pick is None:
        pick = cookies.keys()

    cookies = {k: v for k, v in cookies.items() if k in pick}

    return "; ".join([f"{k}={v}" for k, v in cookies.items()])


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

"""
URL / Request handling
"""

import time
from typing import Dict, Optional, Tuple

import requests
import xbmc
import xbmcaddon
from requests.models import Response

from . import nhk_api

# Get Plug-In path
ADDON = xbmcaddon.Addon()
PLUGIN_PATH = ADDON.getAddonInfo("path")

# Cache configuration (60 minutes)
URL_CACHE_MINUTES = 60

# Simple in-memory cache
# Format: {url: (response_text, expiry_timestamp)}
_response_cache: Dict[str, Tuple[str, float]] = {}


def _get_cache_key(url: str, params: Optional[dict] = None) -> str:
    """Generate cache key from URL and parameters"""
    if params:
        # Sort params for consistent cache keys
        param_str = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{url}?{param_str}"
    return url


def _get_cached_response(url: str, params: Optional[dict] = None) -> Optional[str]:
    """Get cached response if available and not expired"""
    cache_key = _get_cache_key(url, params)
    if cache_key in _response_cache:
        content, expiry = _response_cache[cache_key]
        if time.time() < expiry:
            xbmc.log(f"Cache hit for: {url}", xbmc.LOGDEBUG)
            return content
        else:
            # Expired, remove from cache
            del _response_cache[cache_key]
            xbmc.log(f"Cache expired for: {url}", xbmc.LOGDEBUG)
    return None


def _cache_response(url: str, content: str, params: Optional[dict] = None):
    """Cache response with expiration time"""
    cache_key = _get_cache_key(url, params)
    expiry = time.time() + (URL_CACHE_MINUTES * 60)
    _response_cache[cache_key] = (content, expiry)
    xbmc.log(f"Cached response for: {url}", xbmc.LOGDEBUG)


# Instantiate request session
session = requests.Session()
# Act like a browser
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/88.0.4324.182"
session.headers.update({"User-Agent": user_agent})


def check_url_exists(url):
    """Check if a URL exists of it returns a 404

    Arguments:
        url {str} -- URL to check
    """
    # Don't cache existence checks
    request = session.get(url)
    if request.status_code == 404:
        return False
    else:
        return True


def check_stream_available(url, timeout=5):
    """Check if a stream URL is available with a quick HEAD/GET request

    Args:
        url (str): Stream URL to check
        timeout (int): Request timeout in seconds (default 5)

    Returns:
        bool: True if URL returns 200 or 206 (partial content), False otherwise
    """
    try:
        # Don't cache stream availability checks
        # Use stream=True to avoid downloading the entire file
        request = session.get(url, timeout=timeout, stream=True)
        return request.status_code in (200, 206)
    except Exception as e:
        xbmc.log(
            f"check_stream_available: Failed to check {url}: {e}",
            xbmc.LOGDEBUG,
        )
        return False


def upgrade_to_1080p(url):
    """Upgrade a video URL to highest quality available

    Fetches the master playlist and parses it to find the highest
    bitrate stream. Falls back to o-master.m3u8 pattern if parsing
    fails.

    Args:
        url (str): Original video URL (master.m3u8)

    Returns:
        str: Highest quality stream URL, or original if parsing fails
    """
    if not url or "/master.m3u8" not in url:
        xbmc.log(
            "upgrade_to_1080p: URL doesn't contain /master.m3u8, returning original",
            xbmc.LOGDEBUG,
        )
        return url

    # Try o-master.m3u8 pattern first (contains 1080p variants)
    url_1080p_master = url.replace("/master.m3u8", "/o-master.m3u8")

    xbmc.log(
        f"upgrade_to_1080p: Fetching playlist: {url_1080p_master}",
        xbmc.LOGINFO,
    )

    try:
        # Fetch the master playlist (don't cache live content)
        response = session.get(url_1080p_master, timeout=10)
        if response.status_code != 200:
            xbmc.log(
                "upgrade_to_1080p: Failed to fetch o-master, trying regular",
                xbmc.LOGINFO,
            )
            response = session.get(url, timeout=10)
            if response.status_code != 200:
                return url

        playlist_content = response.text
        base = url_1080p_master if response.url == url_1080p_master else url
        highest_bitrate_url = _parse_highest_bitrate_stream(playlist_content, base)

        if highest_bitrate_url:
            xbmc.log(
                f"upgrade_to_1080p: Selected highest quality: {highest_bitrate_url}",
                xbmc.LOGINFO,
            )
            return highest_bitrate_url
        else:
            xbmc.log(
                "upgrade_to_1080p: Could not parse playlist, using master",
                xbmc.LOGINFO,
            )
            if check_stream_available(url_1080p_master):
                return url_1080p_master
            else:
                return url

    except Exception as e:
        xbmc.log(
            f"upgrade_to_1080p: Error parsing playlist: {e}, using fallback",
            xbmc.LOGWARNING,
        )
        # Fallback to checking o-master.m3u8 availability
        if check_stream_available(url_1080p_master):
            return url_1080p_master
        return url


def _parse_highest_bitrate_stream(playlist_content, base_url):
    """Parse HLS master playlist and return URL of highest bitrate stream

    Args:
        playlist_content (str): Content of the master playlist
        base_url (str): Base URL to resolve relative paths

    Returns:
        str: URL of highest bitrate stream, or None if parsing fails
    """
    import re
    from urllib.parse import urljoin

    highest_bitrate = 0
    highest_url = None

    lines = playlist_content.split("\n")
    for i, line in enumerate(lines):
        # Look for EXT-X-STREAM-INF lines with BANDWIDTH
        if line.startswith("#EXT-X-STREAM-INF:"):
            # Extract BANDWIDTH value
            match = re.search(r"BANDWIDTH=(\d+)", line)
            if match:
                bitrate = int(match.group(1))
                # Next line should contain the stream URL
                if i + 1 < len(lines):
                    stream_url = lines[i + 1].strip()
                    if stream_url and not stream_url.startswith("#"):
                        # Convert relative URL to absolute
                        if not stream_url.startswith("http"):
                            # Get base path from master URL
                            base_path = base_url.rsplit("/", 1)[0]
                            stream_url = f"{base_path}/{stream_url}"
                        else:
                            stream_url = urljoin(base_url, stream_url)

                        if bitrate > highest_bitrate:
                            highest_bitrate = bitrate
                            highest_url = stream_url

    if highest_url:
        xbmc.log(
            f"_parse_highest_bitrate_stream: Found stream with "
            f"bitrate {highest_bitrate}: {highest_url}",
            xbmc.LOGINFO,
        )

    return highest_url


def get_json(url, cached=True):
    """Get JSON object from a URL with improved error handling

    Args:
        url ([str]): URL to retrieve
        cached (bool, optional): Use request_cache. Defaults to True.

    Returns:
        [dict]: JSON dictionary
    """
    request = get_url(url, cached)
    if request.status_code == 200:
        try:
            result = request.json()
            xbmc.log(f"Successfully loaded JSON from API: {url}")
            return result
        except ValueError:
            # Failure - no way to handle - probably an issue with the NHK API
            xbmc.log(f"Could not parse JSON from API: {url}")
    else:
        # Failure - could not connect to site
        xbmc.log(f"Could not connect to API: {url}")


def get_api_request_params(url):
    """Returns the API request parameters for the NHK API

    Args:
        url ([str]): Url
    Returns:
        [dict]: Empty dict for API URLs (no auth needed), None for others
    """

    # Check if this is an NHK API URL
    if nhk_api.NHK_API_BASE in url or nhk_api.NHK_BASE in url:
        # API key is no longer required per commit 05d1548
        request_params = {}
    else:
        request_params = None

    return request_params


def request_url(url, cached=True):
    """HELPER: Request URL with handling basic error conditions

    Args:
        url ([str]): URL to retrieve
        cached (bool, optional): Use in-memory cache. Defaults to True.

    Returns:
        [response]: Response object - can be None
    """

    request_params = get_api_request_params(url)
    request = Response()

    try:
        # Check cache first if caching is enabled
        if cached:
            cached_content = _get_cached_response(url, request_params)
            if cached_content:
                # Create a fake response object from cached content
                request.status_code = 200
                request._content = cached_content.encode("utf-8")
                return request

        # Make actual request
        if request_params is not None:
            request = session.get(url, params=request_params)
        else:
            request = session.get(url)

        # Cache successful responses
        if cached and request.status_code == 200:
            _cache_response(url, request.text, request_params)

        return request
    except requests.ConnectionError:
        # Could not establish connection at all
        request.status_code = 10001
    return request


def get_url(url, cached=True):
    """Get a URL with automatic retries
        NHK sometimes have intermittent problems with 502 Bad Gateway

    Args:
        url ([str]): URL to retrieve
        cached (bool, optional): Use in-memory cache. Defaults to True.

    Returns:
        [response]: Response object
    """

    # maximum number of retries
    max_retries = 3
    current_try = 1

    while current_try <= max_retries:
        # Make an API Call
        xbmc.log(f"Fetching URL:{url} ({current_try} of {max_retries})")

        request = request_url(url, cached)
        status_code = request.status_code

        if status_code == 200:
            # Call was successful
            xbmc.log(f"Successfully fetched URL: {url} - Status {status_code}")
            break

        elif status_code == 502:
            # Bad Gateway - can be retried
            if current_try == max_retries:
                # Max retries reached - still could not get url
                xbmc.log(
                    f"FATAL: Could not get URL {url} after {current_try} retries",
                    xbmc.LOGDEBUG,
                )
                break
            else:
                # Try again - this usually fixes the error
                xbmc.log(
                    f"Temporary failure fetching URL: {url} with Status {status_code})",
                    xbmc.LOGDEBUG,
                )

                # Wait for 1s before the next call
                time.sleep(1)
        else:
            # Other HTTP error - FATAL, do not retry
            xbmc.log(
                f"FATAL: Could not get URL: {url} - HTTP Status Code {status_code}",
                xbmc.LOGDEBUG,
            )
            break

        current_try = current_try + 1

    return request


def get_nhk_website_url(path):
    """Return a full URL from the partial URLs in the JSON results"""
    nhk_website = nhk_api.NHK_BASE
    return nhk_website + path

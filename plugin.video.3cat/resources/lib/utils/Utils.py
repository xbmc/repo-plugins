import http.client
import json
import re
import urllib.error
import urllib.parse
import urllib.request

import xbmc
import xbmcgui

USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
              '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
TIMEOUT = 15
RETRIES = 2


def buildUrl(query, base_url):
    return base_url + '?' + urllib.parse.urlencode(query)


def fetch(url, timeout=TIMEOUT, retries=RETRIES):
    """Download url and return the body as bytes.

    Timeouts, dropped connections and 5xx responses are retried, because the 3cat
    servers fail intermittently. 4xx responses are raised at once. When every attempt
    fails the last error is raised.
    """
    attempt = 0
    while True:
        try:
            request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt >= retries:
                raise
            error = e
        except (OSError, http.client.HTTPException) as e:
            if attempt >= retries:
                raise
            error = e

        attempt += 1
        xbmc.log("plugin.video.3cat - retry " + str(attempt) + " for " + url + " after: " + str(error),
                 xbmc.LOGWARNING)
        if xbmc.Monitor().waitForAbort(attempt):
            raise error


def getHtml(url):
    try:
        return fetch(url)
    except Exception as e:
        xbmc.log("plugin.video.3cat - getHtml error for " + url + ": " + str(e), xbmc.LOGWARNING)
        return None


def getJson(url, **kwargs):
    return json.loads(fetch(url, **kwargs))


def parseDurada(durada):
    """Return the duration in seconds of '00:32:28:20' (hh:mm:ss:frames), '00:32:28' or 'PT00H32M13S'."""
    if not durada:
        return 0
    if isinstance(durada, (int, float)):
        return int(durada)

    durada = str(durada).strip()
    iso = re.match(r'^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$', durada)
    if iso:
        h, m, s = (int(x or 0) for x in iso.groups())
        return h * 3600 + m * 60 + s

    parts = durada.split(':')
    if len(parts) < 2 or not all(p.isdigit() for p in parts):
        return 0
    numbers = [int(p) for p in parts[:3]]
    if len(numbers) == 2:
        return numbers[0] * 60 + numbers[1]
    return numbers[0] * 3600 + numbers[1] * 60 + numbers[2]


def parseDate(date):
    """Convert 3cat's 'dd/mm/yyyy hh:mm:ss' to the 'yyyy-mm-dd' Kodi expects."""
    match = re.match(r'^(\d{2})/(\d{2})/(\d{4})', str(date or ''))
    if not match:
        return ''
    return match.group(3) + '-' + match.group(2) + '-' + match.group(1)


def cleanText(text):
    if not text:
        return ''
    text = re.sub(r'<br\s*/?>', '\n', str(text), flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return text.replace('\r\n', '\n').strip()


def notify(message, icon=xbmcgui.NOTIFICATION_ERROR):
    xbmcgui.Dialog().notification('3Cat', message, icon)

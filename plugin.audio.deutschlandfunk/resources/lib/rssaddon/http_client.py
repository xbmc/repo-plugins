from resources.lib.rssaddon.http_status_error import HttpStatusError

import requests

import xbmc

def http_request(addon, url, headers=dict(), method="GET"):

    useragent = f"{addon.getAddonInfo('id')}/{addon.getAddonInfo('version')} (Kodi/{xbmc.getInfoLabel('System.BuildVersionShort')})"
    headers["User-Agent"] = useragent

    if method == "GET":
        req = requests.get
    elif method == "POST":
        req = requests.post
    else:
        raise HttpStatusError(
            addon.getLocalizedString(32152) % method)

    try:
        res = req(url, headers=headers)
    except requests.exceptions.RequestException as error:
        xbmc.log("Request Exception: %s" % str(error), xbmc.LOGERROR)
        raise HttpStatusError(addon.getLocalizedString(32153))

    if res.status_code == 200:
        if res.encoding and res.encoding != "utf-8":
            rv = res.text.encode(res.encoding).decode("utf-8")
        else:
            rv = res.text

        return rv, res.cookies

    else:
        raise HttpStatusError(addon.getLocalizedString(
            32154) % (res.status_code, url))
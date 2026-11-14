"""What Kodi needs to play a stream through the local proxy: path, MIME type, ListItem properties.

The service hands it to the plugin as JSON, so only the standard library at import;
the Kodi side builds the ListItem from it (see resolveditem).
"""

import json
from urllib.parse import quote

from resources.lib.stream import dash

LICENCE_HEADERS = "Content-Type=text%2Fplain"


def spec(stream, manifest_url, license_url, kodi_major):
    """Return a JSON-serialisable description of the ListItem for one stream."""
    manifest_type = "hls" if stream["type"].startswith("hls") else "mpd"
    props = {
        "inputstream": "inputstream.adaptive",
        "inputstream.adaptive.stream_headers": "User-Agent=%s" % quote(stream["user_agent"]),
    }
    if stream.get("from_start"):
        props["inputstream.adaptive.play_timeshift_buffer"] = "true"
    elif kodi_major >= 22:  # ISA's wiki: live_delay moved into manifest_config on Kodi 22
        props["inputstream.adaptive.manifest_config"] = json.dumps({"live_delay": dash.LIVE_DELAY})
    else:
        props["inputstream.adaptive.live_delay"] = str(dash.LIVE_DELAY)
    # The properties by Kodi version, as inputstream.adaptive's wiki has them: one JSON "drm" property
    # from Kodi 22, where the old license_* properties are deprecated (wiki "Integration DRM"); manifest_type
    # only before 21, which detects the type itself (wiki "Integration").
    if kodi_major >= 22:
        drm = {"license": {"server_url": license_url, "req_headers": LICENCE_HEADERS}}
        if stream["server_certificate"]:
            drm["license"]["server_certificate"] = stream["server_certificate"]
        props["inputstream.adaptive.drm"] = json.dumps({"com.widevine.alpha": drm})
    else:
        if kodi_major < 21:
            props["inputstream.adaptive.manifest_type"] = manifest_type
        props["inputstream.adaptive.license_type"] = "com.widevine.alpha"
        props["inputstream.adaptive.license_key"] = "%s|%s|R{SSM}|" % (license_url, LICENCE_HEADERS)
        if stream["server_certificate"]:
            props["inputstream.adaptive.server_certificate"] = stream["server_certificate"]
    return {
        "path": manifest_url,
        "mimetype": "application/dash+xml" if manifest_type == "mpd" else "application/vnd.apple.mpegurl",
        "properties": props,
        "details": stream.get("details"),
        "logo": stream.get("logo"),
    }

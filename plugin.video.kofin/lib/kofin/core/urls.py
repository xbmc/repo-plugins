"""The one builder of ``plugin://`` URLs.

Kodi keys what it remembers about a plugin row — its resume bookmark, its
play count — on the exact URL string, so every ``plugin://`` URL is built
here.
"""

from urllib.parse import urlencode

BASE_URL = "plugin://plugin.video.kofin/"

# The play route's own parameters: the context item and the stream menu
# build a play URL with them, and the play route reads them. A request
# carrying any of STREAM_REQUEST_PARAMS names a stream or a quality the
# server must serve, which is what keeps it off a download.
PARAM_TRANSCODE = "transcode"
PARAM_BITRATE = "bitrate"
PARAM_MEDIA_SOURCE = "mediasourceid"
PARAM_AUDIO_INDEX = "audioindex"
PARAM_SUBTITLE_INDEX = "subtitleindex"
PARAM_BURN_SUBS = "burnsubs"
STREAM_REQUEST_PARAMS = (
    PARAM_TRANSCODE,
    PARAM_BITRATE,
    PARAM_MEDIA_SOURCE,
    PARAM_AUDIO_INDEX,
    PARAM_SUBTITLE_INDEX,
    PARAM_BURN_SUBS,
)
# A play no one at this Kodi started (a SyncPlay group start, the server's
# remote control): the play route asks nothing.
PARAM_UNATTENDED = "unattended"


def plugin_url(params: dict[str, str]) -> str:
    return BASE_URL + "?" + urlencode(params)

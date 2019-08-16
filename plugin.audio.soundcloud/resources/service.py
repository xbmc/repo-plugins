import xbmc
import xbmcaddon
from resources.lib.kodi.settings import Settings
from resources.lib.soundcloud.api_v2 import ApiV2

addon = xbmcaddon.Addon()
settings = Settings(addon)


def run():
    # Extract the SoundCloud API key and save it to settings
    try:
        api_v2_client_id = ApiV2.fetch_client_id()
        settings.set("apiv2.clientid", api_v2_client_id)
        xbmc.log(
            "plugin.audio.soundcloud::ApiV2() Successfully extracted client id",
            xbmc.LOGDEBUG
        )
    except Exception as exception:
        xbmc.log(
            "plugin.audio.soundcloud::ApiV2() " + str(exception),
            xbmc.LOGDEBUG
        )

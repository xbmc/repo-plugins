from enum import Enum

import xbmc


class _KodiMagicValues:
    WEATHER_WINDOW_ID = 12600  # see https://kodi.wiki/view/Weather_addons at "Required output"
    ADDON_INFO_PATH_ID = "path"
    ADDON_INFO_ADDON_ID = "id"
    ADDON_INFO_NAME_ID = "name"
    REGION_TEMPERATURE_UNIT_ID = "tempunit"
    REGION_WIND_SPEED_UNIT_ID = "speedunit"
    REGION_TIME_FORMAT_ID = "time"
    REGION_SHORT_DATE_FORMAT_ID = "dateshort"
    REGION_LONG_DATE_FORMAT_ID = "datelong"
    MESSAGE_OFFSET_DAY_SHORT = 10
    MESSAGE_OFFSET_DAY_LONG = 40


class KodiLogLevel(Enum):
    DEBUG = xbmc.LOGDEBUG
    INFO = xbmc.LOGINFO
    WARNING = xbmc.LOGWARNING
    ERROR = xbmc.LOGERROR
    CRITICAL = xbmc.LOGFATAL

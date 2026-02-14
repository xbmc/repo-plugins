from enum import IntEnum

from lib.kodi import KodiWeatherPluginAdapter, KodiPluginSetting


class _HomeAssistantWeatherPluginSettings(KodiPluginSetting):
    LOCATION_TITLE = KodiPluginSetting(setting_id="loc_title", setting_type=str)
    USE_HOME_ASSISTANT_LOCATION_NAME = KodiPluginSetting(setting_id="useHALocName", setting_type=bool)
    HOME_ASSISTANT_SERVER = KodiPluginSetting(setting_id="ha_server", setting_type=str)
    HOME_ASSISTANT_TOKEN = KodiPluginSetting(setting_id="ha_key", setting_type=str)
    HOME_ASSISTANT_WEATHER_FORECAST_ENTITY_ID = KodiPluginSetting(
        setting_id="ha_weather_forecast_entity_id", setting_type=str
    )
    HOME_ASSISTANT_SUN_ENTITY_ID = KodiPluginSetting(setting_id="ha_sun_entity_id", setting_type=str)
    LOG_ENABLED = KodiPluginSetting(setting_id="logEnabled", setting_type=bool)
    CHECK_SSL =  KodiPluginSetting(setting_id="ha_check_ssl", setting_type=bool)
    ERR_NOT_INFORM = KodiPluginSetting(setting_id="errNotInform", setting_type=bool)


class _HomeAssistantWeatherPluginStrings(IntEnum):
    SETTINGS_REQUIRED = 30010
    HOMEASSISTANT_UNAUTHORIZED = 30011
    HOMEASSISTANT_UNREACHABLE = 30013
    HOMEASSISTANT_UNEXPECTED_RESPONSE = 30014
    ADDON_SHORT_NAME = 30200


class _KodiHomeAssistantWeatherPluginAdapter(KodiWeatherPluginAdapter):
    def __init__(self) -> None:
        super().__init__()
        self._allow_logging = self._get_setting(setting=_HomeAssistantWeatherPluginSettings.LOG_ENABLED)

    def required_settings_done(self) -> bool:
        return (
            bool(self.home_assistant_token)
            and bool(self.home_assistant_url)
            and bool(self.home_assistant_entity_forecast)
            and bool(self.home_assistant_entity_sun)
        )
    @property
    def get_check_ssl(self) -> bool:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.CHECK_SSL)

    @property
    def get_err_not_inform(self) -> bool:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.ERR_NOT_INFORM)


    @property
    def home_assistant_url(self) -> str:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_SERVER)

    @property
    def home_assistant_entity_forecast(self) -> str:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_WEATHER_FORECAST_ENTITY_ID)

    @property
    def home_assistant_entity_sun(self) -> str:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_SUN_ENTITY_ID)

    @property
    def home_assistant_token(self) -> str:
        return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.HOME_ASSISTANT_TOKEN)

    @property
    def override_location(self) -> str:
        if not self._get_setting(setting=_HomeAssistantWeatherPluginSettings.USE_HOME_ASSISTANT_LOCATION_NAME):
            return self._get_setting(setting=_HomeAssistantWeatherPluginSettings.LOCATION_TITLE)
        else:
            return ""

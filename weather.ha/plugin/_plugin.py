from typing import Tuple, Union

from lib.homeassistant import HomeAssistantAdapter, RequestError, HomeAssistantForecast, HomeAssistantSunInfo
from lib.kodi import KodiLogLevel
from .util.forecast_converter import ForecastConverter
from ._kodi_adapter import _KodiHomeAssistantWeatherPluginAdapter, _HomeAssistantWeatherPluginStrings


class KodiHomeAssistantWeatherPlugin:
    def __init__(self):
        self._kodi_adapter = _KodiHomeAssistantWeatherPluginAdapter()
        self._kodi_adapter.log("Home Assistant Weather started.")

        if not self._kodi_adapter.required_settings_done():
            if not self._kodi_adapter.get_err_not_inform:
                self._kodi_adapter.dialog(message_id=_HomeAssistantWeatherPluginStrings.SETTINGS_REQUIRED)
            self._kodi_adapter.log("Settings for Home Assistant Weather not yet provided. Plugin will not work.")
        else:
            self.apply_forecast()
        self._kodi_adapter.log("Home Assistant Weather init finished.")

    def _get_forecast_handling_errors(self) \
            -> Tuple[Union[HomeAssistantForecast, None], Union[HomeAssistantSunInfo, None]]:
        try:
            return (
                HomeAssistantAdapter.get_forecast(
                    server_url=self._kodi_adapter.home_assistant_url,
                    entity_id=self._kodi_adapter.home_assistant_entity_forecast,
                    token=self._kodi_adapter.home_assistant_token,
                    check_ssl=self._kodi_adapter.get_check_ssl
                ),
                HomeAssistantAdapter.get_sun_info(
                    server_url=self._kodi_adapter.home_assistant_url,
                    entity_id=self._kodi_adapter.home_assistant_entity_sun,
                    token=self._kodi_adapter.home_assistant_token,
                    check_ssl=self._kodi_adapter.get_check_ssl
                )
            )
        except RequestError as e:
            self._kodi_adapter.log(
                message=f"Could not retrieve forecast from Home Assistant: {e.error_code}", level=KodiLogLevel.ERROR
            )
            if e.error_code == 401:
                message = _HomeAssistantWeatherPluginStrings.HOMEASSISTANT_UNAUTHORIZED
            elif e.error_code == -1:
                message = _HomeAssistantWeatherPluginStrings.HOMEASSISTANT_UNREACHABLE
            else:
                message = _HomeAssistantWeatherPluginStrings.HOMEASSISTANT_UNEXPECTED_RESPONSE
            if not self._kodi_adapter.get_err_not_inform:
                self._kodi_adapter.dialog(message_id=message)
            return None, None

    def apply_forecast(self):
        forecast, sun_info = self._get_forecast_handling_errors()
        if forecast is None:
            self._kodi_adapter.log(message="No forecasts were found.", level=KodiLogLevel.WARNING)
            self._kodi_adapter.clear_weather_properties()
            return
        if sun_info is None:
            self._kodi_adapter.log(message="No sun info was found.", level=KodiLogLevel.WARNING)
            self._kodi_adapter.clear_weather_properties()
            return
        kodi_forecast = ForecastConverter.translate_ha_forecast_to_kodi_forecast(
            ha_forecast=forecast,
            ha_sun_info=sun_info,
        )
        if self._kodi_adapter.override_location:
            kodi_forecast.General.location = self._kodi_adapter.override_location
        self._kodi_adapter.set_weather_properties(forecast=kodi_forecast)
        self._kodi_adapter.log(message="Weather updated successfully.", level=KodiLogLevel.INFO)

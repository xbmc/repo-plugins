import os.path
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Type, Union

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from lib.unit.speed import Speed, SpeedUnits, SpeedKph
from lib.unit.temperature import Temperature, TemperatureUnits, TemperatureCelsius

from ._forecast import KodiForecastData, KodiHourlyForecastData, KodiDailyForecastData
from ._properties import _KodiWeatherProperties, _KodiHourlyWeatherProperties, _KodiDailyWeatherProperties, \
    _KodiDailyWeatherPropertiesCompat
from ._settings import KodiPluginSetting, _Setting_Type
from ._values import _KodiMagicValues, KodiLogLevel


class KodiWeatherPluginAdapter:

    def __init__(self) -> None:
        self._window = xbmcgui.Window(_KodiMagicValues.WEATHER_WINDOW_ID)   # kwargs unsupported
        self._kodi_addon = xbmcaddon.Addon()
        self.__addon_id = self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_ADDON_ID)
        self._allow_logging = False     # override this after construction if needed

    @property
    def cwd(self) -> str:
        return self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_PATH_ID)

    @property
    def temperature_unit(self) -> Type[Temperature]:
        return TemperatureUnits[xbmc.getRegion(id=_KodiMagicValues.REGION_TEMPERATURE_UNIT_ID)]

    @property
    def wind_speed_unit(self) -> Type[Speed]:
        return SpeedUnits[xbmc.getRegion(id=_KodiMagicValues.REGION_WIND_SPEED_UNIT_ID)]

    @property
    def time_format(self) -> str:
        return xbmc.getRegion(id=_KodiMagicValues.REGION_TIME_FORMAT_ID)

    @property
    def short_date_format(self) -> str:
        return xbmc.getRegion(id=_KodiMagicValues.REGION_SHORT_DATE_FORMAT_ID)

    @property
    def long_date_format(self) -> str:
        return xbmc.getRegion(id=_KodiMagicValues.REGION_LONG_DATE_FORMAT_ID)

    def _get_localized_string(self, string_id: int):
        return self._kodi_addon.getLocalizedString(id=string_id) or xbmc.getLocalizedString(id=string_id)

    def _get_setting(self, setting: KodiPluginSetting) -> _Setting_Type:
        if setting.setting_type == bool:
            return self._kodi_addon.getSettingBool(id=setting.setting_id)
        elif setting.setting_type == int:
            return self._kodi_addon.getSettingInt(id=setting.setting_id)
        elif setting.setting_type == float:
            return self._kodi_addon.getSettingNumber(id=setting.setting_id)
        elif setting.setting_type == str:
            return self._kodi_addon.getSettingString(id=setting.setting_id)
        else:
            return self._kodi_addon.getSetting(id=setting.setting_id)

    def log(self, message: str, level: KodiLogLevel = KodiLogLevel.DEBUG):
        if self._allow_logging:
            xbmc.log(msg=f"[{self.__addon_id}] {message}", level=level.value)

    @abstractmethod
    def required_settings_done(self) -> bool:
        raise NotImplementedError()

    def dialog(self, message_id: int) -> bool:
        return xbmcgui.Dialog().ok(
            heading=self._kodi_addon.getAddonInfo(id=_KodiMagicValues.ADDON_INFO_NAME_ID),
            message=self._get_localized_string(string_id=message_id)
        )
    
    def _set_window_property(self, key: str, value: str) -> None:
        self._window.setProperty(
            key=key,
            value=value
        )
        self.log(message=f"{key} := {value}", level=KodiLogLevel.DEBUG)

    def clear_weather_properties(self) -> None:
        for property_set in _KodiWeatherProperties.all():
            for key in property_set.values:
                self._set_window_property(key=key, value="")

    @staticmethod
    def format_unit(unit: Union[Temperature, Speed], value_format: str = "{:.0f}") -> str:
        if unit is None or unit.value is None:
            return ""
        return (value_format + " {}").format(unit.value, unit.unit)

    def set_weather_properties(self, forecast: KodiForecastData) -> None:
        percent = "{:.0f} %".format
        true = "true"
        self._set_window_property(key=_KodiWeatherProperties.GENERAL.LOCATION_1, value=forecast.General.location)
        self._set_window_property(key=_KodiWeatherProperties.GENERAL.LOCATIONS, value="1")
        # current
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.CONDITION,
            value=forecast.Current.condition_str
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.TEMPERATURE,
            value=self.format_unit(
                TemperatureCelsius.from_si_value(forecast.Current.temperature.si_value())
            ) if forecast.Current.temperature.value is not None else ""
        )   # converted by Kodi from °C
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.UV_INDEX,
            value=str(forecast.Current.uv_index)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.OUTLOOK_ICON,
            value=forecast.Current.outlook_icon
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.FANART_CODE,
            value=str(forecast.Current.fanart_code)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.WIND,
            value=self.format_unit(
                SpeedKph.from_si_value(forecast.Current.wind_speed.si_value())
            ) if forecast.Current.wind_speed.value is not None else ""
        )   # converted by Kodi from km/h
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.WIND_DIRECTION,
            value=self._get_localized_string(string_id=forecast.Current.wind_direction.value)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.HUMIDITY,
            value=str(forecast.Current.humidity) if forecast.Current.humidity is not None else ""
        )    # % is added by Kodi
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.DEW_POINT,
            value=self.format_unit(
                TemperatureCelsius.from_si_value(forecast.Current.dew_point.si_value())
            ) if forecast.Current.dew_point.value is not None else ""
        )     # converted by Kodi from °C
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.FEELS_LIKE,
            value=self.format_unit(
                TemperatureCelsius.from_si_value(forecast.Current.feels_like.si_value())
            ) if forecast.Current.feels_like.value is not None else ""
        )   # converted by Kodi from °C
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.WIND_CHILL,
            value=self.format_unit(
                self.temperature_unit.from_si_value(forecast.Current.feels_like.si_value())
            ) if forecast.Current.feels_like.value is not None else ""
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.PRECIPITATION,
            value=forecast.Current.precipitation or ""
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.CLOUDINESS,
            value=percent(forecast.Current.cloudiness)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.CURRENT.PRESSURE,
            value=forecast.Current.pressure or ""
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.SUNRISE,
            value=forecast.Current.sunrise.strftime(self.time_format)
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.SUNSET,
            value=forecast.Current.sunset.strftime(self.time_format)
        )

        # hourly
        for hourly_forecast, hourly_properties in zip(
                forecast.HourlyForecasts,
                _KodiWeatherProperties.hourlies()
        ):
            hourly_forecast: KodiHourlyForecastData
            hourly_properties: _KodiHourlyWeatherProperties
            self._set_window_property(
                key=hourly_properties.TIME,
                value=hourly_forecast.timestamp.strftime(self.time_format)
            )
            self._set_window_property(
                key=hourly_properties.LONG_DATE,
                value=hourly_forecast.timestamp.strftime(self.long_date_format)
            )
            self._set_window_property(
                key=hourly_properties.SHORT_DATE,
                value=hourly_forecast.timestamp.strftime(self.short_date_format)
            )
            self._set_window_property(
                key=hourly_properties.OUTLOOK,
                value=hourly_forecast.condition_str
            )
            self._set_window_property(
                key=hourly_properties.OUTLOOK_ICON,
                value=hourly_forecast.outlook_icon
            )
            self._set_window_property(
                key=hourly_properties.FANART_CODE,
                value=str(hourly_forecast.fanart_code)
            )
            self._set_window_property(
                key=hourly_properties.WIND_SPEED,
                value=self.format_unit(
                    self.wind_speed_unit.from_si_value(hourly_forecast.wind_speed.si_value())
                ) if hourly_forecast.wind_speed.value is not None else ""
            )
            self._set_window_property(
                key=hourly_properties.WIND_DIRECTION,
                value=self._get_localized_string(string_id=hourly_forecast.wind_direction.value)
            )
            self._set_window_property(
                key=hourly_properties.HUMIDITY,
                value=percent(hourly_forecast.humidity) if hourly_forecast.humidity is not None else ""
            )
            self._set_window_property(
                key=hourly_properties.TEMPERATURE,
                value=self.format_unit(
                    self.temperature_unit.from_si_value(hourly_forecast.temperature.si_value())
                ) if hourly_forecast.temperature.value is not None else ""
            )
            self._set_window_property(
                key=hourly_properties.DEW_POINT,
                value=self.format_unit(
                    self.temperature_unit.from_si_value(hourly_forecast.dew_point.si_value())
                ) if hourly_forecast.dew_point.value is not None else ""
            )
            self._set_window_property(
                key=hourly_properties.FEELS_LIKE,
                value=self.format_unit(
                    self.temperature_unit.from_si_value(hourly_forecast.feels_like.si_value())
                ) if hourly_forecast.feels_like.value is not None else ""
            )
            self._set_window_property(
                key=hourly_properties.PRESSURE,
                value=hourly_forecast.pressure or ""
            )
            self._set_window_property(
                key=hourly_properties.PRECIPITATION,
                value=hourly_forecast.precipitation or ""
            )

        # daily
        for daily_forecast, daily_properties, daily_properties_compat in zip(
            forecast.DailyForecasts,
            _KodiWeatherProperties.dailies(),
            _KodiWeatherProperties.dailies_compat(),
        ):
            daily_forecast: KodiDailyForecastData
            daily_properties: _KodiDailyWeatherProperties
            daily_properties_compat: _KodiDailyWeatherPropertiesCompat
            self._set_window_property(
                key=daily_properties.SHORT_DATE,
                value=daily_forecast.timestamp.strftime(self.short_date_format)
            )
            self._set_window_property(
                key=daily_properties.SHORT_DAY,
                value=self._get_localized_string(
                    string_id=daily_forecast.timestamp.isoweekday() + _KodiMagicValues.MESSAGE_OFFSET_DAY_LONG)
            )
            self._set_window_property(
                key=daily_properties.HIGH_TEMPERATURE,
                value=self.format_unit(
                    self.temperature_unit.from_si_value(daily_forecast.temperature.si_value())
                ) if daily_forecast.temperature.value is not None else ""
            )
            self._set_window_property(
                key=daily_properties.LOW_TEMPERATURE,
                value=self.format_unit(
                    self.temperature_unit.from_si_value(daily_forecast.low_temperature.si_value())
                ) if daily_forecast.low_temperature.value is not None else ""
            )
            self._set_window_property(
                key=daily_properties.OUTLOOK,
                value=daily_forecast.condition_str
            )
            self._set_window_property(
                key=daily_properties.OUTLOOK_ICON,
                value=daily_forecast.outlook_icon
            )
            self._set_window_property(
                key=daily_properties.FANART_CODE,
                value=str(daily_forecast.fanart_code)
            )
            self._set_window_property(
                key=daily_properties.WIND_SPEED,
                value=self.format_unit(
                    self.wind_speed_unit.from_si_value(daily_forecast.wind_speed.si_value())
                ) if daily_forecast.wind_speed.value is not None else ""
            )
            self._set_window_property(
                key=daily_properties.WIND_DIRECTION,
                value=self._get_localized_string(string_id=daily_forecast.wind_direction.value)
            )
            self._set_window_property(
                key=daily_properties.PRECIPITATION,
                value=daily_forecast.precipitation or ""
            )
            self._set_window_property(
                key=daily_properties_compat.TITLE,
                value=self._get_localized_string(
                    string_id=daily_forecast.timestamp.isoweekday() + _KodiMagicValues.MESSAGE_OFFSET_DAY_SHORT)
            )
            self._set_window_property(
                key=daily_properties_compat.HIGH_TEMP,
                value=self.format_unit(
                    TemperatureCelsius.from_si_value(daily_forecast.temperature.si_value())
                ) if daily_forecast.temperature.value is not None else ""
            )   # converted by skins from °C
            self._set_window_property(
                key=daily_properties_compat.LOW_TEMP,
                value=self.format_unit(
                    TemperatureCelsius.from_si_value(daily_forecast.low_temperature.si_value())
                ) if daily_forecast.low_temperature.value is not None else ""
            )   # converted by skins from °C
            self._set_window_property(
                key=daily_properties_compat.OUTLOOK,
                value=daily_forecast.condition_str
            )
            self._set_window_property(
                key=daily_properties_compat.OUTLOOK_ICON,
                value=daily_forecast.outlook_icon
            )
            self._set_window_property(
                key=daily_properties_compat.FANART_CODE,
                value=str(daily_forecast.fanart_code)
            )
        # general
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.CURRENT_LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.REGIONAL_LOCATION,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_CITY,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_COUNTRY,
            value=forecast.General.location
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_LATITUDE,
            value="0"
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_LONGITUDE,
            value="0"
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.FORECAST_UPDATED,
            value=datetime.now(tz=timezone.utc).isoformat()
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.UPDATED,
            value=datetime.now(tz=timezone.utc).isoformat()
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.WEATHER_PROVIDER,
            value=forecast.General.attribution
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.WEATHER_PROVIDER_LOGO,
            value=xbmcvfs.translatePath(os.path.join(self.cwd, "resources", "banner.jpg"))
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.WEATHER_IS_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.CURRENT_IS_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.HOURLY_IS_FETCHED,
            value=true
        )
        self._set_window_property(
            key=_KodiWeatherProperties.GENERAL.DAILY_IS_FETCHED,
            value=true
        )
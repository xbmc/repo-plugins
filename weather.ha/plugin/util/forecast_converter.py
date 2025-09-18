from datetime import datetime
from typing import Union

from lib.homeassistant import (
    HomeAssistantHourlyForecast, HomeAssistantForecastMeta, HomeAssistantDailyForecast,
    HomeAssistantForecast, HomeAssistantSunInfo, HomeAssistantWeatherCondition
)
from lib.kodi import (
    KodiHourlyForecastData, KodiWindDirectionCode, KodiDailyForecastData, KodiForecastData,
    KodiGeneralForecastData, KodiCurrentForecastData, KodiConditionCode
)
from lib.unit.speed import SpeedUnits
from lib.unit.temperature import TemperatureUnits
from lib.util.thermal_comfort import ThermalComfort


class ForecastConverter:
    @staticmethod
    def __translate_hourly_ha_forecast_to_kodi_forecast(
            ha_forecast: HomeAssistantHourlyForecast, forecast_meta: HomeAssistantForecastMeta,
            sunset: datetime, sunrise: datetime
    ) -> KodiHourlyForecastData:
        temperature = TemperatureUnits[forecast_meta.temperature_unit](ha_forecast.temperature)
        wind_speed = SpeedUnits[forecast_meta.wind_speed_unit](ha_forecast.wind_speed)
        timestamp = ForecastConverter.__parse_homeassistant_datetime(datetime_str=ha_forecast.datetime)
        return KodiHourlyForecastData(
            temperature=temperature,
            wind_speed=wind_speed,
            wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.wind_bearing),
            precipitation=ForecastConverter.__format_precipitation(
                precipitation=ha_forecast.precipitation, precipitation_unit=forecast_meta.precipitation_unit
            ),
            humidity=ha_forecast.humidity,
            feels_like=ThermalComfort.feels_like(
                temperature=temperature,
                wind_speed=wind_speed
            ),
            dew_point=ThermalComfort.dew_point(
                temperature=temperature,
                humidity_percent=ha_forecast.humidity
            ),
            condition=ForecastConverter.__translate_condition(
                ha_condition=ha_forecast.condition, is_night=not (sunrise.time() < timestamp.time() < sunset.time())
            ),
            timestamp=timestamp,
            pressure="",
        )

    @staticmethod
    def __translate_daily_ha_forecast_to_kodi_forecast(
            ha_forecast: HomeAssistantDailyForecast, forecast_meta: HomeAssistantForecastMeta) -> KodiDailyForecastData:
        temperature = TemperatureUnits[forecast_meta.temperature_unit](ha_forecast.temperature)
        low_temperature = TemperatureUnits[forecast_meta.temperature_unit](ha_forecast.templow)
        wind_speed = SpeedUnits[forecast_meta.wind_speed_unit](ha_forecast.wind_speed)
        return KodiDailyForecastData(
            temperature=temperature,
            wind_speed=wind_speed,
            wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.wind_bearing),
            precipitation=ForecastConverter.__format_precipitation(
                precipitation=ha_forecast.precipitation, precipitation_unit=forecast_meta.precipitation_unit
            ),
            condition=ForecastConverter.__translate_condition(ha_condition=ha_forecast.condition),
            timestamp=ForecastConverter.__parse_homeassistant_datetime(datetime_str=ha_forecast.datetime),
            low_temperature=low_temperature,
        )

    @staticmethod
    def translate_ha_forecast_to_kodi_forecast(
            ha_forecast: HomeAssistantForecast, ha_sun_info: HomeAssistantSunInfo) -> KodiForecastData:
        temperature = TemperatureUnits[ha_forecast.current.temperature_unit](ha_forecast.current.temperature)
        wind_speed = SpeedUnits[ha_forecast.current.wind_speed_unit](ha_forecast.current.wind_speed)
        sunrise = ForecastConverter.__parse_homeassistant_datetime(ha_sun_info.next_rising)
        sunset = ForecastConverter.__parse_homeassistant_datetime(ha_sun_info.next_setting)

        ha_condition = ha_forecast.current.condition
        if ha_condition is None and len(ha_forecast.hourly) > 0:
            ha_condition = ha_forecast.hourly[0].condition
        if ha_condition is None and len(ha_forecast.daily) > 0:
            ha_condition = ha_forecast.daily[0].condition

        return KodiForecastData(
            General=KodiGeneralForecastData(
                location=ha_forecast.current.friendly_name,
                attribution=ha_forecast.current.attribution,
            ),
            Current=KodiCurrentForecastData(
                temperature=temperature,
                wind_speed=wind_speed,
                wind_direction=KodiWindDirectionCode.from_bearing(bearing=ha_forecast.current.wind_bearing),
                precipitation=ForecastConverter.__format_precipitation(
                    precipitation=ha_forecast.hourly[0].precipitation if len(ha_forecast.hourly) > 0 else None,
                    precipitation_unit=ha_forecast.current.precipitation_unit
                ),  # conversion not implemented in Kodi
                condition=ForecastConverter.__translate_condition(
                    ha_condition=ha_condition,
                    is_night=not (sunrise.time() < datetime.now().time() < sunset.time())
                ),
                humidity=ha_forecast.current.humidity,
                feels_like=ThermalComfort.feels_like(
                    temperature=temperature,
                    wind_speed=wind_speed,
                ),
                dew_point=ThermalComfort.dew_point(
                    temperature=temperature,
                    humidity_percent=ha_forecast.current.humidity
                ),
                uv_index=int(ha_forecast.current.uv_index if ha_forecast.current.uv_index != None else 0),
                cloudiness=int(ha_forecast.current.cloud_coverage if ha_forecast.current.cloud_coverage != None else 0),
                pressure=ForecastConverter.__format_pressure(
                    pressure=ha_forecast.current.pressure if ha_forecast.current.pressure != None else 0, pressure_unit=ha_forecast.current.pressure_unit
                ),
                sunrise=sunrise,
                sunset=sunset,
            ),
            HourlyForecasts=[
                ForecastConverter.__translate_hourly_ha_forecast_to_kodi_forecast(
                    ha_forecast=hourly_forecast,
                    forecast_meta=ha_forecast.current,
                    sunrise=sunrise,
                    sunset=sunset,
                )
                for hourly_forecast in ha_forecast.hourly
            ],
            DailyForecasts=[
                ForecastConverter.__translate_daily_ha_forecast_to_kodi_forecast(
                    ha_forecast=daily_forecast,
                    forecast_meta=ha_forecast.current
                )
                for daily_forecast in ha_forecast.daily
            ]
        )

    @staticmethod
    def __translate_condition(
            ha_condition: Union[HomeAssistantWeatherCondition, None], is_night: bool = False
    ) -> Union[KodiConditionCode, None]:
        if ha_condition is None:
            return None
        elif ha_condition == HomeAssistantWeatherCondition.CLEAR_NIGHT.value:
            return KodiConditionCode.CLEAR_NIGHT
        elif ha_condition == HomeAssistantWeatherCondition.CLOUDY.value:
            return KodiConditionCode.CLOUDY if not is_night else KodiConditionCode.MOSTLY_CLOUDY_NIGHT
        elif ha_condition == HomeAssistantWeatherCondition.FOG.value:
            return KodiConditionCode.FOGGY
        elif ha_condition == HomeAssistantWeatherCondition.HAIL.value:
            return KodiConditionCode.HAIL
        elif ha_condition == HomeAssistantWeatherCondition.LIGHTNING.value:
            return KodiConditionCode.THUNDERSTORMS
        elif ha_condition == HomeAssistantWeatherCondition.LIGHTNING_RAINY.value:
            return KodiConditionCode.THUNDERSHOWERS
        elif ha_condition == HomeAssistantWeatherCondition.PARTLY_CLOUDY.value:
            return KodiConditionCode.PARTLY_CLOUDY if not is_night else KodiConditionCode.PARTLY_CLOUDY_NIGHT
        elif ha_condition == HomeAssistantWeatherCondition.POURING.value:
            return KodiConditionCode.SHOWERS_2
        elif ha_condition == HomeAssistantWeatherCondition.RAINY.value:
            return KodiConditionCode.SHOWERS
        elif ha_condition == HomeAssistantWeatherCondition.SNOWY.value:
            return KodiConditionCode.SNOW
        elif ha_condition == HomeAssistantWeatherCondition.SNOWY_RAINY.value:
            return KodiConditionCode.MIXED_RAIN_AND_SNOW
        elif ha_condition == HomeAssistantWeatherCondition.SUNNY.value:
            return KodiConditionCode.SUNNY
        elif ha_condition == HomeAssistantWeatherCondition.WINDY.value:
            return KodiConditionCode.WINDY
        elif ha_condition == HomeAssistantWeatherCondition.WINDY_CLOUDY.value:
            return KodiConditionCode.WINDY
        elif ha_condition == HomeAssistantWeatherCondition.EXCEPTIONAL.value:
            return KodiConditionCode.SEVERE_THUNDERSTORMS
        else:
            raise ValueError(f"Unknown condition: {ha_condition}")

    @staticmethod
    def __format_precipitation(precipitation: Union[float, None], precipitation_unit: str) -> Union[str, None]:
        if precipitation is None:
            return None
        # scientific rounding to 0 or 1 significant decimal
        if precipitation > 3:
            fmt = "{:.0f} {}"
        else:
            fmt = "{:.1f} {}"
        return fmt.format(precipitation, precipitation_unit)

    @staticmethod
    def __format_pressure(pressure: Union[float, None], pressure_unit: str) -> str:
        if pressure is None:
            return ""
        return "{:.0f} {}".format(pressure, pressure_unit)

    @staticmethod
    def __parse_homeassistant_datetime(datetime_str: str) -> datetime:
        # tz=None adds time offset to match Kodi's set time
        return datetime.fromisoformat(datetime_str).astimezone(tz=None)
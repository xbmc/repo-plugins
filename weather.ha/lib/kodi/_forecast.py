from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from typing import List

from lib.unit.speed import Speed
from lib.unit.temperature import Temperature


class KodiConditionCode(IntEnum):
    TORNADO = 0
    TROPICAL_STORM = 1
    HURRICANE = 2
    SEVERE_THUNDERSTORMS = 3
    THUNDERSTORMS = 4
    MIXED_RAIN_AND_SNOW = 5
    MIXED_RAIN_AND_SLEET = 6
    MIXED_SNOW_AND_SLEET = 7
    FREEZING_DRIZZLE = 8
    DRIZZLE = 9
    FREEZING_RAIN = 10
    SHOWERS = 11
    SHOWERS_2 = 12
    SNOW_FLURRIES = 13
    LIGHT_SNOW_SHOWERS = 14
    BLOWING_SNOW = 15
    SNOW = 16
    HAIL = 17
    SLEET = 18
    DUST = 19
    FOGGY = 20
    HAZE = 21
    SMOKY = 22
    BLUSTERY = 23
    WINDY = 24
    COLD = 25
    CLOUDY = 26
    MOSTLY_CLOUDY_NIGHT = 27
    MOSTLY_CLOUDY = 28
    PARTLY_CLOUDY_NIGHT = 29
    PARTLY_CLOUDY = 30
    CLEAR_NIGHT = 31
    SUNNY = 32
    FAIR_NIGHT = 33
    FAIR_DAY = 34
    MIXED_RAIN_AND_HAIL = 35
    HOT = 36
    ISOLATED_THUNDERSTORMS = 37
    SCATTERED_THUNDERSTORMS = 38
    SCATTERED_THUNDERSTORMS_2 = 39
    SCATTERED_SHOWERS = 40
    HEAVY_SNOW = 41
    SCATTERED_SNOW_SHOWERS = 42
    HEAVY_SNOW_2 = 43
    PARTLY_CLOUDY_2 = 44
    THUNDERSHOWERS = 45
    SNOW_SHOWERS = 46
    ISOLATED_THUNDERSHOWERS = 47

    def __str__(self):
        return self.name.lower().replace('_', ' ')


class KodiWindDirectionCode(IntEnum):
    # https://raw.githubusercontent.com/xbmc/xbmc/master/addons/resource.language.en_gb/resources/strings.po from #71
    N = 71
    NNE = 72
    NE = 73
    ENE = 74
    E = 75
    ESE = 76
    SE = 77
    SSE = 78
    S = 79
    SSW = 80
    SW = 81
    WSW = 82
    W = 83
    WNW = 84
    NW = 85
    NNW = 86
    VAR = 87

    @staticmethod
    def from_bearing(bearing: float):
        if bearing is None:
            return KodiWindDirectionCode.VAR
        elif isinstance(bearing, str):
             bearing=bearing.upper()
             if bearing == 'N':
                 return KodiWindDirectionCode.N
             elif bearing == 'NNE':
                 return KodiWindDirectionCode.NNE

             elif bearing == 'NE':
                 return KodiWindDirectionCode.NE
             elif bearing == 'ENE':
                 return KodiWindDirectionCode.ENE
             elif bearing == 'E':
                 return KodiWindDirectionCode.E
             elif bearing == 'ESE':
                 return KodiWindDirectionCode.ESE
             elif bearing == 'SE':
                 return KodiWindDirectionCode.SE
             elif bearing == 'SSE':
                 return KodiWindDirectionCode.SSE
             elif bearing == 'S':
                 return KodiWindDirectionCode.S
             elif bearing == 'SSW':
                 return KodiWindDirectionCode.SSW
             elif bearing == 'SW':
                 return KodiWindDirectionCode.SW
             elif bearing == 'WSW':
                 return KodiWindDirectionCode.WSW
             elif bearing == 'W':
                 return KodiWindDirectionCode.W
             elif bearing == 'WNW':
                 return KodiWindDirectionCode.WNW
             elif bearing == 'NW':
                 return KodiWindDirectionCode.NW
             elif bearing == 'NNW':
                 return KodiWindDirectionCode.NNW
        elif bearing >= 349 or bearing <= 11:
            return KodiWindDirectionCode.N
        elif 12 <= bearing <= 33:
            return KodiWindDirectionCode.NNE
        elif 34 <= bearing <= 56:
            return KodiWindDirectionCode.NE
        elif 57 <= bearing <= 78:
            return KodiWindDirectionCode.ENE
        elif 79 <= bearing <= 101:
            return KodiWindDirectionCode.E
        elif 102 <= bearing <= 123:
            return KodiWindDirectionCode.ESE
        elif 124 <= bearing <= 146:
            return KodiWindDirectionCode.SE
        elif 147 <= bearing <= 168:
            return KodiWindDirectionCode.SSE
        elif 169 <= bearing <= 191:
            return KodiWindDirectionCode.S
        elif 192 <= bearing <= 213:
            return KodiWindDirectionCode.SSW
        elif 214 <= bearing <= 236:
            return KodiWindDirectionCode.SW
        elif 237 <= bearing <= 258:
            return KodiWindDirectionCode.WSW
        elif 259 <= bearing <= 281:
            return KodiWindDirectionCode.W
        elif 282 <= bearing <= 303:
            return KodiWindDirectionCode.WNW
        elif 304 <= bearing <= 326:
            return KodiWindDirectionCode.NW
        elif 327 <= bearing <= 348:
            return KodiWindDirectionCode.NNW
        return KodiWindDirectionCode.VAR


@dataclass
class _KodiForecastCommon:
    temperature: Temperature
    wind_speed: Speed
    wind_direction: KodiWindDirectionCode   # eg: NNE
    precipitation: str                      # with unit


@dataclass
class _KodiDetailedForecastCommon:
    humidity: float     # unit: %
    feels_like: Temperature
    dew_point: Temperature


@dataclass
class _KodiConditionedForecastCommon:
    condition: KodiConditionCode

    @property
    def condition_str(self) -> str:
        return str(self.condition) if self.condition is not None else ""

    @property
    def fanart_code(self) -> int:
        return self.condition.value if self.condition is not None else 0

    @property
    def outlook_icon(self) -> str:
        return f"{self.condition.value}.png" if self.condition is not None else ""


@dataclass
class _KodiFutureForecastCommon:
    timestamp: datetime


@dataclass
class KodiGeneralForecastData:
    location: str
    attribution: str


@dataclass
class KodiCurrentForecastData(_KodiForecastCommon, _KodiDetailedForecastCommon, _KodiConditionedForecastCommon):
    uv_index: int
    cloudiness: int     # unit: %
    pressure: str       # with unit
    sunrise: datetime
    sunset: datetime


@dataclass
class KodiHourlyForecastData(
    _KodiFutureForecastCommon, _KodiForecastCommon, _KodiDetailedForecastCommon, _KodiConditionedForecastCommon
):
    pressure: str       # with unit


@dataclass
class KodiDailyForecastData(_KodiFutureForecastCommon, _KodiForecastCommon, _KodiConditionedForecastCommon):
    low_temperature: Temperature


@dataclass
class KodiForecastData:
    General: KodiGeneralForecastData
    Current: KodiCurrentForecastData
    HourlyForecasts: List[KodiHourlyForecastData]
    DailyForecasts: List[KodiDailyForecastData]
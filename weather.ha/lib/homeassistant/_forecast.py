from dataclasses import dataclass
from enum import Enum
from typing import List, Union


class HomeAssistantWeatherCondition(str, Enum):
    CLEAR_NIGHT = "clear-night"
    CLOUDY = "cloudy"
    FOG = "fog"
    HAIL = "hail"
    LIGHTNING = "lightning"
    LIGHTNING_RAINY = "lightning-rainy"
    PARTLY_CLOUDY = "partlycloudy"
    POURING = "pouring"
    RAINY = "rainy"
    SNOWY = "snowy"
    SNOWY_RAINY = "snowy-rainy"
    SUNNY = "sunny"
    WINDY = "windy"
    WINDY_CLOUDY = "windy-cloudy"
    EXCEPTIONAL = "exceptional"


@dataclass
class _HomeAssistantForecastCommon:
    wind_bearing: float
    wind_speed: float
    temperature: float
    humidity: float


@dataclass
class HomeAssistantForecastMeta:
    temperature_unit: str
    pressure_unit: str
    wind_speed_unit: str
    visibility_unit: str
    precipitation_unit: str
    attribution: str
    friendly_name: str
    supported_features: int


@dataclass
class _HomeAssistantFutureForecast:
    condition: HomeAssistantWeatherCondition
    datetime: str
    precipitation: float

    def __post_init__(self):
        self.condition = HomeAssistantWeatherCondition(self.condition)


@dataclass
class HomeAssistantCurrentForecast(_HomeAssistantForecastCommon, HomeAssistantForecastMeta):
    condition: HomeAssistantWeatherCondition
    dew_point: float
    cloud_coverage: float
    pressure: float
    uv_index: float

    def __post_init__(self):
        self.condition = HomeAssistantWeatherCondition(self.condition)


@dataclass
class HomeAssistantHourlyForecast(_HomeAssistantForecastCommon, _HomeAssistantFutureForecast):
    cloud_coverage: float
    uv_index: float


@dataclass
class HomeAssistantDailyForecast(_HomeAssistantForecastCommon, _HomeAssistantFutureForecast):
    templow: float
    uv_index: Union[float, None] = None


@dataclass
class HomeAssistantForecast:
    current: HomeAssistantCurrentForecast
    hourly: List[HomeAssistantHourlyForecast]
    daily: List[HomeAssistantDailyForecast]

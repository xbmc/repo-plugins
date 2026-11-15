import math

from lib.unit.speed import Speed, SpeedKph
from lib.unit.temperature import Temperature, TemperatureCelsius


class ThermalComfort:
    @staticmethod
    def dew_point(temperature: Temperature, humidity_percent: float) -> TemperatureCelsius:
        if temperature.value is None or humidity_percent is None:
            return TemperatureCelsius(None)

        temperature_celsius = TemperatureCelsius.from_si_value(temperature.si_value())
        # obtain saturation vapor pressure (pressure at which water in air will condensate)
        vapor_pressure_sat = 6.11 * 10.0 ** (7.5 * temperature_celsius.value / (237.7 + temperature_celsius.value))
        # we set a minimum of .075 % to make the math defined
        humidity_percent = max(humidity_percent, 0.075)
        # calculate actual vapor pressure (water in air will condensate at approx. 100 % humidity), linear correlation
        vapor_pressure_act = (humidity_percent * vapor_pressure_sat) / 100
        # Now you are ready to use the following formula to obtain the dewpoint temperature.
        return TemperatureCelsius(
            (-430.22 + 237.7 * math.log(vapor_pressure_act)) / (-math.log(vapor_pressure_act) + 19.08)
        )

    @staticmethod
    def feels_like(temperature: Temperature, wind_speed: Speed) -> TemperatureCelsius:
        if temperature.value is None or wind_speed.value is None:
            return TemperatureCelsius(None)

        temperature_celsius = TemperatureCelsius.from_si_value(temperature.si_value())
        wind_speed_kph = SpeedKph.from_si_value(wind_speed.si_value())
        # Model: Wind Chill JAG/TI Environment Canada
        # see https://en.wikipedia.org/wiki/Wind_chill#North_American_and_United_Kingdom_wind_chill_index
        return TemperatureCelsius(
            + 13.12
            + 0.6215 * temperature_celsius.value
            - 11.37 * wind_speed_kph.value ** 0.16
            + 0.3965 * temperature_celsius.value * wind_speed_kph.value ** 0.16
        )
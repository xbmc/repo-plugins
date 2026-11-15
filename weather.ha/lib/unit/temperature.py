from abc import abstractmethod
from typing import Mapping, Type

from ._util import _ValueWithUnit


class Temperature(_ValueWithUnit):

    @staticmethod
    @abstractmethod
    def from_si_value(value: float) -> 'Temperature':
        raise NotImplementedError()


# Conversions see https://en.wikipedia.org/wiki/Conversion_of_scales_of_temperature
class TemperatureCelsius(Temperature):
    unit = "°C"

    def si_value(self) -> float:
        return (self.value if self.value is not None else 0) + 273.15

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureCelsius':
        return TemperatureCelsius((value if value is not None else 0) - 273.15)


class TemperatureFahrenheit(Temperature):
    unit = "°F"

    def si_value(self) -> float:
        return (self.value + 459.67) / 1.8

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureFahrenheit':
        return TemperatureFahrenheit(value * 1.8 - 459.67)


class TemperatureKelvin(Temperature):
    unit = "K"

    def si_value(self) -> float:
        return self.value

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureKelvin':
        return TemperatureKelvin(value)


class TemperatureRankine(Temperature):
    unit = "°Ra"

    def si_value(self) -> float:
        return self.value / 1.8

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureRankine':
        return TemperatureRankine(value * 1.8)


class TemperatureReaumur(Temperature):
    unit = "°Ré"

    def si_value(self) -> float:
        return self.value / 0.8 + 273.15

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureReaumur':
        return TemperatureReaumur((value - 273.15) * 0.8)


class TemperatureRomer(Temperature):
    unit = "°Rø"

    def si_value(self) -> float:
        return (self.value - 7.5) / 0.525 + 273.15

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureRomer':
        return TemperatureRomer((value - 273.15) * 0.525 + 7.5)


class TemperatureDelisle(Temperature):
    unit = "°De"

    def si_value(self) -> float:
        return 373.15 - self.value / 1.5

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureDelisle':
        return TemperatureDelisle((373.15 - value) * 1.5)


class TemperatureNewton(Temperature):
    unit = "°N"

    def si_value(self) -> float:
        return self.value / 0.33 + 273.15

    @staticmethod
    def from_si_value(value: float) -> 'TemperatureNewton':
        return TemperatureNewton((value - 273.15) * 0.33)


TemperatureUnits: Mapping[str, Type[Temperature]] = {
    TemperatureCelsius.unit: TemperatureCelsius,
    TemperatureFahrenheit.unit: TemperatureFahrenheit,
    TemperatureKelvin.unit: TemperatureKelvin,
    TemperatureReaumur.unit: TemperatureReaumur,
    TemperatureRankine.unit: TemperatureRankine,
    TemperatureRomer.unit: TemperatureRomer,
    TemperatureDelisle.unit: TemperatureDelisle,
    TemperatureNewton.unit: TemperatureNewton,
}

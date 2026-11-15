from abc import abstractmethod
from typing import Mapping, Type

from ._util import _ValueWithUnit


class Speed(_ValueWithUnit):

    @staticmethod
    @abstractmethod
    def from_si_value(value: float) -> 'Speed ':
        raise NotImplementedError()


_feet_per_meter = 3.28084
_meters_per_mile = 1609.34
_meters_per_inch = 0.0254
_inches_per_yard = 36.0
_yards_per_furlong = 220.0
_meters_per_nautic_mile = 1852.0
_meters_per_kilometer = 1000.0
_seconds_per_fortnight = 1209600.0
_seconds_per_minute = 60.0
_minutes_per_hour = 60.0
# https://en.wikipedia.org/wiki/Beaufort_scale
# upper bound non-inclusive
_beaufort_mps_conversion_table = {
    0: (0, 0.3),
    1: (0.3, 1.6),
    2: (1.6, 3.4),
    3: (3.4, 5.5),
    4: (5.5, 8.0),
    5: (8.0, 10.8),
    6: (10.8, 13.9),
    7: (13.9, 17.2),
    8: (17.2, 20.8),
    9: (20.8, 24.5),
    10: (24.5, 28.5),
    11: (28.5, 32.7),
    12: (32.7, 1000000),
}


class SpeedKph(Speed):
    unit = "km/h"

    def si_value(self) -> float:
        return self.value * _meters_per_kilometer / (_seconds_per_minute * _minutes_per_hour)

    @staticmethod
    def from_si_value(value: float) -> 'SpeedKph':
        kilometer_per_second = value / _meters_per_kilometer
        kilometer_per_hour = kilometer_per_second * _seconds_per_minute * _minutes_per_hour
        return SpeedKph(kilometer_per_hour)


class SpeedMpmin(Speed):
    unit = "m/min"

    def si_value(self) -> float:
        return self.value / _seconds_per_minute

    @staticmethod
    def from_si_value(value: float) -> 'SpeedMpmin':
        return SpeedMpmin(value * _seconds_per_minute)


class SpeedMps(Speed):
    unit = "m/s"

    def si_value(self) -> float:
        return self.value

    @staticmethod
    def from_si_value(value: float) -> 'SpeedMps':
        return SpeedMps(value)


class SpeedFtph(Speed):
    unit = "ft/h"

    def si_value(self) -> float:
        feet_per_second = self.value / (_seconds_per_minute * _minutes_per_hour)
        meter_per_second = feet_per_second / _feet_per_meter
        return meter_per_second

    @staticmethod
    def from_si_value(value: float) -> 'SpeedFtph':
        feet_per_second = value * _feet_per_meter
        feet_per_hour = feet_per_second * _seconds_per_minute * _minutes_per_hour
        return SpeedFtph(feet_per_hour)


class SpeedFtpm(Speed):
    unit = "ft/min"

    def si_value(self) -> float:
        feet_per_second = self.value / _seconds_per_minute
        meter_per_second = feet_per_second / _feet_per_meter
        return meter_per_second

    @staticmethod
    def from_si_value(value: float) -> 'SpeedFtpm':
        feet_per_second = value * _feet_per_meter
        feet_per_minute = feet_per_second * _seconds_per_minute
        return SpeedFtpm(feet_per_minute)


class SpeedFtps(Speed):
    unit = "ft/s"

    def si_value(self) -> float:
        return self.value / _feet_per_meter

    @staticmethod
    def from_si_value(value: float) -> 'SpeedFtps':
        return SpeedFtps(value * _feet_per_meter)


class SpeedMph(Speed):
    unit = "mph"

    def si_value(self) -> float:
        meter_per_hour = self.value * _meters_per_mile
        meter_per_second = meter_per_hour / (_seconds_per_minute * _minutes_per_hour)
        return meter_per_second

    @staticmethod
    def from_si_value(value: float) -> 'SpeedMph':
        meter_per_hour = value * (_seconds_per_minute * _minutes_per_hour)
        miles_per_hour = meter_per_hour / _meters_per_mile
        return SpeedMph(miles_per_hour)


class SpeedKts(Speed):
    unit = "kts"    # kts = nm/h

    def si_value(self) -> float:
        meter_per_hour = self.value * _meters_per_nautic_mile
        meter_per_second = meter_per_hour / (_seconds_per_minute * _minutes_per_hour)
        return meter_per_second

    @staticmethod
    def from_si_value(value: float) -> 'SpeedKts':
        meter_per_hour = value * _seconds_per_minute * _minutes_per_hour
        nautic_miles_per_hour = meter_per_hour / _meters_per_nautic_mile
        return SpeedKts(nautic_miles_per_hour)


class SpeedBft(Speed):
    unit = "Beaufort"

    def si_value(self) -> float:
        # Lower Bounds are used here
        return _beaufort_mps_conversion_table[int(self.value)][0]

    @staticmethod
    def from_si_value(value: float) -> 'SpeedBft':
        for bft, bounds in _beaufort_mps_conversion_table.items():
            if bounds[0] <= value < bounds[1]:
                return SpeedBft(bft)


class SpeedInps(Speed):
    unit = "inch/s"

    def si_value(self) -> float:
        return self.value * _meters_per_inch

    @staticmethod
    def from_si_value(value: float) -> 'SpeedInps':
        return SpeedInps(value / _meters_per_inch)


class SpeedYdps(Speed):
    unit = "yard/s"

    def si_value(self) -> float:
        inches_per_second = self.value * _inches_per_yard
        return inches_per_second * _meters_per_inch

    @staticmethod
    def from_si_value(value: float) -> 'SpeedYdps':
        inches_per_second = value / _meters_per_inch
        return SpeedYdps(inches_per_second / _inches_per_yard)


class SpeedFpf(Speed):
    unit = "Furlong/Fortnight"

    def si_value(self) -> float:
        meters_per_fortnight = self.value * _yards_per_furlong * _inches_per_yard * _meters_per_inch
        meters_per_second = meters_per_fortnight / _seconds_per_fortnight
        return meters_per_second

    @staticmethod
    def from_si_value(value: float) -> 'SpeedFpf':
        meters_per_fortnight = value * _seconds_per_fortnight
        furlongs_per_fortnight = meters_per_fortnight / (_meters_per_inch * _inches_per_yard * _yards_per_furlong)
        return SpeedFpf(furlongs_per_fortnight)


SpeedUnits: Mapping[str, Type[Speed]] = {
    SpeedKph.unit: SpeedKph,
    SpeedMpmin.unit: SpeedMpmin,
    SpeedMps.unit: SpeedMps,
    SpeedFtph.unit: SpeedFtph,
    SpeedFtpm.unit: SpeedFtpm,
    SpeedFtps.unit: SpeedFtps,
    SpeedMph.unit: SpeedMph,
    SpeedKts.unit: SpeedKts,
    SpeedBft.unit: SpeedBft,
    SpeedInps.unit: SpeedInps,
    SpeedYdps.unit: SpeedYdps,
    SpeedFpf.unit: SpeedFpf,
}

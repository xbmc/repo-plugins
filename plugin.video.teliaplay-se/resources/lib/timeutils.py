import functools
from datetime import datetime, timedelta
import pytz


class TimestampsException(Exception):
    pass


def unit_conversion(method):
    def get_unit(*args, **kwargs):
        try:
            return args[1]
        except IndexError:
            try:
                return kwargs["units"]
            except KeyError:
                return "s"

    @functools.wraps(method)
    def unit_conversion_wrapper(*args, **kwargs):
        if get_unit(*args, **kwargs) == "s":
            factor = 1
        elif get_unit(*args, **kwargs) == "ms":
            factor = 1000
        elif get_unit(*args, **kwargs) == "us":
            factor = 1000000
        else:
            unit = get_unit(*args, **kwargs)
            raise TimestampsException("Invalid time unit '{0}'".format(unit))
        return int(method(*args, **kwargs) * factor)
    return unit_conversion_wrapper


class TimezoneStamps():

    def __init__(self, area):
        self.timezone = pytz.timezone(area)

    @unit_conversion
    def yesterday(self, units="s"):
        yesterday_date = datetime.now(self.timezone) - timedelta(1)
        yesterday_date = datetime(
            yesterday_date.year, yesterday_date.month, yesterday_date.day, 0,
            0, 0, 0
        )
        return datetime.timestamp(yesterday_date)

    @unit_conversion
    def today(self, units="s"):
        today_date = datetime.now(self.timezone)
        today_date = datetime(
            today_date.year, today_date.month, today_date.day, 0, 0,
            0, 0
        )
        return datetime.timestamp(today_date)

    @unit_conversion
    def now(self, units="s"):
        now_date = datetime.now(self.timezone)
        return datetime.timestamp(now_date)

    @unit_conversion
    def tonight(self, units="s"):
        tonight_date = datetime.now(self.timezone)
        tonight_date = datetime(
            tonight_date.year, tonight_date.month, tonight_date.day, 20, 0,
            0, 0
        )
        return datetime.timestamp(tonight_date)

    @unit_conversion
    def tomorrow(self, units="s"):
        tomorrow_date = datetime.now(self.timezone) + timedelta(1)
        tomorrow_date = datetime(
            tomorrow_date.year, tomorrow_date.month, tomorrow_date.day, 0, 0,
            0, 0
        )
        return datetime.timestamp(tomorrow_date)

    @staticmethod
    def local_datetime_str(timestamp, units, time_format):
        if units == "s":
            factor = 1
        elif units == "ms":
            factor = 1000
        elif units == "us":
            factor = 1000000
        else:
            raise TimestampsException("Invalid time unit '{0}'".format(units))

        datetime_object = datetime.fromtimestamp(timestamp // factor)
        return datetime_object.strftime(time_format)

    @staticmethod
    def strip_seconds(time_str):
        time_str_split = time_str.split()
        time_str = time_str_split[0][:-3]
        try:
            time_str = time_str + " " + time_str_split[1]
        except IndexError:
            pass
        return time_str

    @staticmethod
    def convert_to_seconds(duration_str):
        duration_str_split = duration_str.split()

        seconds = 0
        for i in range(0, len(duration_str_split), 2):
            value = duration_str_split[i]
            unit = duration_str_split[i+1]
            if unit == "sek":
                seconds += int(value)
            elif unit == "min":
                seconds += int(value)*60
            elif unit == "tim":
                seconds += int(value)*3600
        return seconds

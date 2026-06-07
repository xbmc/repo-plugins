import functools
from datetime import datetime, timedelta
import pytz


class TimestampsException(Exception):
    pass


def unit_conversion_factor(units):
    if units == "s":
        factor = 1
    elif units == "ms":
        factor = 1000
    elif units == "us":
        factor = 1000000
    else:
        raise TimestampsException("Invalid time unit '{0}'".format(units))
    return factor


class TimezoneStamps():

    def __init__(self, area):
        self.timezone = pytz.timezone(area)

    def today(self, day_offset=0, units="s"):
        factor = unit_conversion_factor(units)
        today_date = datetime.now(self.timezone) + timedelta(days=day_offset)
        today_date = datetime(
            today_date.year, today_date.month, today_date.day, 0, 0,
            0, 0
        )
        return int(datetime.timestamp(today_date) * factor)

    def now(self, units="s"):
        factor = unit_conversion_factor(units)
        now_date = datetime.now(self.timezone)
        return int(datetime.timestamp(now_date) * factor)

    @staticmethod
    def local_datetime_str(timestamp, time_format, units):
        factor = unit_conversion_factor(units)
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

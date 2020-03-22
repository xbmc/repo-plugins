# SPDX-License-Identifier: CC-BY-NC-SA-4.0
import datetime
import pytz
import time


class DateHelper(object):
    """Helper class to parse datenames into numbers"""

    def __init__(self):
        """No initialisation, just statics"""

        raise NotImplementedError("Just statics")

    @staticmethod
    def is_dst(time_obj=time.localtime()):
        """ Is Daylight Saving active for the given time

        :param time.struct_time time_obj:
        :return: If Daylight Saving is enabled for the time

        """

        return time_obj.tm_isdst

    @staticmethod
    def this_year():
        """ Returns the current year

        :return: the current year.
        :rtype: int

        """

        now = datetime.datetime.now()
        return now.year

    @staticmethod
    def get_date_for_next_day(day, possibilities=None, tomorrow="Morgen", today="Vandaag"):
        """ Gets the date for the next Weekday (default ["ma", "di", "wo", "do", "vr", "za", "zo"]).

        :param str day:                 Weekday (present in "possibilities" parameter) to find
                                        the actual date for.
        :param list[str] possibilities: A list of possible day string values for monday to sunday.
        :param str tomorrow:            A possible alternative str for the day `tomorrow`.
        :param str today:               A possible alternative str for the day `today`.

        :return: The datetime for when the next `day` occurs.
        :rtype: datetime.datetime

        """

        if not possibilities:
            possibilities = ["ma", "di", "wo", "do", "vr", "za", "zo"]

        date = datetime.datetime.now()
        day_now = date.weekday()

        if day.lower() == today.lower():
            return date

        if day.lower() == tomorrow.lower():
            return date + datetime.timedelta(days=1)

        day_of_week_to_find = possibilities.index(day)

        if day_now < day_of_week_to_find:
            date_to_find = date + datetime.timedelta(days=day_of_week_to_find - day_now)
        else:
            # Now: Su (6), Need Mo (0)
            date_to_find = date + datetime.timedelta(days=day_of_week_to_find + 7 - day_now)

        return date_to_find

    @staticmethod
    def get_date_for_previous_day(day, possibilities=None, yesterday="Gisteren"):
        """ Gets the date for the previous Weekday (default ["ma", "di", "wo", "do", "vr", "za", "zo"]).

        :param str day:                 Weekday (present in "possibilities" parameter) to find
                                        the actual date for.
        :param list[str] possibilities: A list of possible day string values for monday to sunday.
        :param str yesterday:           A possible alternative str for the day `yesterday`.

        :return: Returns the date for the previous `day`.
        :rtype: datetime.datetime

        """

        if not possibilities:
            possibilities = ["ma", "di", "wo", "do", "vr", "za", "zo"]

        date = datetime.datetime.now()
        day_now = date.weekday()

        if day.lower() == yesterday.lower():
            return date + datetime.timedelta(days=-1)

        day_of_week_to_find = possibilities.index(day)

        if day_now >= day_of_week_to_find:
            date_to_find = date - datetime.timedelta(days=day_now - day_of_week_to_find)
        else:
            # Now: Su (6), Need Mo (0)
            date_to_find = date - datetime.timedelta(days=day_now + 7 - day_of_week_to_find)

        return date_to_find

    @staticmethod
    def get_month_from_name(month, language, short=None):
        """ Gets the month number from the name.

        :param str month:           Name of the month.
        :param str language:        Language code (nl, en).
        :param bool|None short:     Indicates the monthnames are short. Default: None.

        :return: The month number.
        :rtype: int

        """

        if short is None:
            try:
                return DateHelper.__get_month_from_name(month, language)
            except:
                return DateHelper.__get_month_from_name(month, language, False)
        else:
            return DateHelper.__get_month_from_name(month, language, short)

    @staticmethod
    def get_date_from_posix(posix, tz=None):
        """ Creates a datetime from a Posix Time stamp

        :param float posix:         The posix time stamp integer.
        :param datetime.tzinfo tz:  A possible timezone info object.

        :return: A valid datetime.datetime object for the given posix time stamp.
        :rtype: datetime.datetime

        """

        # don't use use fromtimestamp to prevent errors like:
        #   "ValueError: timestamp out of range for platform time_t"
        # https://docs.python.org/3/library/datetime.html reads:
        #   fromtimestamp() may raise OverflowError, if the timestamp is out of the range
        #   of values supported by the platform C localtime() or gmtime() functions, and
        #   OSError on localtime() or gmtime() failure. It's common for this to be restricted
        #   to years in 1970 through 2038
        # return datetime.datetime.fromtimestamp(posix, tz)
        return datetime.datetime(1970, 1, 1, tzinfo=tz) + datetime.timedelta(seconds=posix)

    @staticmethod
    def get_datetime_from_string(value, date_format="%Y-%m-%dT%H:%M:%S", time_zone=None):
        """ Parses a string and returns a TZ aware date time object

        :param str value:           The string value to parse
        :param str date_format:     The format to use
        :param str time_zone:       The timezone name for the TZ to use

        :return: A datetime object that might be timezone aware if a timezone was specified.
        :rtype: datetime.datetime

        """

        time_tuple = DateHelper.get_date_from_string(value, date_format)
        naive_datetime = datetime.datetime(*time_tuple[:6])

        if time_zone is None:
            return naive_datetime

        tz_info = pytz.timezone(time_zone)
        aware_datetime = tz_info.localize(naive_datetime)
        return aware_datetime

    @staticmethod
    def get_date_from_string(value, date_format="%Y-%m-%dT%H:%M:%S+00:00"):
        """ Converts a formatted date-time string to a time struct.

        time.struct_time values:
        0 	tm_year 	(for example, 1993)
        1 	tm_mon 	    range [1, 12]
        2 	tm_mday 	range [1, 31]
        3 	tm_hour 	range [0, 23]
        4 	tm_min 	    range [0, 59]
        5 	tm_sec 	    range [0, 61]; see (2) in strftime() description
        6 	tm_wday 	range [0, 6], Monday is 0
        7 	tm_yday 	range [1, 366]
        8 	tm_isdst 	0, 1 or -1; see below

        The datetime.strptime does not work in Kodi. See:
        https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior

        :param str value:           The string value to parse
        :param str date_format:     The format to use

        :return: A time.struct_time for the parsed date and time
        :rtype: time.struct_time

        """

        return time.strptime(value, date_format)

    @staticmethod
    def __get_month_from_name(month, language, short=True):
        """Gets the month number from the name.

        Returns:
        the month number

        :param str month:       Name of the month
        :param str language:    Language code (nl, en)
        :param bool short:      Indicates the monthnames are short. Default: True

        :return: The month number for the give month name.
        :rtype: int

        """

        if language == "nl" and short:
            month_lookup = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        elif language == "nl":
            month_lookup = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]

        elif language == "no" and short:
            month_lookup = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]
        elif language == "no":
            month_lookup = ["januar", "februar", "mars", "april", "mai", "juni", "juli", "august", "september", "oktober", "november", "desember"]

        elif language == "en" and short:
            month_lookup = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        elif language == "en":
            month_lookup = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

        elif language == "se" and short:
            month_lookup = ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]
        elif language == "se":
            month_lookup = ["januari", "februari", "mars", "april", "maj", "juni", "juli", "augusti", "september", "oktober", "november", "december"]

        else:
            error = "Language code '%s' not implemented" % (language, )
            raise NotImplementedError(error)

        if month_lookup.count(month.lower()) > 0:
            month_value = month_lookup.index(month.lower()) + 1
        else:
            error = "Month '%s' not found for language '%s'" % (month, language)
            raise ValueError(error)
        return month_value

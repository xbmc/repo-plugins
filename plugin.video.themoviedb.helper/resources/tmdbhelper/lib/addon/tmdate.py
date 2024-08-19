# import _strptime  # fix for py2.7 bug with import log shouldnt be a problem in py3.6+
import datetime
import time
import jurialmunkey.tmdate as jurialmunkey_tmdate


get_timestamp = jurialmunkey_tmdate.get_timestamp
set_timestamp = jurialmunkey_tmdate.set_timestamp


def get_datetime_combine(*args, **kwargs):
    return datetime.datetime.combine(*args, **kwargs)


def get_datetime_time(*args, **kwargs):
    return datetime.time(*args, **kwargs)


def get_datetime_utcnow_isoformat():
    return f'{datetime.datetime.utcnow().isoformat()}Z'


def get_datetime_now():
    return datetime.datetime.now()


def get_datetime_today():
    return datetime.datetime.today()


def get_timedelta(*args, **kwargs):
    return datetime.timedelta(*args, **kwargs)


def get_datetime_datetime(*args, **kwargs):
    return datetime.datetime(*args, **kwargs)


def convert_to_timestamp(date_time):
    '''Converts a datetime object to unix timestamp'''
    try:
        return int(time.mktime(date_time.timetuple()))
    except OverflowError:
        return 2145916800  # Y2038 bug in time.mktime on 32bit float systems. Use 2038 Jan 1 UTC for db timestamp instead.


def format_date(time_str, str_fmt="%A", time_fmt="%Y-%m-%d", time_lim=10, utc_convert=False, region_fmt=None):
    if not time_str:
        return
    time_obj = convert_timestamp(time_str, time_fmt, time_lim, utc_convert=utc_convert)
    if not time_obj:
        return
    if not region_fmt:
        return time_obj.strftime(str_fmt)
    return get_region_date(time_obj, region_fmt)


def date_in_range(date_str, days=1, start_date=0, date_fmt="%Y-%m-%dT%H:%M:%S", date_lim=19, utc_convert=False):
    date_a = datetime.date.today() + datetime.timedelta(days=start_date)
    if not date_a:
        return
    date_z = date_a + datetime.timedelta(days=days)
    if not date_z:
        return
    mydate = convert_timestamp(date_str, date_fmt, date_lim, utc_convert=utc_convert)
    if not mydate:
        return
    mydate = mydate.date()
    if mydate >= date_a and mydate < date_z:
        return date_str


def get_region_date(date_obj, region_fmt='dateshort', del_fmt=':%S'):
    from xbmc import getRegion
    xbmc_region = getRegion(region_fmt).replace(del_fmt, '')  # Strip seconds from formatting durations
    date_string = date_obj.strftime(xbmc_region.encode('unicode-escape').decode())  # Avoid UnicodeEncode errors in strftime
    return date_string.encode().decode('unicode-escape')  # Restore Unicode characters


def is_future_timestamp(time_str, time_fmt="%Y-%m-%dT%H:%M:%S", time_lim=19, utc_convert=False, use_today=False, days=0):
    time_obj = convert_timestamp(time_str, time_fmt, time_lim, utc_convert)
    if not isinstance(time_obj, datetime.datetime):
        return
    date_obj = datetime.datetime.today() if use_today else datetime.datetime.now()
    if days:
        date_obj = date_obj + datetime.timedelta(days=days)
    if time_obj > date_obj:
        return time_str


def is_unaired_timestamp(date_str, no_date=True):
    """ Checks if premiered date is unaired. If no date passed returns no_date boolean """
    if date_str:
        return is_future_timestamp(date_str, "%Y-%m-%d", 10)
    return no_date


def get_current_date_time(str_fmt='%Y-%m-%d %H:%M'):
    return datetime.datetime.now().strftime(str_fmt)


def get_todays_date(days=0, str_fmt='%Y-%m-%d'):
    date_obj = datetime.datetime.today()
    if days:
        date_obj += datetime.timedelta(days=days)
    return date_obj.strftime(str_fmt)


def get_calendar_name(startdate=0, days=1):
    from tmdbhelper.lib.addon.plugin import get_localized
    if days == 1:
        if startdate == -1:
            return get_localized(32282)  # Yesterday
        if startdate == 0:
            return get_localized(33006)  # Today
        if startdate == 1:
            return get_localized(33007)  # Tomorrow
        return get_todays_date(days=startdate, str_fmt="%A")
    if days == 7:
        if startdate == 0:
            return get_localized(32284)  # This Week
        if startdate == -7:
            return get_localized(32281)  # Last Week
        return
    if days == 14:
        if startdate == 0:
            return get_localized(32285)  # This Fortnight
        if startdate == -14:
            return get_localized(32280)  # Last Fortnight
        return
    if days == 30:
        if startdate == 0:
            return get_localized(32326)  # This Month
        if startdate == -30:
            return get_localized(32327)  # Last Month


def convert_timestamp(time_str, time_fmt="%Y-%m-%dT%H:%M:%S", time_lim=19, utc_convert=False):
    from tmdbhelper.lib.addon.logger import kodi_log
    if not time_str:
        return
    time_str = time_str[:time_lim] if time_lim else time_str
    utc_offset = 0
    if utc_convert:
        utc_offset = -time.timezone // 3600
        utc_offset += 1 if time.localtime().tm_isdst > 0 else 0
    try:
        time_obj = datetime.datetime.strptime(time_str, time_fmt)
        time_obj = time_obj + datetime.timedelta(hours=utc_offset)
        return time_obj
    except TypeError:
        try:
            time_obj = datetime.datetime(*(time.strptime(time_str, time_fmt)[0:6]))
            time_obj = time_obj + datetime.timedelta(hours=utc_offset)
            return time_obj
        except Exception as exc:
            kodi_log(exc, 1)
            return
    except Exception as exc:
        kodi_log(exc, 1)
        return


def age_difference(birthday, deathday=None):
    try:  # Added Error Checking as strptime doesn't work correctly on LibreElec
        deathday = convert_timestamp(deathday, '%Y-%m-%d', 10) if deathday else datetime.datetime.now()
        birthday = convert_timestamp(birthday, '%Y-%m-%d', 10)
        age = deathday.year - birthday.year
        if birthday.month * 100 + birthday.day > deathday.month * 100 + deathday.day:
            age = age - 1  # In year of death person hadn't had their birthday yet
        return age
    except Exception:
        return

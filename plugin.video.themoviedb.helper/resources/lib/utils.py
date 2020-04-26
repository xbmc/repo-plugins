import re
import sys
import time
import xbmc
import xbmcvfs
import xbmcgui
import xbmcaddon
import unicodedata
import datetime
import hashlib
from copy import copy
from contextlib import contextmanager
from resources.lib.constants import TYPE_CONVERSION, VALID_FILECHARS
_addonlogname = '[plugin.video.themoviedb.helper]\n'
_addon = xbmcaddon.Addon()
_debuglogging = _addon.getSettingBool('debug_logging')


@contextmanager
def busy_dialog():
    xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
    try:
        yield
    finally:
        xbmc.executebuiltin('Dialog.Close(busydialognocancel)')


def validify_filename(filename):
    try:
        filename = unicode(filename, 'utf-8')
    except NameError:  # unicode is a default on python 3
        pass
    except TypeError:  # already unicode
        pass
    filename = str(unicodedata.normalize('NFD', filename).encode('ascii', 'ignore').decode("utf-8"))
    filename = ''.join(c for c in filename if c in VALID_FILECHARS)
    return filename


def makepath(path):
        if xbmcvfs.exists(path):
            return xbmc.translatePath(path)
        xbmcvfs.mkdirs(path)
        return xbmc.translatePath(path)


def md5hash(value):
    if sys.version_info.major != 3:
        return hashlib.md5(str(value)).hexdigest()

    value = str(value).encode()
    return hashlib.md5(value).hexdigest()


def type_convert(original, converted):
    return TYPE_CONVERSION.get(original, {}).get(converted, '')


def try_parse_int(string):
    '''helper to parse int from string without erroring on empty or misformed string'''
    try:
        return int(string)
    except Exception:
        return 0


def try_parse_float(string):
    '''helper to parse float from string without erroring on empty or misformed string'''
    try:
        return float(string or 0)
    except Exception:
        return 0


def try_decode_string(string, encoding='utf-8'):
    """helper to decode strings for PY 2 """
    if sys.version_info.major == 3:
        return string
    try:
        return string.decode(encoding)
    except Exception:
        return string


def try_encode_string(string, encoding='utf-8'):
    """helper to encode strings for PY 2 """
    if sys.version_info.major == 3:
        return string
    try:
        return string.encode(encoding)
    except Exception:
        return string


def get_between_strings(string, startswith='', endswith=''):
    exp = startswith + '(.+?)' + endswith
    try:
        return re.search(exp, string).group(1)
    except AttributeError:
        return ''


def get_timestamp(timestamp=None):
    if not timestamp:
        return
    if time.time() > timestamp:
        return
    return timestamp


def get_region_date(date_obj, region='dateshort', del_fmt=':%S'):
    date_fmt = xbmc.getRegion(region).replace(del_fmt, '')
    return date_obj.strftime(date_fmt)


def set_timestamp(wait_time=60):
    return time.time() + wait_time


def normalise_filesize(filesize):
    filesize = try_parse_int(filesize)
    i_flt = 1024.0
    i_str = ['B', 'KB', 'MB', 'GB', 'TB']
    for i in i_str:
        if filesize < i_flt:
            return '{:.2f} {}'.format(filesize, i)
        filesize = filesize / i_flt
    return '{:.2f} {}'.format(filesize, 'PB')


def rate_limiter(addon_name='plugin.video.themoviedb.helper', wait_time=None, api_name=None):
    """
    Simple rate limiter to prevent overloading APIs
    """
    sleep_time = wait_time if wait_time and 0 < wait_time < 1 else 1
    wait_time = wait_time if wait_time else 2
    api_name = '.{0}'.format(api_name) if api_name else ''
    timestamp_id = '{0}{1}.timestamp'.format(addon_name, api_name)

    # WAIT UNTIL UNLOCKED AND THEN SET LOCK TO PREVENT OTHERS RUNNING
    lock_id = '{0}{1}.locked'.format(addon_name, api_name)
    lock = xbmcgui.Window(10000).getProperty(lock_id)
    while not xbmc.Monitor().abortRequested() and lock == 'True':
        xbmc.Monitor().waitForAbort(1)
        lock = xbmcgui.Window(10000).getProperty(lock_id)
    xbmcgui.Window(10000).setProperty(lock_id, 'True')

    # CHECK THAT WAIT TIME SINCE LAST REQUEST HAS ELAPSED ELSE WAIT
    pre_timestamp = xbmcgui.Window(10000).getProperty(timestamp_id)
    pre_timestamp = try_parse_float(pre_timestamp)
    cur_timestamp = pre_timestamp - time.time() + wait_time
    while not xbmc.Monitor().abortRequested() and cur_timestamp > 0:
        xbmc.Monitor().waitForAbort(sleep_time)
        cur_timestamp -= sleep_time

    # SET TIMESTAMP AND CLEAR LOCK
    xbmcgui.Window(10000).setProperty(timestamp_id, str(time.time()))
    xbmcgui.Window(10000).clearProperty(lock_id)


def get_property(name, setproperty=None, clearproperty=False, prefix=None, window_id=None):
        window = xbmcgui.Window(window_id) if window_id else xbmcgui.Window(xbmcgui.getCurrentWindowId())
        name = '{0}.{1}'.format(prefix, name) if prefix else name
        if clearproperty:
            window.clearProperty(name)
            return
        elif setproperty:
            window.setProperty(name, setproperty)
            return setproperty
        return window.getProperty(name)


def dialog_select_item(items=None, details=False, usedetails=True):
    item_list = split_items(items)
    item_index = 0
    if len(item_list) > 1:
        if details:
            detailed_item_list = []
            for item in item_list:
                icon = details.get_icon(item)
                dialog_item = xbmcgui.ListItem(details.get_title(item))
                dialog_item.setArt({'icon': icon, 'thumb': icon})
                detailed_item_list.append(dialog_item)
            item_index = xbmcgui.Dialog().select(_addon.getLocalizedString(32006), detailed_item_list, preselect=0, useDetails=usedetails)
        else:
            item_index = xbmcgui.Dialog().select(_addon.getLocalizedString(32006), item_list)
    if item_index > -1:
        return item_list[item_index]


def filtered_item(item, key, value, exclude=False):
    boolean = False if exclude else True  # Flip values if we want to exclude instead of include
    if key and value:
        if item.get(key) and item.get(key) == value:
            boolean = exclude
        return boolean


def age_difference(birthday, deathday=''):
    try:  # Added Error Checking as strptime doesn't work correctly on LibreElec
        deathday = convert_timestamp(deathday, '%Y-%m-%d', 10) if deathday else datetime.datetime.now()
        birthday = convert_timestamp(birthday, '%Y-%m-%d', 10)
        age = deathday.year - birthday.year
        if birthday.month * 100 + birthday.day > deathday.month * 100 + deathday.day:
            age = age - 1
        return age
    except Exception:
        return


def iterate_extraart(artworklist, artworkdict={}):
    idx = len(artworkdict) + 1
    for art in artworklist:
        ef_name = 'fanart{}'.format(idx)
        artworkdict[ef_name] = art
        idx += 1
    return artworkdict


def convert_timestamp(time_str, time_fmt="%Y-%m-%dT%H:%M:%S", time_lim=19, utc_convert=False):
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


def date_to_format(time_str, str_fmt="%A", time_fmt="%Y-%m-%d", time_lim=10, utc_convert=False):
    if not time_str:
        return
    time_obj = convert_timestamp(time_str, time_fmt, time_lim, utc_convert=utc_convert)
    if not time_obj:
        return
    return time_obj.strftime(str_fmt)


def date_in_range(date_str, days=1, start_date=0, date_fmt="%Y-%m-%dT%H:%M:%S", date_lim=19, utc_convert=False):
    date_a = datetime.date.today() + datetime.timedelta(days=start_date)
    date_z = date_a + datetime.timedelta(days=days)
    mydate = convert_timestamp(date_str, date_fmt, date_lim, utc_convert=utc_convert).date()
    if not mydate or not date_a or not date_z:
        return
    if mydate >= date_a and mydate < date_z:
        return date_str


def kodi_log(value, level=0):
    try:
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        logvalue = u'{0}{1}'.format(_addonlogname, value)
        if sys.version_info < (3, 0):
            logvalue = logvalue.encode('utf-8', 'ignore')
        if level == 2 and _debuglogging:
            xbmc.log(logvalue, level=xbmc.LOGNOTICE)
        elif level == 1:
            xbmc.log(logvalue, level=xbmc.LOGNOTICE)
        else:
            xbmc.log(logvalue, level=xbmc.LOGDEBUG)
    except Exception as exc:
        xbmc.log(u'Logging Error: {}'.format(exc), level=xbmc.LOGNOTICE)


def dictify(r, root=True):
    if root:
        return {r.tag: dictify(r, False)}
    d = copy(r.attrib)
    if r.text:
        d["_text"] = r.text
    for x in r.findall("./*"):
        if x.tag not in d:
            d[x.tag] = []
        d[x.tag].append(dictify(x, False))
    return d


def del_dict_keys(dictionary, keys):
    for key in keys:
        if dictionary.get(key):
            del dictionary[key]
    return dictionary


def concatinate_names(items, key, separator):
    concat = ''
    for i in items:
        if i.get(key):
            concat = u'{0} {1} {2}'.format(concat, separator, i.get(key)) if concat else i.get(key)
    return concat


def dict_to_list(items, key):
    return [i.get(key) for i in items if i.get(key)]


def find_dict_in_list(list_of_dicts, key, value):
    return [list_index for list_index, dic in enumerate(list_of_dicts) if dic.get(key) == value]


def get_dict_in_list(list_of_dicts, key, value, basekeys=[]):
    for d in list_of_dicts:
        if not isinstance(d, dict):
            continue
        base = d
        for basekey in basekeys:
            d = d.get(basekey, {}) if basekey else d
        if d.get(key) == value:
            return base


def split_items(items, separator='/'):
    separator = ' {0} '.format(separator)
    if items and separator in items:
        items = items.split(separator)
    items = [items] if not isinstance(items, list) else items  # Make sure we return a list to prevent a string being iterated over characters
    return items


def iter_props(items, property, itemprops, **kwargs):
    func = kwargs.pop('func', None)
    for k, v in kwargs.items():
        x = 0
        while x < 10 and itemprops.get('{0}.{1}.{2}'.format(property, x + 1, k)):
            x += 1  # Find next empty prop
        for i in items:
            if x > 9:
                break  # only add ten items
            # if not i.get(v):
            #     continue
            x += 1
            itemprops['{0}.{1}.{2}'.format(property, x, k)] = i.get(v) if not func else func(i.get(v))
    return itemprops


def del_empty_keys(d, values=[]):
    my_dict = d.copy()
    for k, v in d.items():
        if not v or v in values:
            del my_dict[k]
    return my_dict


def merge_two_dicts(x, y):
    z = x.copy()   # start with x's keys and values
    z.update(y)    # modifies z with y's keys and values & returns None
    return z


def merge_two_dicts_deep(x, y):
    """ Deep merge y keys into copy of x """
    z = x.copy()
    for k, v in y.items():
        if isinstance(v, dict):
            merge_two_dicts_deep(z.setdefault(k, {}), v)
        elif v:
            z[k] = v
    return z


def make_kwparams(params):
    tempparams = params.copy()
    return del_dict_keys(tempparams, ['info', 'type', 'tmdb_id', 'filter_key', 'filter_value',
                                      'with_separator', 'with_id', 'season', 'episode', 'prop_id',
                                      'exclude_key', 'exclude_value'])


try:
    _throwaway = time.strptime("2001-01-01", "%Y-%m-%d")  # Throwaway to deal with PY2 _strptime import bug
except Exception as exc:
    kodi_log(exc, 1)

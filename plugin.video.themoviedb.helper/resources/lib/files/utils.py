import re
import os
import json
import xbmcgui
import xbmcvfs
import unicodedata
from resources.lib.addon.timedate import get_timedelta, get_datetime_now
from resources.lib.addon.parser import try_int
from resources.lib.addon.plugin import ADDON, ADDONDATA, kodi_log
from resources.lib.addon.constants import ALPHANUM_CHARS, INVALID_FILECHARS
from resources.lib.addon.timedate import is_future_timestamp
try:
    import cPickle as _pickle
except ImportError:
    import pickle as _pickle  # Newer versions of Py3 just use pickle


def validify_filename(filename, alphanum=False):
    filename = unicodedata.normalize('NFD', filename)
    filename = u''.join([c for c in filename if (not alphanum or c in ALPHANUM_CHARS) and c not in INVALID_FILECHARS])
    return filename.strip('.')


def normalise_filesize(filesize):
    filesize = try_int(filesize)
    i_flt = 1024.0
    i_str = ['B', 'KB', 'MB', 'GB', 'TB']
    for i in i_str:
        if filesize < i_flt:
            return u'{:.2f} {}'.format(filesize, i)
        filesize = filesize / i_flt
    return u'{:.2f} {}'.format(filesize, 'PB')


def get_files_in_folder(folder, regex):
    return [x for x in xbmcvfs.listdir(folder)[1] if re.match(regex, x)]


def read_file(filepath):
    vfs_file = xbmcvfs.File(filepath)
    content = ''
    try:
        content = vfs_file.read()
    finally:
        vfs_file.close()
    return content


def write_to_file(filepath, content):
    f = xbmcvfs.File(filepath, 'w')
    f.write(content)
    f.close()


def get_tmdb_id_nfo(basedir, foldername, tmdb_type='tv'):
    try:
        folder = basedir + foldername + '/'

        # Get files ending with .nfo in folder
        nfo_list = get_files_in_folder(folder, regex=r".*\.nfo$")

        # Check our nfo files for TMDb ID
        for nfo in nfo_list:
            content = read_file(folder + nfo)  # Get contents of .nfo file
            tmdb_id = content.replace(u'https://www.themoviedb.org/{}/'.format(tmdb_type), '')  # Clean content to retrieve tmdb_id
            tmdb_id = tmdb_id.replace(u'&islocal=True', '')
            tmdb_id = try_int(tmdb_id)
            if tmdb_id:
                return u'{}'.format(tmdb_id)

    except Exception as exc:
        kodi_log(u'ERROR GETTING TMDBID FROM NFO:\n{}'.format(exc))


def get_file_path(folder, filename, join_addon_data=True):
    return os.path.join(get_write_path(folder, join_addon_data), filename)


def delete_file(folder, filename, join_addon_data=True):
    xbmcvfs.delete(get_file_path(folder, filename, join_addon_data))


def dumps_to_file(data, folder, filename, indent=2, join_addon_data=True):
    path = os.path.join(get_write_path(folder, join_addon_data), filename)
    with open(path, 'w') as file:
        json.dump(data, file, indent=indent)
    return path


def get_write_path(folder, join_addon_data=True):
    main_dir = os.path.join(xbmcvfs.translatePath(ADDONDATA), folder) if join_addon_data else xbmcvfs.translatePath(folder)
    if not os.path.exists(main_dir):
        try:  # Try makedir to avoid race conditions
            os.makedirs(main_dir)
        except FileExistsError:
            pass
    return main_dir


def _del_file(folder, filename):
    file = os.path.join(folder, filename)
    os.remove(file)


def del_old_files(folder, limit=1):
    folder = get_write_path(folder, True)
    for filename in sorted(os.listdir(folder))[:-limit]:
        _del_file(folder, filename)


def make_path(path, warn_dialog=False):
    if xbmcvfs.exists(path):
        return xbmcvfs.translatePath(path)
    if xbmcvfs.mkdirs(path):
        return xbmcvfs.translatePath(path)
    if ADDON.getSettingBool('ignore_folderchecking'):
        kodi_log(u'Ignored xbmcvfs folder check error\n{}'.format(path), 2)
        return xbmcvfs.translatePath(path)
    kodi_log(u'XBMCVFS unable to create path:\n{}'.format(path), 2)
    if not warn_dialog:
        return
    xbmcgui.Dialog().ok(
        'XBMCVFS', u'{} [B]{}[/B]\n{}'.format(
            ADDON.getLocalizedString(32122), path, ADDON.getLocalizedString(32123)))


def get_pickle_name(cache_name, alphanum=False):
    cache_name = cache_name or ''
    cache_name = cache_name.replace('\\', '_').replace('/', '_').replace('.', '_').replace('?', '_').replace('&', '_').replace('=', '_').replace('__', '_')
    return validify_filename(cache_name, alphanum=alphanum).rstrip('_')


def set_pickle(my_object, cache_name, cache_days=14, json_dump=False):
    if not my_object:
        return
    cache_name = get_pickle_name(cache_name)
    if not cache_name:
        return
    timestamp = get_datetime_now() + get_timedelta(days=cache_days)
    cache_obj = {'my_object': my_object, 'expires': timestamp.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(os.path.join(get_write_path('pickle'), cache_name), 'w' if json_dump else 'wb') as file:
        json.dump(cache_obj, file, indent=4) if json_dump else _pickle.dump(cache_obj, file)
    return my_object


def get_pickle(cache_name, json_dump=False):
    cache_name = get_pickle_name(cache_name)
    if not cache_name:
        return
    try:
        with open(os.path.join(get_write_path('pickle'), cache_name), 'r' if json_dump else 'rb') as file:
            cache_obj = json.load(file) if json_dump else _pickle.load(file)
    except IOError:
        cache_obj = None
    if cache_obj and is_future_timestamp(cache_obj.get('expires', '')):
        return cache_obj.get('my_object')


def use_pickle(func, *args, **kwargs):
    """
    Simplecache takes func with args and kwargs
    Returns the cached item if it exists otherwise does the function
    """
    cache_name = kwargs.pop('cache_name', '')
    cache_only = kwargs.pop('cache_only', False)
    cache_refresh = kwargs.pop('cache_refresh', False)
    my_object = get_pickle(cache_name) if not cache_refresh else None
    if my_object:
        return my_object
    elif not cache_only:
        my_object = func(*args, **kwargs)
        return set_pickle(my_object, cache_name)

import xbmcvfs
import jurialmunkey.futils
from jurialmunkey.parser import try_int
from tmdbhelper.lib.addon.plugin import ADDONDATA, get_localized, get_setting
from tmdbhelper.lib.addon.logger import kodi_log


class FileUtils(jurialmunkey.futils.FileUtils):
    addondata = ADDONDATA   # Override module addon_data with plugin addon_data


FILEUTILS = FileUtils()


json_loads = jurialmunkey.futils.json_loads
json_dumps = jurialmunkey.futils.json_dumps
validate_join = jurialmunkey.futils.validate_join
validify_filename = jurialmunkey.futils.validify_filename
get_filecache_name = jurialmunkey.futils.get_filecache_name
get_file_path = FILEUTILS.get_file_path
get_write_path = FILEUTILS.get_write_path
dumps_to_file = FILEUTILS.dumps_to_file


def normalise_filesize(filesize):
    filesize = try_int(filesize)
    i_flt = 1024.0
    i_str = ['B', 'KB', 'MB', 'GB', 'TB']
    for i in i_str:
        if filesize < i_flt:
            return f'{filesize:.2f} {i}'
        filesize = filesize / i_flt
    return f'{filesize:.2f} PB'


def get_files_in_folder(folder, regex):
    import re
    return [x for x in xbmcvfs.listdir(folder)[1] if re.match(regex, x)]


def read_file(filepath):
    content = ''
    with xbmcvfs.File(filepath) as vfs_file:
        content = vfs_file.read()
    return content


def get_tmdb_id_nfo(basedir, foldername, tmdb_type='tv'):
    try:
        folder = basedir + foldername + '/'

        # Get files ending with .nfo in folder
        nfo_list = get_files_in_folder(folder, regex=r".*\.nfo$")

        # Check our nfo files for TMDb ID
        for nfo in nfo_list:
            content = read_file(folder + nfo)  # Get contents of .nfo file
            tmdb_id = content.replace(f'https://www.themoviedb.org/{tmdb_type}/', '')  # Clean content to retrieve tmdb_id
            tmdb_id = tmdb_id.replace(u'&islocal=True', '')
            tmdb_id = try_int(tmdb_id)
            if tmdb_id:
                return f'{tmdb_id}'

    except Exception as exc:
        kodi_log(f'ERROR GETTING TMDBID FROM NFO:\n{exc}')


def delete_file(folder, filename, join_addon_data=True):
    xbmcvfs.delete(get_file_path(folder, filename, join_addon_data, make_dir=False))


def delete_folder(folder, join_addon_data=True, force=False, check_exists=False):
    path = get_write_path(folder, join_addon_data, make_dir=False)
    if check_exists and not xbmcvfs.exists(path):
        return
    xbmcvfs.rmdir(path, force=force)


def write_file(data, path):
    with xbmcvfs.File(path, 'w') as f:
        f.write(data)
    return path


def write_to_file(data, folder, filename, join_addon_data=True, append_to_file=False):
    path = get_file_path(folder, filename, join_addon_data)
    if append_to_file:
        data = '\n'.join([read_file(path), data])
    return write_file(data, path)


def del_old_files(folder, limit=1):
    folder = get_write_path(folder, True)
    for filename in sorted(xbmcvfs.listdir(folder))[:-limit]:
        delete_file(folder, filename, False)


def make_path(path, warn_dialog=False):
    if xbmcvfs.exists(path):
        return xbmcvfs.translatePath(path)
    if xbmcvfs.mkdirs(path):
        return xbmcvfs.translatePath(path)
    if xbmcvfs.exists(path):  # mkdirs doesn't return true on success on some systems so double check
        return xbmcvfs.translatePath(path)
    if get_setting('ignore_folderchecking'):  # some systems lag in reporting folder exists after creation so allow overriding check
        kodi_log(f'Ignored xbmcvfs folder check error\n{path}', 2)
        return xbmcvfs.translatePath(path)
    kodi_log(f'XBMCVFS unable to create path:\n{path}', 2)
    if not warn_dialog:
        return
    from xbmcgui import Dialog
    Dialog().ok('XBMCVFS', f'{get_localized(32122)} [B]{path}[/B]\n{get_localized(32123)}')


def pickle_deepcopy(obj):
    import pickle
    return pickle.loads(pickle.dumps(obj))


def set_json_filecache(my_object, cache_name, cache_days=14):
    from json import dump
    from tmdbhelper.lib.addon.tmdate import get_timedelta, get_datetime_now

    if not my_object:
        return

    cache_name = get_filecache_name(cache_name)
    if not cache_name:
        return

    timestamp = ''
    if cache_days:
        timestamp = get_datetime_now() + get_timedelta(days=cache_days)
        timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S")

    cache_obj = {'my_object': my_object, 'expires': timestamp}

    with xbmcvfs.File(validate_join(get_write_path('pickle'), cache_name), 'w') as file:
        dump(cache_obj, file, indent=4)

    return my_object


def get_json_filecache(cache_name):
    import json
    cache_name = get_filecache_name(cache_name)
    if not cache_name:
        return
    try:
        with xbmcvfs.File(validate_join(get_write_path('pickle'), cache_name), 'r') as file:
            cache_obj = json.load(file)
    except (IOError, json.JSONDecodeError):
        cache_obj = None
    from tmdbhelper.lib.addon.tmdate import is_future_timestamp
    if cache_obj and (not cache_obj.get('expires') or is_future_timestamp(cache_obj.get('expires', ''))):
        return cache_obj.get('my_object')


def use_json_filecache(func, *args, cache_name='', cache_only=False, cache_refresh=False, **kwargs):
    """
    Simplecache takes func with args and kwargs
    Returns the cached item if it exists otherwise does the function
    """
    my_object = get_json_filecache(cache_name) if not cache_refresh else None
    if my_object:
        return my_object
    elif not cache_only:
        my_object = func(*args, **kwargs)
        return set_json_filecache(my_object, cache_name)

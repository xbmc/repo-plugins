import re
import xbmcvfs
from xbmcgui import Dialog
from resources.lib.addon.consts import ALPHANUM_CHARS, INVALID_FILECHARS
from resources.lib.addon.tmdate import get_timedelta, get_datetime_now, is_future_timestamp
from resources.lib.addon.parser import try_int
from resources.lib.addon.plugin import ADDONDATA, get_localized, get_setting
from resources.lib.addon.logger import kodi_log

""" Lazyimports
import unicodedata
import json
import pickle
"""


def validate_join(folder, filename):
    path = '/'.join([folder, filename])
    return xbmcvfs.validatePath(xbmcvfs.translatePath(path))


def validify_filename(filename, alphanum=False):
    import unicodedata
    filename = unicodedata.normalize('NFD', filename)
    filename = u''.join([c for c in filename if (not alphanum or c in ALPHANUM_CHARS) and c not in INVALID_FILECHARS])
    return filename.strip('.')


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


def get_file_path(folder, filename, join_addon_data=True, make_dir=True):
    return validate_join(get_write_path(folder, join_addon_data, make_dir), filename)


def delete_file(folder, filename, join_addon_data=True):
    xbmcvfs.delete(get_file_path(folder, filename, join_addon_data, make_dir=False))


def delete_folder(folder, join_addon_data=True, force=False, check_exists=False):
    path = get_write_path(folder, join_addon_data, make_dir=False)
    if check_exists and not xbmcvfs.exists(path):
        return
    xbmcvfs.rmdir(path, force=force)


def dumps_to_file(data, folder, filename, indent=2, join_addon_data=True):
    from json import dump
    path = get_file_path(folder, filename, join_addon_data)
    with xbmcvfs.File(path, 'w') as file:
        dump(data, file, indent=indent)
    return path


def write_file(data, path):
    with xbmcvfs.File(path, 'w') as f:
        f.write(data)
    return path


def write_to_file(data, folder, filename, join_addon_data=True, append_to_file=False):
    path = get_file_path(folder, filename, join_addon_data)
    if append_to_file:
        data = '\n'.join([read_file(path), data])
    return write_file(data, path)


def get_write_path(folder, join_addon_data=True, make_dir=True):
    if join_addon_data:
        folder = f'{ADDONDATA}{folder}/'
    main_dir = xbmcvfs.validatePath(xbmcvfs.translatePath(folder))
    if make_dir and not xbmcvfs.exists(main_dir):
        try:  # Try makedir to avoid race conditions
            xbmcvfs.mkdirs(main_dir)
        except FileExistsError:
            pass
    return main_dir


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
    Dialog().ok('XBMCVFS', f'{get_localized(32122)} [B]{path}[/B]\n{get_localized(32123)}')


def json_loads(obj):
    import json

    def json_int_keys(ordered_pairs):
        result = {}
        for key, value in ordered_pairs:
            try:
                key = int(key)
            except ValueError:
                pass
            result[key] = value
        return result
    try:
        return json.loads(obj, object_pairs_hook=json_int_keys)
    except json.JSONDecodeError:
        return


def json_dumps(obj, separators=(',', ':')):
    from json import dumps
    return dumps(obj, separators=separators)


def pickle_deepcopy(obj):
    import pickle
    return pickle.loads(pickle.dumps(obj))


def get_filecache_name(cache_name, alphanum=False):
    cache_name = cache_name or ''
    cache_name = cache_name.replace('\\', '_').replace('/', '_').replace('.', '_').replace('?', '_').replace('&', '_').replace('=', '_').replace('__', '_')
    return validify_filename(cache_name, alphanum=alphanum).rstrip('_')


def set_json_filecache(my_object, cache_name, cache_days=14):
    from json import dump
    if not my_object:
        return
    cache_name = get_filecache_name(cache_name)
    if not cache_name:
        return
    timestamp = get_datetime_now() + get_timedelta(days=cache_days)
    cache_obj = {'my_object': my_object, 'expires': timestamp.strftime("%Y-%m-%dT%H:%M:%S")}

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
    if cache_obj and is_future_timestamp(cache_obj.get('expires', '')):
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

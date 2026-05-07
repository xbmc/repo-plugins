#!/usr/bin/python
# coding: utf-8

########################

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import xbmcplugin
import json
import time
import datetime
import os
import sys
import hashlib
import urllib.parse as urllib

########################

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_DATA_PATH = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/%s" % ADDON_ID))
ADDON_DATA_IMG_PATH = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/%s/img" % ADDON_ID))
ADDON_DATA_IMG_TEMP_PATH = os.path.join(xbmcvfs.translatePath("special://profile/addon_data/%s/img/tmp" % ADDON_ID))

# Ensure addon data directory exists on first run
if not xbmcvfs.exists(ADDON_DATA_PATH):
    xbmcvfs.mkdirs(ADDON_DATA_PATH)

INFO = xbmc.LOGINFO
WARNING = xbmc.LOGWARNING
DEBUG = xbmc.LOGDEBUG
ERROR = xbmc.LOGERROR

DIALOG = xbmcgui.Dialog()

PLAYER = xbmc.Player()
VIDEOPLAYLIST = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
MUSICPLAYLIST = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

########################

def log(txt,loglevel=DEBUG,force=False):
    if (ADDON.getSettingBool('log') or force) and loglevel not in [WARNING, ERROR]:
        loglevel = INFO

    message = u'[ %s ] %s' % (ADDON_ID, txt)
    xbmc.log(msg=message, level=loglevel)


def remove_quotes(label):
    if not label:
        return ''

    if label.startswith("'") and label.endswith("'") and len(label) > 2:
        label = label[1:-1]
        if label.startswith('"') and label.endswith('"') and len(label) > 2:
            label = label[1:-1]
        elif label.startswith('&quot;') and label.endswith('&quot;'):
            label = label[6:-6]

    return label


def get_joined_items(item):
    if len(item) > 0 and item is not None:
        item = ' / '.join(item)
    else:
        item = ''

    return item


def execute(cmd):
    log('Execute: %s' % cmd, DEBUG)
    xbmc.executebuiltin(cmd)


def condition(condition):
    return xbmc.getCondVisibility(condition)


def clear_playlists():
    log('Clearing existing playlists')
    VIDEOPLAYLIST.clear()
    MUSICPLAYLIST.clear()


def get_bool(value,string='true'):
    try:
        if value.lower() == string:
            return True
        raise Exception

    except Exception:
        return False


def url_quote(string):
    return urllib.quote(string)


def url_unquote(string):
    return urllib.unquote(string)


def md5hash(value):
    value = str(value).encode()
    return hashlib.md5(value).hexdigest()


def touch_file(filepath):
    os.utime(filepath,None)


def winprop(key, value=None, clear=False, window_id=10000):
    window = xbmcgui.Window(window_id)

    if clear:
        window.clearProperty(key.replace('.json', '').replace('.bool', ''))

    elif value is not None:

        if key.endswith('.json'):
            key = key.replace('.json', '')
            value = json.dumps(value)

        elif key.endswith('.bool'):
            key = key.replace('.bool', '')
            value = 'true' if value else 'false'

        window.setProperty(key, value)

    else:
        result = window.getProperty(key.replace('.json', '').replace('.bool', ''))

        if result:
            if key.endswith('.json'):
                result = json.loads(result)
            elif key.endswith('.bool'):
                result = result in ('true', '1')

        return result


def json_call(method,properties=None,sort=None,query_filter=None,limit=None,params=None,item=None,options=None,limits=None,debug=False):
    json_string = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': {}}

    if properties is not None:
        json_string['params']['properties'] = properties

    if limit is not None:
        json_string['params']['limits'] = {'start': 0, 'end': int(limit)}

    if sort is not None:
        json_string['params']['sort'] = sort

    if query_filter is not None:
        json_string['params']['filter'] = query_filter

    if options is not None:
        json_string['params']['options'] = options

    if limits is not None:
        json_string['params']['limits'] = limits

    if item is not None:
        json_string['params']['item'] = item

    if params is not None:
        json_string['params'].update(params)

    jsonrpc_call = json.dumps(json_string)
    result = xbmc.executeJSONRPC(jsonrpc_call)
    result = json.loads(result)

    if debug:
        log('--> JSON CALL: ' + json_prettyprint(json_string), force=True)
        log('--> JSON RESULT: ' + json_prettyprint(result), force=True)

    return result


def json_prettyprint(string):
    return json.dumps(string, sort_keys=True, indent=4, separators=(',', ': '))


def reload_widgets(instant=False,reason='Timer'):
    log('Force widgets to refresh (%s)' % reason)

    timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())

    if instant:
        if condition('System.HasAlarm(WidgetRefresh)'):
            execute('CancelAlarm(WidgetRefresh,silent)')

        winprop('AeonTajoWidgetUpdate', timestamp)

    else:
        execute('AlarmClock(WidgetRefresh,SetProperty(AeonTajoWidgetUpdate,%s,home),00:10,silent)' % timestamp)


def sync_library_tags(tags=None,recreate=False):
    save = False

    if tags is None:
        tags = get_library_tags()

    try:
        whitelist = addon_data('tags_whitelist.' + xbmc.getSkinDir() +'.data')
    except Exception:
        whitelist = []
        save = True

    try:
        old_tags = addon_data('tags_all.data')
    except Exception:
        old_tags = []
        save = True

    ''' cleanup removed old tags
    '''
    for tag in old_tags:
        if tag not in tags:
            save = True
            old_tags.remove(tag)
            if tag in whitelist:
                whitelist.remove(tag)

    ''' recognize new available tags
    '''
    new_tags = []
    for tag in tags:
        if tag not in old_tags:
            save = True
            new_tags.append(tag)

    if save or recreate:
        known_tags = old_tags + new_tags

        ''' automatically whitelist new tags if enabled
        '''
        if condition('Skin.HasSetting(AutoLibraryTags)'):
            tags_to_whitelist = known_tags if recreate else new_tags

            for tag in tags_to_whitelist:
                if tag not in whitelist:
                    whitelist.append(tag)

        addon_data('tags_all.data', known_tags)

    set_library_tags(tags, whitelist, save=save)


def get_library_tags():
    tags = {}
    all_tags = []
    duplicate_handler = []
    tag_blacklist = ['Favorite tvshows', # Emby
                     'Favorite movies' # Emby
                     ]

    movie_tags = json_call('VideoLibrary.GetTags',
                           properties=['title'],
                           params={'type': 'movie'}
                           )

    tvshow_tags = json_call('VideoLibrary.GetTags',
                            properties=['title'],
                            params={'type': 'tvshow'}
                            )

    try:
        for tag in movie_tags['result']['tags']:
            label, tagid = tag['label'], tag['tagid']

            if label in tag_blacklist:
                continue

            tags[label] = {'type': 'movies', 'id': str(tagid)}
            all_tags.append(label)
            duplicate_handler.append(label)

    except KeyError:
        pass

    try:
        for tag in tvshow_tags['result']['tags']:
            label, tagid = tag['label'], tag['tagid']

            if label in tag_blacklist:
                continue

            if label not in duplicate_handler:
                tags[label] = {'type': 'tvshows', 'id': str(tagid)}
                all_tags.append(label)
            else:
                tags[label] = {'type': 'mixed', 'id': str(tagid)}

    except KeyError:
        pass

    all_tags.sort()
    winprop('library.tags.all', get_joined_items(all_tags))

    return tags


def set_library_tags(tags,whitelist=None,save=True,clear=False):
    setting = 'tags_whitelist.' + xbmc.getSkinDir() +'.data'
    index = 0

    if tags and not clear:
        if not whitelist:
            try:
                whitelist = addon_data('tags_whitelist.' + xbmc.getSkinDir() +'.data')
            except Exception:
                pass

        for item in tags:
            if item in whitelist:
                winprop('library.tags.%d.title' % index, item)
                winprop('library.tags.%d.type' % index, tags[item].get('type'))
                winprop('library.tags.%d.id' % index, tags[item].get('id'))
                index += 1

    for clean in range(index,30):
        winprop('library.tags.%d.title' % clean, clear=True)
        winprop('library.tags.%d.type' % clean, clear=True)
        winprop('library.tags.%d.id' % clean, clear=True)

    whitelist.sort()
    winprop('library.tags', get_joined_items(whitelist))

    if save:
        addon_data('tags_whitelist.' + xbmc.getSkinDir() +'.data', whitelist)


def addon_data_cleanup(number_of_days=60):
    time_in_secs = time.time() - (number_of_days * 24 * 60 * 60)

    ''' Image storage maintaining. Deletes all created images which were unused in the
        last 60 days. The image functions are touching existing files to update the
        modification date. Often used images are never get deleted by this task.
    '''
    try:
        for file in os.listdir(ADDON_DATA_IMG_PATH):
            full_path = os.path.join(ADDON_DATA_IMG_PATH, file)
            if os.path.isfile(full_path):
                stat = os.stat(full_path)
                if stat.st_mtime <= time_in_secs:
                    os.remove(full_path)
    except Exception:
        return

    ''' Deletes old temporary files on startup
    '''
    try:
        for file in os.listdir(ADDON_DATA_IMG_TEMP_PATH):
            full_path = os.path.join(ADDON_DATA_IMG_TEMP_PATH, file)
            if os.path.isfile(full_path):
                os.remove(full_path)
    except Exception:
        pass


def addon_data(file,content=False):
    targetfile = os.path.join(ADDON_DATA_PATH, file)

    if content is False:
        data = []

        if xbmcvfs.exists(targetfile):
            with open(targetfile, 'r') as f:
                try:
                    setting = json.load(f)
                    data = setting['data']

                except Exception:
                    pass

        return data

    else:
        data = {}
        data['data'] = content

        if not xbmcvfs.exists(ADDON_DATA_PATH):
            xbmcvfs.mkdirs(ADDON_DATA_PATH)

        with open(targetfile, 'w') as f:
            json.dump(data, f)


def set_plugincontent(content=None,category=None):
    if category:
        xbmcplugin.setPluginCategory(int(sys.argv[1]), category)
    if content:
        xbmcplugin.setContent(int(sys.argv[1]), content)

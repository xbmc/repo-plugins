'''
    OneDrive for Kodi
    Copyright (C) 2015 - Carlos Guzman

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

    Created on Mar 1, 2015
    @author: Carlos Guzman (cguZZman) carlosguzmang@hotmail.com
'''

import json
import os
import sys
import threading
import time
import traceback
import urllib
import urllib2
import urlparse

from resources.lib.api import utils
from resources.lib.api.onedrive import OneDrive, OneDriveException, AccountNotFoundException
from resources.lib.api.account import AccountManager

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs


base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
monitor = xbmc.Monitor()

action = args.get('action', None)
try:
    content_type = args.get('content_type')[0]
except:
    wid = xbmcgui.getCurrentWindowId()
    if wid == 10005 or wid == 10500 or wid == 10501 or wid == 10502:
        content_type = 'audio'
    elif wid == 10002:
        content_type = 'image'
    else:
        content_type = 'video'

extra_parameters = {'expand': 'thumbnails'}
dialog = xbmcgui.Dialog();
progress_dialog = xbmcgui.DialogProgress()
pg_created = False
progress_dialog_bg = xbmcgui.DialogProgressBG()
pg_bg_created = False
export_progress_dialog_bg = xbmcgui.DialogProgressBG()
export_pg_bg_created = False
big_folder_min = 0

account_manager = AccountManager()

shared_json_path = account_manager.addon_data_path + '/shared.json'

ext_videos = ['mkv', 'mp4', 'avi', 'iso', 'nut', 'ogg', 'vivo', 'pva', 'nuv', 'nsv', 'nsa', 'fli', 'flc', 'wtv']
ext_audio = ['mp3', 'wav', 'flac', 'alac', 'aiff', 'amr', 'ape', 'shn', 's3m', 'nsf', 'spc']

def cancelOperation(onedrive):
    return monitor.abortRequested() or (pg_created and progress_dialog.iscanceled()) or (pg_bg_created and progress_dialog_bg.isFinished()) or onedrive.cancelOperation()

def set_audio_info(list_item, data):
    if 'audio' in data:
        list_item.setInfo('music', {
            'tracknumber' : utils.Utils.get_safe_value(data['audio'], 'track'), \
            'discnumber' : utils.Utils.get_safe_value(data['audio'], 'disc'), \
            'duration' : int(utils.Utils.get_safe_value(data['audio'], 'duration') or '0')/1000, \
            'year' : utils.Utils.get_safe_value(data['audio'], 'year'), \
            'genre' : utils.Utils.get_safe_value(data['audio'], 'genre'), \
            'album': utils.Utils.get_safe_value(data['audio'], 'album'), \
            'artist': utils.Utils.get_safe_value(data['audio'], 'artist'), \
            'title': utils.Utils.get_safe_value(data['audio'], 'title') \
        })

def set_video_info(list_item, data):
    if 'video' in data:
        video = data['video']
        if 'thumbnails' in data and len(data['thumbnails']) > 0:
            thumbnails = data['thumbnails'][0]
            list_item.setIconImage(thumbnails['large']['url'])
            list_item.setThumbnailImage(thumbnails['large']['url'])
        list_item.addStreamInfo('video', { 'width': video['width'], 'height': video['height'], 'duration': video['duration']/1000 })

def process_files(files, driveid, child_count, child_loaded, big_folder):
    onedrive = account_manager.get(driveid)
    if '@odata.nextLink' in files and (child_loaded+201) >= child_count:
        child_count += 200
    for f in files['value']:
        f = utils.Utils.get_safe_value(f, 'remoteItem', f)
        item_id = f['id']
        item_driveid = utils.Utils.get_safe_value(utils.Utils.get_safe_value(f, 'parentReference', {}), 'driveId', driveid)
        file_name = utils.Utils.unicode(utils.Utils.get_safe_value(f, 'name', 'No name found: ' + utils.Utils.str(item_id)))
        is_folder = 'folder' in f
        url = None
        list_item = xbmcgui.ListItem(file_name)
        extension = utils.Utils.get_extension(file_name);
        if is_folder:
            params = {'action':'open_folder', 'content_type': content_type, 'item_driveid': item_driveid, 'item_id': item_id, 'driveid': driveid, 'child_count' : f['folder']['childCount']}
            url = base_url + '?' + urllib.urlencode(params)
            context_options = []
            if content_type == 'audio' or content_type == 'video':
                params['action'] = 'export_folder'
                context_options.append((addon.getLocalizedString(32004), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')'))
            elif content_type == 'image':
                params['action'] = 'slideshow'
                context_options.append((addon.getLocalizedString(32032), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')'))
            params['action'] = 'search'
            params['c'] = time.time()
            cmd = 'ActivateWindow(%d,%s?%s,return)' % (xbmcgui.getCurrentWindowId(), base_url, urllib.urlencode(params))
            context_options.append((addon.getLocalizedString(32039), cmd))
            list_item.addContextMenuItems(context_options)
        elif (('video' in f or extension in ext_videos) and content_type == 'video') or (('audio' in f or extension in ext_audio) and content_type == 'audio'):
            params = {'action':'play', 'content_type': content_type, 'item_driveid': item_driveid, 'item_id': item_id, 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            set_info = set_audio_info if content_type == 'audio' else set_video_info
            set_info(list_item, f)
            list_item.setProperty('IsPlayable', 'true')
        elif ('image' in f or 'photo' in f) and content_type == 'image' and extension != 'mp4':
            params = {'access_token' : onedrive.access_token}
            url = f['@microsoft.graph.downloadUrl']
            list_item.setInfo('pictures', {'size': f['size']})
            list_item.setProperty('mimetype', utils.Utils.get_safe_value(f['file'], 'mimeType'))
            if 'thumbnails' in f and len(f['thumbnails']) > 0:
                thumbnails = f['thumbnails'][0]
                list_item.setIconImage(thumbnails['large']['url'])
        if not url is None:
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, is_folder)
        child_loaded += 1
        if big_folder and not cancelOperation(onedrive):
            p = int(round(float(child_loaded)/child_count*100))
            counter = (utils.Utils.str(child_loaded) , utils.Utils.str(child_count))
            msg = 32048 if action[0] == 'search' else 32047
            progress_dialog_bg.update(p, addonname, addon.getLocalizedString(msg) % counter)
        if cancelOperation(onedrive):
            break;
    if '@odata.nextLink' in files and not cancelOperation(onedrive):
        next_list = onedrive.get(files['@odata.nextLink'], raw_url=True)
        if not cancelOperation(onedrive):
            process_files(next_list, driveid, child_count, child_loaded, big_folder)
def print_slideshow_info(onedrive):
    if xbmcgui.getCurrentWindowId() == 12007:
        print 'Slideshow is there...'
    elif cancelOperation(onedrive):
        print 'Abort requested...'

def refresh_slideshow(driveid, item_driveid, item_id, child_count, waitForSlideshow):
    onedrive = account_manager.get(driveid)
    if waitForSlideshow:
        print 'Waiting up to 10 minutes until the slideshow of folder ' + item_id + ' starts...'
        current_time = time.time()
        max_waiting_time = current_time + 10 * 60
        while not cancelOperation(onedrive) and xbmcgui.getCurrentWindowId() != 12007 and max_waiting_time > current_time:
            if monitor.waitForAbort(2):
                break
            current_time = time.time()
        print_slideshow_info(onedrive)
    interval = addon.getSetting('slideshow_refresh_interval')
    print 'Waiting up to ' + interval + ' minute(s) to check if it is needed to refresh the slideshow of folder ' + item_id + '...'
    current_time = time.time()
    target_time = current_time + int(interval) * 60
    while not cancelOperation(onedrive) and target_time > current_time and xbmcgui.getCurrentWindowId() == 12007:
        if monitor.waitForAbort(10):
            break
        current_time = time.time()
    print_slideshow_info(onedrive)
    if not cancelOperation(onedrive) and xbmcgui.getCurrentWindowId() == 12007:
        try:
            start_auto_refreshed_slideshow(driveid, item_driveid, item_id, child_count)
        except Exception as e:
            print 'Slideshow fails to auto refresh. Will be restarted when possible. Error: '
            if isinstance(e, OneDriveException):
                try:
                    print ''.join(traceback.format_exception(type(e.origin), e.origin, e.tb))
                except:
                    traceback.print_exc()
            else:
                traceback.print_exc()
            refresh_slideshow(driveid, item_driveid, item_id, -1, waitForSlideshow)
    else:
        print 'Slideshow is not running anymore or abort requested.'

def start_auto_refreshed_slideshow(driveid, item_driveid, item_id, oldchild_count):
    onedrive = account_manager.get(driveid)
    f = onedrive.get('/drives/'+item_driveid+'/items/'+item_id)
    if cancelOperation(onedrive):
        return
    if 'folder' in f:
        child_count = int(f['folder']['childCount'])
        waitForSlideshow = False
        if oldchild_count != child_count:
            if oldchild_count >=0:
                print 'Slideshow child count changed. Refreshing slideshow...'
            params = {'action':'open_folder', 'content_type': content_type, 'item_driveid': item_driveid, 'item_id': item_id, 'driveid': driveid, 'child_count': child_count}
            url = base_url + '?' + urllib.urlencode(params)
            xbmc.executebuiltin('SlideShow('+url+')')
            waitForSlideshow = True
        else:
            print 'Slideshow child count is the same, nothing to refresh...'
        t = threading.Thread(target=refresh_slideshow, args=(driveid, item_driveid, item_id, child_count, waitForSlideshow,))
        t.setDaemon(True)
        t.start()
    else:
        dialog.ok(addonname, addon.getLocalizedString(32034) % utils.Utils.unicode(f['name']))

def close_dialog_timeout(dialog, timeout):
    current_time = time.time()
    target_time = current_time + timeout
    while not cancelOperation(onedrive) and target_time > current_time:
        if monitor.waitForAbort(1):
            break
        current_time = time.time()
    dialog.close()

def export_folder(basename, item_driveid, item_id, driveid, destination_folder, base_folder, directLink=None):
    onedrive = account_manager.get(driveid)
    parent_folder = os.path.join(os.path.join(destination_folder, basename), '')
    if not xbmcvfs.exists(parent_folder):
        try:
            xbmcvfs.mkdirs(parent_folder)
        except:
            monitor.waitForAbort(3)
            xbmcvfs.mkdirs(parent_folder)
    if directLink is None:
        files = onedrive.get('/drives/'+item_driveid+'/items/'+item_id+'/children')
    else:
        files = onedrive.get(directLink, raw_url=True)
    if cancelOperation(onedrive):
        return
    for f in files['value']:
        if cancelOperation(onedrive):
            break
        if 'folder' in f:
            onedrive.exporting_target += int(f['folder']['childCount'])
    if cancelOperation(onedrive):
        return
    for f in files['value']:
        if cancelOperation(onedrive):
            break
        is_folder = 'folder' in f
        extension = utils.Utils.get_extension(f['name']);
        name = utils.Utils.ascii(f['name'])
        if is_folder:
            export_folder(name, item_driveid, f['id'], driveid, parent_folder, base_folder)
        elif (('video' in f or extension in ext_videos) and content_type == 'video') or ('audio' in f and content_type == 'audio'):
            params = {'action':'play', 'content_type': content_type, 'item_driveid': item_driveid, 'item_id': f['id'], 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            f = xbmcvfs.File(os.path.join(parent_folder, name + '.strm'), 'w')
            f.write(url)
            f.close()
        onedrive.exporting_count += 1
        p = int(onedrive.exporting_count/float(onedrive.exporting_target)*100)
        if onedrive.exporting_percent < p:
            onedrive.exporting_percent = p
        file_path = os.path.join(parent_folder, name)
        export_progress_dialog_bg.update(onedrive.exporting_percent, addonname + ' ' + addon.getLocalizedString(32024), file_path[len(base_folder):])
    if '@odata.nextLink' in files and not cancelOperation(onedrive):
        export_folder(basename, item_driveid, item_id, driveid, destination_folder, base_folder, files['@odata.nextLink'])

def report_error(e):
    tb = traceback.format_exc()
    if isinstance(e, OneDriveException):
        try:
            tb += '\n--Origin: --\n' + utils.Utils.str(e.tb)
            tb += '\n--url--\n' + e.url
            tb += '\n--body--\n' + utils.Utils.str(e.body)
        except:
            tb += '\n--Exception trying build the report: --\n' + traceback.format_exc()
    tb += '\nVersion: %s' % addon.getAddonInfo('version')
    xbmc.log(tb, xbmc.LOGDEBUG)
    if addon.getSetting('report_error') == 'true':
        try:
            urllib2.urlopen('http://onedrive.daro.mx/report-error.jsp', urllib.urlencode({'stacktrace':tb})).read()
        except Exception as ex:
            xbmc.log(utils.Utils.str(ex), xbmc.LOGDEBUG)
try:
    if action is None:
        onedrives = account_manager.map()
        for driveid in onedrives:
            onedrive = onedrives[driveid]
            list_item = xbmcgui.ListItem(onedrive.name)
            params = {'action':'open_drive', 'content_type': content_type, 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            params = {'action':'remove_account', 'content_type': content_type, 'driveid': driveid}
            context_options = [(addon.getLocalizedString(32007), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')')]
            params['action'] = 'search'
            params['c'] = time.time()
            cmd = 'ActivateWindow(%d,%s?%s,return)' % (xbmcgui.getCurrentWindowId(), base_url, urllib.urlencode(params))
            context_options.append((addon.getLocalizedString(32039), cmd))
            list_item.addContextMenuItems(context_options)
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(32006))
        params = {'action':'add_account', 'content_type': content_type}
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item)
        xbmcplugin.endOfDirectory(addon_handle, True)
    elif action[0] == 'add_account':
        progress_dialog.create(addonname, addon.getLocalizedString(32008))
        pg_created = True
        onedrive = OneDrive(addon.getSetting('client_id_oauth2'))
        pin = utils.Utils.str(onedrive.begin_signin())
        progress_dialog.close()
        pg_created = False
        if pin and dialog.yesno(addonname, addon.getLocalizedString(32009),addon.getLocalizedString(32010) % pin, '', addon.getLocalizedString(32011), addon.getLocalizedString(32012)):
            progress_dialog.create(addonname, addon.getLocalizedString(32013))
            pg_created = True
            json_result = onedrive.finish_signin(pin)
            if json_result['success']:
                loginFailed = False
                if not loginFailed and not cancelOperation(onedrive):
                    try:
                        progress_dialog.update(30, addon.getLocalizedString(32014))
                        onedrive.login(json_result['code']);
                    except Exception as e:
                        loginFailed = True
                        progress_dialog.close()
                        pg_created = False
                        if not cancelOperation(onedrive):
                            dialog.ok(addonname, addon.getLocalizedString(32015), utils.Utils.unicode(e), addon.getLocalizedString(32016))
                            report_error(e)
                if not loginFailed and not cancelOperation(onedrive):
                    try:
                        progress_dialog.update(60, addon.getLocalizedString(32017))
                        info = onedrive.get('/drive')
                        onedrive.driveid = info['id']
                    except Exception as e:
                        loginFailed = True
                        progress_dialog.close()
                        pg_created = False
                        if not cancelOperation(onedrive):
                            dialog.ok(addonname, addon.getLocalizedString(32018), utils.Utils.unicode(e), addon.getLocalizedString(32016))
                            report_error(e)
                if not loginFailed and not cancelOperation(onedrive):
                    try:
                        progress_dialog.update(80, addon.getLocalizedString(32064))
                        info = onedrive.get('/me')
                        onedrive.name = utils.Utils.ascii(info['displayName'])
                    except Exception as e:
                        loginFailed = True
                        progress_dialog.close()
                        pg_created = False
                        if not cancelOperation(onedrive):
                            dialog.ok(addonname, addon.getLocalizedString(32065), utils.Utils.unicode(e), addon.getLocalizedString(32016))
                            report_error(e)
                if not loginFailed and not cancelOperation(onedrive):
                    try:
                        progress_dialog.update(95, addon.getLocalizedString(32020))
                        account_manager.save(onedrive)
                        progress_dialog.close()
                        pg_created = False
                    except Exception as e:
                        progress_dialog.close()
                        pg_created = False
                        if not cancelOperation(onedrive):
                            dialog.ok(addonname, addon.getLocalizedString(32021), utils.Utils.unicode(e), addon.getLocalizedString(32016))
                            report_error(e)
                if not loginFailed and not cancelOperation(onedrive):
                    xbmc.executebuiltin('Container.Refresh')
            else:
                progress_dialog.close()
                pg_created = False
                dialog.ok(addonname, addon.getLocalizedString(32022), addon.getLocalizedString(32016), addon.getLocalizedString(32029))
    elif action[0] == 'remove_account':
        driveid = args.get('driveid')[0]
        onedrive = account_manager.get(driveid)
        if dialog.yesno(addonname, addon.getLocalizedString(32023) % utils.Utils.unicode(onedrive.name), None):
            account_manager.remove(driveid)
        xbmc.executebuiltin('Container.Refresh')
    elif action[0] == 'open_drive':
        driveid = args.get('driveid')[0]
        list_item = xbmcgui.ListItem(addon.getLocalizedString(32052))
        params = {'action':'open_drive_folder', 'folder':'root', 'content_type': content_type, 'driveid': driveid}
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(32053))
        params['action'] = 'open_simple_folder'
        params['folder'] = 'recent'
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        if content_type == 'image':
            list_item = xbmcgui.ListItem(addon.getLocalizedString(32055))
            params['action'] = 'open_drive_folder'
            params['folder'] = 'special/photos'
            url = base_url + '?' + urllib.urlencode(params)
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        if content_type == 'audio':
            list_item = xbmcgui.ListItem(addon.getLocalizedString(32056))
            params['action'] = 'open_drive_folder'
            params['folder'] = 'special/music'
            url = base_url + '?' + urllib.urlencode(params)
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        #list_item = xbmcgui.ListItem(addon.getLocalizedString(32057))
        #params['action'] = 'open_simple_folder'
        #params['folder'] = 'shared'
        #url = base_url + '?' + urllib.urlencode(params)
        #xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(32058))
        params['action'] = 'open_shared_with_me'
        params['folder'] = ''
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_drive_folder':
        driveid = args.get('driveid')[0]
        onedrive = account_manager.get(driveid)
        item_driveid = args.get('item_driveid', [driveid])[0]
        folder = args.get('folder')[0]
        root = onedrive.get('/drives/'+item_driveid+'/' + folder, params=extra_parameters)
        if not cancelOperation(onedrive):
            child_count = int(root['folder']['childCount'])
            big_folder = child_count > big_folder_min
            if big_folder:
                if pg_bg_created:
                    progress_dialog_bg.close()
                progress_dialog_bg.create(addonname, addon.getLocalizedString(32049) % utils.Utils.str(child_count))
                pg_bg_created = True
                progress_dialog_bg.update(0)
            files = onedrive.get('/drives/'+item_driveid+'/' + folder + '/children', params=extra_parameters)
            if not cancelOperation(onedrive):
                process_files(files, driveid, child_count, 0, big_folder)
            if not cancelOperation(onedrive):
                xbmcplugin.endOfDirectory(addon_handle)
                if big_folder:
                    progress_dialog_bg.close()
                    pg_bg_created = False
    elif action[0] == 'open_simple_folder':
        driveid = args.get('driveid')[0]
        onedrive = account_manager.get(driveid)
        item_driveid = args.get('item_driveid', [driveid])[0]
        folder = args.get('folder')[0]
        extra_parameters['select'] = 'id,name,size,file,folder,audio,video,image,photo,@microsoft.graph.downloadUrl,@odata.nextLink,remoteItem'
        if folder == 'recent':
            extra_parameters['expand'] = ''
        files = onedrive.get('/drives/'+item_driveid+'/' + folder, params = extra_parameters)
        if not cancelOperation(onedrive):
            process_files(files, driveid, 0, 0, False)
        if not cancelOperation(onedrive):
            xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_shared_with_me':
        driveid = args.get('driveid')[0]
        onedrive = account_manager.get(driveid)
        files = onedrive.get('/drives/'+driveid+'/sharedWithMe')
        user_dic = {}
        if not cancelOperation(onedrive):
            for f in files['value']:
                remote_user = utils.Utils.get_safe_value(utils.Utils.get_safe_value(f['remoteItem'], 'createdBy', {}), 'user', {})
                if remote_user is not None:
                    remote_user_id = utils.Utils.unicode(remote_user['id'])
                    if remote_user_id not in user_dic:
                        user_dic[remote_user_id] = [f]
                        list_item = xbmcgui.ListItem(utils.Utils.unicode(remote_user['displayName']))
                        params = {'action':'open_shared_by', 'content_type': content_type, 'remote_user_id': remote_user_id, 'driveid': driveid}
                        url = base_url + '?' + urllib.urlencode(params)
                        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
                    else:
                        user_dic[remote_user_id].append(f)
            with open(shared_json_path, 'wb') as fo:
                fo.write(json.dumps(user_dic))
        if not cancelOperation(onedrive):
            xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_shared_by':
        driveid = args.get('driveid')[0]
        onedrive = account_manager.get(driveid)
        remote_user_id = args.get('remote_user_id')[0]
        with open(shared_json_path, 'rb') as fo:
            files = json.loads(fo.read())
        if not cancelOperation(onedrive):
            process_files({'value' : files[remote_user_id]}, driveid, 0, 0, False)
        if not cancelOperation(onedrive):
            xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_folder':
        driveid = args.get('driveid')[0]
        item_driveid = args.get('item_driveid', [driveid])[0]
        item_id = args.get('item_id')[0]
        onedrive = account_manager.get(driveid)
        child_count = 0 if 'child_count' not in args else int(args.get('child_count')[0])
        big_folder = child_count > big_folder_min
        if big_folder:
            if pg_bg_created:
                progress_dialog_bg.close()
            progress_dialog_bg.create(addonname, addon.getLocalizedString(32049) % utils.Utils.str(child_count))
            pg_bg_created = True
            progress_dialog_bg.update(0)
        files = onedrive.get('/drives/'+item_driveid+'/items/'+item_id+'/children', params=extra_parameters )
        if not cancelOperation(onedrive):
            process_files(files, driveid, child_count, 0, big_folder)
        if not cancelOperation(onedrive):
            xbmcplugin.endOfDirectory(addon_handle)
            if big_folder:
                progress_dialog_bg.close()
                pg_bg_created = False
    elif action[0] == 'export_folder':
        if addon.getSetting('exporting') == 'true':
            dialog.ok(addonname, addon.getLocalizedString(32059) + ' ' + addon.getLocalizedString(32038))
        else:
            driveid = args.get('driveid')[0]
            item_driveid = args.get('item_driveid', [driveid])[0]
            item_id = args.get('item_id')[0]
            onedrive = account_manager.get(driveid)
            string_id = 32002 if content_type == 'audio' else 32001
            string_config = 'music_library_folder' if content_type == 'audio' else 'video_library_folder'
            path = addon.getSetting(string_config)
            if path is None or path == '' or not xbmcvfs.exists(path):
                path = dialog.browse(0, addon.getLocalizedString(string_id), 'files', '', False, False, '')
            if xbmcvfs.exists(path):
                export_progress_dialog_bg.create(addonname + ' ' + addon.getLocalizedString(32024), addon.getLocalizedString(32025))
                export_pg_bg_created = True
                export_progress_dialog_bg.update(0)
                addon.setSetting(string_config, path)
                f = onedrive.get('/drives/'+item_driveid+'/items/'+item_id)
                if not cancelOperation(onedrive):
                    onedrive.exporting_target = int(f['folder']['childCount']) + 1
                    name = utils.Utils.unicode(f['name']).encode('ascii', 'ignore')
                    root = path + name + '/'
                    deleted = True
                    if addon.getSetting('clean_folder') == 'true' and xbmcvfs.exists(root) and not xbmcvfs.rmdir(root, True):
                        deleted = False
                        dialog.ok(addonname, addon.getLocalizedString(32066) % root)
                    if not addon.getSetting('clean_folder') == 'true' or deleted:
                        onedrive.exporting = True
                        addon.setSetting('exporting','true')
                        export_folder(name, item_driveid, item_id, driveid, path, root)
            else:
                dialog.ok(addonname, path + ' ' + addon.getLocalizedString(32026))
    elif action[0] == 'show_image':
        url = args.get('url')[0]
        xbmc.executebuiltin('ShowPicture('+url+')')
    elif action[0] == 'slideshow':
        driveid = args.get('driveid')[0]
        item_driveid = args.get('item_driveid', [driveid])[0]
        item_id = args.get('item_id')[0]
        child_count = int(args.get('child_count')[0])
        start_auto_refreshed_slideshow(driveid, item_driveid, item_id, -1)
    elif action[0] == 'search':
        url = '/drive'
        driveid = args.get('driveid')[0]
        onedrive = account_manager.get(driveid)
        if 'item_id' in args:
            item_id = args.get('item_id')[0]
            url += '/items/'+item_id
        else:
            url += '/root'
        d = dialog.input(addonname + ' - ' + addon.getLocalizedString(32042))
        if d != '':
            progress_dialog.create(addonname, addon.getLocalizedString(32040) % d)
            pg_created = True
            progress_dialog.update(50)
            extra_parameters['q'] = d
            extra_parameters['filter'] = 'file ne null'
            files = onedrive.get(url+'/view.search', params=extra_parameters )
            if not cancelOperation(onedrive):
                progress_dialog.update(75, addon.getLocalizedString(32041))
                size = 0
                if '@search.approximateCount' in files:
                    size = int(files['@search.approximateCount'])
                big_folder = size > big_folder_min
                if big_folder:
                    if pg_bg_created:
                        progress_dialog_bg.close()
                    progress_dialog_bg.create(addonname, 'Loading %s items found, please wait...' % utils.Utils.str(size))
                    pg_bg_created = True
                    progress_dialog_bg.update(0)
                process_files(files, driveid, size, 0, big_folder)
                progress_dialog.close()
                pg_created = False
                if big_folder:
                    progress_dialog_bg.close()
                    pg_bg_created = False
        xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'play':
        driveid = args.get('driveid')[0]
        item_driveid = args.get('item_driveid', [driveid])[0]
        item_id = args.get('item_id')[0]
        onedrive = account_manager.get(driveid)
        f = onedrive.get('/drives/'+item_driveid+'/items/'+item_id)
        if not cancelOperation(onedrive):
            url = f['@microsoft.graph.downloadUrl']
            http_service_url = 'http://localhost:' + addon.getSetting('http.service.port') + '/' + item_id
            try:
                req = urllib2.Request(http_service_url, data='')
                req.add_header('download-url', url)
                urllib2.urlopen(req).read()
            except Exception as e:
                xbmc.log(traceback.format_exc(), xbmc.LOGDEBUG)

            list_item = xbmcgui.ListItem(utils.Utils.unicode(f['name']))
            set_info = set_audio_info if content_type == 'audio' else set_video_info
            set_info(list_item, f)
            list_item.select(True)
            list_item.setPath(http_service_url)
            list_item.setProperty('mimetype', utils.Utils.get_safe_value(f['file'], 'mimeType'))
            if addon.getSetting('set_subtitle') == 'true' and content_type == 'video' and 'parentReference' in f:
                file_name = utils.Utils.unicode(f['name'])
                parent_path = utils.Utils.get_safe_value(f['parentReference'], 'path', '')
                subtitle_name = utils.Utils.replace_extension(file_name, 'srt')
                subtitle_path = parent_path+'/'+urllib.quote(utils.Utils.str(subtitle_name))
                progress_dialog_bg.create(addonname, addon.getLocalizedString(32060) % subtitle_name)
                pg_bg_created = True
                progress_dialog_bg.update(50)
                try:
                    subtitle = onedrive.get(subtitle_path, retry=False)
                    list_item.setSubtitles([subtitle['@microsoft.graph.downloadUrl']])
                    progress_dialog_bg.update(100, addonname, addon.getLocalizedString(32061))
                except Exception as e:
                    progress_dialog_bg.update(100, addonname, addon.getLocalizedString(32062))
                t = threading.Thread(target=close_dialog_timeout, args=(progress_dialog_bg, 4))
                t.setDaemon(True)
                t.start()
                pg_bg_created = False
            xbmcplugin.setResolvedUrl(addon_handle, True, list_item)
except Exception as e:
    ex = e
    requested_url = None
    report = True
    selection = None
    if isinstance(ex, OneDriveException):
        ex = ex.origin
        requested_url = e.url
    if isinstance(ex, urllib2.HTTPError):
        if ex.code >= 500:
            dialog.ok(addonname, addon.getLocalizedString(32035), addon.getLocalizedString(32038))
        if ex.code >= 400:
            login_url = OneDrive('')._login_url
            if requested_url is not None and requested_url == login_url:
                selection = False
                report = False
                if dialog.yesno(addonname, addon.getLocalizedString(32046) % '\n'):
                    xbmc.executebuiltin('RunPlugin('+base_url + '?' + urllib.urlencode({'action':'add_account', 'content_type': content_type})+')')
                    selection = True
            else:
                if ex.code == 404:
                    dialog.ok(addonname, addon.getLocalizedString(32037))
                    report = False
                elif ex.code == 401:
                    selection = False
                    if dialog.yesno(addonname, addon.getLocalizedString(32046) % '\n'):
                        xbmc.executebuiltin('RunPlugin('+base_url + '?' + urllib.urlencode({'action':'add_account', 'content_type': content_type})+')')
                        selection = True
                elif ex.code == 403 and requested_url is not None and ('sharedWithMe' in requested_url or 'recent' in requested_url):
                    report = False
                    dialog.ok(addonname, utils.Utils.str(ex), addon.getLocalizedString(32038))
                else:
                    dialog.ok(addonname, addon.getLocalizedString(32036), addon.getLocalizedString(32038))
    elif isinstance(ex, AccountNotFoundException):
        if dialog.yesno(addonname, addon.getLocalizedString(32063) % '\n'):
            xbmc.executebuiltin('RunPlugin('+base_url + '?' + urllib.urlencode({'action':'add_account', 'content_type': content_type})+')')
    else:
        dialog.ok(addonname, addon.getLocalizedString(32027), utils.Utils.unicode(ex), addon.getLocalizedString(32016))
    if report:
        if isinstance(e, OneDriveException):
            e.body += '\n--selection: --\n' + utils.Utils.str(selection)
        report_error(e)
finally:
    addon.setSetting('exporting','false')
    if export_pg_bg_created:
        export_progress_dialog_bg.close()
    if pg_bg_created:
        progress_dialog_bg.close()
    if pg_created:
        progress_dialog.close()
    onedrives = account_manager.map()
    for driveid in onedrives:
        onedrive = onedrives[driveid]
        if onedrive.pg_bg_created:
            onedrive.progress_dialog_bg.close()
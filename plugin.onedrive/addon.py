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

import os
import stat
import shutil
import sys
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import traceback
import urllib
import urllib2
import ConfigParser
from resources.lib.api.onedrive import OneDrive, OneDriveException
from resources.lib.api import utils
import threading
import time
import json

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
big_folder_min = 0

addon_data_path = utils.Utils.unicode(xbmc.translatePath(addon.getAddonInfo('profile')))
if not os.path.exists(addon_data_path):
    try:
        os.makedirs(addon_data_path)
    except:
        monitor.waitForAbort(3)
        os.makedirs(addon_data_path)

config_path = addon_data_path + '/onedrive.ini'
shared_json_path = addon_data_path + '/shared.json'
old_config_path = xbmc.translatePath('special://home/onedrive.ini')
if os.path.exists(old_config_path) and not os.path.exists(config_path):
    try:
        shutil.move(old_config_path, config_path)
    except Exception as e:
        dialog.ok(addonname, addon.getLocalizedString(30028) % config_path)

onedrives = {}
login_url = ''

config = ConfigParser.ConfigParser()
config.read(config_path)

ext_videos = ['mkv', 'iso']

def cancelOperation(onedrive):
    return monitor.abortRequested() or (pg_created and progress_dialog.iscanceled()) or (pg_bg_created and progress_dialog_bg.isFinished()) or onedrive.cancelOperation()
    
def onedrive_event_listener(onedrive, event, obj):
    if event == 'login_success':
        save_onedrive_config(config, onedrive)

def save_onedrive_config(config, onedrive):
    config.set(onedrive.driveid, 'name', onedrive.name)
    config.set(onedrive.driveid, 'access_token', onedrive.access_token)
    config.set(onedrive.driveid, 'refresh_token', onedrive.refresh_token)
    with open(config_path, 'wb') as configfile:
        config.write(configfile)

for driveid in config.sections():
    onedrives[driveid] = OneDrive(addon.getSetting('client_id'))
    onedrives[driveid].driveid = driveid
    onedrives[driveid].event_listener = onedrive_event_listener
    onedrives[driveid].name = config.get(driveid, 'name')
    onedrives[driveid].access_token = config.get(driveid, 'access_token')
    onedrives[driveid].refresh_token = config.get(driveid, 'refresh_token')
    login_url = onedrives[driveid]._login_url

def set_audio_info(list_item, data):
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
    onedrive = onedrives[driveid]
    if '@odata.nextLink' in files and (child_loaded+201) >= child_count:
        child_count += 200
    for f in files['value']:
        f = utils.Utils.get_safe_value(f, 'remoteItem', f)
        item_id = f['id']
        file_name = utils.Utils.unicode(f['name'])
        is_folder = 'folder' in f
        url = None
        list_item = xbmcgui.ListItem(file_name)
        extension = utils.Utils.get_extension(file_name);
        if is_folder:
            params = {'action':'open_folder', 'content_type': content_type, 'item_id': item_id, 'driveid': driveid, 'child_count' : f['folder']['childCount']}
            url = base_url + '?' + urllib.urlencode(params)
            context_options = []
            if content_type == 'audio' or content_type == 'video':
                params['action'] = 'export_folder'
                context_options.append((addon.getLocalizedString(30004), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')'))
            elif content_type == 'image':
                params['action'] = 'slideshow'
                context_options.append((addon.getLocalizedString(30032), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')'))
            params['action'] = 'search'
            params['c'] = time.time()
            cmd = 'ActivateWindow(%d,%s?%s,return)' % (xbmcgui.getCurrentWindowId(), base_url, urllib.urlencode(params))
            context_options.append((addon.getLocalizedString(30039), cmd))
            list_item.addContextMenuItems(context_options)
        elif (('video' in f or extension in ext_videos) and content_type == 'video') or ('audio' in f and content_type == 'audio'):
            params = {'action':'play', 'content_type': content_type, 'item_id': item_id, 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            set_info = set_audio_info if content_type == 'audio' else set_video_info
            set_info(list_item, f)
            list_item.setProperty('IsPlayable', 'true')
        elif ('image' in f or 'photo' in f) and content_type == 'image' and extension != 'mp4':
            params = {'access_token' : onedrive.access_token}
            url = f['@content.downloadUrl'] + '?' + urllib.urlencode(params)
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
            counter = (str(child_loaded) , str(child_count))
            msg = 30048 if action[0] == 'search' else 30047
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

def refresh_slideshow(driveid, item_id, child_count, waitForSlideshow):
    onedrive = onedrives[driveid]
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
            start_auto_refreshed_slideshow(driveid, item_id, child_count)
        except Exception as e:
            print 'Slideshow fails to auto refresh. Will be restarted when possible. Error: '
            if isinstance(e, OneDriveException):
                try:
                    print ''.join(traceback.format_exception(type(e.origin), e.origin, e.tb))
                except:
                    traceback.print_exc()
            else:
                traceback.print_exc()
            refresh_slideshow(driveid, item_id, -1, waitForSlideshow)
    else:
        print 'Slideshow is not running anymore or abort requested.'

def start_auto_refreshed_slideshow(driveid, item_id, oldchild_count):
    onedrive = onedrives[driveid]
    f = onedrive.get('/drive/items/'+item_id)
    if cancelOperation(onedrive):
        return
    if 'folder' in f:
        child_count = int(f['folder']['childCount'])
        waitForSlideshow = False
        if oldchild_count != child_count:
            if oldchild_count >=0:
                print 'Slideshow child count changed. Refreshing slideshow...'
            params = {'action':'open_folder', 'content_type': content_type, 'item_id': item_id, 'driveid': driveid, 'child_count': child_count}
            url = base_url + '?' + urllib.urlencode(params)
            xbmc.executebuiltin('SlideShow('+url+')')
            waitForSlideshow = True
        else:
            print 'Slideshow child count is the same, nothing to refresh...'
        t = threading.Thread(target=refresh_slideshow, args=(driveid, item_id, child_count, waitForSlideshow,))
        t.setDaemon(True)
        t.start()
    else:
        dialog.ok(addonname, addon.getLocalizedString(30034) % utils.Utils.unicode(f['name']))

def export_folder(name, item_id, driveid, destination_folder, directLink=None):
    onedrive = onedrives[driveid]
    parent_folder = os.path.join(destination_folder, name)
    if not os.path.exists(parent_folder):
        try:
            os.makedirs(parent_folder)
        except:
            monitor.waitForAbort(3)
            os.makedirs(parent_folder)
    if directLink is None:
        files = onedrive.get('/drive/items/'+item_id+'/children')
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
            export_folder(name, f['id'], driveid, parent_folder)
        elif (('video' in f or extension in ext_videos) and content_type == 'video') or ('audio' in f and content_type == 'audio'):
            params = {'action':'play', 'content_type': content_type, 'item_id': f['id'], 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            with open(os.path.join(parent_folder, name + '.strm'), 'wb') as fo:
                fo.write(url)
        onedrives[driveid].exporting_count += 1
        p = int(onedrive.exporting_count/float(onedrive.exporting_target)*100)
        if onedrive.exporting_percent < p:
            onedrive.exporting_percent = p
        progress_dialog.update(onedrive.exporting_percent, parent_folder, name)
    if '@odata.nextLink' in files and not cancelOperation(onedrive):
        export_folder(os.path.basename(parent_folder), item_id, driveid, destination_folder, files['@odata.nextLink'])

def remove_readonly(fn, path, excinfo):
    if fn is os.rmdir:
        os.chmod(path, stat.S_IWRITE)
        os.rmdir(path)
    elif fn is os.remove:
        os.chmod(path, stat.S_IWRITE)
        os.remove(path)

def report_error(e):
    tb = traceback.format_exc()
    if isinstance(e, OneDriveException):
        try:
            tb += '\n--Origin: --\n' + e.tb
            tb += '\n--url--\n' + e.url
            tb += '\n--body--\n' + utils.Utils.str(e.body)
        except Exception as e:
            tb += '\n--Exception trying build the report: --\n' + traceback.format_exc()
    tb += '\nVersion: %s' % addon.getAddonInfo('version')
    print tb
    if addon.getSetting('report_error') == 'true':
        try:
            urllib2.urlopen('http://onedrive.daro.mx/report-error.jsp', urllib.urlencode({'stacktrace':tb})).read()
        except Exception as e:
            print traceback.format_exc()
try:
    if action is None:
        for driveid in onedrives:
            list_item = xbmcgui.ListItem(onedrives[driveid].name)
            params = {'action':'open_drive', 'content_type': content_type, 'driveid': onedrives[driveid].driveid}
            url = base_url + '?' + urllib.urlencode(params)
            params = {'action':'remove_account', 'content_type': content_type, 'driveid': onedrives[driveid].driveid}
            context_options = [(addon.getLocalizedString(30007), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')')]
            params['action'] = 'search'
            params['c'] = time.time()
            cmd = 'ActivateWindow(%d,%s?%s,return)' % (xbmcgui.getCurrentWindowId(), base_url, urllib.urlencode(params))
            context_options.append((addon.getLocalizedString(30039), cmd))
            list_item.addContextMenuItems(context_options)
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30006))
        params = {'action':'add_account', 'content_type': content_type}
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item)
        xbmcplugin.endOfDirectory(addon_handle, True)
    elif action[0] == 'add_account':
        progress_dialog.create(addonname, addon.getLocalizedString(30008))
        pg_created = True
        onedrive = OneDrive(addon.getSetting('client_id'))
        pin = onedrive.begin_signin()
        progress_dialog.close()
        pg_created = False
        if dialog.yesno(addonname, addon.getLocalizedString(30009),addon.getLocalizedString(30010) % pin, '', addon.getLocalizedString(30011), addon.getLocalizedString(30012)):
            progress_dialog.create(addonname, addon.getLocalizedString(30013))
            pg_created = True
            json_result = onedrive.finish_signin(pin)
            if json_result['success']:
                loginFailed = False
                try:
                    progress_dialog.update(30, addon.getLocalizedString(30014))
                    onedrive.login(json_result['code']);
                except Exception as e:
                    dialog.ok(addonname, addon.getLocalizedString(30015), utils.Utils.unicode(e), addon.getLocalizedString(30016))
                    report_error(e)
                    loginFailed = True
                if not loginFailed:
                    try:
                        progress_dialog.update(70, addon.getLocalizedString(30017))
                        info = onedrive.get('/drive')
                    except Exception as e:
                        if not cancelOperation(onedrive):
                            info = None
                            dialog.ok(addonname, addon.getLocalizedString(30018), utils.Utils.unicode(e), addon.getLocalizedString(30016))
                            report_error(e)
                    if not cancelOperation(onedrive):
                        if info is None:
                            progress_dialog.close()
                            pg_created = False
                        else:
                            try:
                                progress_dialog.update(90, addon.getLocalizedString(30020))
                                onedrive.driveid = info['id']
                                onedrive.name = utils.Utils.ascii(info['owner']['user']['displayName'])
                                if info['id'] not in onedrives:
                                    config.add_section(onedrive.driveid)
                                save_onedrive_config(config, onedrive)
                                progress_dialog.close()
                                pg_created = False
                            except Exception as e:
                                print e
                                dialog.ok(addonname, addon.getLocalizedString(30021), utils.Utils.unicode(e), addon.getLocalizedString(30016))
                                report_error(e)
                xbmc.executebuiltin('Container.Refresh')
            else:
                progress_dialog.close()
                pg_created = False
                dialog.ok(addonname, addon.getLocalizedString(30022), addon.getLocalizedString(30016), addon.getLocalizedString(30029))
    elif action[0] == 'remove_account':
        driveid = args.get('driveid')[0]
        if dialog.yesno(addonname, addon.getLocalizedString(30023) % utils.Utils.unicode(config.get(driveid, 'name')), None):
            config.remove_section(driveid)
            with open(config_path, 'wb') as configfile:
                config.write(configfile)
        xbmc.executebuiltin('Container.Refresh')
    elif action[0] == 'open_drive':
        driveid = args.get('driveid')[0]
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30052))
        params = {'action':'open_drive_folder', 'folder':'root', 'content_type': content_type, 'driveid': driveid}
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30053))
        params['action'] = 'open_simple_folder'
        params['folder'] = 'view.recent'
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30055))
        params['action'] = 'open_drive_folder'
        params['folder'] = 'special/photos'
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30056))
        params['folder'] = 'special/music'
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30057))
        params['action'] = 'open_simple_folder'
        params['folder'] = 'shared'
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30058))
        params['action'] = 'open_shared_with_me'
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_drive_folder':
        driveid = args.get('driveid')[0]
        onedrive = onedrives[driveid]
        folder = args.get('folder')[0]
        root = onedrive.get('/drive/' + folder, params=extra_parameters)
        if not cancelOperation(onedrive):
            child_count = int(root['folder']['childCount'])
            big_folder = child_count > big_folder_min
            if big_folder:
                if pg_bg_created:
                    progress_dialog_bg.close()
                progress_dialog_bg.create(addonname, addon.getLocalizedString(30049) % str(child_count))
                pg_bg_created = True
                progress_dialog_bg.update(0)
            files = onedrive.get('/drive/' + folder + '/children', params=extra_parameters)
            if not cancelOperation(onedrive):
                process_files(files, driveid, child_count, 0, big_folder)
            if not cancelOperation(onedrive):
                xbmcplugin.endOfDirectory(addon_handle)
                if big_folder:
                    progress_dialog_bg.close()
                    pg_bg_created = False
    elif action[0] == 'open_simple_folder':
        driveid = args.get('driveid')[0]
        onedrive = onedrives[driveid]
        folder = args.get('folder')[0]
        extra_parameters['select'] = 'id,name,size,file,folder,audio,video,image,photo,@content.downloadUrl,@odata.nextLink,remoteItem'
        if folder == 'view.recent':
            extra_parameters['expand'] = ''
        files = onedrive.get('/drive/' + folder, params = extra_parameters)
        if not cancelOperation(onedrive):
            process_files(files, driveid, 0, 0, False)
        if not cancelOperation(onedrive):
            xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_shared_with_me':
        driveid = args.get('driveid')[0]
        onedrive = onedrives[driveid]
        files = onedrive.get('/drive/view.sharedWithMe')
        user_dic = {}
        if not cancelOperation(onedrive):
            for f in files['value']:
                remote_user = utils.Utils.get_safe_value(utils.Utils.get_safe_value(utils.Utils.get_safe_value(f['remoteItem'], 'shared', {}), 'owner', {}), 'user');
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
        onedrive = onedrives[driveid]
        remote_user_id = args.get('remote_user_id')[0]
        with open(shared_json_path, 'rb') as fo:
            files = json.loads(fo.read())
        if not cancelOperation(onedrive):
            process_files({'value' : files[remote_user_id]}, driveid, 0, 0, False)
        if not cancelOperation(onedrive):
            xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_folder':
        driveid = args.get('driveid')[0]
        item_id = args.get('item_id')[0]
        onedrive = onedrives[driveid]
        child_count = 0 if 'child_count' not in args else int(args.get('child_count')[0])
        big_folder = child_count > big_folder_min
        if big_folder:
            if pg_bg_created:
                progress_dialog_bg.close()
            progress_dialog_bg.create(addonname, addon.getLocalizedString(30049) % str(child_count))
            pg_bg_created = True
            progress_dialog_bg.update(0)
        files = onedrive.get('/drive/items/'+item_id+'/children', params=extra_parameters )
        if not cancelOperation(onedrive):
            process_files(files, driveid, child_count, 0, big_folder)
        if not cancelOperation(onedrive):
            xbmcplugin.endOfDirectory(addon_handle)
            if big_folder:
                progress_dialog_bg.close()
                pg_bg_created = False
    elif action[0] == 'export_folder':
        driveid = args.get('driveid')[0]
        item_id = args.get('item_id')[0]
        onedrive = onedrives[driveid]
        string_id = 30002 if content_type == 'audio' else 30001
        string_config = 'music_library_folder' if content_type == 'audio' else 'video_library_folder'
        path = addon.getSetting(string_config)
        if path is None or path == '' or not os.path.exists(path):  
            path = dialog.browse(0, addon.getLocalizedString(string_id), 'files', '', False, False, '')
        if os.path.exists(path):
            progress_dialog.create(addonname + ' ' + addon.getLocalizedString(30024), addon.getLocalizedString(30025))
            pg_created = True
            progress_dialog.update(0)
            addon.setSetting(string_config, path)
            f = onedrive.get('/drive/items/'+item_id)
            if not cancelOperation(onedrive):
                onedrive.exporting_target = int(f['folder']['childCount']) + 1
                name = utils.Utils.unicode(f['name']).encode('ascii', 'ignore')
                if addon.getSetting('clean_folder') == 'true':
                    root = os.path.join(path, name)
                    if os.path.exists(root):
                        try:
                            shutil.rmtree(root, onerror=remove_readonly)
                        except:
                            monitor.waitForAbort(3)
                            shutil.rmtree(root, onerror=remove_readonly)
                export_folder(name, item_id, driveid, path)
                onedrive.exporting_count += 1
        else:
            dialog.ok(addonname, addon.getLocalizedString(30026))
    elif action[0] == 'show_image':
        url = args.get('url')[0]
        xbmc.executebuiltin('ShowPicture('+url+')')
    elif action[0] == 'slideshow':
        driveid = args.get('driveid')[0]
        item_id = args.get('item_id')[0]
        child_count = int(args.get('child_count')[0])
        start_auto_refreshed_slideshow(driveid, item_id, -1)
    elif action[0] == 'search':
        url = '/drive'
        driveid = args.get('driveid')[0]
        onedrive = onedrives[driveid]
        if 'item_id' in args:
            item_id = args.get('item_id')[0]
            url += '/items/'+item_id
        else:
            url += '/root'
        d = dialog.input(addonname + ' - ' + addon.getLocalizedString(30042))
        if d != '':
            progress_dialog.create(addonname, addon.getLocalizedString(30040) % d)
            pg_created = True
            progress_dialog.update(50)
            extra_parameters['q'] = d
            extra_parameters['filter'] = 'file ne null'
            files = onedrive.get(url+'/view.search', params=extra_parameters )
            if not cancelOperation(onedrive):
                progress_dialog.update(75, addon.getLocalizedString(30041))
                size = 0
                if '@search.approximateCount' in files:
                    size = int(files['@search.approximateCount'])
                big_folder = size > big_folder_min
                if big_folder:
                    if pg_bg_created:
                        progress_dialog_bg.close()
                    progress_dialog_bg.create(addonname, 'Loading %s items found, please wait...' % str(size))
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
        item_id = args.get('item_id')[0]
        onedrive = onedrives[driveid]
        f = onedrive.get('/drive/items/'+item_id)
        if not cancelOperation(onedrive):
            url = f['@content.downloadUrl']
            list_item = xbmcgui.ListItem(utils.Utils.unicode(f['name']))
            set_info = set_audio_info if content_type == 'audio' else set_video_info
            set_info(list_item, f)
            list_item.select(True)
            list_item.setPath(url)
            list_item.setProperty('mimetype', utils.Utils.get_safe_value(f['file'], 'mimeType'))
            if addon.getSetting('set_subtitle') == 'true' and content_type == 'video' and 'parentReference' in f:
                file_name = utils.Utils.unicode(f['name'])
                parent_path = utils.Utils.get_safe_value(f['parentReference'], 'path', '')
                subtitle_path = parent_path+'/'+utils.Utils.replace_extension(file_name, 'srt')
                try:
                    subtitle = onedrive.get(subtitle_path, retry=False)
                    if not cancelOperation(onedrive):
                        list_item.setSubtitles([subtitle['@content.downloadUrl']])
                except:
                    None
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
            dialog.ok(addonname, addon.getLocalizedString(30035), addon.getLocalizedString(30038))
        if ex.code >= 400:
            if requested_url is not None and requested_url == login_url:
                selection = False
                if dialog.yesno(addonname, addon.getLocalizedString(30046) % '\n'):
                    xbmc.executebuiltin('RunPlugin('+base_url + '?' + urllib.urlencode({'action':'add_account', 'content_type': content_type})+')')
                    selection = True
            else:
                if ex.code == 404:
                    dialog.ok(addonname, addon.getLocalizedString(30037))
                elif ex.code == 401:
                    selection = False
                    if dialog.yesno(addonname, addon.getLocalizedString(30046) % '\n'):
                        xbmc.executebuiltin('RunPlugin('+base_url + '?' + urllib.urlencode({'action':'add_account', 'content_type': content_type})+')')
                        selection = True
                else:
                    dialog.ok(addonname, addon.getLocalizedString(30036), addon.getLocalizedString(30038))
    else:
        dialog.ok(addonname, addon.getLocalizedString(30027), utils.Utils.unicode(ex), addon.getLocalizedString(30016))
    if report:
        if isinstance(e, OneDriveException):
            e.body += '\n--selection: --\n' + utils.Utils.str(selection)
        report_error(e)
finally:
    if pg_bg_created:
        progress_dialog_bg.close()
    if pg_created:
        progress_dialog.close()
    for driveid in onedrives:
        if onedrives[driveid].pg_bg_created:
            onedrives[driveid].progress_dialog_bg.close()
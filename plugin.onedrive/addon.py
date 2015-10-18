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
import urllib
import ConfigParser
from resources.lib.api.onedrive import OneDrive
from resources.lib.api import utils
base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')

action = args.get('action', None)
try:
    content_type = args.get('content_type')[0]
except:
    content_type = 'video'
extra_parameters = {'expand': 'thumbnails'}
dialog = xbmcgui.Dialog();
progress_dialog = xbmcgui.DialogProgress() 
root_url = '/drive/root/children'
old_config_path = xbmc.translatePath('special://home/onedrive.ini')
config_path = utils.Utils.unicode(xbmc.translatePath(addon.getAddonInfo('profile'))) + '/onedrive.ini'
if os.path.exists(old_config_path) and not os.path.exists(config_path):
    try:
        shutil.move(old_config_path, config_path)
    except:
        dialog.ok(addonname, addon.getLocalizedString(30028) % config_path)

onedrives = {}

config = ConfigParser.ConfigParser()
config.read(config_path)
    
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

def set_audio_info(list_item, data):
    list_item.setInfo('music', {
        'tracknumber' : utils.Utils.get_safe_value(data['audio'], 'track'), \
        'discnumber' : utils.Utils.get_safe_value(data['audio'], 'disc'), \
        'duration' : int(utils.Utils.get_safe_value(data['audio'], 'duration'))/1000, \
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
    
def process_files(files, driveid):
    for f in files['value']:
        item_id = f['id']
        file_name = utils.Utils.str(f['name'])
        is_folder = 'folder' in f
        url = None
        list_item = xbmcgui.ListItem(file_name)
        extension = utils.Utils.get_extension(file_name);
        if is_folder:
            params = {'action':'open_folder', 'content_type': content_type, 'item_id': item_id, 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            if content_type == 'audio' or content_type == 'video':
                params['action'] = 'export_folder'
                list_item.addContextMenuItems([(addon.getLocalizedString(30004), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')')])
        elif (('video' in f or extension == 'mkv') and content_type == 'video') or ('audio' in f and content_type == 'audio'):
            params = {'action':'play', 'content_type': content_type, 'item_id': item_id, 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            set_info = set_audio_info if content_type == 'audio' else set_video_info
            set_info(list_item, f)
            list_item.setProperty('IsPlayable', 'true')
        elif ('image' in f or 'photo' in f) and content_type == 'image':
            params = {'action':'show_image', 'content_type': content_type, 'url': f['@content.downloadUrl']}
            list_item.addContextMenuItems([(addon.getLocalizedString(30005), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')')], True)
            url = f['@content.downloadUrl']
            list_item.setInfo('pictures', {'size': f['size']})
            if 'thumbnails' in f and len(f['thumbnails']) > 0:
                thumbnails = f['thumbnails'][0]
                list_item.setIconImage(thumbnails['large']['url'])
        if not url is None:
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, is_folder)
    if '@odata.nextLink' in files:
        process_files(onedrives[driveid].get(files['@odata.nextLink'], raw_url=True), driveid)

def export_folder(name, item_id, driveid, destination_folder):
    parent_folder = os.path.join(destination_folder, name)
    if not os.path.exists(parent_folder):
        try:
            os.makedirs(parent_folder)
        except:
            xbmc.sleep(3000)
            os.makedirs(parent_folder)
    files = onedrives[driveid].get('/drive/items/'+item_id+'/children')
    onedrives[driveid].exporting_target += len(files['value'])
    for f in files['value']:
        if progress_dialog.iscanceled():
            break
        is_folder = 'folder' in f
        extension = utils.Utils.get_extension(f['name']);
        name = utils.Utils.unicode(f['name']).encode('ascii', 'ignore')
        if is_folder:
            export_folder(name, f['id'], driveid, parent_folder)
        elif (('video' in f or extension == 'mkv') and content_type == 'video') or ('audio' in f and content_type == 'audio'):
            params = {'action':'play', 'content_type': content_type, 'item_id': f['id'], 'driveid': driveid}
            url = base_url + '?' + urllib.urlencode(params)
            p = int(onedrives[driveid].exporting_count/float(onedrives[driveid].exporting_target)*100)
            if onedrives[driveid].exporting_percent < p:
                onedrives[driveid].exporting_percent = p
            progress_dialog.update(onedrives[driveid].exporting_percent, parent_folder, name)
            fo = open(os.path.join(parent_folder, name + '.strm'), 'wb')
            fo.write(url)
            fo.close()
        onedrives[driveid].exporting_count += 1
def remove_readonly(fn, path, excinfo):
    if fn is os.rmdir:
        os.chmod(path, stat.S_IWRITE)
        os.rmdir(path)
    elif fn is os.remove:
        os.chmod(path, stat.S_IWRITE)
        os.remove(path)
try:
    if action is None:
        for driveid in onedrives:
            list_item = xbmcgui.ListItem(onedrives[driveid].name)
            params = {'action':'open_drive', 'content_type': content_type, 'driveid': onedrives[driveid].driveid}
            url = base_url + '?' + urllib.urlencode(params)
            params = {'action':'remove_account', 'content_type': content_type, 'driveid': onedrives[driveid].driveid}
            list_item.addContextMenuItems([(addon.getLocalizedString(30007), 'RunPlugin('+base_url + '?' + urllib.urlencode(params)+')')])
            xbmcplugin.addDirectoryItem(addon_handle, url, list_item, True)
        list_item = xbmcgui.ListItem(addon.getLocalizedString(30006))
        params = {'action':'add_account', 'content_type': content_type}
        url = base_url + '?' + urllib.urlencode(params)
        xbmcplugin.addDirectoryItem(addon_handle, url, list_item)
        xbmcplugin.endOfDirectory(addon_handle, True)
    elif action[0] == 'add_account':
        progress_dialog.create(addonname, addon.getLocalizedString(30008))
        onedrive = OneDrive(addon.getSetting('client_id'))
        pin = onedrive.begin_signin()
        progress_dialog.close()
        if dialog.yesno(addonname, addon.getLocalizedString(30009),addon.getLocalizedString(30010) % pin, None, addon.getLocalizedString(30011), addon.getLocalizedString(30012)):
            progress_dialog.create(addonname, addon.getLocalizedString(30013))
            json = onedrive.finish_signin(pin)
            if json['success']:
                loginFailed = False
                try:
                    progress_dialog.update(30, addon.getLocalizedString(30014))
                    onedrive.login(json['code']);
                except Exception as e:
                    dialog.ok(addonname, addon.getLocalizedString(30015), utils.Utils.str(e), addon.getLocalizedString(30016))
                    loginFailed = True
                if not loginFailed:
                    try:
                        progress_dialog.update(70, addon.getLocalizedString(30017))
                        info = onedrive.get('/drive')
                    except Exception as e:
                        info = None
                        dialog.ok(addonname, addon.getLocalizedString(30018), utils.Utils.str(e), addon.getLocalizedString(30016))
                    if info is None:
                        progress_dialog.close()
                    elif info['id'] in onedrives:
                        progress_dialog.close()
                        dialog.ok(addonname, addon.getLocalizedString(30019))
                    else:
                        try:
                            progress_dialog.update(90, addon.getLocalizedString(30020))
                            onedrive.driveid = info['id']
                            onedrive.name = utils.Utils.str(info['owner']['user']['displayName'])
                            config.add_section(onedrive.driveid)
                            save_onedrive_config(config, onedrive)
                            progress_dialog.close()
                        except Exception as e:
                            dialog.ok(addonname, addon.getLocalizedString(30021), utils.Utils.str(e), addon.getLocalizedString(30016))
                xbmc.executebuiltin('Container.Refresh')
            else:
                progress_dialog.close()
                dialog.ok(addonname, addon.getLocalizedString(30022), addon.getLocalizedString(30016))
    elif action[0] == 'remove_account':
        driveid = args.get('driveid')[0]
        if dialog.yesno(addonname, addon.getLocalizedString(30023) % config.get(driveid, 'name'), None):
            config.remove_section(driveid)
            with open(config_path, 'wb') as configfile:
                config.write(configfile)
        xbmc.executebuiltin('Container.Refresh')
    elif action[0] == 'open_drive':
        driveid = args.get('driveid')[0]
        files = onedrives[driveid].get(root_url, params=extra_parameters)
        process_files(files, driveid)
        xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'open_folder':
        driveid = args.get('driveid')[0]
        item_id = args.get('item_id')[0]
        files = onedrives[driveid].get('/drive/items/'+item_id+'/children', params=extra_parameters )
        process_files(files, driveid)
        xbmcplugin.endOfDirectory(addon_handle)
    elif action[0] == 'export_folder':
        driveid = args.get('driveid')[0]
        item_id = args.get('item_id')[0]
        string_id = 30002 if content_type == 'audio' else 30001
        string_config = 'music_library_folder' if content_type == 'audio' else 'video_library_folder'
        path = addon.getSetting(string_config)
        if path is None or path == '' or not os.path.exists(path):  
            path = dialog.browse(0, addon.getLocalizedString(string_id), 'files', '', False, False, '')
        if os.path.exists(path):
            progress_dialog.create(addonname + ' ' + addon.getLocalizedString(30024), addon.getLocalizedString(30025))
            progress_dialog.update(0)
            addon.setSetting(string_config, path)
            f = onedrives[driveid].get('/drive/items/'+item_id)
            name = utils.Utils.unicode(f['name']).encode('ascii', 'ignore')
            if addon.getSetting('clean_folder') == 'true':
                root = os.path.join(path, name)
                if os.path.exists(root):
                    try:
                        shutil.rmtree(root, onerror=remove_readonly)
                    except:
                        xbmc.sleep(3000)
                        shutil.rmtree(root, onerror=remove_readonly)
            export_folder(name, item_id, driveid, path)
            onedrives[driveid].exporting_count += 1
        else:
            dialog.ok(addonname, addon.getLocalizedString(30026))
    elif action[0] == 'show_image':
        url = args.get('url')[0]
        xbmc.executebuiltin("ShowPicture("+url+")")
    elif action[0] == 'play':
        driveid = args.get('driveid')[0]
        item_id = args.get('item_id')[0]
        f = onedrives[driveid].get('/drive/items/'+item_id)
        url = f['@content.downloadUrl']
        list_item = xbmcgui.ListItem(utils.Utils.str(f['name']))
        set_info = set_audio_info if content_type == 'audio' else set_video_info
        set_info(list_item, f)
        list_item.select(True)
        list_item.setPath(url)
        list_item.setProperty('mimetype', f['file']['mimeType'])
        xbmcplugin.setResolvedUrl(addon_handle, True, list_item)
except Exception as ex:
    dialog.ok(addonname, addon.getLocalizedString(30027), utils.Utils.str(ex), addon.getLocalizedString(30016))
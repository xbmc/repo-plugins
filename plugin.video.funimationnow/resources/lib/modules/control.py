# -*- coding: utf-8 -*-

'''
    Funimation|Now Add-on
    Copyright (C) 2016 Funimation|Now

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os;
import xbmc;
import xbmcaddon;
import xbmcplugin;
import xbmcgui;
import xbmcvfs;



integer = 1000;
lang = xbmcaddon.Addon().getLocalizedString;
lang2 = xbmc.getLocalizedString;
setting = xbmcaddon.Addon().getSetting;
setSetting = xbmcaddon.Addon().setSetting;
addon = xbmcaddon.Addon;
addItem = xbmcplugin.addDirectoryItem;
item = xbmcgui.ListItem;
directory = xbmcplugin.endOfDirectory;
content = xbmcplugin.setContent;
property = xbmcplugin.setProperty;
addonInfo = xbmcaddon.Addon().getAddonInfo;
infoLabel = xbmc.getInfoLabel;
condVisibility = xbmc.getCondVisibility;
jsonrpc = xbmc.executeJSONRPC;
window = xbmcgui.Window(10000);
dialog = xbmcgui.Dialog();
progressDialog = xbmcgui.DialogProgress();
progressDialogBG = xbmcgui.DialogProgressBG();
windowDialog = xbmcgui.WindowDialog();
button = xbmcgui.ControlButton;
image = xbmcgui.ControlImage;
keyboard = xbmc.Keyboard;
sleep = xbmc.sleep;
execute = xbmc.executebuiltin;
skin = xbmc.getSkinDir();
player = xbmc.Player();
playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO);
resolve = xbmcplugin.setResolvedUrl;
openFile = xbmcvfs.File;
makeFile = xbmcvfs.mkdir;
deleteFile = xbmcvfs.delete;
listDir = xbmcvfs.listdir;
transPath = xbmc.translatePath;
skinPath = xbmc.translatePath('special://skin/');
addonPath = xbmc.translatePath(addonInfo('path'));
dataPath = xbmc.translatePath(addonInfo('profile')).decode('utf-8');
settingsFile = os.path.join(dataPath, 'settings.xml');
viewsFile = os.path.join(dataPath, 'views.db');
bookmarksFile = os.path.join(dataPath, 'bookmarks.db');
providercacheFile = os.path.join(dataPath, 'providers.5.db');
metacacheFile = os.path.join(dataPath, 'meta.db');
cacheFile = os.path.join(dataPath, 'cache.db');
cookiesFile = os.path.join(dataPath, 'cookies.db');
tokensFile = os.path.join(dataPath, 'tokens.db');
synchFile = os.path.join(dataPath, 'synch.db');


def addonIcon():
    theme = appearance();
    art = artPath();
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'icon.png')
    return addonInfo('icon')


def addonThumb():
    theme = appearance() ; art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'poster.png')
    elif theme == '-': return 'DefaultFolder.png'
    return addonInfo('icon')


def addonPoster():
    theme = appearance() ; art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'poster.png')
    return 'DefaultVideo.png'


def addonBanner():
    theme = appearance() ; art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'banner.png')
    return 'DefaultVideo.png'


def addonFanart():
    theme = appearance();
    art = artPath();

    if not (art == None and theme in ['-', '']): return os.path.join(art, 'fanart.jpg')
    return addonInfo('fanart')


def addonNext():
    theme = appearance() ; art = artPath()
    if not (art == None and theme in ['-', '']): return os.path.join(art, 'next.png')
    return 'DefaultVideo.png'

'''
def artPath():
    theme = appearance()
    if theme in ['-', '']: return
    elif condVisibility('System.HasAddon(script.funimationnow.artwork)'):
        return os.path.join(xbmcaddon.Addon('script.funimationnow.artwork').getAddonInfo('path'), 'resources', 'media', theme)
'''        

def artPath(imgPath = None):

    if imgPath is None:
        return;

    else:
        return os.path.join(xbmcaddon.Addon().getAddonInfo('path'), 'resources', 'media', imgPath);

def appearance():
    appearance = setting('appearance.1').lower() if condVisibility('System.HasAddon(script.funimationnow.artwork)') else setting('appearance.alt').lower()
    return appearance


def artwork():
    execute('RunPlugin(plugin://script.funimationnow.artwork)')


def infoDialog(message, heading=addonInfo('name'), icon='', time=3000, sound=False):
    if icon == '': icon = addonIcon()
    elif icon == 'INFO': icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'WARNING': icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == 'ERROR': icon = xbmcgui.NOTIFICATION_ERROR
    dialog.notification(heading, message, icon, time, sound=sound)


def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=''):
    return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)


def selectDialog(list, heading=addonInfo('name')):
    return dialog.select(heading, list)


def apiLanguage():
    langDict = {'Bulgarian': 'bg', 'Chinese': 'zh', 'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl', 'English': 'en', 'Finnish': 'fi', 'French': 'fr', 'German': 'de', 'Greek': 'el', 'Hebrew': 'he', 'Hungarian': 'hu', 'Italian': 'it', 'Japanese': 'ja', 'Korean': 'ko', 'Norwegian': 'no', 'Polish': 'pl', 'Portuguese': 'pt', 'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Slovak': 'sk', 'Slovenian': 'sl', 'Spanish': 'es', 'Swedish': 'sv', 'Thai': 'th', 'Turkish': 'tr', 'Ukrainian': 'uk'}

    trakt = ['bg','cs','da','de','el','en','es','fi','fr','he','hr','hu','it','ja','ko','nl','no','pl','pt','ro','ru','sk','sl','sr','sv','th','tr','uk','zh']
    tvdb = ['en','sv','no','da','fi','nl','de','it','es','fr','pl','hu','el','tr','ru','he','ja','pt','zh','cs','sl','hr','ko'] 

    name = setting('api.language')
    if name[-1].isupper():
        try: name = xbmc.getLanguage(xbmc.ENGLISH_NAME).split(' ')[0]
        except: pass
    try: name = langDict[name]
    except: name = 'en'
    lang = {'trakt': name} if name in trakt else {'trakt': 'en'}
    lang['tvdb'] = name if name in tvdb else 'en'
    return lang


def version():
    num = ''
    try: version = addon('xbmc.addon').getAddonInfo('version')
    except: version = '999'
    for i in version:
        if i.isdigit(): num += i
        else: break
    return int(num)


def openSettings(query=None, id=addonInfo('id')):
    try:
        idle()
        execute('Addon.OpenSettings(%s)' % id)
        if query == None: raise Exception()
        c, f = query.split('.')
        execute('SetFocus(%i)' % (int(c) + 100))
        execute('SetFocus(%i)' % (int(f) + 200))
    except:
        return


def refresh():
    return execute('Container.Refresh')

def update():
    return execute('Container.Update')


def idle():
    return execute('Dialog.Close(busydialog)')


def queueItem():
    return execute('Action(Queue)')



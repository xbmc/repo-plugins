#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import sys
import re
import os
import time
import subprocess
import xbmcplugin
import xbmcgui
import xbmcaddon


addon = xbmcaddon.Addon()
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
addonPath = addon.getAddonInfo('path')
translation = addon.getLocalizedString
osWin = xbmc.getCondVisibility('system.platform.windows')
osOsx = xbmc.getCondVisibility('system.platform.osx')
osLinux = xbmc.getCondVisibility('system.platform.linux')
osAndroid = xbmc.getCondVisibility('system.platform.android')
useOwnProfile = addon.getSetting("useOwnProfile") == "true"
useCustomPath = addon.getSetting("useCustomPath") == "true"
customPath = xbmc.translatePath(addon.getSetting("customPath"))


userDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
profileFolder = os.path.join(userDataFolder, 'profile')
siteFolder = os.path.join(userDataFolder, 'sites')

if not os.path.isdir(userDataFolder):
    os.mkdir(userDataFolder)
if not os.path.isdir(profileFolder):
    os.mkdir(profileFolder)
if not os.path.isdir(siteFolder):
    os.mkdir(siteFolder)

youtubeUrl = "http://www.youtube.com/leanback"
vimeoUrl = "http://www.vimeo.com/couchmode"

def find_exe(pathlist):
    for path in pathlist:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None

exePath = None

if useCustomPath:
    exePath=find_exe([customPath,])
elif osWin:
    exePath = find_exe(['C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
                        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'])
elif osOsx:
    exePath = find_exe(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",])
elif osLinux:
    exePath = find_exe(["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"])

if not osAndroid and exePath is None:
    xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30005))+'!,5000)')
    addon.openSettings()


def openAndroidBrowser(url):
    xbmc.executebuiltin("StartAndroidActivity(com.android.chrome,,,"+url+")")


def updateOwnProfile():
    # On Linux, chrome kiosk leavs black bars on side/bottom of screen due to an incorrect working size.
    # We can fix the preferences directly
    # cat $prefs |perl -pe "s/\"work_area_bottom.*/\"work_area_bottom\": $(xrandr | grep \* | cut -d' ' -f4 | cut -d'x' -f2),/" > $prefs
    # cat $prefs |perl -pe "s/\"work_area_right.*/\"work_area_right\": $(xrandr | grep \* | cut -d' ' -f4 | cut -d'x' -f1),/" > $prefs
    try:
        width, height = 0,0
        xrandr = subprocess.check_output(['xrandr']).split('\n')
        for line in xrandr:
            match = re.compile('([0-9]+)x([0-9]+).+?\*.+?').findall(line)
            if match:
                width = int(match[0][0])
                height = int(match[0][1])
                break
        prefs = os.path.join(profileFolder, 'Default', 'Preferences')
        # space for non existing controls. Not sure why it needs it, but it does on my setup
        top_margin = 30

        with open(prefs, "rb+") as prefsfile:
            import json
            prefsdata = json.load(prefsfile)
            prefs_browser = prefsdata.get('browser', {})
            prefs_window_placement = prefs_browser.get('window_placement', {})
            prefs_window_placement['always_on_top'] = True
            prefs_window_placement['top'] = top_margin
            prefs_window_placement['bottom'] = height-top_margin
            prefs_window_placement['work_area_bottom'] = height
            prefs_window_placement['work_area_right'] = width
            prefsdata['browser'] = prefs_browser
            prefsdata['browser']['window_placement'] = prefs_window_placement
            prefsfile.seek(0)
            prefsfile.truncate(0)
            json.dump(prefsdata, prefsfile, indent=4, separators=(',', ': '))

    except:
        xbmc.log("Can't update chrome resolution")

def index():
    files = os.listdir(siteFolder)
    for file in files:
        if file.endswith(".link"):
            with open(os.path.join(siteFolder, file), 'r') as fh:
                title = ""
                url = ""
                thumb = ""
                kiosk = "yes"
                stopPlayback = "no"
                for line in fh.readlines():
                    entry = line[:line.find("=")]
                    content = line[line.find("=")+1:]
                    if entry == "title":
                        title = content.strip()
                    elif entry == "url":
                        url = content.strip()
                    elif entry == "thumb":
                        thumb = content.strip()
                    elif entry == "kiosk":
                        kiosk = content.strip()
                    elif entry == "stopPlayback":
                        stopPlayback = content.strip()
            addSiteDir(title, url, 'showSite', thumb, stopPlayback, kiosk)
    addDir("[ Vimeo Couchmode ]", vimeoUrl, 'showSite', os.path.join(addonPath, "vimeo.png"), "yes", "yes")
    addDir("[ Youtube Leanback ]", youtubeUrl, 'showSite', os.path.join(addonPath, "youtube.png"), "yes", "yes")
    addDir("[B]- "+translation(30001)+"[/B]", "", 'addSite', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def addSite(site="", title=""):
    if site:
        filename = getFileName(title)
        content = "title="+title+"\nurl="+site+"\nthumb=DefaultFolder.png\nstopPlayback=no\nkiosk=yes"
        with open(os.path.join(siteFolder, filename+".link"), 'w') as fh:
            fh.write(content)
    else:
        keyboard = xbmc.Keyboard('', translation(30003))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            title = keyboard.getText()
            keyboard = xbmc.Keyboard('http://', translation(30004))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                url = keyboard.getText()
                keyboard = xbmc.Keyboard('no', translation(30009))
                keyboard.doModal()
                if keyboard.isConfirmed() and keyboard.getText():
                    stopPlayback = keyboard.getText()
                    keyboard = xbmc.Keyboard('yes', translation(30016))
                    keyboard.doModal()
                    if keyboard.isConfirmed() and keyboard.getText():
                        kiosk = keyboard.getText()
                        content = "title="+title+"\nurl="+url+"\nthumb=DefaultFolder.png\nstopPlayback="+stopPlayback+"\nkiosk="+kiosk
                        with open(os.path.join(siteFolder, getFileName(title)+".link"), 'w') as fh:
                            fh.write(content)
    xbmc.executebuiltin("Container.Refresh")


def getFileName(title):
    return (''.join(c for c in unicode(title, 'utf-8') if c not in '/\\:?"*|<>')).strip()


def getFullPath(exePath, url, useKiosk, userAgent):
    args = [exePath,]
    if useOwnProfile:
        args.append('--user-data-dir=%s' % profileFolder)
    if useKiosk == 'yes':
        args.append('--kiosk')
        if useOwnProfile and osLinux:
            updateOwnProfile()
    if userAgent:
        args.append('--user-agent="%s" % userAgent')

    # Flashing a white screen on switching to chrome looks bad, so I'll use a temp html file with black background
    # to redirect to our desired location.
    black_background = os.path.join(userDataFolder, "black.html")
    with open(black_background, "w") as launch:
        launch.write('<html><body style="background:black"><script>window.location.href = "%s";</script></body></html>' % url)

    args+=['--start-maximized', '--disable-translate', '--disable-new-tab-first-run', '--no-default-browser-check', '--no-first-run', black_background]
    return args

def bringChromeToFront(pid):
    if osLinux:
        # Ensure chrome is active window
        def currentActiveWindowLinux():
            name = ""
            try:
                # xprop -id $(xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW | cut -f 2) _NET_WM_NAME
                current_window_id = subprocess.check_output(['xprop', '-root', '32x', '\'\t$0\'', '_NET_ACTIVE_WINDOW'])
                current_window_id = current_window_id.strip("'").split()[1]
                current_window_name = subprocess.check_output(['xprop', '-id', current_window_id, "WM_NAME"])
                if "not found" not in current_window_name and "failed request" not in current_window_name:
                    current_window_name = current_window_name.strip().split(" = ")[1].strip('"')
                    name = current_window_name
            except OSError:
                pass
            return name

        def findWid():
            wid = None
            match = re.compile("(0x[0-9A-Fa-f]+)").findall(subprocess.check_output(['xprop','-root','_NET_CLIENT_LIST']))
            if match:
                for id in match:
                    try:
                        wpid = subprocess.check_output(['xprop','-id',id,'_NET_WM_PID'])
                        wname = subprocess.check_output(['xprop','-id',id,'WM_NAME'])
                        if str(pid) in wpid:
                            wid = id
                    except (OSError, subprocess.CalledProcessError): pass
            return wid

        try:
            timeout = time.time() + 10
            while time.time() < timeout:# and "chrome" not in currentActiveWindowLinux().lower():
                #windows = subprocess.check_output(['wmctrl', '-l'])
                #if "Google Chrome" in windows:
                wid = findWid()
                if wid:
                    try:
                        subprocess.Popen(['wmctrl', '-i', '-a', wid])
                    except (OSError, subprocess.CalledProcessError):
                        try:
                            subprocess.Popen(['xdotool', 'windowactivate', wid])
                        except (OSError, subprocess.CalledProcessError):
                            xbmc.log("Please install wmctrl or xdotool")
                    break
                xbmc.sleep(500)
        except (OSError, subprocess.CalledProcessError):
            pass

    elif osOsx:
        timeout = time.time() + 10
        while time.time() < timeout:
            xbmc.sleep(500)
            applescript_switch_chrome = """tell application "System Events"
                    set frontmost of the first process whose unix id is %d to true
                end tell""" % pid
            try:
                subprocess.Popen(['osascript', '-e', applescript_switch_chrome])
                break
            except subprocess.CalledProcessError:
                pass
    elif osWin:
        # TODO: find out if this is needed, and if so how to implement
        pass


def showSite(url, stopPlayback, kiosk, userAgent):
    creationFlags = 0
    if osWin:
        creationFlags = 0x00000008 # DETACHED_PROCESS https://msdn.microsoft.com/en-us/library/windows/desktop/ms684863(v=vs.85).aspx

    if stopPlayback == "yes":
        xbmc.Player().stop()

    if osAndroid:
        openAndroidBrowser(url)
    else:
        params = getFullPath(exePath, url, kiosk, userAgent)
        s = subprocess.Popen(params, shell=False, creationflags=creationFlags, close_fds = True)
        s.communicate()

        bringChromeToFront(s.pid)

        xbmcplugin.endOfDirectory(pluginhandle)
        xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % ("plugin://"+addonID+"/"))


def removeSite(title):
    os.remove(os.path.join(siteFolder, getFileName(title)+".link"))
    xbmc.executebuiltin("Container.Refresh")


def editSite(title):
    filenameOld = getFileName(title)
    file = os.path.join(siteFolder, filenameOld+".link")
    with open(file, 'r') as fh:
        title = ""
        url = ""
        kiosk = "yes"
        thumb = "DefaultFolder.png"
        stopPlayback = "no"
        for line in fh.readlines():
            entry = line[:line.find("=")]
            content = line[line.find("=")+1:]
            if entry == "title":
                title = content.strip()
            elif entry == "url":
                url = content.strip()
            elif entry == "kiosk":
                kiosk = content.strip()
            elif entry == "thumb":
                thumb = content.strip()
            elif entry == "stopPlayback":
                stopPlayback = content.strip()

    oldTitle = title
    keyboard = xbmc.Keyboard(title, translation(30003))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        title = keyboard.getText()
        keyboard = xbmc.Keyboard(url, translation(30004))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            url = keyboard.getText()
            keyboard = xbmc.Keyboard(stopPlayback, translation(30009))
            keyboard.doModal()
            if keyboard.isConfirmed() and keyboard.getText():
                stopPlayback = keyboard.getText()
                keyboard = xbmc.Keyboard(kiosk, translation(30016))
                keyboard.doModal()
                if keyboard.isConfirmed() and keyboard.getText():
                    kiosk = keyboard.getText()
                    content = "title="+title+"\nurl="+url+"\nthumb="+thumb+"\nstopPlayback="+stopPlayback+"\nkiosk="+kiosk
                    with open(os.path.join(siteFolder, getFileName(title)+".link"), 'w') as fh:
                        fh.write(content)

                    if title != oldTitle:
                        os.remove(os.path.join(siteFolder, filenameOld+".link"))
    xbmc.executebuiltin("Container.Refresh")


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addDir(name, url, mode, iconimage, stopPlayback="", kiosk=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)+"&stopPlayback="+urllib.quote_plus(stopPlayback)+"&kiosk="+urllib.quote_plus(kiosk)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addSiteDir(name, url, mode, iconimage, stopPlayback, kiosk):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+urllib.quote_plus(mode)+"&stopPlayback="+urllib.quote_plus(stopPlayback)+"&kiosk="+urllib.quote_plus(kiosk)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})

    liz.addContextMenuItems([(translation(30006), 'RunPlugin(plugin://'+addonID+'/?mode=editSite&url='+urllib.quote_plus(name)+')',), (translation(30002), 'RunPlugin(plugin://'+addonID+'/?mode=removeSite&url='+urllib.quote_plus(name)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
name = urllib.unquote_plus(params.get('name', ''))
url = urllib.unquote_plus(params.get('url', ''))
stopPlayback = urllib.unquote_plus(params.get('stopPlayback', 'no'))
kiosk = urllib.unquote_plus(params.get('kiosk', 'yes'))
userAgent = urllib.unquote_plus(params.get('userAgent', ''))


if mode == 'addSite':
    addSite()
elif mode == 'showSite':
    showSite(url, stopPlayback, kiosk, userAgent)
elif mode == 'removeSite':
    removeSite(url)
elif mode == 'editSite':
    editSite(url)
else:
    index()

import re
import os
import sys
import time
import datetime
import threading
import json

# Elisa session
elisa = None

# Enable Eclipse debugger
REMOTE_DBG = False

# append pydev remote debugger
if REMOTE_DBG:
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
        # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " +
                         "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        sys.exit(1)

try:
    import xbmc
    import xbmcplugin
    import xbmcgui
    import xbmcaddon
    import elisaviihde
    __settings__ = xbmcaddon.Addon(id='plugin.video.elisa.viihde')
    __language__ = __settings__.getLocalizedString
    weekdays = {0: __language__(30006), 1: __language__(30007), 2: __language__(30008),
                3: __language__(30009), 4: __language__(30010), 5: __language__(30011),
                6: __language__(30012)}
except ImportError as err:
    sys.stderr.write(str(err))

# Init Elisa
elisa = elisaviihde.elisaviihde(False)

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

def create_name(prog_data):
    time_raw = prog_data["startTimeUTC"]/1000
    parsed_time = datetime.datetime.fromtimestamp(time_raw).strftime("%d.%m.%Y %H:%M:%S")
    weekday_number = int(datetime.datetime.fromtimestamp(time_raw).strftime("%w"))
    prog_date = datetime.date.fromtimestamp(time_raw)
    today = datetime.date.today()
    diff = today - prog_date
    if diff.days == 0:
        date_name = __language__(30013) + " " + datetime.datetime.fromtimestamp(time_raw).strftime("%H:%M")
    elif diff.days == 1:
        date_name = __language__(30014) + " " + datetime.datetime.fromtimestamp(time_raw).strftime("%H:%M")
    else:
        date_name = str(weekdays[weekday_number]) + " " + datetime.datetime.fromtimestamp(time_raw).strftime("%d.%m.%Y %H:%M")
    return prog_data['name'] + " (" + prog_data['serviceName'] + ", " + date_name + ")"

def show_dir(dirid=0):
    # List folders
    for row in elisa.getfolders(dirid):
        add_dir_link(row['name'] + "/", row['id'])
    
    data = elisa.getrecordings(dirid)
    totalItems = len(data)
    
    # List recordings
    for row in data:
        name = create_name(row)
        add_watch_link(name,
                       row['programId'],
                       totalItems,
                       kwargs = {
                         "title": name,
                         "date": datetime.datetime.fromtimestamp(row["startTimeUTC"]/1000).strftime("%d.%m.%Y"),
                         "duration": ((row["endTimeUTC"]/1000/60) - (row["startTimeUTC"]/1000/60)),
                         "plotoutline": (row['description'] if "description" in row else "N/a").encode('utf8'),
                         "playcount": (1 if row['isWatched'] else 0),
                         "iconimage": (row['thumbnail'] if "thumbnail" in row else "DefaultVideo.png")
                       })

def add_dir_link(name, dirid):
    u = sys.argv[0] + "?dirid=" + str(dirid)
    liz = xbmcgui.ListItem(label=name, iconImage="DefaultFolder.png")
    liz.setInfo('video', {"Title": name})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return liz

def add_watch_link(name, progid, totalItems=None, kwargs={}):
    u = sys.argv[0] + "?progid=" + str(progid) + "&watch=" + json.dumps(kwargs).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    liz = xbmcgui.ListItem(name, iconImage=kwargs["iconimage"])
    liz.setInfo('video', kwargs)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, totalItems=totalItems)
    return liz

def watch_program(progid=0, watch=""):
    url = elisa.getstreamuri(progid)
    kwargs = json.loads(watch.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>'))
    listitem = xbmcgui.ListItem(kwargs["title"])
    listitem.setInfo('video', kwargs)
    xbmc.Player().play(url, listitem)
    return True

def mainloop():
    try:
        elisa.setsession(json.loads(__settings__.getSetting("session")))
    except ValueError as ve:
        __settings__.setSetting("session", "{}")
    
    if not elisa.islogged():
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('XBMC', __language__(30003), __language__(30004))
        if ok == True:
            __settings__.openSettings(url=sys.argv[0])
            
        username = __settings__.getSetting("username")
        password = __settings__.getSetting("password")
        elisa.login(username, password)
        __settings__.setSetting("session", json.dumps(elisa.getsession()))
    
    params = get_params()
    
    dirid = None
    progid = None
    watch = None
    
    try:
        dirid = int(params["dirid"])
    except:
        pass

    try:
        progid = int(params["progid"])
    except:
        pass

    try:
        watch = str(params["watch"])
    except:
        pass

    if dirid == None and progid == None:
        show_dir(0)
    elif progid == None and dirid != None:
        show_dir(dirid)
    elif watch != None and progid != None:
        watch_program(progid, watch)
    else:
        show_dir(0)

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

if __name__ == '__main__':
    mainloop()

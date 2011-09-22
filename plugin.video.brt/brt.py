# coding=utf-8
#
# <BestRussianTV plugin for XBMC>
# Copyright (C) <2011>  <BestRussianTV>
#
#       This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import sys, datetime
import xbmc, xbmcgui, xbmcplugin, urllib
import config, livetv, archive, radio, asx, vod, checkuser

try:
    # new XBMC 10.05 addons:
    import xbmcaddon
except ImportError:
    # old XBMC - create fake xbmcaddon module with same interface as new XBMC 10.05
    class xbmcaddon:
        """ fake xbmcaddon module """
        __version__ = "(old XBMC)"
        class Addon:
            """ fake xbmcaddon.Addon class """
            def __init__(self, id):
                self.id = id

            def getSetting(self, key):
                return xbmcplugin.getSetting(key)

            def openSettings(self):
                xbmc.openSettings()

addon = xbmcaddon.Addon("plugin.video.brt")

for n in range(1, 3):
    Username = addon.getSetting("username")
    Password = addon.getSetting("password")

    if not checkuser.validateLogin(Username, Password):
        addon.openSettings()
    else:
        break

def addItem(name, mode, isFolder, id = "", date = "", icon = "", stream = "", description = "", rating = 0, duration = 0):
    url = sys.argv[0] + "?mode=" + mode + "&name=" + urllib.quote_plus(name) + \
    "&id=" + id + "&date=" + date + "&stream=" + urllib.quote_plus(stream) + \
    "&icon=" + urllib.quote_plus(icon)
    
    if icon != "" and icon != None:
        liz = xbmcgui.ListItem(name, thumbnailImage = icon)
    elif isFolder:
        liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png")
    else:
        liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png")

    liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "Rating": rating, "Duration": str(duration) })
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = url, listitem = liz, isFolder = isFolder)

def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?','')
        if (params[len(params)-1] == '/'):
            params = params[0:len(params)-2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param

params = get_params()
name = None
mode = None
id = None
stream = None
icon = None

try:    name = urllib.unquote_plus(params["name"])
except: pass
try:    mode = params["mode"]
except: pass
try:    id = params["id"]
except: pass
try:    date = params["date"]
except: pass
try:    stream = urllib.unquote_plus(params["stream"])
except: pass
try:    icon = urllib.unquote_plus(params["icon"])
except: pass

daysofweek = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

if mode == None:
    addItem("Прямой эфир", "live", True, "")
    addItem("Архив", "archive", True, "")
    addItem("Видеотека", "vod", True, "")
    addItem("Радио", "radio", True, "")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "live":
    lc = livetv.GetChannels(Username, Password)
    for channel in lc.Request():
        #icon = "http://iptv-distribution.net/includes/image_channel.ashx?itemid=" + channel[1] + "&icontype=100"
        icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + channel[1] + "&t=10"
        addItem(channel[0], "livechannel", False, channel[1], "", icon)
        # icon URLs returned by the service, don't work
        #addItem(channel[0], "livechannel", False, channel[1], "", channel[2])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "livechannel":
    lc = livetv.GetLiveStream(Username, Password, id)
    streamUrl = lc.Request()
    print "Playing: " + streamUrl
    liz = xbmcgui.ListItem(name, thumbnailImage = "DefaultVideo.png")
    liz.setInfo(type="Video", infoLabels={ "Title": name[4:] })
    xbmc.Player().play(streamUrl, liz)

elif mode == "archive":
    lc = archive.GetChannels(Username, Password)
    for channel in lc.Request():
        addItem(channel[0], "archchannel", True, channel[1], "", channel[2])
        #print "Icon: " + channel[2]
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "archchannel":
    for d in range(0, 14):
        dt = datetime.date.today() - datetime.timedelta(days = d)
        addItem(dt.strftime("%Y-%m-%d, ") + daysofweek[dt.weekday()], "archprograms", True, id, str(dt))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "archprograms":
    lc = archive.GetPVREPG(Username, Password, id, date)
    for prog in lc.Request():
        addItem(prog[0], "archplay", False, prog[1], prog[2])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "archplay":
    if False:
        # this is not working properly, no idea how to figure out
        # the multiple stream URLs: multiple programs in the same day
        # seem to result in the same list of streams returned by the server
        lc = archive.GetPvrPlaylist(Username, Password, id)
        streamUrl = lc.Request()
        print "Playing: " + streamUrl
        liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png")
        liz.setInfo(type="Video", infoLabels={ "Title": name[6:] })

        if True or streamUrl.startswith('http://'):
            ap = asx.Parser()
            pl = xbmc.PlayList(1)
            pl.clear()
            for stream in ap.parseString(streamUrl):
                print "Queueing " + stream
                pl.add(stream, liz)
            xbmc.Player().play(pl, liz)
        else:
            xbmc.Player().play(streamUrl, liz)
    else:
        lc = archive.GetArchStream(Username, Password, id)
        streamUrl = lc.Request()
        print "Playing: " + streamUrl
        liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png")
        liz.setInfo(type="Video", infoLabels={ "Title": name[6:] })

        xbmc.Player().play(streamUrl, liz)
    

elif mode == "radio":
    lc = radio.GetRadioStationListByUser(Username)
    for prog in lc.Request():
        addItem(prog[0], "radioplay", False, prog[1], "", prog[2], prog[3])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "radioplay":
    print "Playing: " + stream
    if icon == "" or icon == None:
        icon = "DefaultAudio.png"
    liz = xbmcgui.ListItem(name, iconImage = icon)
    liz.setInfo(type="Audio", infoLabels={ "Title": name[4:] })

    if stream.startswith('http://'):
        ap = asx.Parser()
        stream = ap.parseUrl(stream)[0]
    xbmc.Player().play(stream, liz)

elif mode == "vod":
    addItem("Добавления за неделю", "vodlastweek", True, "")
    addItem("Жанры", "vodgenres", True, "")
    addItem("Поступления", "vodnewest", True, "")
    addItem("Топ 100", "vodtop100", True, "")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "vodlastweek":
    addItem("1 день назад", "vodbyday", True, "1")
    addItem("2 дня назад", "vodbyday", True, "2")
    addItem("3 дня назад", "vodbyday", True, "3")
    addItem("4 дня назад", "vodbyday", True, "4")
    addItem("5 дней назад", "vodbyday", True, "5")
    addItem("6 дней назад", "vodbyday", True, "6")
    addItem("7 дней назад", "vodbyday", True, "7")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "vodbyday":
    lc = vod.GetVODAddedLastWeekByUser(Username, Password, id)
    for prog in lc.Request():
        #icon = prog[3]
        #if icon == "" or icon == None:
        #    icon = "DefaultVideo.png"
        icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1], "", icon, "", prog[2])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "vodplay":
    lc = vod.GetVODStreamURL(Username, Password, id)
    streamUrl = lc.Request()
    print "Playing: " + streamUrl
    icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + id + "&t=1"
    liz = xbmcgui.ListItem(name, thumbnailImage = icon)
    liz.setInfo(type="Video", infoLabels={ "Title": name })
    xbmc.Player().play(streamUrl, liz)

elif mode == "vodgenres":
    lc = vod.GetVODGenresByUser(Username)
    for genre in lc.Request():
        addItem(genre[0], "vodsubgenres", True, genre[1])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "vodsubgenres":
    lc = vod.GetVODSubGenres(id)
    for genre in lc.Request():
        addItem(genre[0], "vodsubgenres", True, genre[1])
    lc = vod.GetVODMoviesBySubGenreUser(Username, Password, id)
    for prog in lc.Request():
        icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        if prog[3] > 1:
            addItem(prog[0], "vodseries", True, prog[1], "", icon, "", prog[2])
        else:
            addItem(prog[0], "vodplay", False, prog[1], "", icon, "", prog[2], prog[3], prog[4])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "vodseries":
    lc = vod.GetVODSeries(Username, Password, id)
    for prog in lc.Request():
        icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1], "", icon, "", prog[2])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
elif mode == "vodnewest":
    lc = vod.GetVODMoviesNewInVODByUser(Username, Password)
    for prog in lc.Request():
        icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1], "", icon, "", prog[2])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode == "vodtop100":
    lc = vod.GetVODMoviesTOP100ByUser(Username, Password)
    for prog in lc.Request():
        icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1], "", icon, "", prog[2])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))











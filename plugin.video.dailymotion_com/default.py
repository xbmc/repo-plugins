#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import xbmcplugin
import xbmcaddon
import xbmcgui
import sys
import os
import re
import base64
import datetime

familyFilter = "1"
socket.setdefaulttimeout(60)
pluginhandle = int(sys.argv[1])
addonID = 'plugin.video.dailymotion_com'
addon = xbmcaddon.Addon(addonID)
translation = addon.getLocalizedString
channelFavsFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")
familyFilterFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/family_filter_off")

if os.path.exists(familyFilterFile):
    familyFilter = "0"

while (not os.path.exists(xbmc.translatePath("special://profile/addon_data/"+addonID+"/settings.xml"))):
    addon.openSettings()

forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
maxVideoQuality = addon.getSetting("maxVideoQuality")
qual = ["480p", "720p", "1080p"]
maxVideoQuality = qual[int(maxVideoQuality)]
language = addon.getSetting("language")
languages = ["en_EN", "ar_ES", "au_EN", "be_FR", "be_NL", "br_PT", "ca_EN", "ca_FR", "de_DE", "es_ES", "es_CA", "gr_EL", "fr_FR", "in_EN", "ie_EN", "it_IT", "mx_ES", "ma_FR", "nl_NL", "at_DE", "pl_PL", "pt_PT", "ru_RU", "ro_RO", "ch_FR", "ch_DE", "ch_IT", "tn_FR", "tr_TR", "en_GB", "en_US", "vn_VI", "jp_JP", "cn_ZH"]
language = languages[int(language)]
dmUser = addon.getSetting("dmUser")
itemsPerPage = addon.getSetting("itemsPerPage")
itemsPage = ["25", "50", "75", "100"]
itemsPerPage = itemsPage[int(itemsPerPage)]


def index():
    if dmUser:
        addDir(translation(30034), "", "personalMain", "")
    else:
        addFavDir(translation(30024), "", "favouriteUsers", "")
    addDir(translation(30006), "", 'listChannels', "")
    addDir(translation(30007), "", 'sortUsers1', "")
    addDir(translation(30042), "ALL", 'listGroups', "")
    addDir(translation(30002), "", 'search', "")
    addDir(translation(30003), "", 'listLive', "")
    addDir(translation(30039), '3D:ALL', 'sortVideos1', '', '')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def personalMain():
    addDir(translation(30041), "https://api.dailymotion.com/user/"+dmUser+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listVideos', "")
    addDir(translation(30035), "https://api.dailymotion.com/user/"+dmUser+"/following?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listUsers', "")
    addDir(translation(30036), "https://api.dailymotion.com/user/"+dmUser+"/subscriptions?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listVideos', "")
    addDir(translation(30037), "https://api.dailymotion.com/user/"+dmUser+"/favorites?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listVideos', "")
    addDir(translation(30038), "https://api.dailymotion.com/user/"+dmUser+"/playlists?fields=id,name,videos_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listUserPlaylists', "")
    addDir(translation(30042), "https://api.dailymotion.com/user/"+dmUser+"/groups?fields=id,name,description&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1", 'listGroups', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listUserPlaylists(url):
    content = getUrl(url)
    match = re.compile('{"id":"(.+?)","name":"(.+?)","videos_total":(.+?)}', re.DOTALL).findall(content)
    for id, title, vids in match:
        addDir(title+" ("+vids+")", urllib.quote_plus(id+"_"+dmUser+"_"+title), 'showPlaylist', '')
    match = re.compile('"page":(.+?),', re.DOTALL).findall(content)
    currentPage = int(match[0])
    nextPage = currentPage+1
    if '"has_more":true' in content:
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listUserPlaylists', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listGroups(url):
    if url == "ALL":
        url = "https://api.dailymotion.com/groups?fields=id,name,description&sort=recent&filters=featured&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    content = getUrl(url)
    match = re.compile('{"id":"(.+?)","name":"(.+?)","description":(.+?)}', re.DOTALL).findall(content)
    for id, title, desc in match:
        addDir(cleanTitle(title), "group:"+id, 'sortVideos1', '', desc)
    match = re.compile('"page":(.+?),', re.DOTALL).findall(content)
    currentPage = int(match[0])
    nextPage = currentPage+1
    if '"has_more":true' in content:
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listGroups', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def showPlaylist(id):
    url = "https://api.dailymotion.com/playlist/"+id+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    listVideos(url)


def favouriteUsers():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if os.path.exists(channelFavsFile):
        fh = open(channelFavsFile, 'r')
        content = fh.read()
        match = re.compile('###USER###=(.+?)###THUMB###=(.*?)###END###', re.DOTALL).findall(content)
        for user, thumb in match:
            addUserFavDir(user, 'owner:'+user, 'sortVideos1', thumb)
        fh.close()
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listChannels():
    content = getUrl("https://api.dailymotion.com/channels?family_filter="+familyFilter+"&localization="+language)
    match = re.compile('{"id":"(.+?)","name":"(.+?)","description":"(.+?)"}', re.DOTALL).findall(content)
    for id, title, desc in match:
        addDir(title, 'channel:'+id, 'sortVideos1', '', desc)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def sortVideos1(url):
    type = url[:url.find(":")]
    id = url[url.find(":")+1:]
    if type == "3D":
        url = "https://api.dailymotion.com/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&filters=3d&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    elif type == "group":
        url = "https://api.dailymotion.com/group/"+id+"/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    else:
        url = "https://api.dailymotion.com/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&"+type+"="+id+"&sort=recent&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    addDir(translation(30008), url, 'listVideos', "")
    addDir(translation(30009), url.replace("sort=recent", "sort=visited"), 'sortVideos2', "")
    addDir(translation(30020), url.replace("sort=recent", "sort=commented"), 'sortVideos2', "")
    addDir(translation(30010), url.replace("sort=recent", "sort=rated"), 'sortVideos2', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def sortVideos2(url):
    addDir(translation(30011), url.replace("sort=visited", "sort=visited-today").replace("sort=commented", "sort=commented-today").replace("sort=rated", "sort=rated-today"), "listVideos", "")
    addDir(translation(30012), url.replace("sort=visited", "sort=visited-week").replace("sort=commented", "sort=commented-week").replace("sort=rated", "sort=rated-week"), "listVideos", "")
    addDir(translation(30013), url.replace("sort=visited", "sort=visited-month").replace("sort=commented", "sort=commented-month").replace("sort=rated", "sort=rated-month"), "listVideos", "")
    addDir(translation(30014), url, 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def sortUsers1():
    url = "https://api.dailymotion.com/users?fields=username,avatar_large_url,videos_total,views_total&sort=popular&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1"
    addDir(translation(30040), url, 'sortUsers2', "")
    addDir(translation(30016), url+"&filters=featured", 'sortUsers2', "")
    addDir(translation(30017), url+"&filters=official", 'sortUsers2', "")
    addDir(translation(30018), url+"&filters=creative", 'sortUsers2', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def sortUsers2(url):
    addDir(translation(30019), url, 'listUsers', "")
    addDir(translation(30020), url.replace("sort=popular", "sort=commented"), 'listUsers', "")
    addDir(translation(30021), url.replace("sort=popular", "sort=rated"), 'listUsers', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listVideos(url):
    content = getUrl(url)
    match = re.compile('{"description":"(.*?)","duration":(.+?),"id":"(.+?)","owner.username":"(.+?)","taken_time":(.+?),"thumbnail_large_url":"(.*?)","title":"(.+?)","views_total":(.+?)}', re.DOTALL).findall(content)
    for desc, duration, id, user, date, thumb, title, views in match:
        duration = str(int(duration)/60+1)
        try:
            date = datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d')
        except:
            date = ""
        desc = "User: "+user+"  |  "+views+" Views  |  "+date+"\n"+desc
        if user == "hulu":
            pass
        elif user == "cracklemovies":
            pass
        elif user == "ARTEplus7":
            addLink(cleanTitle(title), id, 'playArte', thumb.replace("\\", ""), user, desc, duration)
        else:
            addLink(cleanTitle(title), id, 'playVideo', thumb.replace("\\", ""), user, desc, duration)
    match = re.compile('"page":(.+?),', re.DOTALL).findall(content)
    currentPage = int(match[0])
    nextPage = currentPage+1
    if '"has_more":true' in content:
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listUsers(url):
    content = getUrl(url)
    match = re.compile('{"username":"(.+?)","avatar_large_url":"(.*?)","videos_total":(.+?),"views_total":(.+?)}', re.DOTALL).findall(content)
    for user, thumb, videos, views in match:
        addUserDir(cleanTitle(user), 'owner:'+user, 'sortVideos1', thumb.replace("\\", ""), "Views: "+views+"\nVideos: "+videos)
    match = re.compile('"page":(.+?),', re.DOTALL).findall(content)
    currentPage = int(match[0])
    nextPage = currentPage+1
    if '"has_more":true' in content:
        addDir(translation(30001)+" ("+str(nextPage)+")", url.replace("page="+str(currentPage), "page="+str(nextPage)), 'listUsers', "")
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def listLive():
    content = getUrl("https://api.dailymotion.com/videos?fields=id,thumbnail_large_url%2Ctitle%2Cviews_last_hour&filters=live&sort=visited-hour&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language)
    match = re.compile('\\{"id":"(.+?)","thumbnail_large_url":"(.+?)","title":"(.+?)","views_last_hour":(.+?)\\}', re.DOTALL).findall(content)
    for id, thumb, title, views in match:
        addLiveLink(cleanTitle(title), id, 'playLiveVideo', thumb.replace("\\", ""), views)
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def search():
    keyboard = xbmc.Keyboard('', translation(30002))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos("https://api.dailymotion.com/videos?fields=description,duration,id,owner.username,taken_time,thumbnail_large_url,title,views_total&search="+search_string+"&sort=relevance&limit="+itemsPerPage+"&family_filter="+familyFilter+"&localization="+language+"&page=1")


def playVideo(id):
    listitem = xbmcgui.ListItem(path=getStreamUrl(id))
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def getStreamUrl(id):
    content = getUrl2("http://www.dailymotion.com/embed/video/"+id)
    if content.find('"statusCode":410') > 0 or content.find('"statusCode":403') > 0:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30022))+' (DailyMotion)!,5000)')
        return ""
    else:
        matchFullHD = re.compile('"stream_h264_hd1080_url":"(.+?)"', re.DOTALL).findall(content)
        matchHD = re.compile('"stream_h264_hd_url":"(.+?)"', re.DOTALL).findall(content)
        matchHQ = re.compile('"stream_h264_hq_url":"(.+?)"', re.DOTALL).findall(content)
        matchSD = re.compile('"stream_h264_url":"(.+?)"', re.DOTALL).findall(content)
        matchLD = re.compile('"stream_h264_ld_url":"(.+?)"', re.DOTALL).findall(content)
        url = ""
        if matchFullHD and maxVideoQuality == "1080p":
            url = urllib.unquote_plus(matchFullHD[0]).replace("\\", "")
        elif matchHD and (maxVideoQuality == "720p" or maxVideoQuality == "1080p"):
            url = urllib.unquote_plus(matchHD[0]).replace("\\", "")
        elif matchHQ:
            url = urllib.unquote_plus(matchHQ[0]).replace("\\", "")
        elif matchSD:
            url = urllib.unquote_plus(matchSD[0]).replace("\\", "")
        elif matchLD:
            url = urllib.unquote_plus(matchSD2[0]).replace("\\", "")
        return url


def playLiveVideo(id):
    content = getUrl2("http://www.dailymotion.com/sequence/"+id)
    if content.find('"statusCode":410') > 0 or content.find('"statusCode":403') > 0:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30022))+' (DailyMotion)!,5000)')
    else:
        matchFullHD = re.compile('"hd1080URL":"(.+?)"', re.DOTALL).findall(content)
        matchHD = re.compile('"hd720URL":"(.+?)"', re.DOTALL).findall(content)
        matchHQ = re.compile('"hqURL":"(.+?)"', re.DOTALL).findall(content)
        matchSD = re.compile('"sdURL":"(.+?)"', re.DOTALL).findall(content)
        matchLD = re.compile('"video_url":"(.+?)"', re.DOTALL).findall(content)
        url = ""
        if matchFullHD and maxVideoQuality == "1080p":
            url = urllib.unquote_plus(matchFullHD[0]).replace("\\", "")
        elif matchHD and (maxVideoQuality == "720p" or maxVideoQuality == "1080p"):
            url = urllib.unquote_plus(matchHD[0]).replace("\\", "")
        elif matchHQ:
            url = urllib.unquote_plus(matchHQ[0]).replace("\\", "")
        elif matchSD:
            url = urllib.unquote_plus(matchSD[0]).replace("\\", "")
        elif matchLD:
            url = urllib.unquote_plus(matchSD2[0]).replace("\\", "")
        if url:
            url = getUrl(url)
            listitem = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def playArte(id):
    try:
        content = getUrl("http://www.dailymotion.com/video/"+id)
        match = re.compile('<a class="link" href="http://videos.arte.tv/(.+?)/videos/(.+?).html">', re.DOTALL).findall(content)
        lang = match[0][0]
        vid = match[0][1]
        url = "http://videos.arte.tv/"+lang+"/do_delegate/videos/"+vid+",view,asPlayerXml.xml"
        content = getUrl(url)
        match = re.compile('<video lang="'+lang+'" ref="(.+?)"', re.DOTALL).findall(content)
        url = match[0]
        content = getUrl(url)
        match1 = re.compile('<url quality="hd">(.+?)</url>', re.DOTALL).findall(content)
        match2 = re.compile('<url quality="sd">(.+?)</url>', re.DOTALL).findall(content)
        urlNew = ""
        if match1:
            urlNew = match1[0]
        elif match2:
            urlNew = match2[0]
        urlNew = urlNew.replace("MP4:", "mp4:")
        base = urlNew[:urlNew.find("mp4:")]
        playpath = urlNew[urlNew.find("mp4:"):]
        listitem = xbmcgui.ListItem(path=base+" playpath="+playpath+" swfVfy=1 swfUrl=http://videos.arte.tv/blob/web/i18n/view/player_24-3188338-data-5168030.swf")
        xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
    except:
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30022))+' (Arte)!,5000)')


def addFav():
    keyboard = xbmc.Keyboard('', translation(30033))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        user = keyboard.getText()
        channelEntry = "###USER###="+user+"###THUMB###=###END###"
        if os.path.exists(channelFavsFile):
            fh = open(channelFavsFile, 'r')
            content = fh.read()
            fh.close()
            if content.find(channelEntry) == -1:
                fh = open(channelFavsFile, 'a')
                fh.write(channelEntry+"\n")
                fh.close()
        else:
            fh = open(channelFavsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30030))+'!,5000)')


def favourites(param):
    mode = param[param.find("###MODE###=")+11:]
    mode = mode[:mode.find("###")]
    channelEntry = param[param.find("###USER###="):]
    if mode == "ADD":
        if os.path.exists(channelFavsFile):
            fh = open(channelFavsFile, 'r')
            content = fh.read()
            fh.close()
            if content.find(channelEntry) == -1:
                fh = open(channelFavsFile, 'a')
                fh.write(channelEntry+"\n")
                fh.close()
        else:
            fh = open(channelFavsFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
        xbmc.executebuiltin('XBMC.Notification(Info:,'+str(translation(30030))+'!,5000)')
    elif mode == "REMOVE":
        refresh = param[param.find("###REFRESH###=")+14:]
        refresh = refresh[:refresh.find("###USER###=")]
        fh = open(channelFavsFile, 'r')
        content = fh.read()
        fh.close()
        entry = content[content.find(channelEntry):]
        fh = open(channelFavsFile, 'w')
        fh.write(content.replace(channelEntry+"\n", ""))
        fh.close()
        if refresh == "TRUE":
            xbmc.executebuiltin("Container.Refresh")


def cleanTitle(title):
    #test = u"\u00a1\u00a1\u00a1\u00a1\u00a1".encode('utf8')
    #title = unicode(title)
    #title = u"%s" % (title)
    #title = title.encode('utf-8')
    title = decodeUnicode(title)
    title = title.replace("\\", "").strip()
    return title


def decodeUnicode(content):
    uc = {"\u00a0": " ", "\u00a1": "¡", "\u00a2": "¢", "\u00a3": "£", "\u00a4": "¤", "\u00a5": "¥", "\u00a6": "¦", "\u00a7": "§", "\u00a9": "©", "\u00aa": "ª", "\u00ab": "«", "\u00ac": "¬", "\u00ae": "®", "\u00b0": "°", "\u00b1": "±", "\u00b2": "²", "\u00b3": "³", "\u00b5": "µ", "\u00b6": "¶", "\u00b7": "·", "\u00b8": "¸", "\u00b9": "¹", "\u00ba": "º", "\u00bb": "»", "\u00bc": "¼", "\u00bd": "½", "\u00be": "¾", "\u00bf": "¿", "\u00c0": "À", "\u00c1": "Á", "\u00c2": "Â", "\u00c3": "Ã", "\u00c4": "Ä", "\u00c5": "Å", "\u00c6": "Æ", "\u00c7": "Ç", "\u00c8": "È", "\u00c9": "É", "\u00ca": "Ê", "\u00cb": "Ë", "\u00cc": "Ì", "\u00cd": "Í", "\u00ce": "Î", "\u00cf": "Ï", "\u00d0": "Ð", "\u00d1": "Ñ", "\u00d2": "Ò", "\u00d3": "Ó", "\u00d4": "Ô", "\u00d5": "Õ", "\u00d6": "Ö", "\u00d7": "×", "\u00d8": "Ø", "\u00d9": "Ù", "\u00da": "Ú", "\u00db": "Û", "\u00dc": "Ü", "\u00dd": "Ý", "\u00de": "Þ", "\u00df": "ß", "\u00e0": "à", "\u00e1": "á", "\u00e2": "â", "\u00e3": "ã", "\u00e4": "ä", "\u00e5": "å", "\u00e6": "æ", "\u00e7": "ç", "\u00e8": "è", "\u00e9": "é", "\u00ea": "ê", "\u00eb": "ë", "\u00ec": "ì", "\u00ed": "í", "\u00ee": "î", "\u00ef": "ï", "\u00f0": "ð", "\u00f1": "ñ", "\u00f2": "ò", "\u00f3": "ó", "\u00f4": "ô", "\u00f5": "õ", "\u00f6": "ö", "\u00f7": "÷", "\u00f8": "ø", "\u00f9": "ù", "\u00fa": "ú", "\u00fb": "û", "\u00fc": "ü", "\u00fd": "ý", "\u00fe": "þ", "\u00ff": "ÿ", "\u0100": "Ā", "\u0101": "ā", "\u0102": "Ă", "\u0103": "ă", "\u0104": "Ą", "\u0105": "ą", "\u0106": "Ć", "\u0107": "ć", "\u0108": "Ĉ", "\u0109": "ĉ", "\u010c": "Č", "\u010d": "č", "\u010e": "Ď", "\u010f": "ď", "\u0110": "Đ", "\u0111": "đ", "\u0112": "Ē", "\u0113": "ē", "\u0114": "Ĕ", "\u0115": "ĕ", "\u0118": "Ę", "\u0119": "ę", "\u011a": "Ě", "\u011b": "ě", "\u011c": "Ĝ", "\u011d": "ĝ", "\u011e": "Ğ", "\u011f": "ğ", "\u0122": "Ģ", "\u0123": "ģ", "\u0124": "Ĥ", "\u0125": "ĥ", "\u0126": "Ħ", "\u0127": "ħ", "\u0128": "Ĩ", "\u0129": "ĩ", "\u012a": "Ī", "\u012b": "ī", "\u012c": "Ĭ", "\u012d": "ĭ", "\u012e": "Į", "\u012f": "į", "\u0131": "ı", "\u0134": "Ĵ", "\u0135": "ĵ", "\u0136": "Ķ", "\u0137": "ķ", "\u0138": "ĸ", "\u0139": "Ĺ", "\u013a": "ĺ", "\u013b": "Ļ", "\u013c": "ļ", "\u013d": "Ľ", "\u013e": "ľ", "\u0141": "Ł", "\u0142": "ł", "\u0143": "Ń", "\u0144": "ń", "\u0145": "Ņ", "\u0146":"ņ","\u0147":"Ň","\u0148":"ň","\u014a":"Ŋ","\u014b":"ŋ","\u014c":"Ō","\u014d":"ō","\u014e":"Ŏ","\u014f":"ŏ","\u0150":"Ő","\u0151":"ő","\u0152":"Œ","\u0153":"œ","\u0154":"Ŕ","\u0155":"ŕ","\u0156":"Ŗ","\u0157":"ŗ","\u0158":"Ř","\u0159":"ř","\u015a":"Ś","\u015b":"ś","\u015c":"Ŝ","\u015d":"ŝ","\u015e":"Ş","\u015f":"ş","\u0160":"Š","\u0161":"š","\u0162":"Ţ","\u0163":"ţ","\u0164":"Ť","\u0165":"ť","\u0166":"Ŧ","\u0167":"ŧ","\u0168":"Ũ","\u0169":"ũ","\u016a":"Ū","\u016b":"ū","\u016c":"Ŭ","\u016d":"ŭ","\u016e":"Ů","\u016f":"ů","\u0170":"Ű","\u0171":"ű","\u0172":"Ų","\u0173":"ų","\u0174":"Ŵ","\u0175":"ŵ","\u0176":"Ŷ","\u0177":"ŷ","\u0178":"Ÿ","\u0179":"Ź","\u017a":"ź","\u017d":"Ž","\u017e":"ž","\u017f":"ſ","\u0180":"ƀ","\u0197":"Ɨ","\u01b5":"Ƶ","\u01b6":"ƶ","\u01cd":"Ǎ","\u01ce":"ǎ","\u01cf":"Ǐ","\u01d0":"ǐ","\u01d1":"Ǒ","\u01d2":"ǒ","\u01d3":"Ǔ","\u01d4":"ǔ","\u01e4":"Ǥ","\u01e5":"ǥ","\u01e6":"Ǧ","\u01e7":"ǧ","\u01e8":"Ǩ","\u01e9":"ǩ","\u01ea":"Ǫ","\u01eb":"ǫ","\u01f0":"ǰ","\u01f4":"Ǵ","\u01f5":"ǵ","\u01f8":"Ǹ","\u01f9":"ǹ","\u021e":"Ȟ","\u021f":"ȟ","\u0228":"Ȩ","\u0229":"ȩ","\u0232":"Ȳ","\u0233":"ȳ","\u0259":"ə","\u0268":"ɨ","\u1e10":"Ḑ","\u1e11":"ḑ","\u1e20":"Ḡ","\u1e21":"ḡ","\u1e26":"Ḧ","\u1e27":"ḧ","\u1e28":"Ḩ","\u1e29":"ḩ","\u1e30":"Ḱ","\u1e31":"ḱ","\u1e3e":"Ḿ","\u1e3f":"ḿ","\u1e54":"Ṕ","\u1e55":"ṕ","\u1e7c":"Ṽ","\u1e7d":"ṽ","\u1e80":"Ẁ","\u1e81":"ẁ","\u1e82":"Ẃ","\u1e83":"ẃ","\u1e84":"Ẅ","\u1e85":"ẅ","\u1e8c":"Ẍ","\u1e8d":"ẍ","\u1e90":"Ẑ","\u1e91":"ẑ","\u1e97":"ẗ","\u1e98":"ẘ","\u1e99":"ẙ","\u1ebc":"Ẽ","\u1ebd":"ẽ","\u1ef2":"Ỳ","\u1ef3":"ỳ","\u1ef8":"Ỹ","\u1ef9":"ỹ","\u2008":" ","\u2013":"–","\u2014":"—","\u2018":"‘","\u2019":"’","\u201a":"‚","\u201c":"“","\u201d":"”","\u201e":"„","\u2030":"‰","\u2039":"‹","\u203a":"›","\u2070":"⁰","\u2071":"ⁱ","\u2074":"⁴","\u2075":"⁵","\u2076":"⁶","\u2077":"⁷","\u2078":"⁸","\u2079":"⁹","\u207a":"⁺","\u207c":"⁼","\u207d":"⁽","\u207e":"⁾","\u207f":"ⁿ","\u2080":"₀","\u2081":"₁","\u2082":"₂","\u2083":"₃","\u2084":"₄","\u2085":"₅","\u2086":"₆","\u2087":"₇","\u2088":"₈","\u2089":"₉","\u208a":"₊","\u208c":"₌","\u208d":"₍","\u208e":"₎","\u20a0":"₠","\u20a1":"₡","\u20a2":"₢","\u20a3":"₣","\u20a4":"₤","\u20a5":"₥","\u20a6":"₦","\u20a7":"₧","\u20a8":"₨","\u20a9":"₩","\u20ab":"₫","\u20ac":"€","\u2120":"℠","\u2122":"™","\u301d":"〝","\u301e":"〞"}
    for key, value in uc.iteritems():
        content = content.replace(key, value)
    return content


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def getUrl2(url):
    if familyFilter == "1":
        ff = "on"
    else:
        ff = "off"
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
    req.add_header('Cookie', "lang="+language+"; family_filter="+ff)
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, user, desc, duration):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Duration": duration})
    liz.setProperty('IsPlayable', 'true')
    entries = []
    if dmUser == "":
        playListInfos = "###MODE###=ADD###USER###="+user+"###THUMB###=DefaultVideo.png###END###"
        entries.append((translation(30028), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',))
    entries.append((translation(30043), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',))
    liz.addContextMenuItems(entries)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addLiveLink(name, url, mode, iconimage, desc):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, desc=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addUserDir(name, url, mode, iconimage, desc):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    if dmUser == "":
        playListInfos = "###MODE###=ADD###USER###="+name+"###THUMB###="+iconimage+"###END###"
        liz.addContextMenuItems([(translation(30028), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addFavDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.addContextMenuItems([(translation(30033), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=addFav)',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addUserFavDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    if dmUser == "":
        playListInfos = "###MODE###=REMOVE###REFRESH###=TRUE###USER###="+name+"###THUMB###="+iconimage+"###END###"
        liz.addContextMenuItems([(translation(30029), 'XBMC.RunPlugin(plugin://plugin.video.dailymotion_com/?mode=favourites&url='+urllib.quote_plus(playListInfos)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listLive':
    listLive()
elif mode == 'listUsers':
    listUsers(url)
elif mode == 'listChannels':
    listChannels()
elif mode == 'listGroups':
    listGroups(url)
elif mode == 'favourites':
    favourites(url)
elif mode == 'addFav':
    addFav()
elif mode == 'personalMain':
    personalMain()
elif mode == 'listPersonalUsers':
    listPersonalUsers()
elif mode == 'favouriteUsers':
    favouriteUsers()
elif mode == 'listUserPlaylists':
    listUserPlaylists(url)
elif mode == 'showPlaylist':
    showPlaylist(url)
elif mode == 'sortVideos1':
    sortVideos1(url)
elif mode == 'sortVideos2':
    sortVideos2(url)
elif mode == 'sortUsers1':
    sortUsers1()
elif mode == 'sortUsers2':
    sortUsers2(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playLiveVideo':
    playLiveVideo(url)
elif mode == 'playArte':
    playArte(url)
elif mode == "queueVideo":
    queueVideo(url, name)
elif mode == 'search':
    search()
else:
    index()

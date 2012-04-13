# coding=utf-8
#
# <BestRussianTV plugin for XBMC>
# Copyright (C) <2012>  <BestRussianTV>
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
# -*- coding: utf-8 -*-
import os
import sys, datetime, time, calendar, thread, threading
import xbmc, xbmcgui, xbmcplugin, urllib
import ClientService, ContentService, MediaService, Content, GetBest, RusKeyboard, ArcSearch, VodSearch
import archive, vod, asx, radio, livetv
from BeautifulSoup import BeautifulSoup

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
            def setSetting(self, key, value):
                return xbmcplugin.setSetting(key, value)

addon = xbmcaddon.Addon("plugin.video.brt")
Username = addon.getSetting("username")
Password = addon.getSetting("password")
iconpath = os.path.join(xbmc.translatePath(addon.getAddonInfo('path')), 'icon')

def addItem(name = '', mode = '', isFolder = False, id='', description = '', icon = '', page = '1', rating = 0, duration = '', year = '', month = '', day = '', date = '', type = '', keyword = '', stream = ''):
    url = sys.argv[0] + '?name=' + urllib.quote_plus(name) + '&mode=' + mode + '&id=' + id + '&page=' + page + '&year=' + year + '&month=' + month + '&day=' + day + '&icon=' + urllib.quote_plus(icon) + '&type=' + type + '&keyword=' + keyword + '&date=' + date + '&stream=' + urllib.quote_plus(stream) 
    if description != '':
        url = url + '&description=' + urllib.quote_plus(description)
    if icon == '':
        if isFolder == True:
            liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png")
        else:
            liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png")
    else:
        liz = xbmcgui.ListItem(name, thumbnailImage = icon)
    liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "Rating": rating, "Duration": duration })
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = url, listitem = liz, isFolder = isFolder)


if addon.getSetting('imageTemp') == '':
    imageUrl = MediaService.MediaImageUrlTemplate()
    addon.setSetting('imageTemp', imageUrl)


def getImage(id, t):
    imageUrl = addon.getSetting('imageTemp')
    imageUrl = imageUrl.replace('{0}',id).replace('{1}',t).replace('&amp;n={2}','').replace('&amp;', '&')
    return imageUrl

def loop(seconds):
    while xbmc.Player().isPlaying()==False:
            time.sleep(1)
    xbmc.Player().seekTime(seconds)
            
    
def SessionID():
    if Username != "" and Password != "":
        try:
            x =  ClientService.Login(Username, Password)
        except:
            xbmcgui.Dialog().ok("BRTV", "Нет соединения с сервером", "")
        
        if x.appSettings.sessionID != "":
            return x.appSettings.sessionID
        else:
            xbmcgui.Dialog().ok("BRTV", "Неверный Логин или Пароль", "")
            addon.openSettings()
            
            xbmc.executebuiltin('XBMC.Resolution(' + addon.getSetting('resolution') + ')')            
            #xbmc.executebuiltin('XBMC.Container.Refresh()') 
            x =  ClientService.Login(addon.getSetting("username"), addon.getSetting("password"))
            if x.appSettings.sessionID !='':
               return x.appSettings.sessionID
            else:
               xbmcgui.Dialog().ok("BRTV", "Неверный Логин или Пароль", "")   
    else:
        xbmcgui.Dialog().ok("BRTV", "Введите Логин и Пароль", "")
        addon.openSettings()            
        xbmc.executebuiltin('XBMC.Resolution(' + addon.getSetting('resolution') + ')')
        xbmc.executebuiltin('XBMC.Container.Refresh()') 
        x =  ClientService.Login(Username, Password)
        return x.appSettings.sessionID   

def GetInHMS(seconds):
    hours = seconds / 3600
    seconds -= 3600*hours
    minutes = seconds / 60
    seconds -= 60*minutes
    ti = "%02d:%02d:%02d" % (hours, minutes, seconds)
    ti = str(ti) 
    return ti

    
def dayweek(y, m, d):
    return datetime.date(y, m, d).weekday()

def timeplay(n):
    if ('.' in  n):
        n = n[:19] 
    t = time.strptime(n, "%Y-%m-%dT%H:%M:%S")
    t = time.strftime("%Y-%m-%d %H:%M", t)   
    return t


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
name = ''
mode = None
id = ''
page = '1'
year = ''
month = ''
day = ''
icon = ''
date = ''
type = ''
keyword = ''
description = ''
stream = ''
#cont = 'false'
try:    name = urllib.unquote_plus(params["name"])
except: pass
try:    description = urllib.unquote_plus(params["description"])
except: pass
try:    stream = urllib.unquote_plus(params["stream"])
except: pass
try:    mode = params["mode"]
except: pass
try:    id = params["id"]
except: pass
try:    page = params['page']
except: pass
try:    year = params['year']
except: pass
try:    month = params['month']
except: pass
try:    day = params['day']
except: pass
try:    date = params['date']
except: pass
try:    type = params['type']
except: pass
try:    keyword = params['keyword']
except: pass
try:    icon = urllib.unquote_plus(params['icon'])
except: pass
#try:    cont = params['cont']
#except: pass



daysofweek = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
months = ["Январь","Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август" ,"Сентябрь" ,"Октябрь" ,"Ноябрь" ,"Декабрь"]
monthday = ["Января","Февраля", "Марта", "Апреля", "Мая", "Июня", "Июля", "Августа" ,"Сентября" ,"Октября" ,"Ноября" ,"Декабря"]

try:
 if mode == None or mode == "":
    list = ""
    #channels = Content.Channels()
    #channels.Invoke(ContentService.GetClientChannel(SessionID(), type = 'LiveTV'))
    #for channel in channels.items:
        #list = list + channel.name + ','
    addon.setSetting('chlist', list)    
    addon.setSetting('imageTemp', '')
    addItem('Прямой эфир', 'LiveTV', True, icon=os.path.join(iconpath, 'icon_tv_live.png'))
    addItem('Архив', 'archive', True, icon=os.path.join(iconpath, 'icon_tv_archive.png'))
    addItem("Видеотека", "vod", True, icon=os.path.join(iconpath, 'icon_movies.png'))
    addItem('Телетека', 'ArcPlus', True, icon=os.path.join(iconpath, 'icon_teleteka.png'))
    addItem("Радио", "radio", True, icon=os.path.join(iconpath, 'icon_radio.png'))
    addItem('Поиск', 'Search', True)#, icon=os.path.join(iconpath, 'icon_tv_live.png'))
    addItem("Настройки", "setting", False, "")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
    
 elif mode == "setting": 
    addon.openSettings()
    ClientService.SetSett(SessionID())
    xbmc.executebuiltin('XBMC.Resolution(' + addon.getSetting('resolution') + ')')

 elif mode == 'LiveTV': 
    #datnow = ContentService.GetUTC()
    #channels = Content.Channels()
    #sessID = SessionID()
    #channels.Invoke(ContentService.GetClientChannel(sessID, type = 'LiveTV', pagItems = '13', pagNum = page))
    channels = livetv.LoadTV(SessionID())
    for channel in channels:
        icon = getImage(channel.id, '4')
        name = channel.name + '  ' + channel.times + '  ' + channel.descr
        addItem(name, 'LiveStream', False, channel.id, channel.descr, icon)   
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode == 'LiveStream':    
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        video = MediaService.GetClientStreamUri(SessionID(), 'LiveTV' ,id)
        if video.startswith('http://'):
            video = urllib.unquote(video)
            video = video.replace('http://','mms://').replace('&amp;','&') + '&MSWMExt=.asf'
        else:
            video = urllib.unquote(video)
            video = video.replace('&amp;','&')
        cat = description.replace('\n', ". ")
        cat = name  + ". " + cat
        icon = getImage(id, '4')
        listitem = xbmcgui.ListItem(cat, thumbnailImage=icon)
        listitem.setInfo('video', {'title' : cat})
        playlist.add(url=video, listitem=listitem, index=7)
        xbmc.Player().play(playlist)
    
 elif mode == 'ArcPlus':
    addon.setSetting("GenreXml","")
    addItem('Каналы', 'ArcPlusCh', True)
    addItem('Жанры', 'ArcPlusGenre', True)
    addItem('Лучшее', 'ArcBest', True)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode == 'ArcPlusCh':
    channels = Content.Channels()
    channels.Invoke(ContentService.GetClientChannel(SessionID(), type = 'ArcPlus',  pagItems = '200', pagNum = '1'))
    for channel in channels.items:
        icon = getImage(channel.id, '4')
        addItem(channel.name, 'ArcTimes', True, channel.id, icon = icon)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    

 elif mode == 'ArcTimes':
    today = datetime.date.today() 
    addItem('Сегодня', 'ArcDay', True, id, icon = icon, year=str(today.year), month=str(today.month), day=str(today.day))
    addItem('За неделю', 'ArcWeek', True, id, icon = icon)
    addItem('За месяц', 'ArcMonth', True, id, icon = icon)
    for i in range(2009, today.year + 1):
        addItem(str(i) + " год", "ArcYear", True, id, "", icon, year=str(i))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == 'ArcWeek':
    today = datetime.date.today()
    for i in range (0, 7):
        day1 = today - datetime.timedelta(days=i)
        daten = daysofweek[dayweek(day1.year, day1.month, day1.day)]
        addItem(daten + ", " + str(day1.day) + " " + monthday[(int(day1.month)-1)], "ArcDay", True, id, "", icon,  year=str(day1.year), month=str(day1.month), day=str(day1.day))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == 'ArcMonth':
    today = datetime.date.today()
    for i in range (0, 30):
        day1 = today - datetime.timedelta(days=i)
        daten = daysofweek[dayweek(day1.year, day1.month, day1.day)]
        addItem(daten + ", " + str(day1.day) + " " + monthday[(int(day1.month)-1)], "ArcDay", True, id, "", icon,  year=str(day1.year), month=str(day1.month), day=str(day1.day))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode ==  'ArcDay':
    date = datetime.date(int(year), int(month), int(day))
    channels = ContentService.Search(SessionID(), "0", page=1, date=date.strftime("%Y-%m-%d"), id=id)
    
    for channel in channels.items:
        icon = getImage(channel.id, '16')
        addItem(channel.name, "ArcPlusPlay", False, channel.id, channel.descr, icon = icon, duration=GetInHMS(int(channel.length)))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
       
    
 elif mode== 'ArcYear':
    today = datetime.date.today()
    if year == str(today.year):
        for i in range(0, today.month):
            addItem(months[i] + ", " + year, "ArcMonth", True, id, "", icon, year=year, month=str(i+1))     
    else:
        for i in range(0,12):
            addItem(months[i] + ", " + year, "ArcMonth", True, id, "", icon, year=year, month=str(i+1))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

    
 elif mode == 'ArcMonth':
    today = datetime.date.today()
    if month == str(today.month):
        if year == str(today.year):
            for i in range(1, today.day + 1):
                daten = daysofweek[dayweek(today.year, today.month, i)]
                year = str(today.year)
                month = str(today.month)
                addItem(daten + ", " + str(i) + " " + monthday[(int(month)-1)], "ArcDay", True, id, "", icon, year=year, month=month, day=str(i))
        else:
            lastday = calendar.monthrange(int(year), int(month))[1]
            for i in range(1, lastday + 1):
                daten = daysofweek[dayweek(int(year), int(month), i)]
                addItem(daten + ", " + str(i) + " " + monthday[(int(month)-1)], "ArcDay", True, id, "", icon, year=year, month=month, day=str(i))
    else:
        lastday = calendar.monthrange(int(year), int(month))[1]
        for i in range(1, lastday + 1):
            daten = daysofweek[dayweek(int(year), int(month), i)]
            addItem(daten + ", " + str(i) + " " + monthday[(int(month)-1)], "ArcDay", True, id, "", icon, year=year, month=month, day=str(i))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode == 'ArcPlusGenre':
    channels = ContentService.GetClientGenres(ContentService.GenreRequest(SessionID(), 0),"0")
    for channel in channels:
            addItem(channel.name, "ArcPlusGenreSub", True, channel.id)       
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode == 'ArcPlusGenreSub':
    channels = ContentService.GetClientGenres(ContentService.GenreRequest(SessionID(), 0), id)
    if len(channels) == 0:
        channels = ContentService.GetClientProgramGuide(SessionID(), id, 0, page=int(page))
        for channel in channels.items:
            icon = getImage(channel.id, '16')
            t = timeplay(channel.startTime)
            
            if channel.cont == 'true':
                addItem(channel.name, "ArcPlusGenreMovie", True, channel.id, channel.descr, icon = icon, page = '1')
            else:
                addItem(t + ' ' + channel.name, "ArcPlusPlay", False, channel.id, channel.descr, icon = icon, duration=GetInHMS(int(channel.length)))
        if channels.tpage > int(page):
            page = str(int(page) + 1)
            addItem("...Следующая страница...","ArcPlusGenreSub",True, id, page=page)
    else: 
        for channel in channels:
            addItem(channel.name, "ArcPlusGenreSub", True, channel.id)       
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


 elif mode == 'ArcPlusGenreMovie':
    channels = ContentService.GetRelProgram(SessionID(), id, page)
    for channel in channels.items:
            t = timeplay(channel.startTime)
            icon = getImage(channel.id, '16')
            addItem(t + ' ' + channel.name, "ArcPlusPlay", False, channel.id, channel.descr, icon = icon, duration=GetInHMS(int(channel.length)))
    if channels.tpage > int(page):
            page = str(int(page) + 1)
            addItem("...Следующая страница...","ArcPlusGenreMovie",True, id, page=page)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


 elif mode == 'ArcBest':
    channels = []
    if type == "":
        addItem("За неделю", "ArcBest", True, "", type = "week")
        addItem("За месяц", "ArcBest", True, "", type = "month")
        addItem("За все время", "ArcBest", True, "", type = "all")
    elif type == "week":
        channels = GetBest.GetItem(SessionID(),1)
    elif type == "month":
        channels = GetBest.GetItem(SessionID(),2)
    elif type == "all":
        channels = GetBest.GetItem(SessionID(),3)        
    for channel in channels:
        t = timeplay(channel.startTime)
        icon = getImage(channel.id, '16')
        if id == channel.id:
            addItem(t + " " + channel.name, "ArcPlusPlay", False, channel.id, channel.descr, icon, duration=GetInHMS(int(channel.length)))
        else:
            if channel.cont == "true":
                addItem(channel.name, "ArcPlusGenreMovie", True, channel.id, channel.descr, icon)
            else:
                addItem(t + " " + channel.name, "ArcPlusPlay", False, channel.id, channel.descr, icon, duration=GetInHMS(int(channel.length)))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


    
 elif mode == 'ArcPlusPlay':
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        video = MediaService.GetClientStreamUri(SessionID(), 'ArcPlus' ,id)
        if video.startswith('http://'):
            video = urllib.unquote(video)
            video = video.replace('http://','mms://').replace('&amp;','&') + '&MSWMExt=.asf'
        cat = description.replace('\n', ". ")
        cat = '"' + name + '"' + ". " + cat
        icon = getImage(id, '16')
        listitem = xbmcgui.ListItem(name, thumbnailImage=icon)
        listitem.setInfo('video', {'title' : cat})
        playlist.add(url=video, listitem=listitem, index=7)
        xbmc.Player().play(playlist)
    

 elif mode == "archive":
  #chlist = addon.getSetting('chlist')
  #d = chlist.split(',')
  channels = Content.Channels()
  channels.Invoke(ContentService.GetClientChannel(SessionID(), type = 'LiveTV', pagItems = '200', pagNum = '1'))
  
  lc = archive.GetChannels(Username, Password)
  lcr = lc.Request()
  for d in channels.items:
  #for i in range(0,len(d)-2):  
    for channel in lcr:
        if channel[0][4:]==d.name:
          icon = getImage(id, '7') 
          addItem(channel[0], "archchannel", True, channel[1], "", icon)
          break 
  xbmcplugin.endOfDirectory(int(sys.argv[1]))



 elif mode == "archchannel":
    for d in range(0, 14):
        dt = datetime.date.today() - datetime.timedelta(days = d)
        addItem(dt.strftime("%Y-%m-%d, ") + daysofweek[dt.weekday()], "archprograms", True, id=id, icon=icon, date=dt.strftime("%Y-%m-%d"))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "archprograms":
    
    lc = archive.GetPVREPG(Username, Password, id, date)
    for prog in lc.Request():
        icon = getImage(prog[1], '4')
        addItem(prog[0], "archplay", False, prog[1],icon=icon, description=prog[2])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "archplay":
    video = MediaService.GetArcStreamUri(SessionID(), id)
    soup = BeautifulSoup(video)
    starttime = []
    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    pl.clear()
    #liz = xbmcgui.ListItem(name, iconImage=icon)
    #liz.setInfo(type="Video", infoLabels={ "Title": name[6:] + ". " + description })    
    for entry in soup('entry'):
        sup = BeautifulSoup(entry.prettify())
        starttime.append(sup.find('starttime').attrs[0][1])
        pl.add(sup.find('ref').attrs[0][1])
        
    start = []
    start = starttime[0].split(':')
    seconds = 0
    if len(start) == 3:
        seconds = int(start[2]) + (int(start[1])*60) + (int(start[0])*3600)
    elif len(start) == 2:
        seconds = int(start[1]) + (int(start[0])*60)
    #print seconds
    #liz = xbmcgui.ListItem(name, iconImage=icon)
    #liz.setInfo(type="Video", infoLabels={ "Title": name[6:] + ". " + description })
    xbmc.Player().play(pl)
    xbmc.Player().seekTime(seconds)
    #thread.start_new_thread(loop,(seconds))                 
        
         
    
    
    

           


 elif mode == "Search":
    #addItem("ТВ Архив", "key", False, "", type="2")
    addItem("Телетека", "key", False, "", type="0")
    addItem("Видеотека", "key", False, "", type="1")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "key":
    keyboard = RusKeyboard.Key()
    keyboard.type = type
    keyboard.urlpath = sys.argv[0]
    keyboard.doModal()
    del keyboard
    

 elif mode == "search1":
    if type == '0':
        f = ArcSearch.GetItem(SessionID(), type, page=int(page), keyword=keyword)
    else:
        f = VodSearch.GetItem(SessionID(), page=int(page), keyword=keyword) 
    k = f.items
    for i in k:
        if type == '0':
            icon = getImage(id, '16')
            t = timeplay(i.startTime)
            addItem(t + " " + i.name, "ArcPlusPlay", False, i.id, i.descr, icon, duration=GetInHMS(int(i.length)))
        else:
            icon = getImage(id, '3') 
            t = ''
            
            if id == i.id:
                addItem(t + " " + i.name, "VodPlay", False, i.id, i.descr, icon, duration=GetInHMS(int(i.length)))
            else:
                if i.cont == "true":
                    addItem(i.name, "GetRelVOD", True, i.id, i.descr, icon, )
                else:
                        addItem(t + " " + i.name, "VodPlay", False, i.id, i.descr, icon, duration=GetInHMS(int(i.length)))
    if f.tpage > int(page):
        p = int(page) + 1
        addItem("...Следующая страница...","search1",True, "0", page=str(p), keyword=keyword, type=type)
    if f.tpage == int(page) or f.tpage > int(page):
        addItem("На главную", "", True, "0")

    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == 'GetRelVOD':
    channels = ContentService.GetRelVod(SessionID(), id, page)
    for channel in channels.items:
        addItem(channel.name, "VodPlay", False, channel.id, channel.descr, icon, duration=GetInHMS(int(channel.length)))
    if channels.tpage > int(page):
        p = int(page) + 1
        addItem("...Следующая страница...","GetRelVOD",True, "0", page=str(p), keyword=keyword, type=type)
    if channels.tpage == int(page) or channels.tpage > int(page):
        addItem("На главную", "", True, "0")    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode == 'VodPlay':
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        video = MediaService.GetClientStreamUri(SessionID(), 'VOD' ,id)
        if video.startswith('http://'):
            video = urllib.unquote(video)
            video = video.replace('http://','mms://').replace('&amp;','&') + '&MSWMExt=.asf'
        cat = description.replace('\n', ". ")
        cat = '"' + name + '"' + ". " + cat
        icon = getImage(id, '16')
        listitem = xbmcgui.ListItem(cat, thumbnailImage=icon)
        listitem.setInfo('video', {'title' : cat})
        playlist.add(url=video, listitem=listitem, index=7)
        xbmc.Player().play(playlist) 
        
        
 elif mode == "vod":
    addItem("Добавления за неделю", "vodlastweek", True, "")
    addItem("Жанры", "vodgenres", True, "")
    addItem("Поступления", "vodnewest", True, "")
    addItem("Топ 100", "vodtop100", True, "")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "vodlastweek":
    addItem("Сегодня", "vodbyday", True, "0")
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
    l = lc.Request()
    for prog in l:
        icon = getImage(prog[1], '1')
        #icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1],prog[2], icon)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "vodplay":
    lc = vod.GetVODStreamURL(Username, Password, id)
    streamUrl = lc.Request()
    icon = getImage(id, '1')
    #icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + id + "&t=1"
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)    
    liz = xbmcgui.ListItem(name, thumbnailImage = icon)
    liz.setInfo(type="Video", infoLabels={"Title": name + ". " + description})
    playlist.clear()
    playlist.add(url=streamUrl, listitem=liz, index=1)
    xbmc.Player().play(playlist)

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
        icon = getImage(prog[1], '1')
        #icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        if prog[3] > 1:
            addItem(prog[0], "vodseries", True, prog[1],prog[2], icon)
        else:
            addItem(prog[0], "vodplay", False, prog[1], prog[2],icon, rating= prog[4], duration=prog[5])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "vodseries":
    lc = vod.GetVODSeries(Username, Password, id)
    for prog in lc.Request():
        icon = getImage(prog[1], '1')
        #icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1], "", icon, "", prog[2])
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RATING)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode == "vodnewest":
    lc = vod.GetVODMoviesNewInVODByUser(Username, Password)
    for prog in lc.Request():
        icon = getImage(prog[1], '1')
        #icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1], prog[2], icon)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "vodtop100":
    lc = vod.GetVODMoviesTOP100ByUser(Username, Password)
    for prog in lc.Request():
        icon = getImage(prog[1], '1')
        #icon = "http://www2.iptv-distribution.net/ui/ImageHandler.ashx?e=" + prog[1] + "&t=1"
        addItem(prog[0], "vodplay", False, prog[1],prog[2], icon,rating = prog[3])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    
 elif mode == "radio":
    lc = radio.GetRadioStationListByUser(Username)
    for prog in lc.Request():
        addItem(prog[0], "radioplay", False, prog[1],"", prog[2], stream = prog[3])
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

 elif mode == "radioplay":
    
    if icon == "" or icon == None:
        icon = "DefaultAudio.png"
    liz = xbmcgui.ListItem(name, iconImage = icon)
    liz.setInfo(type="Audio", infoLabels={ "Title": name[4:] })

    if stream.startswith('http://'):
        ap = asx.Parser()
        stream = ap.parseUrl(stream)[0]
    xbmc.Player().play(stream, liz)
except: 
    xbmcgui.Dialog().ok("BRTV", "Нет соединения с сервером", "")   
#print x.appSettings.sessionID

#print y.get()
#c.__len__()  
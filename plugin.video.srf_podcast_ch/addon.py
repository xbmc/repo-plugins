#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import urllib
import urllib2
import socket
import re
import xml.etree.ElementTree as ET
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import os

#'Base settings'
#'Start of the plugin functionality is at the end of the file'
addon = xbmcaddon.Addon()
addonID = 'plugin.video.srf_podcast_ch'
pluginhandle = int(sys.argv[1])
baseurl = 'http://www.srf.ch/podcasts'
socket.setdefaulttimeout(30)
translation = addon.getLocalizedString
xbmcplugin.setPluginCategory(pluginhandle,"News")
xbmcplugin.setContent(pluginhandle,"tvshows")
addon_work_folder = xbmc.translatePath("special://profile/addon_data/"+addonID)
if not os.path.isdir(addon_work_folder):
    os.mkdir(addon_work_folder)
FavoritesFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/"+addonID+".favorites")

#'this method writes the main index list of this plugin'
def index():
    addMenuItem(translation(30001), "", "listTvShows", "")
    addMenuItem(translation(30002), "", "showFavorites", "")
    xbmcplugin.endOfDirectory(pluginhandle)

#'this method writes the main index list of this plugin'
def showFavorites():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if os.path.exists(FavoritesFile):
        fh = open(FavoritesFile, 'r')
        all_lines = fh.readlines()
        for line in all_lines:
            title = line[line.find("###TITLE###=")+12:]
            title = title[:title.find("#")]
            url = line[line.find("###URL###=")+10:]
            url = url[:url.find("#")]
            thumb = line[line.find("###THUMB###=")+12:]
            thumb = thumb[:thumb.find("#")]
            addShow(title, title, "listEpisodes", "", thumb)
        fh.close()
    xbmcplugin.endOfDirectory(pluginhandle)
    #if forceViewMode:
    #    xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

#'this method list all TV shows from SRF when SRF-Podcast was selected in the main menu'
def listTvShows(url):
#    'start the podcast retrieving'
    tvshows = dict()
#    'load initial html page'
    splitedcontent = getHTMLContentFromSRFCH()
#    'iterate through every show and list details'
    getShowsFromHTMLContent(splitedcontent, tvshows, '')
#    'list shows'
    for showtitle in tvshows:
        show = tvshows.get(showtitle)
        addShow(showtitle, showtitle, 'listEpisodes', show[0] ,show[1])
    xbmcplugin.addSortMethod(pluginhandle,1)
    xbmcplugin.endOfDirectory(pluginhandle)
    #if forceViewMode:
    #    xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

#'this method list all episodes of the selected show'
def listEpisodes(showtitle):
#    'start the podcast retrieving'
    tvshows = dict()
#    'load initial html page'
    splitedcontent = getHTMLContentFromSRFCH()
#    'iterate through every show and list details'
    getShowsFromHTMLContent(splitedcontent, tvshows, showtitle)
    # get 
    showdetails = tvshows.get(showtitle)
    hd_showlist = showdetails[5]
    sd_showlist = showdetails[3]
    
#    'add HD episodes with urls'
    for hdepisodetitle in hd_showlist:
        hdepissodedetails = hd_showlist.get(hdepisodetitle)
        addLink(hdepissodedetails[0], hdepissodedetails[1], 'playepisode', hdepissodedetails[2],hdepissodedetails[3],hdepissodedetails[4],hdepissodedetails[5])
#    'add SD episodes with urls'
    for sdepissodetitle in sd_showlist:
        sdepissodedetails = sd_showlist.get(sdepissodetitle)
        addLink(sdepissodedetails[0], sdepissodedetails[1], 'playepisode', sdepissodedetails[2],sdepissodedetails[3],sdepissodedetails[4],sdepissodedetails[5])
    
    #xbmcplugin.addSortMethod(pluginhandle,1)
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    xbmcplugin.endOfDirectory(pluginhandle)
    
#'this method plays the selected episode'    
def playepisode(episodeurl):
    listitem = xbmcgui.ListItem(path=episodeurl)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

#'load the content from the podcast site of srf.ch'
def getHTMLContentFromSRFCH():
    try:
        req = urllib2.Request(baseurl)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
        response = urllib2.urlopen(req)
        content = response.read()
        response.close()
        #print ("before split")
        splitedcontent = content.split('<li class="shows" data-filter-options="')
        #print (splitedcontent)
    except:
        print 'error to connect to url: ' + url
    return splitedcontent

#'helper method to retrieve tv shows from html content'
def getShowsFromHTMLContent(splitedcontent, tvshows, showtitle):
        for i in range(1, (len(splitedcontent) -1), 1):
            entry = splitedcontent[i]
            entry = entry.replace("  ", "")
            entry = entry.replace("\n", "")
            #print("html entry ")
            #print (entry)
            
            #category tv or radio
            category = ''
            match = re.compile('<h3 class="(.+?)"', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                category = match[0]
    
            #get show title
            title = ''
            match = re.compile('<a href="(.+?)">(.+?)</a>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                title = match[1][1]
                title = cleanTitle(title)
    
            # get show description
            description = ''
            match = re.compile('<p>(.+?)</p>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                description = match[0]
                description = cleanTitle(description)
                
            # get show image
            tvShowIconUrl = ''
            match = re.compile('data-retina-src="(.+?)"', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                tvShowIconUrl = match[0]
    
            #if tv
            if (category == 'tv'):
                tvshows[title] =[description,tvShowIconUrl, '', '','', '']
                if showtitle != '' and title == showtitle:
                    getEpisodeUrlsForTvShowInHDorSD(title, description, tvShowIconUrl, entry, tvshows)
                
                
#try to find the rss feeds on the page
def getEpisodeUrlsForTvShowInHDorSD(title, description, tvShowIconUrl, entry, tvshows):
        show_items_sd = dict()
        show_items_hd = dict()
        rss_link_sd = ''
        rss_link_hd = ''
        
        #Check if there is an SD RSS feed option 1
        match = re.compile('<label for="(.+?)-sd">(.+?)</label>', re.DOTALL).findall(entry)
        if (len(match) >= 1):
            match = re.compile('<input id="(.+?)" class="input-xlarge" type="text" name="aac-feed" data-readonly="true" value="(.+?)"/>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                rss_link_sd = match[0][1]
                #extract shows and details from RSS feed and add them to the sd list
                getEpisodeUrlsFromRssFeed(show_items_sd, rss_link_sd, tvShowIconUrl, ' SD ')
        else:
            #Check if there is an SD RSS feed option 2
            match = re.compile('<input id="(.+?)" class="input-xlarge no-label" type="text" name="aac-feed" data-readonly="true" value="(.+?)"/>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                rss_link_sd = match[0][1]
                #extract shows and details from rss feed and add them to the sd list
                getEpisodeUrlsFromRssFeed(show_items_sd, rss_link_sd, tvShowIconUrl, ' SD ')
        
        #Check if there is an HD RSS feed
        match = re.compile('<label for="(.+?)-hd">(.+?)</label>', re.DOTALL).findall(entry)
        if (len(match) >= 1):
            match = re.compile('<input id="(.+?)" class="input-xlarge" type="text" name="hd-feed" data-readonly="true" value="(.+?)"/>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                rss_link_hd = match[0][1]
                #extract shows and details from rss feed and add them to the hd list
                getEpisodeUrlsFromRssFeed(show_items_hd, rss_link_hd, tvShowIconUrl, ' HD ')
        # add to tv show list
        tvshows[title] =[description, tvShowIconUrl, rss_link_sd, show_items_sd,rss_link_hd, show_items_hd]

#extract shows and details from RSS feed
def getEpisodeUrlsFromRssFeed(show_items_xx, rss_link_sd, tvShowIconUrl, sd_or_hd):
    try:
        req = urllib2.Request(rss_link_sd)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:22.0) Gecko/20100101 Firefox/22.0')
        response = urllib2.urlopen(req)
        rss_content = response.read()
        response.close()
    except:
        print 'error to connect to url: ' + rss_link_sd
    try:
        splitedcontent = rss_content.split('<item>')
        for i in range(1, (len(splitedcontent) -1), 1):
            entry = splitedcontent[i]
            entry = entry.replace("  ", "")
            entry = entry.replace("\n", "")
            #print("html entry ")
            #print (entry)
            
            #title
            episode_title = ''
            match = re.compile('<title>(.+?)</title>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                episode_title = match[0]
                episode_title = cleanTitle(episode_title)
    
            #get public date
            pubdate = ''
            match = re.compile('<pubDate>(.+?)</pubDate>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                pubdate = match[0]
                
            #get episode title
            length = ''
            match = re.compile('<itunes:duration>(.+?)</itunes:duration>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                length = match[0]
    
            # get show description
            description = ''
            match = re.compile('<description>(.+?)</description>', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                description = match[0]
                description = cleanTitle(description)
               
            # get show image
            EpisodeUrl = ''
            match = re.compile('<enclosure url="(.+?)"', re.DOTALL).findall(entry)
            if (len(match) >= 1):
                EpisodeUrl = match[0]
    
            show_items_xx[episode_title] = [episode_title + sd_or_hd,EpisodeUrl,description,tvShowIconUrl,length,pubdate]

    except:
        print 'error to connect to url: ' + rss_link_sd

#'helper method to create a folder with subitems'
def addMenuItem(name, url, mode, iconimage):
    ok = True
    directoryurl = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    li.setInfo(type="Video", infoLabels={"Title": name})
    xbmcplugin.setContent(pluginhandle, 'tvshows')
    ok = xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=li, isFolder=True)
    return ok

#'helper method to create a folder with subitems'
def addShow(name, url, mode, desc, iconimage):
    ok = True
    directoryurl = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
    playListInfosAdd = "###MODE###=ADD###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
    playListInfosRemove = "###MODE###=REMOVE###TITLE###="+name+"###URL###="+urllib.quote_plus(url)+"###THUMB###="+iconimage+"###END###"
    liz.addContextMenuItems([(translation(30003), 'RunPlugin(plugin://'+addonID+'/?mode=manageFavorites&url='+urllib.quote_plus(playListInfosAdd)+')',),(translation(30004), 'RunPlugin(plugin://'+addonID+'/?mode=manageFavorites&url='+urllib.quote_plus(playListInfosRemove)+')',)])
    xbmcplugin.setContent(pluginhandle, 'tvshows')
    ok = xbmcplugin.addDirectoryItem(pluginhandle, url=directoryurl, listitem=liz, isFolder=True)
    return ok
    
#'helper method to create an item in the list'
def addLink(name, url, mode, desc, iconurl, length, pubdate):
    ok = True
    linkurl = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    liz = xbmcgui.ListItem(name)
    liz.setInfo(type='Video', infoLabels={"Title": name, "Duration": length, "Plot": desc, "Aired" : pubdate})
    liz.setProperty('IsPlayable', 'true')
    xbmcplugin.setContent(pluginhandle,"episodes")
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=linkurl, listitem=liz)
    return ok

def manageFavorites(param):
    mode = param[param.find("###MODE###=")+11:]
    mode = mode[:mode.find("###")]
    print("param " + param)
    channelEntry = param[param.find("###TITLE###="):]
    if mode == "ADD":
        if os.path.exists(FavoritesFile):
            fh = open(FavoritesFile, 'r')
            content = fh.read()
            fh.close()
            if content.find(channelEntry) == -1:
                fh = open(FavoritesFile, 'a')
                fh.write(channelEntry+"\n")
                fh.close()
        else:
            fh = open(FavoritesFile, 'a')
            fh.write(channelEntry+"\n")
            fh.close()
    elif mode == "REMOVE":
        fh = open(FavoritesFile, 'r')
        content = fh.read()
        fh.close()
        entry = content[content.find(channelEntry):]
        print("channelentry " + channelEntry)
        print("entry " + entry)
        fh = open(FavoritesFile, 'w')
        fh.write(content.replace(channelEntry+"\n", ""))
        fh.close()
        xbmc.executebuiltin("Container.Refresh")


#'helper method to retrieve parameters in a dict from the arguments given to this plugin by xbmc'
def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

#'helper method to clean title fetch from html content'
def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "\\").replace("&quot;", "\"").replace("&szlig;", "�").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö").replace("&eacute;", "é").replace("&egrave;", "à")
    title = title.replace("&#x00c4","�").replace("&#x00e4","�").replace("&#x00d6","�").replace("&#x00f6","�").replace("&#x00dc","�").replace("&#x00fc","�").replace("&#x00df","�").strip()
    title = title.replace("&apos;","'").strip()
    return title


#'Start'
#'What to do... if nothing is given we start with the index'
params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
#name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listTvShows':
    listTvShows(url)
elif mode == 'listEpisodes':
    listEpisodes(url)
elif mode == 'playepisode':
    playepisode(url)
elif mode == 'showFavorites':
    showFavorites()
elif mode == 'manageFavorites':
    manageFavorites(url)    
else:
    index() 
    
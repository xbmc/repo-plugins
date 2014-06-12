import sys

import urllib
import urllib2
import re
import urlparse

from bs4 import BeautifulSoup as bsoup

DWNLD_SCRIPT_LOC = xbmc.translatePath("special://home/addons/plugin.video.democracynownow/"+\
                   "resources/lib/download_episode.py") 

#TODO: Add an Episode class

def get_past_shows():
    """
    Scrapes links to monthly pages for past Democracy Now shows and headlines.
    Returns a dictionary with the available years as keys and a list of tuples
    containing 1. month name and 2. url of month page.
    
    ex. {'1996' : [(u'December', 'http://www.democracynow.org/shows/1996/12'),
    (u'November', 'http://www.democracynow.org/shows/1996/11'),  ...]
    ...} 
    """
    html_content = urllib2.urlopen("http://www.democracynow.org/shows/")
    soup = bsoup(html_content.read())
    html_content.close()
    content = soup.find("div", {"id":"content_body"})
    year_re = re.compile("(?P<year>2[0-9]{3})")
    past_shows_by_year = {}
    for link in content.find_all('a'):
        mat = year_re.search(link.parent.get('data-clicky-title'))
        try:
            if not mat: continue
            year = mat.groupdict()["year"]
            if int(year) <= 2001: #Videos not available until ~ 08/18/2001
                if int(year) == 2001:
                    month = link.get('href').split('/')[-1]
                    if int(month) < 9: continue
                else: continue
            if past_shows_by_year.has_key(year):
                past_shows_by_year[year].append(
                (link.getText(), link.get('href')))                
            else:
                past_shows_by_year[year] = [(link.getText(), 
                                             link.get('href'))]
        except KeyError:
            print "Could not find year for "+\
                     link.parent.get('data-clicky-title') + ", " +\
                     link.getText()+" => "+link.get('href')
            if past_shows_by_year.has_key("Unknown"):
                past_shows_by_year["Unknown"].append(
                (link.getText(), link.get('href')))
            else: past_shows_by_year["Unknown"] = [(link.getText(), 
                                                    link.get('href'))]
    return past_shows_by_year

def get_episode_match(mn_url):
    """
    Returns a list of re match objects for urls to past episodes in a given
    month.  Each match object captures the month, day, and year of the episode
    as well as the url itself.
    
    Keyword Arguments:
    mn_url -- url to monthly page of past episodes.
    """
    html_cont = urllib2.urlopen(mn_url)
    soup = bsoup(html_cont)
    html_cont.close()
    episode_re = re.compile("/dn(?P<year>[0-9]*)-(?P<month>[0-9]{2})"+\
    "(?P<day>[0-9]{2})[A-Za-z0-9_]*\.mp4")
    alt_episode_re = re.compile("(?P<month>[A-Z][a-z]*)(?P<day>[0-2][0-9])"+\
                                "(?P<year>2[0-9]{3})[0-9]*.mp4")
    mats = []
    #TODO: Improve efficiency of this loop
    for link in soup.findAll("a"):    
        alink = link.get("href")
        if alink:
            mat = episode_re.search(alink)
            if mat: mats.append(mat)
            else:
                mat = alt_episode_re.search(alink)
                if mat: mats.append(mat)
    return mats

def build_url(burl, query):
    return burl + '?' + urllib.urlencode(query)
       
if __name__ == '__main__':
    import xbmc
    import xbmcgui
    import xbmcplugin       
    base_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    args = urlparse.parse_qs(sys.argv[2][1:])
    
    #TODO: Change mode to a list of possible modes
    mode = args.get('mode', None)
    dnurl = args.get('url', None)
    foldername = args.get('foldername', None)
    episode_title = args.get('title', None)
    
    xbmcplugin.setContent(addon_handle, 'episodes')
    
    if mode is None: #Plugin has been just accessed from XBMC
        items = []
        ps = get_past_shows()
        if ps:
            for yr in sorted(ps, key=ps.get, reverse=True):
                for mn in ps[yr]:
                    url = build_url(base_url, 
                                    {'mode': 'month_folder', 
                                     'foldername': yr + ", " + mn[0], 
                                     'url':mn[1]})
                    li = xbmcgui.ListItem(yr + ", " + mn[0],
                                          iconImage='DefaultFolder.png')
                    items.append((url, li, True))    
            xbmcplugin.addDirectoryItems(handle=addon_handle, items=items, 
                                         totalItems=len(items))
            xbmcplugin.endOfDirectory(addon_handle)   
        else: raise RuntimeError("Within mode: None.")
    elif mode[0] == "month_folder": #User has selected 
        foldername, month_name = [None]*2
        try:
            foldername = args['foldername'][0]
            month_name = foldername.split()[1].upper() #ISOK: This maybe dangerous
            dnurl = dnurl[0]
        except IndexError:
            xbmc.log("Variable 'foldername' does not appear to have been in"+\
                     "the form '<year>, <month>'.", xbmc.LOGERROR)
        
        epmatchs = get_episode_match(dnurl)
        items = []
        for m in epmatchs:
            mdict = m.groupdict()
            eptitle = mdict["month"]+"/"+mdict["day"]+"/"+mdict["year"]
            url = build_url(base_url, 
                            {'mode': 'episodes', 
                             'foldername': eptitle, 
                             'url':m.string,
                             'title' : eptitle})    
    
            li = xbmcgui.ListItem(eptitle, iconImage="DefaultFolder.png")    
            items.append((url, li, True))
            xbmc.log(m.string, xbmc.LOGDEBUG)
        xbmcplugin.addDirectoryItems(handle=addon_handle, items=items, 
                                     totalItems=len(items))
        xbmcplugin.endOfDirectory(addon_handle)
    elif mode[0] == "episodes": 
        li = xbmcgui.ListItem(str(foldername[0]), iconImage="DefaultMovie.png")
        scriptArgs = str(dnurl[0])+", "+args['title'][0]
        li.addContextMenuItems([
                                ('Download', 'XBMC.RunScript(%s,%s)' % (DWNLD_SCRIPT_LOC, scriptArgs))
                                ])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=str(dnurl[0]), 
                                    listitem=li, totalItems=1, isFolder=False)
        xbmcplugin.endOfDirectory(addon_handle)
    else: raise RuntimeError("Probably a problem with mode.")

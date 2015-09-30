import urllib,requests,sys,re,xbmcplugin,xbmcgui,xbmcaddon,xbmc,os

__addonid__ = "plugin.video.iplayerwww"
__plugin_handle__ = int(sys.argv[1])


def GetAddonInfo():
    dict = {}
    dict["id"]       = __addonid__
    dict["addon"]    = xbmcaddon.Addon(__addonid__)
    dict["language"] = dict["addon"].getLocalizedString
    dict["version"]  = dict["addon"].getAddonInfo("version")
    dict["path"]     = dict["addon"].getAddonInfo("path")
    dict["profile"]  = xbmc.translatePath(dict["addon"].getAddonInfo('profile'))
    return dict


__addoninfo__ = GetAddonInfo()
ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')
DIR_USERDATA   = xbmc.translatePath(__addoninfo__["profile"])


def CATEGORIES():
    AddMenuEntry('Highlights','url',106,'','','')
    AddMenuEntry('Most Popular','url',105,'','','')
    AddMenuEntry('Programme List A-Z','url',102,'','','')
    AddMenuEntry('Categories','url',103,'','','')
    AddMenuEntry('Search','url',104,'','','')
    AddMenuEntry('Watch Live','url',101,'','','')
 
      
# ListLive creates menu entries for all live channels.                                                                     
def ListLive():
    channel_list = [
                        ('bbc_one_hd','bbc_one', 'BBC One'),
                        ('bbc_two_hd', 'bbc_two', 'BBC Two'),
                        ('bbc_three_hd','bbc_three', 'BBC Three'),
                        ('bbc_four_hd','bbc_four', 'BBC Four'),
                        ('cbbc_hd','cbbc', 'CBBC'),
                        ('cbeebies_hd','cbeebies', 'CBeebies'),
                        ('bbc_news24','bbc_news24', 'BBC News Channel'),
                        ('bbc_parliament','bbc_parliament', 'BBC Parliament'),
                        ('bbc_alba','bbc_alba', 'Alba'),
                        ('s4cpbs','s4c','S4C'),
                        ('bbc_one_scotland_hd','bbc_one', 'BBC One Scotland'),
                        ('bbc_one_northern_ireland_hd','bbc_one', 'BBC One Northern Ireland'),
                        ('bbc_one_wales_hd','bbc_one', 'BBC One Wales'),
                        ('bbc_two_scotland', 'bbc_two', 'BBC Two Scotland'),
                        ('bbc_two_northern_ireland_digital', 'bbc_two', 'BBC Two Northern Ireland'),
                        ('bbc_two_wales_digital', 'bbc_two', 'BBC Two Wales'),
                   ]
    for id, img, name in channel_list :
        iconimage = xbmc.translatePath(os.path.join('special://home/addons/plugin.video.iplayerwww/media',img+'.png'))
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name,id,203,iconimage,'','')
        else:
            AddMenuEntry(name,id,123,iconimage,'','')       


# GetAtoZ allows to list programmes based on alphabetical order.
# GetAtoZ only creates the corresponding directories for each character.
def ListAtoZ():
    characters = [ ('A','a'),('B','b'),('C','c'),('D','d'),('E','e'),('F','f'),('G','g'),('H','h'),('I','i'),
                   ('J','j'),('K','k'),('L','l'),('M','m'),('N','n'),('O','o'),('P','p'),('Q','q'),('R','r'),
                   ('S','s'),('T','t'),('U','u'),('V','v'),('W','w'),('X','x'),('Y','y'),('Z','z'),('0-9','0-9')]
    for name, url in characters:
        AddMenuEntry(name,url,124,'','','')


# GetAtoZPage allows to list programmes based on alphabetical order.
# GetAtoZPage creates the list of programmes for one character.
def GetAtoZPage(url):
    link=OpenURL('http://www.bbc.co.uk/iplayer/a-z/%s'%url)
    match=re.compile('<a href="/iplayer/brand/(.+?)".+?<span class="title">(.+?)</span>',re.DOTALL).findall (link)
    for programme_id , name in match:
        AddMenuEntry(name,programme_id,121,'','','')


# ScrapeSearchEpisodes extracts the episode IDs from the search result HTML.
# If there are more pages of search results, ScrapeSearchEpisodes also returns the page number of the next result page.
def ScrapeSearchEpisodes(url):
    html=OpenURL(url)
    # In search mode, available and unavailable programmes will be found.
    # While unavailable programmes are all marked by "unavailable", there are several classes of "available" programmes.
    # Thus, we need to match all of them.
    match1=re.compile('programme"  data-ip-id="(.+?)">.+?class="title top-title">(.+?)<.+?img src="(.+?)".+?<p class="synopsis">(.+?)</p>',re.DOTALL).findall(html.replace('amp;',''))
    for programme_id, name, iconimage, plot in match1:
        # Some programmes actually contain multiple episodes (haven't seen that for episodes yet).
        # These can be recognized by some extra HTML code
        match_episodes=re.search('<a class="view-more-container avail stat" href="/iplayer/episodes/%s"'%programme_id,html)
        # If multiple episodes are found, the programme_id is suitable to add a new directory.
        if match_episodes:
            num_episodes=re.compile('<a class="view-more-container avail stat" href="/iplayer/episodes/%s".+?<em class="view-more-heading">(.+?)<'%programme_id,re.DOTALL).findall(html)
            AddMenuEntry("%s - %s available episodes"%(name,num_episodes[0]),programme_id,121,iconimage,plot,'')
        else:
            episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % programme_id
            CheckAutoplay(name,episode_url,iconimage,plot)
    match1=re.compile('episode"  data-ip-id="(.+?)">.+?" title="(.+?)".+?img src="(.+?)".+?<p class="synopsis">(.+?)</p>',re.DOTALL).findall(html.replace('amp;',''))
    for programme_id, name, iconimage, plot in match1:
        episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % programme_id
        CheckAutoplay(name,episode_url,iconimage,plot)
    nextpage=re.compile('<span class="next txt"> <a href=".+?page=(\d+)">').findall(html)
    return nextpage


# EvaluateSearch parses the Search result page(s) for available programmes and lists them.
def EvaluateSearch(url):
    nextpage=ScrapeSearchEpisodes(url)
    # To make matters worse, there is a LOT of unavailable programmes and no way to search only for availble programs, so we need to parse several pages.
    # This is also why search takes a couple of seconds at least.
    while 1:
        try:
            temp_url='%s&page=%s' % (url,nextpage[0])
            nextpage=ScrapeSearchEpisodes(temp_url)
        except:break
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)      


# ListCategories parses the available categories and creates directories for selecting one of them.
# The category names are scraped from the website.
def ListCategories():
    category_name=[]
    category_url=[]
    html=OpenURL('http://www.bbc.co.uk/iplayer')
    match=re.compile('<a href="/iplayer/categories/(.+?)" class="stat">(.+?)</a>').findall(html.replace('amp;',''))
    for url , name in match:
        AddMenuEntry(name, url, 125, '', '','')

# ListCategoryFilters parses the available category filters (if available) and creates directories for selcting them.
# If there are no filters available, all programmes will be listed using GetFilteredCategory.
def ListCategoryFilters(url):
    NEW_URL='http://www.bbc.co.uk/iplayer/categories/%s/all?sort=atoz'%url
    # Read selected category's page.
    html=OpenURL(NEW_URL)
    # Some categories offer filters, we want to provide these filters as options.
    match1=re.compile('<li class="filter"> <a class="name" href="/iplayer/categories/(.+?)"> (.+?)</a>',re.DOTALL).findall(html.replace('amp;',''))
    if match1:
        AddMenuEntry('All', url, 126, '', '','')
        for url, name in match1:
            AddMenuEntry(name, url, 126, '', '','')
    else:
        GetFilteredCategory(url)


# ScrapeCategoryEpisodes scrapes the episode IDs from the category pages.
# It also returns the ID of the next page, if there are more pages in the same category.
def ScrapeCategoryEpisodes(url):
    # Read selected category's page.
    html=OpenURL(url)
    # Scrape all programmes on this page and create one menu entry each.
    match=re.compile('data-ip-id="(.+?)">.+?<a href="/iplayer/episode/(.+?)/.+?"title top-title">(.+?)<.+?img src="(.+?)"(.+?)<p class="synopsis">(.+?)</p>',re.DOTALL).findall(html.replace('amp;',''))
    for programme_id, episode_id, name, iconimage, sub_content, plot in match:
        # Some programmes actually contain multiple episodes.
        # These can be recognized by some extra HTML code
        match_episodes=re.search('<a class="view-more-container avail stat" href="/iplayer/episodes/%s"'%programme_id,html)
        # If multiple episodes are found, the programme_id is suitable to add a new directory.
        if match_episodes:
            num_episodes=re.compile('<a class="view-more-container avail stat" href="/iplayer/episodes/%s".+?<em class="view-more-heading">(.+?)<'%programme_id,re.DOTALL).findall(html)
            AddMenuEntry("%s - %s available episodes"%(name,num_episodes[0]),programme_id,121,iconimage,plot,'')
        # If only one episode is found, the episode_id is suitable to add a directory or stream.
        # This is required because some programmes which have their own page will redirect
        # the programme_id to the program page which may look entirely different from
        # the regular page.
        else:
            # Some episodes have additional subtitles or episode descriptions.
            subtitle_match=re.compile('<div class="subtitle">(.+?)</div>',re.DOTALL).findall(sub_content)
            if subtitle_match:
                name += ", %s"%subtitle_match[0]
            episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % episode_id
            CheckAutoplay(name,episode_url,iconimage,plot)
        # Check if a next page exists and if so return the index
    nextpage=re.compile('<span class="next txt"> <a href=".+?page=(\d+)">').findall(html)
    return nextpage


# GetFilteredCategory parses the programmes available in the category view.
def GetFilteredCategory(url):
    NEW_URL='http://www.bbc.co.uk/iplayer/categories/%s/all?sort=atoz'%url
    nextpage=ScrapeCategoryEpisodes(NEW_URL)
    # Some categories consist of several pages, we need to parse all of them.
    while 1:
        try:
            temp_url='%s&page=%s' % (NEW_URL,nextpage[0])
            nextpage=ScrapeCategoryEpisodes(temp_url)
        except:break


# ListHighlights creates a list of the programmes in the highlights section.
# All entries are scraped of the intro page and the pages linked from the intro page.
def ListHighlights():
    html=OpenURL('http://www.bbc.co.uk/iplayer')
    match1=re.compile('<p class=" typo typo--goose">.+?<a href="/iplayer/group/(.+?)" class="grouped-items__title grouped-items__title--desc stat"><strong>(.+?)</strong></a>.+?<em>(.+?)</em>',re.DOTALL).findall(html.replace('amp;',''))
    for episode_id, name, num_episodes in match1:
        AddMenuEntry('Collection: %s - %s available programmes'%(name,num_episodes), episode_id, 127, '', '','')
    match1=re.compile('href="/iplayer/episode/(.+?)/.+?\nclass="single-item stat".+?class="single-item__title.+?<strong>(.+?)</strong>(.+?)data-ip-src="(.+?)".+?class="single-item__overlay__desc">(.+?)<',re.DOTALL).findall(html.replace('amp;',''))
    for episode_id, name, subtitle, iconimage, plot in match1:
        episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % episode_id
        sub_match=re.compile('class="single-item__subtitle.+?>(.+?)<',re.DOTALL).findall(subtitle)
        if len(sub_match)==1:
            CheckAutoplay("%s: %s"%(name,sub_match[0]),episode_url,iconimage,plot)
        else:
            CheckAutoplay(name,episode_url,iconimage,plot)


# GetGroups scrapes information on a particular group, a special kind of collection.
def GetGroups(url):
    new_url="http://www.bbc.co.uk/iplayer/group/%s"%url
    html=OpenURL(new_url)
    # In group mode, different kind of programmes can be found-
    # Unfortunately, there are several classes of "available" programmes.
    # Thus, we need to match all of them.
    match1=re.compile('data-ip-id="(.+?)">.+?" title="(.+?)".+?img src="(.+?)".+?<p class="synopsis">(.+?)</p>',re.DOTALL).findall(html.replace('amp;',''))
    for episode_id , name , iconimage, plot in match1:
        episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % episode_id 
        CheckAutoplay(name,episode_url,iconimage,plot)
    # Some groups consist of several pages of programmes. We want to find all of them, of course.
    while 1:
        try:
            nextpage=re.compile('<span class="next txt">.+?page=(.+?)">',re.DOTALL).findall(html)
            temp_url='%s?page=%s' % (new_url,nextpage[0])
            html=OpenURL(temp_url)
            match1=re.compile('data-ip-id="(.+?)">.+?" title="(.+?)".+?img src="(.+?)".+?<p class="synopsis">(.+?)</p>',re.DOTALL).findall(html.replace('amp;',''))
            for episode_id , name , iconimage, plot in match1:
                episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % episode_id 
                CheckAutplay(name,episode_url,iconimage,plot)
        except:break
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)      


# ListMostPopular scrapes all episodes of the most popular page.
def ListMostPopular():
    html=OpenURL('http://www.bbc.co.uk/iplayer/group/most-popular')
    match1=re.compile('data-ip-id="(.+?)">.+?href="(.+?)" title="(.+?)".+?img src="(.+?)".+?<p class="synopsis">(.+?)</p>',re.DOTALL).findall(html.replace('amp;',''))
    for programme_id, url, name, iconimage, plot in match1:
        try:
            # If there is a special block of HTML code, there are several episodes available for this programme.
            getseries=html.split(url)[1]
            number=re.compile('<em>(.+?)</em>').findall(getseries)[0]
            if not programme_id in url:
                name='%s - [COLOR orange](%s Available)[/COLOR]' % (name,number.strip())
        except:
            name=name    
        url_out='http://www.bbc.co.uk%s' %url
        if not programme_id in url_out:
            programme_id=programme_id
        else:
            programme_id=''
        CheckAutoplay(name,url_out,iconimage.replace('336x189','832x468') ,plot)


# Search simply calls the online search function. The search is then evaluated in EvaluateSearch.
def Search():
        search_entered = ''
        keyboard = xbmc.Keyboard(search_entered, 'Search iPlayer')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText() .replace(' ','%20')  # sometimes you need to replace spaces with + or %20
            if search_entered == None:
                return False  
        NEW_URL='http://www.bbc.co.uk/iplayer/search?q=%s'%search_entered
        EvaluateSearch(NEW_URL)


# GetEpisodes gets all programmes corresponding to a certain programme ID.
def GetEpisodes(programme_id):
    # Construct URL and load HTML
    url='http://www.bbc.co.uk/iplayer/episodes/%s' %programme_id
    html=OpenURL(url)
    # Extract all programmes from the page
    match=re.compile('data-ip-id=".+?">.+?<a href="(.+?)" title="(.+?)".+?data-ip-src="(.+?)">.+?class="synopsis">(.+?)</p>',re.DOTALL).findall (html)
    # If there is only one match, this is one programme only. We can stop and get the available streams right away.
    if len(match)==1:
        _URL_='http://www.bbc.co.uk/%s' %match[0][0]
        name=match[0][1]
        iconimage=match[0][2]
        plot=match[0][3]
        CheckAutoplay(name,_URL_,iconimage.replace('336x189','832x468') ,plot)
    # If there are multiple programmes on this page, we need to add them all as entries to the menu.
    else:    
        for URL , name , iconimage, plot in match:
            _URL_='http://www.bbc.co.uk/%s' %URL
            CheckAutoplay(name,_URL_,iconimage.replace('336x189','832x468') ,plot)
        # Some programmes consist of several pages, we need to parse all of them.
        while 1:
            try:
                # Check if a next page exists and if so load it.
                nextpage=re.compile('<span class="next bp1"> <a href=".+?page=(\d+)">').findall(html)
                temp_url='%s?page=%s' % (url,nextpage[0])
                html=OpenURL(temp_url)
                # Parse all programmes on this page and create one menu entry each.
                match=re.compile('data-ip-id=".+?">.+?<a href="(.+?)" title="(.+?)".+?data-ip-src="(.+?)">.+?class="synopsis">(.+?)</p>',re.DOTALL).findall (html)
                for URL , name , iconimage, plot in match:
                    _URL_='http://www.bbc.co.uk/%s' %URL
                    CheckAutoplay(name,_URL_,iconimage.replace('336x189','832x468') ,plot)
            except:break
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)    
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)    


# AddAvailableStreamsDirectory will create one menu entry for each available stream of a particular stream_id
def AddAvailableStreamsDirectory(name,stream_id,iconimage,description):
    # print "Stream ID: %s"%stream_id
    streams=ParseStreams(stream_id)
    # print streams
    if streams[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams[1][0]
        # print subtitles_url
    else:
        subtitles_url = ''
    suppliers=['','Akamai','Limelight','Level3']
    bitrates=[0,800,1012,1500,1800,2400,3116,5510]
    for supplier, bitrate, url in streams[0]:
        if (int(bitrate) == 7) or (int(bitrate) == 5) :
            TITLE=name+' - [COLOR white]%s[/COLOR] - [COLOR green]%s kbps[/COLOR]'%(suppliers[supplier],bitrates[bitrate])
        elif (int(bitrate) == 6) or (int(bitrate) == 3):
            TITLE=name+' - [COLOR white]%s[/COLOR] - [COLOR yellow]%s kbps[/COLOR]'%(suppliers[supplier],bitrates[bitrate])
        elif int(bitrate) == 4:
            TITLE=name+' - [COLOR white]%s[/COLOR] - [COLOR orange]%s kbps[/COLOR]'%(suppliers[supplier],bitrates[bitrate])
        else:
            TITLE=name+' - [COLOR white]%s[/COLOR] - [COLOR red]%s kbps[/COLOR]'%(suppliers[supplier],bitrates[bitrate])
        AddMenuEntry(TITLE,url,201,iconimage,description,subtitles_url)


def ParseStreams(stream_id):
    retlist=[]
    # print "Parsing streams for PID: %s"%stream_id[0]
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL="http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id[0]
    html = OpenURL(NEW_URL)
    # Parse the different streams and add them as new directory entries.
    match=re.compile('connection authExpires=".+?href="(.+?)".+?supplier="mf_(.+?)".+?transferFormat="(.+?)"').findall(html.replace('amp;',''))
    for m3u8_url, supplier, transfer_format in match:
        tmp_sup=0
        tmp_br=0
        if transfer_format == 'hls':
            if supplier == 'akamai_uk_hls':
                tmp_sup=1
            elif supplier == 'limelight_uk_hls':
                tmp_sup=2
            m3u8_breakdown=re.compile('(.+?)iptv.+?m3u8(.+?)$').findall(m3u8_url)
            # print m3u8_url
            m3u8_html = OpenURL(m3u8_url)
            m3u8_match=re.compile('BANDWIDTH=(.+?),.+?RESOLUTION=(.+?)\n(.+?)\n').findall(m3u8_html)
            for bandwidth, resolution, stream in m3u8_match:
                # print bandwidth
                # print resolution
                # print stream
                url="%s%s%s"%(m3u8_breakdown[0][0],stream,m3u8_breakdown[0][1])
                if int(bandwidth) == 1012300 :
                    tmp_br=2
                elif int(bandwidth) == 1799880 :
                    tmp_br=4
                elif int(bandwidth) == 3116400 :
                    tmp_br=6
                elif int(bandwidth) == 5509880 :
                    tmp_br=7
                retlist.append((tmp_sup,tmp_br,url))
    # It may be useful to parse these additional streams as a default as they offer additional bandwidths.
    match=re.compile('kind="video".+?connection href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"').findall(html.replace('amp;',''))
    # print match
    unique = []
    [unique.append(item) for item in match if item not in unique]
    # print unique
    for m3u8_url, supplier, transfer_format in unique:
        tmp_sup=0
        tmp_br=0
        if transfer_format == 'hls':
            if supplier == 'akamai_hls_open':
                tmp_sup=1
            elif supplier == 'limelight_hls_open':
                tmp_sup=2
            m3u8_breakdown=re.compile('.+?master.m3u8(.+?)$').findall(m3u8_url)
        # print m3u8_url
        # print m3u8_breakdown
        m3u8_html = OpenURL(m3u8_url)
        # print m3u8_html
        m3u8_match=re.compile('BANDWIDTH=(.+?),RESOLUTION=(.+?),.+?\n(.+?)\n').findall(m3u8_html)
        # print m3u8_match
        for bandwidth, resolution, stream in m3u8_match:
            # print bandwidth
            # print resolution
            # print stream
            url="%s%s"%(stream,m3u8_breakdown[0][0])
            # This is not entirely correct, displayed bandwidth may be higher or lower than actual bandwidth.
            if int(bandwidth) <= 801000 :
                tmp_br=1
            elif int(bandwidth) <= 1510000 :
                tmp_br=3
            elif int(bandwidth) <= 2410000 :
                tmp_br=5
            retlist.append((tmp_sup,tmp_br,url))
    match=re.compile('service="captions".+?connection href="(.+?)"').findall(html.replace('amp;',''))
    # print "Subtitle URL: %s"%match
    # print retlist
    return retlist, match


def CheckAutoplay(name, url, iconimage, plot):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name,url,202,iconimage,plot,'')
    else:
        AddMenuEntry(name,url,122,iconimage,plot,'')        


def ScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    # Search for standard programmes.
    stream_id_st=re.compile('"vpid":"(.+?)"').findall(html)
    # Optionally, Signed programmes can be searched for. These have a different ID.
    if ADDON.getSetting('search_signed') == 'true':
        stream_id_sl=re.compile('data-download-sl="bbc-ipd:download/.+?/(.+?)/sd/').findall(html)
    else:
        stream_id_sl=[]
    # Optionally, Audio Described programmes can be searched for. These have a different ID.
    if ADDON.getSetting('search_ad') == 'true':
        url_ad=re.compile('<a href="(.+?)" class="version link watch-ad-on"').findall(html)
        url_tmp="http://www.bbc.co.uk%s"%url_ad[0]
        html=OpenURL(url_tmp)
        stream_id_ad=re.compile('"vpid":"(.+?)"').findall(html)
        # print stream_id_ad
    else:
        stream_id_ad=[]
    return {'stream_id_st':stream_id_st, 'stream_id_sl':stream_id_sl, 'stream_id_ad':stream_id_ad}

# AddAvailableStreamItem play a streamm based on settings for preferred catchup source and bitrate.
def AddAvailableStreamItem(name,url,iconimage,description):
    stream_ids = ScrapeAvailableStreams(url)
    if stream_ids['stream_id_ad']:
        streams_all=ParseStreams(stream_ids['stream_id_ad'])
    elif stream_ids['stream_id_sl']:
        streams_all=ParseStreams(stream_ids['stream_id_sl'])
    else:
        streams_all=ParseStreams(stream_ids['stream_id_st'])
    if streams_all[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams_all[1][0]
        # print subtitles_url
    else:
        subtitles_url = ''
    streams=streams_all[0]
    source=int(ADDON.getSetting('catchup_source'))
    bitrate=int(ADDON.getSetting('catchup_bitrate'))
    # print "Selected source is %s"%source
    # print "Selected bitrate is %s"%bitrate
    # print streams
    if source > 0:
        if bitrate > 0:
            # Case 1: Selected source and selected bitrate
            match=[x for x in streams if ((x[0] == source) and (x[1] == bitrate))]
            if len(match)==0:
                # Fallback: Use same bitrate but different supplier.
                match=[x for x in streams if (x[1] == bitrate)]
                if len(match)==0:
                    # Second Fallback: Use any lower bitrate from selected source.
                    match=[x for x in streams if (x[0] == source) and (x[1] in range(1,bitrate))]
                    match.sort(key=lambda x: x[1], reverse=True)
                    if len(match)==0:
                         # Third Fallback: Use any lower bitrate from any source.
                         match=[x for x in streams if (x[1]  in range(1,bitrate))]
                         match.sort(key=lambda x: x[1], reverse=True)
        else:
            # Case 2: Selected source and any bitrate
            match=[x for x in streams if (x[0] == source)]
            if len(match)==0:
                # Fallback: Use any source and any bitrate
                match=streams
            match.sort(key=lambda x: x[1], reverse=True)
    else:
        if bitrate > 0:
            # Case 3: Any source and selected bitrate
            match=[x for x in streams if (x[1] == bitrate)]
            if len(match)==0:
                # Fallback: Use any source and any lower bitrate
                match=streams
                match=[x for x in streams if (x[1]  in range(1,bitrate))]
                match.sort(key=lambda x: x[1], reverse=True)
        else:
            # Case 4: Any source and any bitrate
            # Play highest available bitrate
            match=streams
            match.sort(key=lambda x: x[1], reverse=True)
    PlayStream(name,match[0][2],iconimage,description,subtitles_url)


# GetAvailableStreams calls AddAvailableStreamsDirectory based on user settings
def GetAvailableStreams(name,url,iconimage,description):
    stream_ids = ScrapeAvailableStreams(url)
    AddAvailableStreamsDirectory(name,stream_ids['stream_id_st'],iconimage,description)
    # If we searched for Audio Described programmes and they have been found, append them to the list.
    if stream_ids['stream_id_ad']:
        AddAvailableStreamsDirectory(name+' - (Audio Described)',stream_ids['stream_id_ad'],iconimage,description)
    # If we search for Signed programmes and they have been found, append them to the list.
    if stream_ids['stream_id_sl']:
        AddAvailableStreamsDirectory(name+' - (Signed)',stream_ids['stream_id_sl'],iconimage,description)


# AddAvailableLiveStreamItem play a live stream based on settings for preferred live source and bitrate.
def AddAvailableLiveStreamItem(name,channelname,iconimage):
    stream_bitrates=[9999,345,501,923,1470,1700,2128,2908,3628,5166]
    if int(ADDON.getSetting('live_source'))==1:
        providers=[('ak','Akamai')]
    elif int(ADDON.getSetting('live_source'))==2:
        providers=[('llnw','Limelight')]
    else:
        providers=[('ak','Akamai'),('llnw','Limelight')]
    bitrate_selected=int(ADDON.getSetting('live_bitrate'))
    for provider_url, provider_name in providers:
        # First we query the available streams from this website
        url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio_video/simulcast/hds/uk/pc/%s/%s.f4m' % (provider_url,channelname)
        html = OpenURL(url)
        # Use regexp to get the different versions using various bitrates
        match=re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html.replace('amp;',''))
        streams_available=[]
        for address, bitrate in match:
            url=address.replace('f4m','m3u8')
            streams_available.append((int(bitrate),url))
        streams_available.sort(key=lambda x: x[0], reverse=True)
        # print streams_available
        # Play the prefered option
        if bitrate_selected>0:
            match=[x for x in streams_available if (x[0] == stream_bitrates[bitrate_selected])]
            if len(match)==0:
                # Fallback: Use any lower bitrate from any source.
                match=[x for x in streams_available if (x[0]  in range(1,stream_bitrates[bitrate_selected-1]+1))]
                match.sort(key=lambda x: x[0], reverse=True)
            # print "Selected bitrate is %s"%stream_bitrates[bitrate_selected]
            # print match
            # print "Playing %s from %s with bitrate %s"%(name, match[0][1], match [0][0])
            PlayStream(name,match[0][1],iconimage,'','')
        # Play the fastest available stream of the preferred provider
        else:
            PlayStream(name,streams_available[0][1],iconimage,'','')


# AddAvailableLiveStreamsDirectory retrieves the available live streams for a channel
# Input parameters name and iconimage are only used for displaying the channel.
# Input parameter channelname determines which channel is queried.
def AddAvailableLiveStreamsDirectory(name,channelname,iconimage):
    providers=[('ak','Akamai'),('llnw','Limelight')]
    for provider_url, provider_name in providers:
        # First we query the available streams from this website
        url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio_video/simulcast/hds/uk/pc/%s/%s.f4m' % (provider_url,channelname)
        html = OpenURL(url)
        # Use regexp to get the different versions using various bitrates
        match=re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html.replace('amp;',''))
        # Add each of them to the Kodi selection menu
        for address, bitrate in match:
            url=address.replace('f4m','m3u8')
            # For easier selection use colors to indicate high and low bitrate streams
            if int(bitrate) > 2100 :
                title=name+' - [COLOR white]%s[/COLOR] - [COLOR green]%s kbps[/COLOR]'%(provider_name,bitrate)
            elif int(bitrate) > 1000:
                title=name+' - [COLOR white]%s[/COLOR] - [COLOR yellow]%s kbps[/COLOR]'%(provider_name,bitrate)
            elif int(bitrate) > 600:
                title=name+' - [COLOR white]%s[/COLOR] - [COLOR orange]%s kbps[/COLOR]'%(provider_name,bitrate)
            else:
                title=name+' - [COLOR white]%s[/COLOR] - [COLOR red]%s kbps[/COLOR]'%(provider_name,bitrate)
            # Finally add them to the selection menu.
            AddMenuEntry(title,url,201,iconimage,'','') 


def OpenURL(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:38.0) Gecko/20100101 Firefox/41.0'}
    r = requests.get(url, headers=headers)
    return r.content

    
def PlayStream(name,url,iconimage,description,subtitles_url):
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels={'Title':name})
    liz.setProperty("IsPlayable","true")
    liz.setPath(url)
    # print url
    # print subtitles_url
    # print name
    # print iconimage
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        subtitles_file = download_subtitles(subtitles_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        # Successfully started playing something?
        while 1:
            if xbmc.Player().isPlaying():
                break;
            else:
                xbmc.sleep(500)
        # print subtitles_file
        # print "Now playing subtitles"
        xbmc.Player().setSubtitles(subtitles_file)
    # else:
        # print "Not playing subtitles"


def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

re_date = re.compile('([0-9]{1,2})[/]([0-9]{1,2})[/]([0-9]{4})')

# AddMenuEntry adds a new line to the Kodi list of playables.
# It is used in multiple ways in the plugin, which are distinguished by modes.
def AddMenuEntry(name,url,mode,iconimage,description,subtitles_url):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&description="+urllib.quote_plus(description)+"&subtitles_url="+urllib.quote_plus(subtitles_url)
        # print u
        liz=xbmcgui.ListItem(label=name, label2=description, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        # Sometimes the names contain dates, e.g. for programmes which are broadcast daily.
        # In this case, try to extract the date from the title and add it as an InfoLabel to allow sorting by date.
        date = re_date.findall(name)
        if date:
            date_string = "%s.%s.%s"%(date[0][0],date[0][1],date[0][2])
            # print date_string
        else:
            # Use a dummy date for all entries without a date.
            date_string = "01.01.2999"
        liz.setInfo( "video", infoLabels={ "title": name, "plot": description, "plotoutline": description, "date": date_string} )
        menu=[]
        # Modes 201-299 will create a new playable line.
        if ((mode==201) or (mode==202) or (mode==203)):
            # print "Adding playable entry with subtitles file: %s"%subtitles_url
            liz.setProperty("IsPlayable","true")
            liz.setProperty("IsFolder","false")
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        # Other modes will create a new directory line.
        else:
            liz.setProperty("IsPlayable","false")
            liz.setProperty("IsFolder","true")
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        liz.setProperty("Property(Addon.Name)","iPlayer WWW")
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
        return True

re_subtitles = re.compile('^\s*<p.*?begin=\"(.*?)\.([0-9]+)\"\s+.*?end=\"(.*?)\.([0-9]+)\"\s*>(.*?)</p>')

def download_subtitles(url):
    # Download and Convert the TTAF format to srt
    # SRT:
    #1
    #00:01:22,490 --> 00:01:26,494
    #Next round!
    #
    #2
    #00:01:33,710 --> 00:01:37,714
    #Now that we've moved to paradise, there's nothing to eat.
    #

    # TT:
    #<p begin="0:01:12.400" end="0:01:13.880">Thinking.</p>

    outfile = os.path.join(DIR_USERDATA, 'iplayer.srt')
    # print "Downloading subtitles from %s to %s"%(url, outfile)
    fw = open(outfile, 'w')

    if not url:
        fw.write("1\n0:00:00,001 --> 0:01:00,001\nNo subtitles available\n\n")
        fw.close()
        return

    txt = OpenURL(url)

    # print txt

    i=0
    prev = None

    # some of the subtitles are a bit rubbish in particular for live tv
    # with lots of needless repeats. The follow code will collapse sequences
    # of repeated subtitles into a single subtitles that covers the total time
    # period. The downside of this is that it would mess up in the rare case
    # where a subtitle actually needs to be repeated
    for line in txt.split('\n'):
        entry = None
        m = re_subtitles.match(line)
        # print line
        # print m
        if m:
            start_mil = "%s000" % m.group(2) # pad out to ensure 3 digits
            end_mil   = "%s000" % m.group(4)

            ma = {'start'     : m.group(1),
                  'start_mil' : start_mil[:3],
                  'end'       : m.group(3),
                  'end_mil'   : end_mil[:3],
                  'text'      : m.group(5)}

            ma['text'] = ma['text'].replace('&amp;', '&')
            ma['text'] = ma['text'].replace('&gt;', '>')
            ma['text'] = ma['text'].replace('&lt;', '<')
            ma['text'] = ma['text'].replace('<br />', '\n')
            ma['text'] = ma['text'].replace('<br/>', '\n')
            ma['text'] = re.sub('<.*?>', '', ma['text'])
            ma['text'] = re.sub('&#[0-9]+;', '', ma['text'])
            #ma['text'] = ma['text'].replace('<.*?>', '')
            # print ma
            if not prev:
                # first match - do nothing wait till next line
                prev = ma
                continue

            if prev['text'] == ma['text']:
                # current line = previous line then start a sequence to be collapsed
                prev['end'] = ma['end']
                prev['end_mil'] = ma['end_mil']
            else:
                i += 1
                entry = "%d\n%s,%s --> %s,%s\n%s\n\n" % (i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], prev['text'])
                prev = ma
        elif prev:
            i += 1
            entry = "%d\n%s,%s --> %s,%s\n%s\n\n" % (i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], prev['text'])

        if entry: fw.write(entry)

    fw.close()
    return outfile

        
params=get_params()
url=None
name=None
mode=None
iconimage=None
description=None
subtitles_url=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        iconimage=urllib.unquote_plus(params["iconimage"])
except:
        pass
try:        
        mode=int(params["mode"])
except:
        pass
try:        
        description=urllib.unquote_plus(params["description"])
except:
        pass
try:        
        subtitles_url=urllib.unquote_plus(params["subtitles_url"])
except:
        pass

 
        
# These are the modes which tell the plugin where to go.
if mode==None or url==None or len(url)<1:
        CATEGORIES()
       
# Modes 101-119 will create a main directory menu entry
elif mode==101:
        ListLive()        
        
elif mode==102:
        ListAtoZ()
     
elif mode==103:
        ListCategories()

elif mode==104:
        Search()

elif mode==105:
        ListMostPopular()

elif mode==106:
        ListHighlights()

# Modes 121-199 will create a sub directory menu entry
elif mode==121:
        GetEpisodes(url)

elif mode==122:
        GetAvailableStreams(name,url,iconimage,description)

elif mode==123:
        AddAvailableLiveStreamsDirectory(name,url,iconimage)

elif mode==124:
        GetAtoZPage(url)

elif mode==125:
        ListCategoryFilters(url)

elif mode==126:
        GetFilteredCategory(url)

elif mode==127:
        GetGroups(url)

# Modes 201-299 will create a playable menu entry, not a directory
elif mode==201:
        PlayStream(name,url,iconimage,description,subtitles_url)

elif mode==202:
        AddAvailableStreamItem(name,url,iconimage,description)

elif mode==203:
        AddAvailableLiveStreamItem(name,url,iconimage)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

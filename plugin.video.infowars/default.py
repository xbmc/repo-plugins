### ############################################################################################################
### ############################################################################################################
###	#	
### # Project: 			#		Infowars.com Plugin
###	#	
#### Email @ thomasmeadows@gmail.com
### ############################################################################################################
### ############################################################################################################

### ############################################################################################################
### ############################################################################################################
### ############################################################################################################
##### Imports #####
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import urllib,urllib2,re,os,sys,htmllib,string,StringIO,logging,random,array,time,datetime
import copy
import HTMLParser, htmlentitydefs
try: 		from sqlite3 										import dbapi2 as sqlite; print "Loading sqlite3 as DB engine"
except: from pysqlite2 									import dbapi2 as sqlite; print "Loading pysqlite2 as DB engine"
try: 			from addon.common.addon 				import Addon
except:
	try: 		from t0mm0.common.addon 				import Addon
	except: 
		try: from c_t0mm0_common_addon 				import Addon
		except: pass
##### /\ ##### Imports #####

### ############################################################################################################
### ############################################################################################################
### ############################################################################################################



### ############################################################################################################
### ############################################################################################################
### ############################################################################################################
### Plugin Settings ###

_addon=Addon('plugin.video.infowars', sys.argv); addon=_addon; 
addon=_addon; 
_domain_url="infowars.com"
_addonPath	=xbmc.translatePath('Infowars')
_addon_path_art= ""
_artPath		=xbmc.translatePath(os.path.join(_addonPath,_addon_path_art))
_datapath 	=xbmc.translatePath(_addon.get_profile()); 
_artIcon		=_addon.get_icon(); 
_artFanart	=_addon.get_fanart()
__plugin__ = "Infowars"
__authors__ = "Prafit | Spinalcracker"
__plugin__= "Infowars"
__credits__= ""
_addon_id="plugin.video.infowars"
_database_name="infowars"
_plugin_id= "plugin.video.infowars"
_database_file=os.path.join(xbmc.translatePath("special://database"),'infowars.db'); 
_debugging= False

### ##### /\ ##### Plugin Settings ###

### ############################################################################################################
### ############################################################################################################
### ############################################################################################################


### ############################################################################################################
### ############################################################################################################
### ############################################################################################################
##plugin tools


module_log_enabled = False

# Write something on XBMC log
def log(message):
    xbmc.log(message)

# Write this module messages on XBMC log
def _log(message):
    if module_log_enabled:
        xbmc.log(""+message)

# Parse XBMC params - based on script.module.parsedom addon    
def get_params():
    _log("get_params")
    
    param_string = sys.argv[2]
    
    _log("get_params "+str(param_string))
    
    commands = {}

    if param_string:
        split_commands = param_string[param_string.find('?') + 1:].split('&')
    
        for command in split_commands:
            _log("get_params command="+str(command))
            if len(command) > 0:
                if "=" in command:
                    split_command = command.split('=')
                    key = split_command[0]
                    value = urllib.unquote_plus(split_command[1])
                    commands[key] = value
                else:
                    commands[command] = ""
    
    _log("get_params "+repr(commands))
    return commands

# Fetch text content from an URL
def read(url):
    _log("read "+url)

    f = urllib2.urlopen(url)
    data = f.read()
    f.close()
    
    return data

# Parse string and extracts multiple matches using regular expressions
def find_multiple_matches(text,pattern):
    _log("find_multiple_matches pattern="+pattern)
    
    matches = re.findall(pattern,text,re.DOTALL)

    return matches

# Parse string and extracts first match as a string
def find_single_match(text,pattern):
    _log("find_single_match pattern="+pattern)

    result = ""
    try:    
        matches = re.findall(pattern,text, flags=re.DOTALL)
        result = matches[0]
    except:
        result = ""

    return result

def add_item( action="" , title="" , plot="" , url="" ,thumbnail="" , folder=True ):
    _log("add_item action=["+action+"] title=["+title+"] url=["+url+"] thumbnail=["+thumbnail+"] folder=["+str(folder)+"]")

    listitem = xbmcgui.ListItem( title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail )
    listitem.setInfo( "video", { "Title" : title, "FileName" : title, "Plot" : plot } )
    
    if url.startswith("plugin://"):
        itemurl = url
        listitem.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=itemurl, listitem=listitem)
    else:
        itemurl = '%s?action=%s&title=%s&url=%s&thumbnail=%s&plot=%s' % ( sys.argv[ 0 ] , action , urllib.quote_plus( title ) , urllib.quote_plus(url) , urllib.quote_plus( thumbnail ) , urllib.quote_plus( plot ))
        xbmcplugin.addDirectoryItem( handle=int(sys.argv[1]), url=itemurl, listitem=listitem, isFolder=folder)

def close_item_list():
    _log("close_item_list")
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

def play_resolved_url(url):
    _log("play_resolved_url ["+url+"]")
    listitem = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)

## / plugin tools

def filename_from_title(title, video_type):
    if video_type == 'tvshow':
        filename = '%s S%sE%s.strm'
        filename = filename % (title, '%s', '%s')
    else:
        filename = '%s.strm' % title

    filename = re.sub(r'(?!%s)[^\w\-_\. ]', '_', filename)
    xbmc.makeLegalFilename(filename)
    return filename
	
def addpr(r,s=''): return _addon.queries.get(r,s) ## Get Params
def tfalse(r,d=False): ## Get True / False
	if   (r.lower()=='true' ): return True
	elif (r.lower()=='false'): return False
	else: return d

_setting={}; 

def eod(): xbmcplugin.endOfDirectory(int(sys.argv[1]))
def myNote(header='',msg='',delay=5000,image=''): _addon.show_small_popup(title=header,msg=msg,delay=delay,image=image)
def cFL( t,c="green"): return '[COLOR '+c+']'+t+'[/COLOR]' ### For Coloring Text ###
def cFL_(t,c="green"): return '[COLOR '+c+']'+t[0:1]+'[/COLOR]'+t[1:] ### For Coloring Text (First Letter-Only) ###
def notification(header="", message="", sleep=5000 ): xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i)" % ( header, message, sleep ) )
def WhereAmI(t): ### for Writing Location Data to log file ###
	if (_debugging==True): print 'Where am I:  '+t
def deb(s,t): ### for Writing Debug Data to log file ###
	if (_debugging==True): print s+':  '+t
def debob(t): ### for Writing Debug Object to log file ###
	if (_debugging==True): print t
def nolines(t):
	it=t.splitlines(); t=''
	for L in it: t=t+L
	t=((t.replace("\r","")).replace("\n",""))
	return t
def isPath(path): return os.path.exists(path)
def isFile(filename): return os.path.isfile(filename)
def askSelection(option_list=[],txtHeader=''):
	if (option_list==[]): 
		if (debugging==True): print 'askSelection() >> option_list is empty'
		return None
	dialogSelect = xbmcgui.Dialog();
	index=dialogSelect.select(txtHeader, option_list)
	return index
def iFL(t): return '[I]'+t+'[/I]' ### For Italic Text ###
def bFL(t): return '[B]'+t+'[/B]' ### For Bold Text ###
def _FL(t,c,e=''): ### For Custom Text Tags ###
	if (e==''): d=''
	else: d=' '+e
	return '['+c.upper()+d+']'+t+'[/'+c.upper()+']'

def build_listitem(video_type, title, year, img, resurl, movie_num='', imdbnum='', season='', episode='', extra_cms=None, subs=None):
    if not subs: subs = []
    if not extra_cms: extra_cms = []
    menu_items = extra_cms
    queries = {'mode': 'add_to_library', 'video_type': video_type, 'movie_num': movie_num, 'title': title, 'img': img, 'year': year, 'url': resurl, 'imdbnum':imdbnum}
    runstring = 'RunPlugin(%s)' % _addon.build_plugin_url(queries)
    menu_items.append(('Add to Library', runstring), )

    disp_title = title
    listitem = xbmcgui.ListItem(disp_title, iconImage=img, thumbnailImage=img)
    listitem.addContextMenuItems(menu_items, replaceItems=True)
    return listitem


def add_to_library(video_type, url, title, img, year, imdbnum, movie_num=''):
    try: _addon.log('Creating .strm for %s %s %s %s %s %s' % (video_type, title, imdbnum, url, img, year))
    except: pass
    if video_type == 'tvshow':
        save_path = _addon.get_setting('tvshow-folder')
        save_path = xbmc.translatePath(save_path)
        strm_string = _addon.build_plugin_url(
            {'mode': 'NightlyNewsSubMenu','dialog': '1'})
        if year: title = '%s (%s)' % (title, year)
        filename = filename_from_title(title + ' s1e1', 'movie')
        title = re.sub(r'[^\w\-_\. ]', '_', title)
        titles = title
        final_path = os.path.join(save_path, title, filename)
        final_path = xbmc.makeLegalFilename(final_path)
        if not xbmcvfs.exists(os.path.dirname(final_path)):
            try:
                try: xbmcvfs.mkdirs(os.path.dirname(final_path))
                except: os.path.mkdir(os.path.dirname(final_path))
            except Exception, e:
                try: _addon.log('Failed to create directory %s' % final_path)
                except: pass
                # if not xbmcvfs.exists(final_path):
                #temp disabled bc of change in .strm format. Reenable in next version
        try:
            file_desc = xbmcvfs.File(final_path, 'w')
            file_desc.write(strm_string)
            file_desc.close()
        except Exception, e:
            _addon.log('Failed to create .strm file: %s\n%s' % (final_path, e))
    elif video_type == 'movie':
        save_path = _addon.get_setting('movie-folder')
        save_path = xbmc.translatePath(save_path)
        strm_string = _addon.build_plugin_url(
            {'mode': 'DocSubMenu','dialog': '1', 'movie_num': movie_num})
        if year: title = '%s (%s)' % (title, year)
        filename = filename_from_title(title, 'movie')
        title = re.sub(r'[^\w\-_\. ]', '_', title)
        final_path = os.path.join(save_path, title, filename)
        final_path = xbmc.makeLegalFilename(final_path)
        if not xbmcvfs.exists(os.path.dirname(final_path)):
            try:
                try: xbmcvfs.mkdirs(os.path.dirname(final_path))
                except: os.path.mkdir(os.path.dirname(final_path))
            except Exception, e:
                try: _addon.log('Failed to create directory %s' % final_path)
                except: pass
                # if not xbmcvfs.exists(final_path):
                #temp disabled bc of change in .strm format. Reenable in next version
        try:
            file_desc = xbmcvfs.File(final_path, 'w')
            file_desc.write(strm_string)
            file_desc.close()
        except Exception, e:
            _addon.log('Failed to create .strm file: %s\n%s' % (final_path, e))

	
### ############################################################################################################
### ############################################################################################################
##### Queries #####
_param={}
##Notes-> add more here for whatever params you want to use then you can just put the tagname within _param[''] to fetch it later.  or you can use addpr('tagname','defaultvalue').
_param['mode']=addpr('mode',''); _param['url']=addpr('url',''); _param['pagesource'],_param['pageurl'],_param['pageno'],_param['pagecount']=addpr('pagesource',''),addpr('pageurl',''),addpr('pageno',0),addpr('pagecount',1)
_param['img']=addpr('img',''); _param['fanart']=addpr('fanart',''); _param['thumbnail'],_param['thumbnail'],_param['thumbnail']=addpr('thumbnail',''),addpr('thumbnailshow',''),addpr('thumbnailepisode','')
_param['section']=addpr('section','movies'); _param['title']=addpr('title',''); _param['year']=addpr('year',''); _param['genre']=addpr('genre','')
_param['by']=addpr('by',''); _param['letter']=addpr('letter',''); _param['showtitle']=addpr('showtitle',''); _param['showyear']=addpr('showyear',''); _param['listitem']=addpr('listitem',''); _param['infoLabels']=addpr('infoLabels',''); _param['season']=addpr('season',''); _param['episode']=addpr('episode','')
_param['pars']=addpr('pars',''); _param['labs']=addpr('labs',''); _param['name']=addpr('name',''); _param['thetvdbid']=addpr('thetvdbid','')
_param['plot']=addpr('plot',''); _param['tomode']=addpr('tomode',''); _param['country']=addpr('country','')
_param['thetvdb_series_id']=addpr('thetvdb_series_id',''); _param['dbid']=addpr('dbid',''); _param['user']=addpr('user','')
_param['subfav']=addpr('subfav',''); _param['episodetitle']=addpr('episodetitle',''); _param['special']=addpr('special',''); _param['studio']=addpr('studio','')


### ############################################################################################################
### ############################################################################################################
### ############################################################################################################
##### Player Functions #####
def PlayURL(url):
	play=xbmc.Player() ### xbmc.PLAYER_CORE_AUTO | xbmc.PLAYER_CORE_DVDPLAYER | xbmc.PLAYER_CORE_MPLAYER | xbmc.PLAYER_CORE_PAPLAYER
	try: _addon.resolve_url(url)
	except: t=''
	try: play.play(url)
	except: t=''
	
def play(params):
    play_resolved_url( params.get("url") )	
    
### ############################################################################################################
### ############################################################################################################
### ############################################################################################################

def Menu_MainMenu(): #The Main Menu
    WhereAmI('@ the Main Menu')
    _addon.add_directory({'mode': 'PlayURL','url':'http://infowarslive-lh.akamaihd.net/i/infowarslivestream_1@353459/index_800_av-p.m3u8?sd=10&rebase=on'},{'title':  cFL_('Infowars.com Live Video(Loops After Airing)','lime')},is_folder=False,img=_artIcon,fanart=_artFanart)
    _addon.add_directory({'mode': 'PlayURL','url':'http://www.infowars.com/stream.pls'},{'title':  cFL_('Infowars.com Live Audio(Loops After Airing)','lime')},is_folder=False,img=_artIcon,fanart=_artFanart)
    video_type = ('tvshow')
    title = ('Infowars Nightly News')
    year = ('')
    img = _artIcon
    imdbnum = ''
    url = 'plugin://plugin.video.infowars'
    resurl = 'plugin://plugin.video.infowars'
    listitem = build_listitem(video_type, title, year, img, resurl)
    #url = '%s/%s' % (BASE_URL, resurl)
    queries = {'mode': 'NightlyNewsSubMenu'}
    li_url = _addon.build_plugin_url(queries)
    xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=True)
    #_addon.add_directory({'mode': 'NightlyNewsSubMenu','title':'Infowars Nightly News'},{'title':  cFL_('Infowars Nightly News','red')},is_folder=True,img=_artIcon,fanart=_artFanart)
    _addon.add_directory({'mode': 'ClipsSubMenu','title':'Infowars Nightly News'},{'title':  cFL_('Infowars Clips','red')},is_folder=True,img=_artIcon,fanart=_artFanart)
    _addon.add_directory({'mode': 'DocSubMenu','title':'Acclaimed Documentaries'},{'title':  cFL_('Acclaimed Documentaries','blanchedalmond')},is_folder=True,img=_artIcon,fanart=_artFanart)
    _addon.add_directory({'mode': 'HistoricShowsSubMenu','title':'Past Alex Jones Shows(video)'},{'title':  cFL_('Past Alex Jones Shows (Video)','yellow')},is_folder=True,img=_artIcon,fanart=_artFanart)
    _addon.add_directory({'mode': 'HistoricShowsAudioSubMenu','title':'Past Alex Jones Shows(video)'},{'title':  cFL_('Past Alex Jones (Audio)','yellow')},is_folder=True,img=_artIcon,fanart=_artFanart)
    _addon.add_directory({'mode': 'PaulJosephWatsonSubMenu','title':'Paul Joseph Watson (Video)'},{'title':  cFL_('Paul Joseph Watson (Video)','blue')},is_folder=True,img=_artIcon,fanart=_artFanart)
    eod()


def Documentary_Sub_Menu(title='', movie_num=''): #The Main Menu
    WhereAmI('@ Documentaries')
    #mode left blank for main menu.
    if not movie_num:
        video_type = ('movie')
        title = ('Strategic Relocation')
        img = _artIcon
        year = ''
        movie_num = '19'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        li_url = 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=jzjm9MJFSA8'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('911 Truth Hollywood Speaks Out')
        img = _artIcon
        year = ''
        movie_num = '18'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=3X4hbIDnq5k'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Invisible Empire A New World Order Defined ')
        img = _artIcon
        year = ''
        movie_num = '17'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=NO24XmP1c5E'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Police State 4 The Rise of Fema')
        img = _artIcon
        year = ''
        movie_num = '16'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=Klqv9t1zVww'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Fall of the Republic')
        img = _artIcon
        year = ''
        movie_num = '15'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=VebOTc-7shU'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('The Obama Deception')
        img = _artIcon
        year = ''
        movie_num = '14'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=eAaQNACwaLw'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Truth Rising')
        img = _artIcon
        year = ''
        movie_num = '13'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=t-yscpNIxjI'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('End Game')
        img = _artIcon
        year = ''
        movie_num = '12'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=x-CrNlilZho'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('TerrorStorm')
        img = _artIcon
        year = ''
        movie_num = '11'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=vrXgLhkv21Y'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Martial Law 911 Rise of the Police State')
        img = _artIcon
        year = ''
        movie_num = '10'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=FIzT6r56CnY'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('911 The Road to Tyranny')
        img = _artIcon
        year = ''
        movie_num = '9'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=OVMyH8eOHKs'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Matrix of Evil')
        img = _artIcon
        year = ''
        movie_num = '8'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=9wRuiqqoHFY'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('America Destroyed by Design')
        img = _artIcon
        year = ''
        movie_num = '7'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=vsKVyhuBf3c'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('American Dictators')
        img = _artIcon
        year = ''
        movie_num = '6'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=1Fr5QC6u2EQ'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Dark Secrets Inside Bohemian Grove')
        img = _artIcon
        year = ''
        movie_num = '5'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=FVtEvplXMLs'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('The Order of Death')
        img = _artIcon
        year = ''
        movie_num = '4'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=VhlRIH9iPD4'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Police State 2000')
        img = _artIcon
        year = ''
        movie_num = '3'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=3zkxyFhqQJ4'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Police State II The Take Over')
        img = _artIcon
        year = ''
        movie_num = '2'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=g7kh1j8ZkEs'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
        video_type = ('movie')
        title = ('Police State 3 Total Enslavement')
        img = _artIcon
        year = ''
        movie_num = '1'
        resurl = 'plugin://plugin.video.infowars'
        listitem = build_listitem(video_type, title, year, img, resurl, movie_num)
        listitem.setProperty('IsPlayable', 'true')
        #url = '%s/%s' % (BASE_URL, resurl)
        li_url ='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=K4RWRm-bgv8'
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), li_url, listitem,isFolder=False)
    elif(movie_num=='19'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=jzjm9MJFSA8') 
    elif(movie_num=='18'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=3X4hbIDnq5k')
    elif(movie_num=='17'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=NO24XmP1c5E')
    elif(movie_num=='16'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=Klqv9t1zVww')
    elif(movie_num=='15'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=VebOTc-7shU')    
    elif(movie_num=='14'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=eAaQNACwaLw')
    elif(movie_num=='13'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=t-yscpNIxjI')
    elif(movie_num=='12'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=x-CrNlilZho')
    elif(movie_num=='11'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=vrXgLhkv21Y')
    elif(movie_num=='10'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=FIzT6r56CnY')
    elif(movie_num=='9'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=OOVMyH8eOHKs')
    elif(movie_num=='8'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=9wRuiqqoHFY')
    elif(movie_num=='7'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=vsKVyhuBf3c')
    elif(movie_num=='6'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=1Fr5QC6u2EQ')
    elif(movie_num=='5'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=FVtEvplXMLs')
    elif(movie_num=='4'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=VhlRIH9iPD4')
    elif(movie_num=='3'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=3zkxyFhqQJ4')
    elif(movie_num=='2'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=g7kh1j8ZkEs')
    elif(movie_num=='1'):
        addon.resolve_url('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=K4RWRm-bgv8')
        
    eod() #Ends the directory listing and prints it to the screen.  if you dont use eod() or something like it, the menu items won't be put to the screen.

def Nightly_News_Sub_Menu(title='',dialog=''): #The Main Menu
    #https://www.youtube.com/user/RonGibsonCF
    WhereAmI('@ Nightly News')
    url = 'https://www.youtube.com/feeds/videos.xml?playlist_id=PLs5CVvsn63q4kI41GLAa-1BCHsPQ1eZrk'
    response = urllib2.urlopen(url)
    if response and response.getcode() == 200:
        content = response.read()
        videos= find_multiple_matches(content,"<entry>(.*?)</entry>")
        sources = []
        for entry in videos: 
            title = find_single_match(entry,"<titl[^>]+>([^<]+)</title>")
            plot = find_single_match(entry,"<media\:descriptio[^>]+>([^<]+)</media\:description>")
            thumbnail = find_single_match(entry,"<media\:thumbnail url=\"(.*?)\"")
            video_id = find_single_match(entry,"<yt\:videoId>([^<]+)</yt\:videoId>")
            url = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
            if title.find('Nightly News') > -1:
                add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False )
            #else:
                #_addon.log('Error while trying to resolve %s' % url)  
    else:
        util.showError(ADDON_ID, 'Could not open URL %s to create menu' % (url))
    eod()


def Historic_Shows_Sub_Menu(title=''): #The Main Menu
    #https://www.youtube.com/user/RonGibsonCF
    WhereAmI('@ Historic Shows Video')
    url = 'https://www.youtube.com/feeds/videos.xml?playlist_id=PLs5CVvsn63q5-cWWrqXo0nhWQCBVWcT8Z'
    response = urllib2.urlopen(url)
    if response and response.getcode() == 200:
        content = response.read()
        videos= find_multiple_matches(content,"<entry>(.*?)</entry>")
        for entry in videos:
            title = find_single_match(entry,"<titl[^>]+>([^<]+)</title>")
            plot = find_single_match(entry,"<media\:descriptio[^>]+>([^<]+)</media\:description>")
            thumbnail = find_single_match(entry,"<media\:thumbnail url=\"(.*?)\"")
            video_id = find_single_match(entry,"<yt\:videoId>([^<]+)</yt\:videoId>")
            url = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
            if title.find('Alex Jones (FULL SHOW Commercial Free)') > -1:
                add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False )
                #if title.find('Podcast') > -1:
                #    add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False )
    else:
        util.showError(ADDON_ID, 'Could not open URL %s to create menu' % (url))

    eod()	

def Clips_Sub_Menu(title=''): #The Main Menu
    #https://www.youtube.com/user/TheAlexJonesChannel
    WhereAmI('@ Clips')
    url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCvsye7V9psc-APX6wV1twLg'
    response = urllib2.urlopen(url)
    if response and response.getcode() == 200:
        content = response.read()
        videos= find_multiple_matches(content,"<entry>(.*?)</entry>")
        for entry in videos:
            title = find_single_match(entry,"<titl[^>]+>([^<]+)</title>")
            plot = find_single_match(entry,"<media\:descriptio[^>]+>([^<]+)</media\:description>")
            thumbnail = find_single_match(entry,"<media\:thumbnail url=\"(.*?)\"")
            video_id = find_single_match(entry,"<yt\:videoId>([^<]+)</yt\:videoId>")
            url = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
            add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False )
    else:
        util.showError(ADDON_ID, 'Could not open URL %s to create menu' % (url))

    eod()

def Historic_Shows_Audio_Sub_Menu(title=''): #The Main Menu
    #https://www.youtube.com/user/RonGibsonCF
    WhereAmI('@ Nightly News')
    url = 'https://www.youtube.com/feeds/videos.xml?playlist_id=PLs5CVvsn63q4r4b-RXs4QAaC-Eoc53NgP'
    response = urllib2.urlopen(url)
    if response and response.getcode() == 200:
        content = response.read()
        videos= find_multiple_matches(content,"<entry>(.*?)</entry>")
        for entry in videos:
            title = find_single_match(entry,"<titl[^>]+>([^<]+)</title>")
            plot = find_single_match(entry,"<media\:descriptio[^>]+>([^<]+)</media\:description>")
            thumbnail = find_single_match(entry,"<media\:thumbnail url=\"(.*?)\"")
            video_id = find_single_match(entry,"<yt\:videoId>([^<]+)</yt\:videoId>")
            url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid="+video_id
            if title.find('AJ Show') > -1:
                add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False )
                #if title.find('Podcast') > -1:
                #    add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False )
    else:
        util.showError(ADDON_ID, 'Could not open URL %s to create menu' % (url))

    eod()

def Paul_Joseph_Watson_Sub_Menu(title=''): #The Main Menu
    #https://www.youtube.com/user/PrisonPlanetLive
    WhereAmI('@ Paul Joseph Watson')
    url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCittVh8imKanO_5KohzDbpg'
    response = urllib2.urlopen(url)
    if response and response.getcode() == 200:
        content = response.read()
        videos= find_multiple_matches(content,"<entry>(.*?)</entry>")
        for entry in videos:
            title = find_single_match(entry,"<titl[^>]+>([^<]+)</title>")
            plot = find_single_match(entry,"<media\:descriptio[^>]+>([^<]+)</media\:description>")
            thumbnail = find_single_match(entry,"<media\:thumbnail url=\"(.*?)\"")
            video_id = find_single_match(entry,"<yt\:videoId>([^<]+)</yt\:videoId>")
            url = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
            add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False )
    else:
        util.showError(ADDON_ID, 'Could not open URL %s to create menu' % (url))

    eod()    
    
def check_mode(mode=''):
    mode = _addon.queries.get('mode', None)
    section = _addon.queries.get('section', '')
    genre = _addon.queries.get('genre', '')
    letter = _addon.queries.get('letter', '')
    sort = _addon.queries.get('sort', '')
    url = _addon.queries.get('url', '')
    title = _addon.queries.get('title', '')
    img = _addon.queries.get('img', '')
    season = _addon.queries.get('season', '')
    query = _addon.queries.get('query', '')
    page = _addon.queries.get('page', '')
    imdbnum = _addon.queries.get('imdbnum', '')
    year = _addon.queries.get('year', '')
    video_type = _addon.queries.get('video_type', '')
    episode = _addon.queries.get('episode', '')
    season = _addon.queries.get('season', '')
    tvdbnum = _addon.queries.get('tvdbnum', '')
    alt_id = _addon.queries.get('alt_id', '')
    dialog = _addon.queries.get('dialog', '')
    day = _addon.queries.get('day', '')
    movie_num = _addon.queries.get('movie_num', '')
    WhereAmI('@ Checking Mode')
    deb('Mode',mode)
    if (mode=='') or (mode=='main') or (mode=='MainMenu'):  Menu_MainMenu() ## Default Menu
    elif (mode=='PlayURL'): 							PlayURL(_param['url']) ## Play Video
    elif (mode=='play'): 							play(params) ## Play Video
    elif (mode=='DocSubMenu'): 						Documentary_Sub_Menu(_param['title'], movie_num) ## Play Video
    elif (mode=='ClipsSubMenu'): 						Clips_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='NightlyNewsSubMenu'): 						Nightly_News_Sub_Menu(_param['title'], dialog) ## Play Video
    elif (mode=='HistoricShowsSubMenu'): 						Historic_Shows_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='HistoricShowsAudioSubMenu'): 						Historic_Shows_Audio_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='PaulJosephWatsonSubMenu'): 						Paul_Joseph_Watson_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='Settings'): 							_addon.addon.openSettings() # Another method: _plugin.openSettings() ## Settings for this addon.
    elif (mode=='ResolverSettings'): 			urlresolver.display_settings()  ## Settings for UrlResolver script.module.
    elif (mode == 'add_to_library'):
        add_to_library(video_type, url, title, img, year, imdbnum, movie_num)
        builtin = "XBMC.Notification(Add to Library,Added '%s' to library,2000, %s)" % (title, _artIcon)
        xbmc.executebuiltin(builtin)
    #
    #
    #elif (mode=='YourMode'): 						YourFunction(_param['url'])
    #
    #
    #
    else: myNote(header='Mode:  "'+mode+'"',msg='[ mode ] not found.'); Menu_MainMenu() ## So that if a mode isn't found, it'll goto the Main Menu and give you a message about it.


deb('param >> title',_param['title'])
deb('param >> url',_param['url']) ### Simply Logging the current query-passed / param -- URL
check_mode(_param['mode']) ### Runs the function that checks the mode and decides what the plugin should do. This should be at or near the end of the file.
### ############################################################################################################
### ############################################################################################################
### ############################################################################################################

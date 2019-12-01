### ############################################################################################################
### ############################################################################################################
###	#	
### # Project: 			#		Infowars.com Plugin
###	#	                        ver. 2.1.4
#### Email @ thomasmeadows@gmail.com
### ############################################################################################################
### ############################################################################################################

### ############################################################################################################
### ############################################################################################################
### ############################################################################################################
##### Imports #####
import xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs, xbmc
import urllib,urllib2,re,os,sys,htmllib,string,StringIO,logging,random,array,time,datetime, ssl, socket
import copy
import json,requests
import HTMLParser, htmlentitydefs

#import simplejson as json
try: 		from sqlite3 										import dbapi2 as sqlite; print("Loading sqlite3 as DB engine")
except: from pysqlite2 									import dbapi2 as sqlite; print("Loading pysqlite2 as DB engine")
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

IW_addon=Addon('plugin.video.infowars', sys.argv); addon=IW_addon; 
addon=IW_addon; 
IW_domain_url="infowars.com"
IW_addonPath	=xbmc.translatePath('Infowars')
IW_addon_path_art= ""
IW_artPath		=xbmc.translatePath(os.path.join(IW_addonPath,IW_addon_path_art))
IW_datapath 	=xbmc.translatePath(IW_addon.get_profile()); 
IW_artIcon		=IW_addon.get_icon(); 
IW_artFanart	=IW_addon.get_fanart();
IW_plugin = "Infowars"
IW_authors = "Prafit, Spinalcracker"
IW_credits= ""
IW_addon_id="plugin.video.infowars"
IW_database_name="infowars"
IW_plugin_id= "plugin.video.infowars"
IW_database_file=os.path.join(xbmc.translatePath("special://database"),'infowars.db'); 
IW_debugging= False
AJSIcon = "https://imgur.com/YYl3GFe.png"
DKSIcon = "https://static.infowars.com/images/DKS-logo.png"
DKSFanart = "https://static.infowars.com/images/DKS-bg.jpg"
WarRoomIcon = "https://static.infowars.com/images/war-room-logo-white.png"
WarRoomFanart = "https://static.infowars.com/images/war-room-studio.jpg"
FPIcon = "https://i.imgur.com/Nc3LAtC.png"
FPFanart = "https://i.imgur.com/VsMhpSz.jpg"
CTIcon = "https://imgur.com/XA1mZtd.png"
CTFanart = "https://imgur.com/KloueqE.jpg"
IWLiveSEIcon = "https://imgur.com/i4TqWhY.png"
IWLiveSEFanart = "https://www.infowars.com/wp-content/uploads/2018/08/jones-censored23.jpg"
PJWIcon = "https://i.imgur.com/A9R4qjv.jpg"
PJWFanart = "https://i.imgur.com/ZksTDyX.jpg"
MWIcon = "https://i.imgur.com/5KMuph0.jpg"
MWFanart = "https://www.infowarsteam.com/wp-content/uploads/2016/10/Millie-Weaver.jpg"
KBIcon = "https://imgur.com/6eHYGNi.jpg"
KBFanart = "https://imgur.com/2tv5KdN.jpg"
IWODIcon = "https://imgur.com/PcR2j1b.png"
IWODFanart = "https://i.imgur.com/40Prkn5.jpg"##"https://imgur.com/Un7aMqX.jpg"
IWODFLSIcon = "https://imgur.com/fgVD9Ps.png"
IWBDVIcon = "https://i.imgur.com/i9YU0t9.png"

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
    elif url.startswith("https://"):
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
	
def addpr(r,s=''): return IW_addon.queries.get(r,s) ## Get Params
def tfalse(r,d=False): ## Get True / False
	if   (r.lower()=='true' ): return True
	elif (r.lower()=='false'): return False
	else: return d

_setting={}; 

def eod(): xbmcplugin.endOfDirectory(int(sys.argv[1]))
def myNote(header='',msg='',delay=5000,image=''): IW_addon.show_small_popup(title=header,msg=msg,delay=delay,image=image)
def cFL( t,c="green"): return '[COLOR '+c+']'+t+'[/COLOR]' ### For Coloring Text ###
def cFL_(t,c="green"): return '[COLOR '+c+']'+t[0:1]+'[/COLOR]'+t[1:] ### For Coloring Text (First Letter-Only) ###
def notification(header="", message="", sleep=5000 ): xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i)" % ( header, message, sleep ) )
def WhereAmI(t): ### for Writing Location Data to log file ###
	if (IW_debugging==True): print('Where am I:  '+t)
def deb(s,t): ### for Writing Debug Data to log file ###
	if (IW_debugging==True): print(s+':  '+t)
def debob(t): ### for Writing Debug Object to log file ###
	if (IW_debugging==True): print(t)
def nolines(t):
	it=t.splitlines(); t=''
	for L in it: t=t+L
	t=((t.replace("\r","")).replace("\n",""))
	return t
def isPath(path): return os.path.exists(path)
def isFile(filename): return os.path.isfile(filename)
def askSelection(option_list=[],txtHeader=''):
	if (option_list==[]): 
		if (debugging==True): print('askSelection() >> option_list is empty')
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
    runstring = 'RunPlugin(%s)' % IW_addon.build_plugin_url(queries)
    menu_items.append(('Add to Library', runstring), )

    disp_title = title
    listitem = xbmcgui.ListItem(disp_title, iconImage=img, thumbnailImage=img)
    listitem.addContextMenuItems(menu_items, replaceItems=True)
    return listitem

def add_to_library(video_type, url, title, img, year, imdbnum, movie_num=''):
    try: IW_addon.log('Creating .strm for %s %s %s %s %s %s' % (video_type, title, imdbnum, url, img, year))
    except: pass
    if video_type == 'tvshow':
        save_path = IW_addon.get_setting('tvshow-folder')
        save_path = xbmc.translatePath(save_path)
        strm_string = IW_addon.build_plugin_url(
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
            except Exception as e:
                try: IW_addon.log('Failed to create directory %s' % final_path)
                except: pass
        try:
            file_desc = xbmcvfs.File(final_path, 'w')
            file_desc.write(strm_string)
            file_desc.close()
        except Exception as e:
            IW_addon.log('Failed to create .strm file: %s\n%s' % (final_path, e))
    elif video_type == 'movie':
        save_path = IW_addon.get_setting('movie-folder')
        save_path = xbmc.translatePath(save_path)
        strm_string = IW_addon.build_plugin_url(
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
            except Exception as e:
                try: IW_addon.log('Failed to create directory %s' % final_path)
                except: pass
        try:
            file_desc = xbmcvfs.File(final_path, 'w')
            file_desc.write(strm_string)
            file_desc.close()
        except Exception as e:
            IW_addon.log('Failed to create .strm file: %s\n%s' % (final_path, e))


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
    play=xbmc.Player()
    try: IW_addon.resolve_url(url)
    except: t=''
    try: play.play(url)
    except: t=''

def play(params):
    play_resolved_url( params.get("url") )	

def playYoutube(url):
    xbmc.log(url)
    video_id = 'TSTaV8g3zwI'
    url = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
    PlayURL(url)

def ToTop():
    wnd = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    id = wnd.getFocusId()
    IW_addon.log(id)
    IW_addon.log("===========================================")
    xbmc.executebuiltin('SetFocus(id, 1)')

    
### ############################################################################################################
### ############################################################################################################
### ############################################################################################################

def Menu_MainMenu(): #The Main Menu
    WhereAmI('@ the Main Menu')
    IW_addon.add_directory({'mode': 'PlayURL','url':'https://infostream.secure.footprint.net/hls-live/infostream-infostream/_definst_/live.m3u8'},{'title':  cFL_('The Alex Jones Show - (Loops After Airing)','lime')},is_folder=False,img=AJSIcon,fanart=IW_artFanart)
    IW_addon.add_directory({'mode': 'PlayURL','url':'https://infostream.secure.footprint.net/hls-live/infostream2-infostream2/_definst_/live.m3u8'},{'title':  cFL_('The David Knight Show - (Loops After Airing)','orange')},is_folder=False,img=DKSIcon,fanart=DKSFanart)
    IW_addon.add_directory({'mode': 'PlayURL','url':'https://infostream.secure.footprint.net/hls-live/infostream3-infostream3/_definst_/live.m3u8'},{'title':  cFL_('War Room with Owen Shroyer - (Loops After Airing)','purple')},is_folder=False,img=WarRoomIcon,fanart=WarRoomFanart)
    IW_addon.add_directory({'mode': 'PlayURL','url':'https://infostream.secure.footprint.net/hls-live/infostream4-infostream4/_definst_/live.m3u8'},{'title':  cFL_('Fire Power with Will Johnson - (Loops After Airing)','red')},is_folder=False,img=FPIcon,fanart=FPFanart)
    IW_addon.add_directory({'mode': 'PlayURL','url':'https://infostream.secure.footprint.net/hls-live/infostream-infostream/_definst_/live.m3u8'},{'title':  cFL_('Live Shows & Special Events','green')},is_folder=False,img=IWLiveSEIcon,fanart=IWLiveSEFanart)
    IW_addon.add_directory({'mode': 'AJShowArchiveSubMenu','title':'On Demand Videos (Banned.video)'},{'title':  cFL_('On Demand Videos (Banned.video)','cyan')},is_folder=True,img=IWODIcon,fanart=IWODFanart)
    IW_addon.add_directory({'mode': 'PaulJosephWatsonSubMenu','title':'Paul Joseph Watson (Youtube Video)'},{'title':  cFL_('Paul Joseph Watson (Youtube)','blue')},is_folder=True,img=PJWIcon,fanart=PJWFanart)
    IW_addon.add_directory({'mode': 'MillieWeaverSubMenu','title':'Millie Weaver (Youtube Video)'},{'title':  cFL_('Millie Weaver (Youtube)','pink')},is_folder=True,img=MWIcon,fanart=MWFanart)
    IW_addon.add_directory({'mode': 'KaitlinBennettSubMenu','title':'Kaitlin Bennett - Liberty Hangout (Youtube Video)'},{'title':  cFL_('Kaitlin Bennett - Liberty Hangout (Youtube)','yellow')},is_folder=True,img=KBIcon,fanart=KBFanart)
    
    eod()

def Paul_Joseph_Watson_Sub_Menu(title=''): 
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

def Millie_Weaver_Sub_Menu(title=''):
    #https://www.youtube.com/channel/UCglVbeKF9JGMCt-RTUAW_TQ
    WhereAmI('@ Millie Weaver')
    url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCglVbeKF9JGMCt-RTUAW_TQ'
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

def Kaitlin_Bennett_Sub_Menu(title=''):
    #https://www.youtube.com/channel/UCglVbeKF9JGMCt-RTUAW_TQ
    WhereAmI('@ Millie Weaver')
    url = 'https://www.youtube.com/feeds/videos.xml?channel_id=UCQMb7c66tJ7Si8IrWHOgAPg'
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

def Full_Show_Sub_Menu(title=''):
    WhereAmI('@ Recent Full Length Shows')
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
    
    urlBannedVideo = 'https://banned.video'
    idBV = ""

    dataBV = None
    reqBV = urllib2.Request(urlBannedVideo, dataBV, hdr)
    responseBV = urllib2.urlopen(reqBV)
    contentBV = responseBV.read()
    idBV = ["5b885d33e6646a0015a6fa2d","5b9301172abf762e22bc22fd","5b92d71e03deea35a4c6cdef","5d72c972f230520013554291","5d7a86b1f30956001545dd71","5d7faf08b468d500160c8e3f","5d7faa8432b5da0013fa65bd","5da504e060be810013cf7252","5d8d03dbd018a5001776876a","5da8c506da090400138c8a6a","5dbb4729ae9e840012c61293","5d9653676f2d2a00179b8a58","5b9429906a1af769bc31efeb","5d7fa9014ffcfc00130304fa","5cf7df690a17850012626701","5dae2e7f612f0a0012d147bf"]
    ##idBV = (find_multiple_matches(contentBV,"<a href=\"\/channel\/(.*?)\""))  *** Save for future switch to javascript dynamic handling ***
    urlMAIN = 'https://api.infowarsmedia.com/api/channel/'
    IW_addon.log('*******  ' + urlMAIN)
    for i in range(len(idBV)):
        dataMAIN = None
        urlMAINID = urlMAIN + str(idBV[i]).strip('[\']') + '/'
        IW_addon.log('*******  ' + urlMAINID)
        reqMAIN = urllib2.Request(urlMAINID, dataMAIN ,hdr)
        responseMAIN = urllib2.urlopen(reqMAIN) 
        dataMAIN = json.load(responseMAIN)

        titleCheck = dataMAIN["title"] 

        url = urlMAINID + 'videos/'

        data = None
        req = urllib2.Request(url, data ,hdr)
        response = urllib2.urlopen(req)
        data = json.load(response)
        for item in data["videos"]:
            title = titleCheck + " - " + item["title"]            
            plot = item["summary"]                               
            thumbnail = item["posterThumbnailUrl"]               
            video_id = item["streamUrl"]                         
            url = video_id
            if ("FULL" in title or "Full" in title) and ("SHOW" in title or "Show" in title):
                add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False)
            

    eod()

def Alex_Jones_Show_Archive_Sub_Menu(title=''):
    #https://www.infowars.com/videos/
    WhereAmI('@ On Demand Videos')
    IW_addon.add_directory({'mode': 'ToTop','title':'=^= Click Here To Return To Top =^='},{'title':  cFL('         ===== Welcome to Banned.video =====','cyan')},is_folder=True,img=IWBDVIcon,fanart=IWODFanart)
    IW_addon.add_directory({'mode': 'FullShowSubMenu','title':'Recent Full Length Shows'},{'title':  cFL('===[ Click Here For Recent Full Length Shows ]===','red')},is_folder=True,img=IWODFLSIcon,fanart=IWODFanart)
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept': 'text/html,application/xhtml+xml,application/xml,application/json;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'}

    urlBannedVideo = 'https://banned.video'
    idBV = ""

    dataBV = None
    reqBV = urllib2.Request(urlBannedVideo, dataBV, hdr)
    responseBV = urllib2.urlopen(reqBV)
    contentBV = responseBV.read()
    idBV = ["5b885d33e6646a0015a6fa2d","5b9301172abf762e22bc22fd","5b92d71e03deea35a4c6cdef","5d72c972f230520013554291","5d7a86b1f30956001545dd71","5d7faf08b468d500160c8e3f","5d7faa8432b5da0013fa65bd","5da504e060be810013cf7252","5d8d03dbd018a5001776876a","5da8c506da090400138c8a6a","5dbb4729ae9e840012c61293","5d9653676f2d2a00179b8a58","5b9429906a1af769bc31efeb","5d7fa9014ffcfc00130304fa","5cf7df690a17850012626701","5dae2e7f612f0a0012d147bf"]
    ##idBV = (find_multiple_matches(contentBV,"<a href=\"\/channel\/(.*?)\""))
    urlMAIN = 'https://api.infowarsmedia.com/api/channel/'
    IW_addon.log('*******  ' + urlMAIN)
    for i in range(len(idBV)):
        dataMAIN = None
        urlMAINID = urlMAIN + str(idBV[i]).strip('[\']') + '/'
        IW_addon.log('*******  ' + urlMAINID)
        reqMAIN = urllib2.Request(urlMAINID, dataMAIN ,hdr)
        responseMAIN = urllib2.urlopen(reqMAIN) 
        dataMAIN = json.load(responseMAIN)

        titleCheck = dataMAIN["title"] 

        url = urlMAINID + 'videos/'

        data = None
        req = urllib2.Request(url, data ,hdr)
        response = urllib2.urlopen(req)
        data = json.load(response)

        for item in data["videos"]:
           title = titleCheck + " - " + item["title"]           
           plot = item["summary"]                               
           thumbnail = item["posterThumbnailUrl"]               
           video_id = item["streamUrl"]                         
           url = video_id
           if not "Full Show" in title:
               add_item( action="play" , title=title , plot=plot , url=url ,thumbnail=thumbnail , folder=False)
        IW_addon.add_directory({'mode': 'ToTop','title':'=^= Click Here To Return To Top =^='},{'title':  cFL('===[ Click Here To Return To Top ]===','grey')},is_folder=True,img=IWODIcon,fanart=IWODFanart)
 
    eod()

def check_mode(mode=''):
    mode = IW_addon.queries.get('mode', None)
    section = IW_addon.queries.get('section', '')
    genre = IW_addon.queries.get('genre', '')
    letter = IW_addon.queries.get('letter', '')
    sort = IW_addon.queries.get('sort', '')
    url = IW_addon.queries.get('url', '')
    title = IW_addon.queries.get('title', '')
    img = IW_addon.queries.get('img', '')
    season = IW_addon.queries.get('season', '')
    query = IW_addon.queries.get('query', '')
    page = IW_addon.queries.get('page', '')
    imdbnum = IW_addon.queries.get('imdbnum', '')
    year = IW_addon.queries.get('year', '')
    video_type = IW_addon.queries.get('video_type', '')
    episode = IW_addon.queries.get('episode', '')
    season = IW_addon.queries.get('season', '')
    tvdbnum = IW_addon.queries.get('tvdbnum', '')
    alt_id = IW_addon.queries.get('alt_id', '')
    dialog = IW_addon.queries.get('dialog', '')
    day = IW_addon.queries.get('day', '')
    movie_num = IW_addon.queries.get('movie_num', '')
    WhereAmI('@ Checking Mode')
    deb('Mode',mode)
    if (mode=='') or (mode=='main') or (mode=='MainMenu'): Menu_MainMenu() ## Default Menu
    elif (mode=='PlayURL'): PlayURL(_param['url']) ## Play Video
    elif (mode=='play'): play(params) ## Play Video
    elif (mode=='playYoutube'): playYoutube('url')
    elif (mode=='ToTop'): ToTop()
    elif (mode=='PaulJosephWatsonSubMenu'): Paul_Joseph_Watson_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='MillieWeaverSubMenu'): Millie_Weaver_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='KaitlinBennettSubMenu'): Kaitlin_Bennett_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='AJShowArchiveSubMenu'): Alex_Jones_Show_Archive_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='FullShowSubMenu'): Full_Show_Sub_Menu(_param['title']) ## Play Video
    elif (mode=='Settings'): IW_addon.addon.openSettings() # Another method: _plugin.openSettings() ## Settings for this addon.
    elif (mode=='ResolverSettings'): urlresolver.display_settings()  ## Settings for UrlResolver script.module.
    elif (mode == 'add_to_library'):
        add_to_library(video_type, url, title, img, year, imdbnum, movie_num)
        builtin = "XBMC.Notification(Add to Library,Added '%s' to library,2000, %s)" % (title, IW_artIcon)
        xbmc.executebuiltin(builtin)
    else: myNote(header='Mode:  "'+mode+'"',msg='[ mode ] not found.'); Menu_MainMenu() ## So that if a mode isn't found, it'll goto the Main Menu and give you a message about it.


deb('param >> title',_param['title'])
deb('param >> url',_param['url']) ### Simply Logging the current query-passed / param -- URL
check_mode(_param['mode']) ### Runs the function that checks the mode and decides what the plugin should do. This should be at or near the end of the file.
### ############################################################################################################
### ############################################################################################################
### ############################################################################################################

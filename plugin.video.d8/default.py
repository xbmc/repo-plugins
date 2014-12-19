# -*- coding: utf-8 -*-
#---------------------------------------------------------------------
# xbmc modules
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
# os and lib modules
import os
import sys 
import urllib
import urllib2
import simplejson as json
# print_exc
from traceback import print_exc
#---------------------------------------------------------------------
__addonID__   = "plugin.video.d8"
__addon__     = xbmcaddon.Addon( __addonID__ )
__addonDir__  = __addon__.getAddonInfo("path")
__author__    = __addon__.getAddonInfo("author")
__date__      = "12-19-2014"
__language__  = __addon__.getLocalizedString
__version__   = __addon__.getAddonInfo("version")
#---------------------------------------------------------------------
# Global Variables
ICON_PATH     = os.path.join(__addonDir__,"icon.png")
FANART_PATH   = os.path.join(__addonDir__,"fanart.jpg")
# Web Variables 
LAB_URL       = 'http://lab.canal-plus.pro/web/app_prod.php/api'
CAT_URL       = LAB_URL+'/replay/1'
LIVE_URL      = "http://www.d8.tv/pid5323-d8-live.html"
PGINFOS_URL   = LAB_URL+'/pfv'
USER_AGENT    = 'Mozilla/5.0 (Windows NT 5.1; rv:15.0) Gecko/20100101 Firefox/15.0.1'
#---------------------------------------------------------------------
class D8:
    """
    main plugin class
    """
    def __init__( self, *args, **kwargs ):
        print "==============================="
        print "  D8 - Version: %s"%__version__
        print "==============================="
        self.set_debug_mode()
        self.params    = self.get_params()
        self.url       = None
        self.name      = None
        self.mode      = None
        self.iconimage = ''            
        try:
            self.url=urllib.unquote_plus(self.params["url"])
        except:
            pass
        try:
            self.name=urllib.unquote_plus(self.params["name"])
        except:
            pass
        try:
            self.mode=int(self.params["mode"])
        except:
            pass
        try:
            self.iconimage=urllib.unquote_plus(self.params["iconimage"])
        except:
            pass            
        if self.debug_mode:
            print "D8 addon : Python version -> %s"%str(sys.version_info)
            print "D8 addon : Addon dir      -> %s"%__addonDir__ 
            print "D8 addon : Mode           -> "+str(self.mode)
            print "D8 addon : URL            -> "+str(self.url)
            print "D8 addon : Name           -> "+str(self.name)
            print "D8 addon : Iconimage      -> "+str(self.iconimage)
 
        if self.mode==None :
            self.GET_CATEGORIES()
            self.end_call()
            
        elif self.mode==1 :
            self.GET_PROGRAMS()
            self.end_call()
            
        elif self.mode==2 :
            self.GET_VIDEOS()
            self.end_call(movies=True)
            
        elif self.mode==3 :
            video_url = self.GET_VIDEO_URL()
            item = xbmcgui.ListItem(path=video_url) 
            xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=item)
                            
        elif self.mode==100:
            video_url = self.GET_LIVE_URL()
            item = xbmcgui.ListItem(path=video_url) 
            xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=item)
    
    def GET_CATEGORIES(self):
        if self.debug_mode : print "D8 addon : GET_CATEGORIES()"
        webcontent = self.get_webcontent(CAT_URL)
        catalogue  = json.loads(webcontent)
        for categorie in catalogue :
            title = categorie['title'].encode('utf-8')
            self.add_item(title,'mode1',1)
            if self.debug_mode : print "D8 addon : Add categorie \"%s\""%title
        self.add_item(__language__(30001),LIVE_URL,100,"",{},FANART_PATH,isPlayable=True) 
        if self.debug_mode : print "D8 addon : Add categorie \"%s\""%__language__(30001)
        
    def GET_LIVE_URL(self):
        webcontent = self.get_webcontent(LIVE_URL)
        html       = webcontent.decode("iso-8859-1")
        #---------------------------------
        # import parseDOM
        import CommonFunctions
        common = CommonFunctions
        common.plugin = "plugin.video.d8" 
        #---------------------------------
        live_id    = common.parseDOM(html,"input",attrs={"type":u"hidden","id":"iVideoEnCours"}, ret="value")[0]
        video_url  = self.get_video_url(live_id)
        if self.debug_mode : print "D8 addon : live video url \"%s\""%video_url
        return video_url
    
    def GET_PROGRAMS(self):
        if self.debug_mode : print "D8 addon : GET_PROGRAMS()"
        webcontent = self.get_webcontent(CAT_URL)
        catalogue  = json.loads(webcontent)
        for categorie in catalogue :
            if categorie['title'].encode('utf-8')==self.name :
                programs = categorie['programs']
                for program in programs :
                    title = program['title'].encode('utf-8')
                    self.add_item(title,self.name,2)
                    if self.debug_mode : print "D8 addon : Add programme \"%s\""%title 
    
    def GET_VIDEO_URL(self):
        if self.debug_mode : print "D8 addon : GET_VIDEO_URL()"
        video_url = self.get_video_url(self.url)
        if self.debug_mode : print "D8 addon : video url \"%s\""%video_url
        return video_url 
        
    def GET_VIDEOS(self):
        if self.debug_mode : print "D8 addon : GET_VIDEOS()"
        webcontent = self.get_webcontent(CAT_URL)
        catalogue  = json.loads(webcontent)
        for categorie in catalogue :
            if categorie['title'].encode('utf-8')==self.url :
                programs = categorie['programs']
                for program in programs :
                    if program['title'].encode('utf-8')==self.name :
                        videos = []
                        videos.append(program['videos_recent'])
                        videos.append(program['videos_view'])
                        videos.append(program['videos_hot'])
                        videoslist = []
                        for item in videos :
                            url         = PGINFOS_URL+'/list/1/%s'%item
                            webcontent  = self.get_webcontent(url)
                            video_infos = json.loads(webcontent)
                            for video in video_infos :
                                try :
                                    video_id = video['ID']
                                    if video_id not in videoslist :
                                        infos          = {}
                                        infos['Plot']  = video['INFOS']['DESCRIPTION'].encode('utf-8')
                                        infos['Title'] = video['INFOS']['TITRAGE']['TITRE'].encode('utf-8')
                                        infos['Sub']   = video['INFOS']['TITRAGE']['SOUS_TITRE'].encode('utf-8')
                                        if infos['Sub'] != "" :
                                            infos['Title'] = "%s - [I]%s[/I]" %(infos['Title'],infos['Sub'])
                                        infos['Thumb'] = video['MEDIA']['IMAGES']['GRAND'].encode('utf-8')
                                        video_fanart   = video['MEDIA']['IMAGES']['GRAND'].encode('utf-8')
                                        video_name     = infos['Title']
                                        self.add_item(video_name,video_id,3,infos['Thumb'],infos,video_fanart,True)                                
                                        videoslist.append(video_id)
                                        if self.debug_mode : print "D8 addon : Add video \"%s\""%video_name
                                except :
                                    pass
    
    def add_item(self,name,url,mode,iconimage="DefaultFolder.png",info={},fanart=FANART_PATH,isPlayable=False):
        if 'Title' not in info :
            info['Title'] = name
        u   = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo(type="Video",infoLabels=info)
        liz.setProperty("Fanart_Image",fanart)
        isFolder = True
        if isPlayable :
            liz.setProperty('IsPlayable','true')
            isFolder = False
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)
    
    def end_call(self,movies=False) :
        if movies :
            xbmcplugin.setContent(int(sys.argv[1]),'movies')
        xbmcplugin.setPluginCategory(handle=int(sys.argv[1]),category=__language__(30000))
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_DURATION)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_EPISODE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_FILE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_PLAYLIST_ORDER)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_PRODUCTIONCODE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_SIZE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_SONG_RATING)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_STUDIO)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_STUDIO_IGNORE_THE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RATING)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        xbmcplugin.addSortMethod(handle=int(sys.argv[ 1 ]),sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR)        
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def get_params(self):
        param  = {}
        params = sys.argv[2]
        if len(params) >= 2 :
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            cleanedparams = params.replace('?','')
            pairsofparams = cleanedparams.split('&')
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]
        return param        
    
    def get_video_url(self,videoid):
        infosurl   = PGINFOS_URL+'/video/1/%s'%videoid
        webcontent = self.get_webcontent(infosurl)
        infosdic   = json.loads(webcontent)
        video_url  = infosdic['main']['MEDIA']['VIDEOS'][__addon__.getSetting('videotype')]
        if video_url == '' :
            video_url = infosdic['main']['MEDIA']['VIDEOS']['IPAD']
        return video_url
    
    def get_webcontent(self,url):
        req  = urllib2.Request(url)
        req.add_header('User-Agent',USER_AGENT)           
        req.add_header('Referer',url)
        webcontent = urllib2.urlopen(req).read()
        if (self.debug_mode):
            print str(webcontent)
        return webcontent

    def set_debug_mode(self):
        self.debug_mode = False
        if __addon__.getSetting('debug') == 'true':
            self.debug_mode = True
        print "D8 addon : debug mode = %s"%self.debug_mode 

#######################################################################################################################    
# BEGIN !
#######################################################################################################################

if ( __name__ == "__main__" ):
    try:
        D8()
    except:
        print_exc()
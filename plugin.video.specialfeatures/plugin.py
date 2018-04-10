from lib.sys_init import *
from lib.iteration import *





class plugRoutine:
    def __init__(self,args):
        self.router(args[2][1:])
    def router(self,params):
        self.params = dict(parse_qsl(params))
        self.var()
        if self.params:
            if self.params.get('directory')=='movies':
                # home.setProperty('sf_here','movies')
                vw.cATEgory(self.params['directory'])
            elif self.params.get('directory')=='tvshows':
                # home.setProperty('sf_here','tvshows')
                vw.cATEgory(self.params['directory'])
            elif self.params.get('directory')=='all':
                # home.setProperty('sf_here','all')
                vw.cATEgory(self.params['directory'])
            elif self.params.get('directory')=='files':
                vw.iteMList(self.params['item'],self.category)
            elif self.params.get('directory')=='widget':
                vw.wiDGet(self.params['item'],self.category)
            elif self.params.get('action')=='play':
                pl.plaYVideo(self.params['video'])
            elif self.params.get('action')=='playall':
                pl.plaYList(self.params['item'])
        else:
            vw.mainDir()
    def var(self):
        global vw
        vw = Views()
        global pl
        pl = Player()
        self.category = self.params.get('category')
        if self.category == 'tvshows':
            self.category = 'tvshows'
        elif self.category == 'tvshow':
            self.category = 'tvshows'
        elif self.category == 'movies':
            self.category = 'movies'
        elif self.category == 'movie':
            self.category = 'movies'
        else:
            self.category = 'videos'
class Views:
    def vAr(self):
        self.DbEE = dbEnterExit()
        self.url    = sys.argv[0]
        self.handle = int(sys.argv[1])
    def itemVar(self):
        self.tid = None
        self.mid = None
        self.tag = None
        self.top = None
        self.tr  = None
        self.co  = None
        try:
            self.tid = self.item['tvshowid']
            self.mt = 'tvshow'
        except:
            self.mid = self.item['movieid']
            self.tr = self.item['trailer']
            self.top = self.item['top250']
            # self.tag = self.item['tag']
            # self.co = self.item['country']
            self.mt = 'movie'
        self.t = self.item['title']
        self.y = self.item['year']
        self.f = self.item['file']
        self.m = self.item['mpaa']
        self.p = self.item['plot']
        self.pr = self.item['premiered']
        self.d = self.item['dateadded']
        self.v = self.item['votes']
        self.r = self.item['rating']
        self.ur = self.item['userrating']
        # self.st = self.item['studio']
        # self.a = self.item['art']
        # self.c = self.item['cast']
        # self.g = self.item['genre']
        # self.ar = self.item['ratings']
        self.st = self.item['sorttitle']
    def constant(self):
        # self.litem.setContentLookup(False)
        # self.litem.setArt(self.item['art'])
        self.litem.setCast(self.item['cast'])
        self.litem.setInfo('video',{'title':self.t, 'year':self.y, 'plot': self.p,'path':self.f, 
                                    'rating':self.r, 'mpaa': self.m, 'dateadded':self.d,'premiered':self.p,
                                    'sorttitle':self.st, 'trailer':self.tr, 'mediatype':self.mt,'votes':self.v})
    def mainDir(self):
        self.dirvis = 'false'
        self.size = 0
        self.maindir = list()
        self.vAr()
        if showalldir =='true':
            self.maindir.append({'title':lang(30057),'category':'all','plot':lang(30058)})
            self.dirvis = 'true'
            self.size = self.size + 1
        if moviedir == 'true':
            self.maindir.append({'title':lang(30059),'category':'movies','plot':lang(30060)})
            self.dirvis = 'true'
            self.size = self.size + 1
        if tvshowdir == 'true':
            self.maindir.append({'title':lang(30061),'category':'tvshows','plot':lang(30062)})
            self.dirvis = 'true'
            self.size = self.size + 1
        if self.dirvis == 'false':
            self.chk = dialog.yesno(lang(30000),lang(30067),lang(30068))
            if self.chk == 1:
                xbmc.executebuiltin('Addon.OpenSettings({})'.format(addonid))
            else:
                return
        if self.size == 1:
            for self.item in self.maindir:
                if self.item.get('category','')=='all':
                        vw.cATEgory('all')
                if self.item.get('category','')=='movies':
                        vw.cATEgory('movies')
                if self.item.get('category','')=='tvshows':
                        vw.cATEgory('tvshows')
        else:
            for self.item in self.maindir:
                self.litem      = xbmcgui.ListItem(label=self.item['title'])
                self.litem.setContentLookup(False)
                self.isfolder  = True 
                self.litem.setInfo('video',{'plot':self.item['plot']})
                self.lurl = self.get_url(directory=self.item['category'])
                self.litem.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, self.lurl, self.litem, self.isfolder)
            xbmcplugin.setContent(self.handle, 'videos')
            xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE )
            xbmcplugin.endOfDirectory(self.handle)
            # except:
            #     error("NEED TO UPDATE DATABASE OR ADD MOVIES OR TVSHOWS")
            #     return
    def cATEgory(self,category):
        self.vAr()
        # self.plugart = False
        if category != 'all':
            self.folder = self.DbEE.initDb(category)
            if not len(self.folder)>0:
                if dialog.yesno(lang(30000),lang(30056)) == 1:
                    xbmc.executebuiltin("RunScript(plugin.video.specialfeatures,scandb)")
                else:
                    exit()
            else:
                for self.item in self.folder:
                    # if self.plugart == False:
                    #     xbmcplugin.setPluginFanart(self.handle,self.item['art']['fanart'])
                    #     self.plugart = True
                    self.litem     = xbmcgui.ListItem(label=self.item['title'])
                    self.itemVar()
                    self.constant()
                    self.litem.setArt(self.item['art'])
                    if self.item.get('tvshowid') is None:
                        category = 'movies'
                    else:
                        category = 'tvshows'
                    self.is_folder  = True
                    self.url        = self.get_url(directory='files', item=self.item['file'], category=category)
                    self.litem.setProperty('IsPlayable', 'false')
                    xbmcplugin.addDirectoryItem(self.handle, self.url, self.litem, self.is_folder)
                xbmcplugin.setContent(self.handle, category)
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_MPAA_RATING )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_RATING )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_DATEADDED  )
                xbmcplugin.endOfDirectory(self.handle)
        else:
            self.folder = self.DbEE.initDb('movies')
            self.folder = self.DbEE.initDb('tvshows')
            if not len(self.folder)>0:
                if dialog.yesno(lang(30000),lang(30056)) == 1:
                    xbmc.executebuiltin("RunScript(plugin.video.specialfeatures,scandb)")
                else:
                    exit()
            else:
                for self.item in self.folder:
                    self.litem     = xbmcgui.ListItem(label=self.item['title'])
                    self.vAr()
                    self.itemVar()
                    self.constant()
                    if self.item.get('tvshowid') is None:
                        category = 'movies'
                    else:
                        category = 'tvshows'
                    self.is_folder  = True
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                    self.url        = self.get_url(directory='files', item=self.item['file'], category=category)
                    self.litem.setProperty('IsPlayable', 'false')
                    xbmcplugin.addDirectoryItem(self.handle, self.url, self.litem, self.is_folder)
                xbmcplugin.setContent(self.handle, 'videos')
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_MPAA_RATING )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_YEAR )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_RATING )
                xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_DATEADDED  )
                xbmcplugin.endOfDirectory(self.handle)
    def iteMList(self,item,category):
            self.vAr()
            self.files = self.DbEE.initDb('file',item)
            if category == 'tvshows':
                category = 'episodes'
            for self.item in self.files:
                self.f = self.item['path']
                self.litem     = xbmcgui.ListItem(label=self.item['title'], path=self.f)
                self.t = self.item['title']
                self.p = self.item['plot']
                self.st = self.item['sorttitle']
                if os.path.splitext(self.f)[1] == '.bdmv':
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                elif os.path.splitext(self.f)[1] == '.IFO':
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                elif os.path.splitext(self.f)[1] == '.iso':
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                else:
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'thumb':self.item['art'].get('thumb')})
                self.litem.setCast(self.item['cast'])
                self.litem.setInfo('video',{'title':self.t, 'plot': self.p,'path':self.f,'sorttitle':self.st})
                self.is_folder  = False
                self.litem.addContextMenuItems([('Manage...', 'RunScript(plugin.video.specialfeatures,editinfo)',)])
                self.litem.setContentLookup(True) 
                # xbmc.getCacheThumbName(self.f)
                self.litem.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, self.f, self.litem, self.is_folder)
            xbmcplugin.setContent(self.handle, category)
            if len(self.files) > 1:
                if playall == 'true':
                    self.playall = xbmcgui.ListItem(label=lang(30054))
                    # self.playall.setArt(self.item['art'])
                    self.playall.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                    self.playall.setCast(self.item['cast'])
                    self.playall.setInfo('video',{'plot':lang(30055)})
                    self.playall.setProperty('IsPlayable', 'true')
                    self.playall.setProperty('PlayAll', 'true')
                    self.url = self.get_url(action='playall', item=item)
                    xbmcplugin.addDirectoryItem(self.handle,self.url, self.playall, self.is_folder)
            xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE )
            xbmcplugin.endOfDirectory(self.handle)
    def wiDGet(self,item,category):
            self.vAr()
            self.files = self.DbEE.initDb('file',item)
            if category == 'tvshows':
                category = 'episodes'
            for self.item in self.files:
                self.f = self.item['path']
                self.litem     = xbmcgui.ListItem(label=self.item['title'], path=self.f)
                self.t = self.item['title']
                self.p = self.item['plot']
                self.st = self.item['sorttitle']
                if os.path.splitext(self.f)[1] == '.bdmv':
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                elif os.path.splitext(self.f)[1] == '.IFO':
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                elif os.path.splitext(self.f)[1] == '.iso':
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'poster':self.item['art'].get('poster')})
                else:
                    self.litem.setArt({'fanart':self.item['art'].get('fanart'),'thumb':self.item['art'].get('thumb')})
                self.litem.setCast(self.item['cast'])
                self.litem.setInfo('video',{'title':self.t, 'plot': self.p,'path':self.f,'sorttitle':self.st})
                self.is_folder  = False
                # self.litem.addContextMenuItems([('Manage...', 'RunScript(plugin.video.specialfeatures,editinfo)',)])
                self.litem.setContentLookup(True) 
                self.litem.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(self.handle, self.f, self.litem, self.is_folder)
            xbmcplugin.setContent(self.handle, category)
            xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_VIDEO_SORT_TITLE )
            xbmcplugin.endOfDirectory(self.handle)
   
    def get_url(self,**kwargs):
        return '{0}?{1}'.format(self.url,urlencode(kwargs))
class Player:
    def var(self):
        self._url           = sys.argv[0]
        self._handle        = int(sys.argv[1])
        self.DbEE = dbEnterExit()
    def item_var(self):
        self.year           = self.item.get('year','')
        self.plot           = self.item.get('plot','')
        self.cast           = self.item.get('cast','')
        self.path           = self.item.get('file','')
        self.rating         = self.item.get('rating','')
        self.mpaa           = self.item.get('mpaa','')
        self.dateadded      = self.item.get('dateadded','')
    def plaYVideo(self,path):
        self.var()
        self.playitem = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(self._handle, True, listitem=self.playitem)
    def plaYList(self,category=''):
        self.var()
        playL.clear()
        self.files = self.DbEE.initDb('file',category)
        self.f = self.files[0].get('path')
        self.item_one = xbmcgui.ListItem(path=self.f)
        self.item_one.setInfo('video',{'title':self.files[0].get('title'),'plot':self.files[0].get('plot'),'sorttitle':self.files[0].get('sorttitle')})
        info(self.files[0].get('art'))
        self.item_one.setCast(self.files[0].get('cast'))
        if os.path.splitext(self.f)[1] == '.bdmv':
            self.item_one.setArt({'fanart':self.files[0].get('art').get('fanart'),'poster':self.files[0].get('art').get('poster')})
        elif os.path.splitext(self.f)[1] == '.IFO':
            self.item_one.setArt({'fanart':self.files[0].get('art').get('fanart'),'poster':self.files[0].get('art').get('poster')})
        elif os.path.splitext(self.f)[1] == '.iso':
            self.item_one.setArt({'fanart':self.files[0].get('art').get('fanart'),'poster':self.files[0].get('art').get('poster')})
        else:
            self.item_one.setArt({'fanart':self.files[0].get('art').get('fanart'),'thumb':self.files[0].get('art').get('thumb')})
        playr.play(item=self.f, listitem=self.item_one)
        xbmcplugin.setResolvedUrl(self._handle, True, listitem=self.item_one)
        if not xbmc.executebuiltin('Window.IsActive(fullscreenvideo)'):
            xbmc.executebuiltin('Action(Fullscreen)')
        for self.item in self.files:
            if self.item != self.files[0]:
                self.f = self.item.get('path')
                self.litem = xbmcgui.ListItem(self.item.get('title'))
                self.title  = self.item.get('title')
                self.litem.setInfo('video',{'title':self.item.get('title'),'plot':self.item.get('plot'),'sorttitle':self.item.get('sorttitle')})
                self.litem.setCast(self.item.get('cast'))
                if os.path.splitext(self.f)[1] == '.bdmv':
                    self.litem.setArt({'fanart':self.item.get('art').get('fanart'),'poster':self.item.get('art').get('poster')})
                elif os.path.splitext(self.f)[1] == '.IFO':
                    self.litem.setArt({'fanart':self.item.get('art').get('fanart'),'poster':self.item.get('art').get('poster')})
                elif os.path.splitext(self.f)[1] == '.iso':
                    self.litem.setArt({'fanart':self.item.get('art').get('fanart'),'poster':self.item.get('art').get('poster')})
                else:
                    self.litem.setArt({'fanart':self.item.get('art').get('fanart'),'thumb':self.item.get('art').get('thumb')})
                playL.add(url=self.item.get('path'), listitem=self.litem)
               
if __name__ =='__main__':
    plugRoutine(sys.argv)



#!/usr/bin/python
# -*- coding: utf8 -*-
"""
TODO :
  - test a silent background scanning behaviour. May probably be done as the plugin still works while scanning.
  - upgrade iptcinfo library (need some unicode improvement)
  - 'add to collections' context menu from any folder in sort by date view
  - 'add to collections' context menu from any folder in sort by folders view
  - test if a 'collection' or 'period' or 'keyword' view doesn't contain any pictures : remove these from the database when deleting pictures
  - Scan : need to fix parameters sending. Right now, recursive or update things are not handled (everything is recursive and updating for new/deleted pics)
  - Set a parameter to prevent small pics to be added to the database (use EXIF_ImageWidth and EXIF_ImageLength metas)
  - Les photos depuis x jours avec x configurable dans les options
"""

__addonname__ = 'plugin.image.mypicsdb'

# common depends on __addonname__
import resources.lib.common as common

import os, sys, time
from os.path import join,isfile,basename,dirname,splitext
from urllib import unquote_plus

from time import strftime,strptime
from traceback import print_exc

import xbmc, xbmcplugin,xbmcgui

#from xbmcgui import Window

# MikeBZH44
try:
    import json as simplejson
    # test json has not loads, call error
    if not hasattr( simplejson, "loads" ):
        raise Exception( "Hmmm! Error with json %r" % dir( simplejson ) )
except Exception, e:
    print "[MyPicsDB] %s" % str( e )
    import simplejson

# MikeBZH44: commoncache for MyPicsDB with 1 hour timeout
try:
   import StorageServer
except:
   import resources.lib.storageserverdummy as StorageServer

# set variables used by other modules   

sys_encoding = sys.getfilesystemencoding()

if sys.modules.has_key("MypicsDB"):
    del sys.modules["MypicsDB"]
import resources.lib.MypicsDB as MPDB
import resources.lib.filterwizard as filterwizard
import resources.lib.translationeditor as translationeditor
import resources.lib.viewer as viewer

# these few lines are taken from AppleMovieTrailers script
# Shared resources
home = common.getaddon_path()
BASE_RESOURCE_PATH = join( home, "resources" )
DATA_PATH = common.getaddon_info('profile')
PIC_PATH = join( BASE_RESOURCE_PATH, "images")
DB_PATH = xbmc.translatePath( "special://database/")

#catching the OS :
#   win32 -> win
#   darwin -> mac
#   linux -> linux
RunningOS = sys.platform

cache = StorageServer.StorageServer("MyPicsDB",1)

global pictureDB

pictureDB = join(DB_PATH,"MyPictures.db")

files_fields_description={"strFilename":common.getstring(30300),
                          "strPath":common.getstring(30301),
                          "Thumb":common.getstring(30302)
                          }


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )
    def has_key(self, key):
        return key in self.__dict__
    def __setitem__(self,key,value):
        self.__dict__[key]=value

    
class Main:
    def __init__(self):
        self.get_args()

    def get_args(self):
        common.log("Main.get_args", "MyPicturesDB plugin called :", xbmc.LOGNOTICE)
        common.log("Main.get_args", "sys.argv[0] = %s"%sys.argv[0], xbmc.LOGNOTICE)
        common.log("Main.get_args", "sys.argv[2] = %s"%sys.argv[2], xbmc.LOGNOTICE)

        self.parm = common.smart_utf8(unquote_plus(sys.argv[2])).replace("\\\\", "\\")
        
        sys.argv[2] = self.parm
        parm = self.cleanup(self.parm[ 1 : ])
        common.log("Main.get_args", parm)
        
        args= "self.args = _Info(%s)" % ( parm )
        exec args
        if not hasattr(self.args, 'page'):
            self.args.page=''

    def cleanup(self, parm):
        
        in_apostrophe=False
        prev_char = ""
        prevprev_char = ""
        output=""
        
        for char in parm:
            if char == "'" and prev_char != "\\" or char == "'" and prev_char =="\\" and prevprev_char == "\\":
                if not in_apostrophe:
                    in_apostrophe = True
                else:
                    in_apostrophe = False
            if char == "&" and not in_apostrophe:
                    char = ","
                
            output += char
            
            prevprev_char = prev_char
            prev_char = char
            if prevprev_char == "\\" and prev_char == "\\" :
                prev_char = ""
                prevprev_char = ""
                
        return output
        
    def Title(self,title):
        pass

    def addDir(self,name,params,action,iconimage,fanart=None,contextmenu=None,total=0,info="*",replacemenu=True):
        #params est une liste de tuples [(nomparametre,valeurparametre),]
        #contitution des paramètres
        common.log("Main.addDir", "Name = %s"%name)
        try:
            parameter="&".join([param+"="+repr(common.quote_param(valeur.encode("utf-8"))) for param,valeur in params])
        except:
            parameter=""
        #création de l'url
        u=sys.argv[0]+"?"+parameter+"&action="+repr(str(action))+"&name="+repr(common.quote_param(name.encode("utf8")))

        #création de l'item de liste
        liz=xbmcgui.ListItem(name, thumbnailImage=iconimage)
        #if fanart:
        #    liz.setProperty( "Fanart_Image", fanart )
        #menu contextuel
        if contextmenu :
            liz.addContextMenuItems(contextmenu,replacemenu)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)#,totalItems=total)


    def addAction(self,name,params,action,iconimage,fanart=None,contextmenu=None,total=0,info="*",replacemenu=True):
        #params est une liste de tuples [(nomparametre,valeurparametre),]
        #contitution des paramètres
        common.log("Main.addAction", "Name = %s"%name)
        try:
            parameter="&".join([param+"="+repr(common.quote_param(valeur.encode("utf-8"))) for param,valeur in params])
        except:
            parameter=""
        #création de l'url
        u=sys.argv[0]+"?"+parameter+"&action="+repr(str(action))+"&name="+repr(common.quote_param(name.encode("utf8")))

        #création de l'item de liste
        liz=xbmcgui.ListItem(name, thumbnailImage=iconimage)
        #if fanart:
        #    liz.setProperty( "Fanart_Image", fanart )
        #menu contextuel
        if contextmenu :
            liz.addContextMenuItems(contextmenu,replacemenu)

        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)#,totalItems=total)


    def addPic(self,picname,picpath,info="*",fanart=None,contextmenu=None,replacemenu=True):
        fullfilepath = join(picpath,picname)
        common.log("Main.addPic", "Name = %s"%fullfilepath)
        
        liz=xbmcgui.ListItem(picname,info)
        date = MPDB.getDate(picpath,picname)
        date = date and strftime("%d.%m.%Y",strptime(date,"%Y-%m-%d %H:%M:%S")) or ""
        suffix=""
        rating=""
        coords=None
        extension = splitext(picname)[1].upper()
        #is the file a video ?
        if extension in ["."+ext.replace(".","").upper() for ext in common.getaddon_setting("vidsext").split("|")]:
            infolabels = { "date": date }
            liz.setInfo( type="video", infoLabels=infolabels )
        #or is the file a picture ?
        elif extension in ["."+ext.replace(".","").upper() for ext in common.getaddon_setting("picsext").split("|")]:
            rating = MPDB.getRating(picpath,picname)
            if int(common.getaddon_setting("ratingmini"))>0:#un rating mini est configuré
                if not rating:  return
                if int(rating) < int(common.getaddon_setting("ratingmini")): return #si on a un rating dans la photo

            coords = MPDB.getGPS(picpath,picname)
            if coords: 
                suffix = suffix + "[COLOR=C0C0C0C0][G][/COLOR]"

            (exiftime,) = MPDB.RequestWithBinds( """select coalesce(ImageDateTime, '0') from files where strPath=? and strFilename=? """,(picpath,picname))
            resolutionX = MPDB.RequestWithBinds( """select coalesce(tc.TagContent,0) from TagTypes tt, TagContents tc, TagsInFiles tif, Files fi
                                                     where tt.TagType = 'EXIF ExifImageWidth'
                                                       and tt.idTagType = tc.idTagType
                                                       and tc.idTagContent = tif.idTagContent
                                                       and tif.idFile = fi.idFile
                                                       and fi.strPath = ?
                                                       and fi.strFilename = ?  """,(picpath,picname))

            resolutionY = MPDB.RequestWithBinds( """select coalesce(tc.TagContent,0) from TagTypes tt, TagContents tc, TagsInFiles tif, Files fi
                                                     where tt.TagType = 'EXIF ExifImageLength'
                                                       and tt.idTagType = tc.idTagType
                                                       and tc.idTagContent = tif.idTagContent
                                                       and tif.idFile = fi.idFile
                                                       and fi.strPath = ?
                                                       and fi.strFilename = ?  """,(picpath,picname))     

            #resolution = MPDB.RequestWithBinds( """select coalesce("EXIF ExifImageWidth", '0'),  coalesce("EXIF ExifImageLength", '0') from files where strPath=? and strFilename=? """,(picpath,picname))
            infolabels = { "picturepath":picname+" "+suffix, "date": date  }
            try:
                if exiftime[0] != None and exiftime[0] != "0":
                    common.log("Main.addPic", "Picture has EXIF Date/Time %s"%exiftime[0])
                    infolabels["exif:exiftime"] = exiftime[0]
            except:
                pass

            try:
                resolutionX = resolutionX[0][0]
                resolutionY = resolutionY[0][0]
                
                if resolutionX != None and resolutionY != None and resolutionX != "0" and resolutionY != "0":
                    common.log("Main.addPic", "Picture has resolution %s x %s"%(str(resolutionX), str(resolutionY)))
                    infolabels["exif:resolution"] = str(resolutionX) + ',' + str(resolutionY)
            except:
                pass

            if rating:
                common.log("Main.addPic", "Picture has rating")
                suffix = suffix + "[COLOR=C0FFFF00]"+("*"*int(rating))+"[/COLOR][COLOR=C0C0C0C0]"+("*"*(5-int(rating)))+"[/COLOR]"

            liz.setInfo( type="pictures", infoLabels=infolabels )

        liz.setLabel(picname+" "+suffix)
        #liz.setLabel2(suffix)
        if contextmenu:
            if coords:
                #géolocalisation
                common.log("Main.addPic", "Picture has geolocation")
                contextmenu.append( (common.getstring(30220),"XBMC.RunPlugin(\"%s?action='geolocate'&place='%s'&path='%s'&filename='%s'&viewmode='view'\" ,)"%(sys.argv[0],"%0.6f,%0.6f"%(coords),
                                                                                                                                                           common.quote_param(picpath.encode('utf-8')),
                                                                                                                                                           common.quote_param(picname.encode('utf-8'))
                                                                                                                                                           )))
                #TODO : add to favourite
                #TODO : ...
            liz.addContextMenuItems(contextmenu,replacemenu)

        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=fullfilepath,listitem=liz,isFolder=False)

    def show_home(self):
        common.log("Main.show_home", "start")
##        # last month
##        self.addDir("last month (betatest)",[("method","lastmonth"),("period",""),("value",""),("page","1"),("viewmode","view")],
##                    "showpics",join(PIC_PATH,"dates.png"),
##                    fanart=join(PIC_PATH,"fanart-date.png"))
        display_all = common.getaddon_setting('m_all')=='true'
        # last scan picture added
        if common.getaddon_setting('m_1')=='true' or display_all:
            self.addDir(common.getstring(30209)%common.getaddon_setting("recentnbdays"),[("method","recentpicsdb"),("period",""),("value",""),("page","1"),("viewmode","view")],
                        "showpics",join(PIC_PATH,"dates.png"),
                        fanart=join(PIC_PATH,"fanart-date.png"))

        # Last pictures
        if common.getaddon_setting('m_2')=='true' or display_all:
            self.addDir(common.getstring(30130)%common.getaddon_setting("lastpicsnumber"),[("method","lastpicsshooted"),("page","1"),("viewmode","view")],
                    "showpics",join(PIC_PATH,"dates.png"),
                    fanart=join(PIC_PATH,"fanart-date.png"))

        # videos
        if common.getaddon_setting('m_3')=='true' or display_all and common.getaddon_setting("usevids") == "true":
            self.addDir(common.getstring(30051),[("method","videos"),("page","1"),("viewmode","view")],
                        "showpics",join(PIC_PATH,"videos.png"),
                        fanart=join(PIC_PATH,"fanart-videos.png"))
        # show filter wizard
        self.addAction(common.getstring(30600),[("wizard",""),("viewmode","view")],"showwizard",
                    join(PIC_PATH,"keywords.png"),
                    fanart=join(PIC_PATH,"fanart-keyword.png"))
        # par années
        if common.getaddon_setting('m_4')=='true' or display_all:
            self.addDir(common.getstring(30101),[("period","year"),("value",""),("viewmode","view")],
                    "showdate",join(PIC_PATH,"dates.png"),
                    fanart=join(PIC_PATH,"fanart-date.png") )
        # par dossiers
        if common.getaddon_setting('m_5')=='true' or display_all:
            self.addDir(common.getstring(30102),[("method","folders"),("folderid",""),("onlypics","non"),("viewmode","view")],
                    "showfolder",join(PIC_PATH,"folders.png"),
                    fanart=join(PIC_PATH,"fanart-folder.png"))

        # tags submenu
        if common.getaddon_setting('m_14')=='true' or display_all:
            self.addDir(common.getstring(30122),[("tags",""),("viewmode","view")],"showtagtypes",
                        join(PIC_PATH,"keywords.png"),
                        fanart=join(PIC_PATH,"fanart-keyword.png"))

        # période
        if common.getaddon_setting('m_10')=='true' or display_all:
            self.addDir(common.getstring(30105),[("period",""),("viewmode","view"),],"showperiod",
                    join(PIC_PATH,"period.png"),
                    fanart=join(PIC_PATH,"fanart-period.png"))
        # Collections
        if common.getaddon_setting('m_11')=='true' or display_all:
            self.addDir(common.getstring(30150),[("collect",""),("method","show"),("viewmode","view")],"showcollection",
                    join(PIC_PATH,"collection.png"),
                    fanart=join(PIC_PATH,"fanart-collection.png"))
        # recherche globale
        if common.getaddon_setting('m_12')=='true' or display_all:
            self.addDir(common.getstring(30098),[("searchterm",""),("viewmode","view")],"globalsearch",
                    join(PIC_PATH,"search.png"),
                    fanart=join(PIC_PATH,"fanart-search.png"))
        # chemin scannés
        self.addDir(common.getstring(30099),[("do","showroots"),("viewmode","view")],"rootfolders",
                    join(PIC_PATH,"settings.png"),
                    fanart=join(PIC_PATH,"fanart-setting.png"))

        # Translation Editor
        self.addAction(common.getstring(30620),[("showtranslationeditor",""),("viewmode","view")],"showtranslationeditor",
                    join(PIC_PATH,"keywords.png"),
                    fanart=join(PIC_PATH,"fanart-keyword.png"))

        # Show readme
        self.addAction(common.getstring(30123),[("help",""),("viewmode","view")],"help",
                    join(PIC_PATH,"keywords.png"),
                    fanart=join(PIC_PATH,"fanart-keyword.png"))        

        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        #xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=unquote_plus("My Pictures Library".encode("utf-8")) )
        xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)

    def show_date(self):
        #period = year|month|date
        #value  = "2009"|"12/2009"|"25/12/2009"
        common.log("Main.show_date", "start")
        action="showdate"
        monthname = common.getstring(30006).split("|")
        fullmonthname = common.getstring(30008).split("|")
        if self.args.period=="year":
            common.log("Main.show_date", "period=year")
            listperiod=MPDB.get_years()
            nextperiod="month"
            allperiod =""
            action="showdate"
            periodformat="%Y"
            displaydate=common.getstring(30004)#%Y
            thisdateformat=""
            displaythisdate=""
        elif self.args.period=="month":
            common.log("Main.show_date", "period=month")
            listperiod=MPDB.get_months(self.args.value)
            nextperiod="date"
            allperiod="year"
            action="showdate"
            periodformat="%Y-%m"
            displaydate=common.getstring(30003)#%b %Y
            thisdateformat="%Y"
            displaythisdate=common.getstring(30004)#%Y
        elif self.args.period=="date":
            common.log("Main.show_date", "period=date")
            listperiod=MPDB.get_dates(self.args.value)
            nextperiod="date"
            allperiod = "month"
            action="showpics"
            periodformat="%Y-%m-%d"
            #page=""
            displaydate=common.getstring(30002)#"%a %d %b %Y"
            thisdateformat="%Y-%m"
            displaythisdate=common.getstring(30003)#"%b %Y"
        else:
            common.log("Main.show_date", "period=empty")
            listperiod=[]
            nextperiod=None

        #if not None in listperiod:
        dptd = displaythisdate
        dptd = dptd.replace("%b",monthname[strptime(self.args.value,thisdateformat).tm_mon - 1])    #replace %b marker by short month name
        dptd = dptd.replace("%B",fullmonthname[strptime(self.args.value,thisdateformat).tm_mon - 1])#replace %B marker by long month name
        nameperiode = strftime(dptd.encode("utf8"),strptime(self.args.value,thisdateformat))
        self.addDir(name      = common.getstring(30100)%(nameperiode.decode("utf8"),MPDB.countPeriod(allperiod,self.args.value)), #libellé#"All the period %s (%s pics)"%(self.args.value,MPDB.countPeriod(allperiod,self.args.value)), #libellé
                    params    = [("method","date"),("period",allperiod),("value",self.args.value),("page",""),("viewmode","view")],#paramètres
                    action    = "showpics",#action
                    iconimage = join(PIC_PATH,"dates.png"),#icone
                    fanart    = join(PIC_PATH,"fanart-date.png"),
                    contextmenu   = [(common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addfolder'&method='date'&period='%s'&value='%s'&viewmode='scan'\")"%(sys.argv[0],allperiod,self.args.value)),
                                     ("diaporama"        ,"XBMC.RunPlugin(\"%s?action='diapo'&method='date'&period='%s'&value='%s'&viewmode='scan'\")"%(sys.argv[0],allperiod,self.args.value))
                                     ]
                    )
        total=len(listperiod)
        for period in listperiod:
            if period:
                if action=="showpics":
                    context = [(common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addfolder'&method='date'&period='%s'&value='%s'&page=''&viewmode='scan'\")"%(sys.argv[0],nextperiod,period))]
                else:
                    context = [(common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addfolder'&method='date'&period='%s'&value='%s'&viewmode='scan'\")"%(sys.argv[0],self.args.period,period))]
                self.addDir(name      = "%s (%s %s)"%(strftime(self.prettydate(displaydate,strptime(period,periodformat)).encode("utf8"),strptime(period,periodformat)).decode("utf8"),
                                                      MPDB.countPeriod(self.args.period,period),
                                                      common.getstring(30050).encode("utf8")), #libellé
                            params    = [("method","date"),("period",nextperiod),("value",period),("viewmode","view")],#paramètres
                            action    = action,#action
                            iconimage = join(PIC_PATH,"dates.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-date.png"),
                            contextmenu   = context,#menucontextuel
                            total = total)#nb total d'éléments

        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_folders(self):
        common.log("Main.show_folders", "start")
        #get the subfolders if any
        if not self.args.folderid: #No Id given, get all the root folders
            childrenfolders=[row for row in MPDB.Request("SELECT idFolder,FolderName FROM folders WHERE ParentFolder is null")]
        else:#else, get subfolders for given folder Id
            childrenfolders=[row for row in MPDB.RequestWithBinds("SELECT idFolder,FolderName FROM folders WHERE ParentFolder=?",(self.args.folderid,)) ]

        #show the folders
        for idchildren, childrenfolder in childrenfolders:
            common.log("Main.show_folders", "children folder = %s"%childrenfolder)
            path = MPDB.RequestWithBinds( "SELECT FullPath FROM folders WHERE idFolder = ?",(idchildren,) )[0][0]
            self.addDir(name      = "%s (%s %s)"%(childrenfolder,MPDB.countPicsFolder(idchildren),common.getstring(30050)), #libellé
                        params    = [("method","folders"),("folderid",str(idchildren)),("onlypics","non"),("viewmode","view")],#paramètres
                        action    = "showfolder",#action
                        iconimage = join(PIC_PATH,"folders.png"),#icone
                        fanart    = join(PIC_PATH,"fanart-folder.png"),
                        contextmenu   = [(common.getstring(30212),"Container.Update(\"%s?action='rootfolders'&do='addrootfolder'&addpath='%s'&exclude='1'&viewmode='view'\",)"%(sys.argv[0],common.quote_param(path.encode('utf-8'))) ),],
                        total = len(childrenfolders))#nb total d'éléments

        #maintenant, on liste les photos si il y en a, du dossier en cours
        picsfromfolder = [row for row in MPDB.RequestWithBinds("SELECT p.FullPath,f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder=? ", (self.args.folderid, ) )]

        for path,filename in picsfromfolder:
            path     = common.smart_unicode(path)
            filename = common.smart_unicode(filename)

            common.log("Main.show_folders", "pic's path = %s  pic's name = %s"%(path,filename))

            context = []
            #context.append( (common.getstring(30303),"SlideShow(%s%s,recursive,notrandom)"%(sys.argv[0],sys.argv[2]) ) )
            context.append( ( common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addtocollection'&viewmode='view'&path='%s'&filename='%s'\")"%(sys.argv[0],
                                                                                                                         common.quote_param(path.encode('utf-8')),
                                                                                                                         common.quote_param(filename.encode('utf-8')))  )
                            )
            self.addPic(filename,path,contextmenu=context,
                        fanart = xbmcplugin.getSetting(int(sys.argv[1]),'usepicasfanart')=='true' and join(path,filename) or join(PIC_PATH,"fanart-folder.png")
                        )

        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE )
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_translationeditor(self):
        ui = translationeditor.TranslationEditor( "translationeditor.xml" , common.getaddon_path(), "Default")
        ui.doModal()
        del ui

    def show_help(self):
        viewer.Viewer()

    def show_wizard(self):
        global GlobalFilterTrue, GlobalFilterFalse, GlobalMatchAll
        #picfanart = join(PIC_PATH,"fanart-keyword.png")
        ui = filterwizard.FilterWizard( "filterwizard.xml" , common.getaddon_path(), "Default")
        ui.setDelegate(filterwizard_delegate)
        ui.doModal()
        del ui

        newtagtrue = ""
        newtagfalse = ""
        matchall = (1 if GlobalMatchAll else 0)

        if len(GlobalFilterTrue) > 0:

            for tag in GlobalFilterTrue:
                if len(newtagtrue)==0:
                    newtagtrue = tag
                else:
                    newtagtrue += "|||" + tag
            newtagtrue = common.smart_unicode(newtagtrue)

        if len(GlobalFilterFalse) > 0:

            for tag in GlobalFilterFalse:
                if len(newtagfalse)==0:
                    newtagfalse = tag
                else:
                    newtagfalse += "|||" + tag
            newtagfalse = common.smart_unicode(newtagfalse)

        if len(GlobalFilterTrue) > 0 or len(GlobalFilterFalse) > 0:
            xbmc.executebuiltin("XBMC.Container.Update(%s?action='showpics'&viewmode='view'&method='wizard'&matchall='%s'&kw='%s'&nkw='%s')" % ( sys.argv[0], matchall, common.quote_param(newtagtrue.encode('utf-8')), common.quote_param(newtagfalse.encode('utf-8'))))


    def show_tagtypes(self):
        #listtags = [u"%s"%k  for k in MPDB.list_TagTypesAndCount()]
        listtags =  MPDB.list_TagTypesAndCount()
        total = len(listtags)
        common.log("Main.show_tagtypes", "total # of tag types = %s"%total)
        for tag, nb in listtags:
            #nb = MPDB.countTagTypes(tag)
            if nb:
                self.addDir(name      = "%s (%s %s)"%(tag,nb,common.getstring(30052)), #libellé
                            params    = [("method","tagtype"),("tagtype",tag),("page","1"),("viewmode","view")],#paramètres
                            action    = "showtags",#action
                            iconimage = join(PIC_PATH,"keywords.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-keyword.png"),
                            contextmenu   = [('','')],
                            total = total)#nb total d'éléments
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_tags(self):
        tagtype = self.args.tagtype.decode("utf8")
        listtags = [k  for k in MPDB.list_TagsAndCount(tagtype)]
        total = len(listtags)
        common.log("Main.show_tags", "total # of tags = %s"%total)
        for tag, nb in listtags:
            #nb = MPDB.countTags(tag, tagtype)
            if nb:
                self.addDir(name      = "%s (%s %s)"%(tag,nb,common.getstring(30050)), #libellé
                            params    = [("method","tag"),("tag",tag),("tagtype",tagtype),("page","1"),("viewmode","view")],#paramètres
                            action    = "showpics",#action
                            iconimage = join(PIC_PATH,"keywords.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-keyword.png"),
                            contextmenu   = [( common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addfolder'&method='tag'&tag='%s'&tagtype='%s'&viewmode='scan'\")"%(sys.argv[0],common.quote_param(tag),tagtype)),
                                             ( common.getstring(30061),"XBMC.RunPlugin(\"%s?action='showpics'&method='tag'&page=''&viewmode='zip'&name='%s'&tag='%s'&tagtype='%s'\")"%(sys.argv[0],common.quote_param(tag),common.quote_param(tag),tagtype) ),
                                             ( common.getstring(30062),"XBMC.RunPlugin(\"%s?action='showpics'&method='tag'&page=''&viewmode='export'&name='%s'&tag='%s'&tagtype='%s'\")"%(sys.argv[0],common.quote_param(tag),common.quote_param(tag),tagtype) )
                                             ],#menucontextuel
                            total = total)#nb total d'éléments
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


    def show_period(self): #TODO finished the datestart and dateend editing
        common.log("show_period", "started")
        update=False
        self.addDir(name      = common.getstring(30106),
                    params    = [("period","setperiod"),("viewmode","view")],#paramètres
                    action    = "showperiod",#action
                    iconimage = join(PIC_PATH,"newperiod.png"),#icone
                    fanart    = join(PIC_PATH,"fanart-period.png"),
                    contextmenu   = None)#menucontextuel
        #If We previously choose to add a new period, this test will ask user for setting the period :
        if self.args.period=="setperiod":
            common.log("show_period", "setperiod")
            dateofpics = MPDB.get_pics_dates()#the choice of the date is made with pictures in database (datetime of pics are used)

            nameddates = [strftime(self.prettydate(common.getstring(30002),strptime(date,"%Y-%m-%d")).encode("utf8"),strptime(date,"%Y-%m-%d")) for date in dateofpics]
            common.log("show_period >> namedates", nameddates)
            
            if len(nameddates):
                
                dialog = xbmcgui.Dialog()
                rets = dialog.select(common.getstring(30107),["[[%s]]"%common.getstring(30114)] + nameddates)#dateofpics)#choose the start date
                if not rets==-1:#is not canceled
                    if rets==0: #input manually the date
                        d = dialog.numeric(1, common.getstring(30117) ,strftime("%d/%m/%Y",strptime(dateofpics[0],"%Y-%m-%d")) )
                        datestart = strftime("%Y-%m-%d",strptime(d.replace(" ","0"),"%d/%m/%Y"))
                        deb=0
                    else:
                        datestart = dateofpics[rets-1]
                        deb=rets-1
    
                    retf = dialog.select(common.getstring(30108),["[[%s]]"%common.getstring(30114)] + nameddates[deb:])#dateofpics[deb:])#choose the end date (all dates before startdate are ignored to preserve begin/end)
                    if not retf==-1:#if end date is not canceled...
                        if retf==0:#choix d'un date de fin manuelle ou choix précédent de la date de début manuelle
                            d = dialog.numeric(1, common.getstring(30118) ,strftime("%d/%m/%Y",strptime(dateofpics[-1],"%Y-%m-%d")) )
                            dateend = strftime("%Y-%m-%d",strptime(d.replace(" ","0"),"%d/%m/%Y"))
                            deb=0
                        else:
                            dateend = dateofpics[deb+retf-1]
                        #now input the title for the period
                        #
                        kb = xbmc.Keyboard(common.smart_utf8(common.getstring(30109)%(datestart,dateend)), common.getstring(30110), False)
                        kb.doModal()
                        if (kb.isConfirmed()):
                            titreperiode = kb.getText()
                        else:
                            titreperiode = common.getstring(30109)%(datestart,dateend)
                        #add the new period inside the database
                        MPDB.addPeriode(common.smart_unicode(titreperiode),common.smart_unicode("datetime('%s')"%datestart),common.smart_unicode("datetime('%s')"%dateend) )
                update=True
            else:
                common.log("show_period", "No pictures with an EXIF date stored in DB")


        #search for inbase periods and show periods
        for periodname,dbdatestart,dbdateend in MPDB.ListPeriodes():
            periodname = common.smart_unicode(periodname)
            dbdatestart = common.smart_unicode(dbdatestart)
            dbdateend = common.smart_unicode(dbdateend)

            datestart,dateend = MPDB.Request("SELECT strftime('%%Y-%%m-%%d',('%s')),strftime('%%Y-%%m-%%d',datetime('%s','+1 days','-1.0 seconds'))"%(dbdatestart,dbdateend))[0]
            datestart = common.smart_unicode(datestart)
            dateend   = common.smart_unicode(dateend)
            self.addDir(name      = "%s [COLOR=C0C0C0C0](%s)[/COLOR]"%(periodname,
                                               common.getstring(30113)%(strftime(self.prettydate(common.getstring(30002).encode("utf8"),strptime(datestart,"%Y-%m-%d")).encode("utf8"),strptime(datestart,"%Y-%m-%d")).decode("utf8"),
                                                                    strftime(self.prettydate(common.getstring(30002).encode("utf8"),strptime(dateend  ,"%Y-%m-%d")).encode("utf8"),strptime(dateend  ,"%Y-%m-%d")).decode("utf8")
                                                                    )), #libellé
                        params    = [("method","date"),("period","period"),("datestart",datestart),("dateend",dateend),("page","1"),("viewmode","view")],#paramètres
                        action    = "showpics",#action
                        iconimage = join(PIC_PATH,"period.png"),#icone
                        fanart    = join(PIC_PATH,"fanart-period.png"),
                        contextmenu   = [ ( common.getstring(30111),"XBMC.RunPlugin(\"%s?action='removeperiod'&viewmode='view'&periodname='%s'&period='period'\")"%(sys.argv[0],common.quote_param(periodname.encode("utf8"))) ),
                                          ( common.getstring(30112),"XBMC.RunPlugin(\"%s?action='renameperiod'&viewmode='view'&periodname='%s'&period='period'\")"%(sys.argv[0],common.quote_param(periodname.encode("utf8"))) ),
                                          ( common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addfolder'&method='date'&period='period'&datestart='%s'&dateend='%s'&viewmode='scan'\")"%(sys.argv[0],datestart,dateend))
                                        ] )#menucontextuel

        xbmcplugin.addSortMethod( int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
        xbmcplugin.endOfDirectory( int(sys.argv[1]),updateListing=update )

    def show_collection(self):
        common.log("show_collection", "started")
        if self.args.method=="setcollection":#ajout d'une collection
            kb = xbmc.Keyboard("",common.getstring(30155) , False)
            kb.doModal()
            if (kb.isConfirmed()):
                namecollection = kb.getText()
            else:
                #name input for collection has been canceled
                return
            #create the collection in the database
            common.log("show_collection", "setcollection = %s"%namecollection)
            MPDB.NewCollection(namecollection)
            refresh=True
        else:
            refresh=False
            
        self.addDir(name      = common.getstring(30160),
                    params    = [("method","setcollection"),("collect",""),("viewmode","view"),],#paramètres
                    action    = "showcollection",#action
                    iconimage = join(PIC_PATH,"newcollection.png"),#icone
                    fanart    = join(PIC_PATH,"fanart-collection.png"),
                    contextmenu   = None)#menucontextuel

        for collection in MPDB.ListCollections():
            self.addDir(name      = collection[0],
                        params    = [("method","collection"),("collect",collection[0]),("page","1"),("viewmode","view")],#paramètres
                        action    = "showpics",#action
                        iconimage = join(PIC_PATH,"collection.png"),#icone
                        fanart    = join(PIC_PATH,"fanart-collection.png"),
                        contextmenu   = [(common.getstring(30158),"XBMC.RunPlugin(\"%s?action='removecollection'&viewmode='view'&collect='%s'\")"%(sys.argv[0],common.quote_param(collection[0].encode('utf-8')) ) ),
                                         (common.getstring(30159),"XBMC.RunPlugin(\"%s?action='renamecollection'&viewmode='view'&collect='%s'\")"%(sys.argv[0],common.quote_param(collection[0].encode('utf-8'))) ),
                                         (common.getstring(30061),"XBMC.RunPlugin(\"%s?action='showpics'&method='collection'&page=''&viewmode='zip'&name='%s'&collect='%s'\")"%(sys.argv[0],common.quote_param(collection[0].encode('utf-8')),common.quote_param(collection[0].encode('utf-8'))) ),
                                         (common.getstring(30062),"XBMC.RunPlugin(\"%s?action='showpics'&method='collection'&page=''&viewmode='export'&name='%s'&collect='%s'\")"%(sys.argv[0],common.quote_param(collection[0].encode('utf-8')),common.quote_param(collection[0].encode('utf-8'))) )
                                         ] )#menucontextuel

        xbmcplugin.addSortMethod( int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
        xbmcplugin.endOfDirectory( int(sys.argv[1]),updateListing=refresh)

    def global_search(self):
        #récupére la liste des colonnes de la table files
        if not self.args.searchterm:
            kb = xbmc.Keyboard("",common.getstring(30115) , False)
            kb.doModal()
            if (kb.isConfirmed()):
                motrecherche = kb.getText()
            else:
                return
            refresh=False
        else:
            motrecherche = self.args.searchterm
            refresh=True


        listtags = [k for k in MPDB.list_TagTypesAndCount()]
        result = False
        for tag, _ in listtags:            
            compte = MPDB.Searchfiles(tag, motrecherche, count=True)
            if compte:
                result = True
                self.addDir(name      = common.getstring(30116)%(compte,motrecherche.decode("utf8"),tag ), #files_fields_description.has_key(colname) and files_fields_description[colname] or colname),
                            params    = [("method","search"),("field",u"%s"%tag.decode("utf8")),("searchterm",u"%s"%motrecherche.decode("utf8")),("page","1"),("viewmode","view")],#paramètres
                            action    = "showpics",#action
                            iconimage = join(PIC_PATH,"search.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-search.png"),
                            contextmenu   = [(common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addfolder'&method='search'&field='%s'&searchterm='%s'&viewmode='scan'\")"%(sys.argv[0],tag,motrecherche))])#menucontextuel
        if not result:
            dialog = xbmcgui.Dialog()
            dialog.ok(common.getstring(30000).encode("utf8"), common.getstring(30119).encode("utf8")%motrecherche)
            return
        xbmcplugin.addSortMethod( int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE )
        xbmcplugin.endOfDirectory( int(sys.argv[1]),updateListing=refresh)

    def show_roots(self):
        #show the root folders

        if self.args.do=="addroot":#add a root to scan
            dialog = xbmcgui.Dialog()
            newroot = dialog.browse(0, common.getstring(30201) , 'pictures')

            if not newroot:
                return

            if str(self.args.exclude)=="1":
                MPDB.AddRoot(newroot,0,0,1)
                xbmc.executebuiltin( "Container.Refresh(\"%s?action='rootfolders'&do='showroots'&exclude='1'&viewmode='view'\",)"%(sys.argv[0],))
                common.log("Main.show_roots", 'Exclude folder "%s" added'%newroot)
                #xbmc.executebuiltin( "Notification(%s,%s,%s,%s)"%(common.getstring(30000).encode("utf8"),common.getstring(30204).encode("utf8"),3000,join(home,"icon.png").encode("utf8") ) )
                dialogok = xbmcgui.Dialog()
                dialogok.ok(common.getstring(30000), common.getstring(30217), common.getstring(30218) )
            else:
                recursive = dialog.yesno(common.getstring(30000),common.getstring(30202)) and 1 or 0 #browse recursively this folder ?
                update = True #dialog.yesno(common.getstring(30000),common.getstring(30203)) and 1 or 0 # Remove files from database if pictures does not exists?

                #ajoute le rootfolder dans la base
                try:
                    if newroot.startswith('multipath://'):
                        common.log("Main.show_roots", 'Adding Multipath: "%s"'%unquote_plus(newroot))
                        newpartialroot = newroot[12:-1].split('/')
                        for item in newpartialroot:
                            MPDB.AddRoot(unquote_plus(item),recursive,update,0)#TODO : traiter le exclude (=0 pour le moment) pour gérer les chemins à exclure
                            common.log("Main.show_roots", 'Multipath addroot for part "%s" done'%unquote_plus(item))
                    else:
                        MPDB.AddRoot(newroot,recursive,update,0)#TODO : traiter le exclude (=0 pour le moment) pour gérer les chemins à exclure
                        common.log("Main.show_roots", 'Singlepath addroot "%s" done'%newroot)

                    xbmc.executebuiltin( "Container.Refresh(\"%s?action='rootfolders'&do='showroots'&exclude='0'&viewmode='view'\",)"%(sys.argv[0],))

                except:
                    common.log("Main.show_roots", 'MPDB.AddRoot failed for "%s"'%newroot, xbmc.LOGERROR)
                common.show_notification(common.getstring(30000),common.getstring(30204),3000,join(home,"icon.png"))
                #xbmc.executebuiltin( "Notification(%s,%s,%s,%s)"%(common.getstring(30000).encode("utf8"),common.getstring(30204).encode("utf8"),3000,join(home,"icon.png").encode("utf8") ) )
                if not(xbmc.getInfoLabel( "Window.Property(DialogAddonScan.IsAlive)" ) == "true"): #si dialogaddonscan n'est pas en cours d'utilisation...
                    if dialog.yesno(common.getstring(30000),common.getstring(30206)):#do a scan now ?
                        if newroot.startswith('multipath://'):
                            common.log("Main.show_roots", "Multipaths" )
                            newpartialroot = newroot[12:-1].split('/')
                            for item in newpartialroot:
                                common.log("Main.show_roots",  'Starting scanpath "%s"'% unquote_plus(item) )
                                common.run_script("%s,%s --rootpath=%s"%( join( home, "scanpath.py"),recursive and "-r, " or "",common.quote_param(unquote_plus(item))))
                                #xbmc.executebuiltin( "RunScript(%s,%s--rootpath=%s)"%( join( home, "scanpath.py").encode("utf8"),recursive and "-r, " or "",common.quote_param(unquote_plus(item))))
                                common.log("Main.show_roots",  'Scanpath "%s" started'% unquote_plus(item) )
                        else:
                            common.log("Main.show_roots",  'Starting scanpath "%s"'%newroot)
                            common.run_script("%s,%s --rootpath=%s"%( join( home, "scanpath.py"),recursive and "-r, " or "",common.quote_param(newroot)))
                            #xbmc.executebuiltin( "RunScript(%s,%s--rootpath=%s)"%( join( home, "scanpath.py").encode("utf8"),recursive and "-r, " or "",common.quote_param(newroot)))
                            common.log("Main.show_roots",  'Scanpath "%s" started'%newroot )
                else:
                    #dialogaddonscan était en cours d'utilisation, on returncommon.log("Main.show_roots", 'Adding Multipath: "%s"'%unquote_plus(newroot))
                    return
                return

        # I don't think that this is ever called because no user knows about it
        elif self.args.do=="addrootfolder":
            if str(self.args.exclude)=="1":
                common.log("Main.show_roots", 'addrootfolder "%s" (exclude) from context menu'%self.args.addpath)
                MPDB.AddRoot(self.args.addpath,0,0,1)

        elif self.args.do=="delroot":
            try:
                common.log("Main.show_roots", 'delroot "%s"'% self.args.delpath)
                MPDB.RemoveRoot( self.args.delpath) 
            except IndexError,msg:
                common.log("Main.show_roots", 'delroot IndexError %s - %s'%( IndexError,msg), xbmc.LOGERROR )
            if self.args.delpath != 'neverexistingpath':
                common.show_notification(common.getstring(30000),common.getstring(30205),3000,join(home,"icon.png"))
                #xbmc.executebuiltin( "Notification(%s,%s,%s,%s)"%(common.getstring(30000).encode("utf8"),common.getstring(30205).encode("utf8"),3000,join(home,"icon.png").encode('utf-8')))
        elif self.args.do=="rootclic":#clic sur un chemin (à exclure ou à scanner)
            if not(xbmc.getInfoLabel( "Window.Property(DialogAddonScan.IsAlive)" ) == "true"): #si dialogaddonscan n'est pas en cours d'utilisation...
                if str(self.args.exclude)=="0":#le chemin choisi n'est pas un chemin à exclure...
                    path,recursive,update,exclude = MPDB.getRoot(self.args.rootpath)
                    common.run_script("%s,%s --rootpath=%s"%( join( home, "scanpath.py"),recursive and "-r, " or "",common.quote_param(path)))
                    #xbmc.executebuiltin( "RunScript(%s,%s--rootpath=%s)"%( join( home, "scanpath.py").encode("utf8"),recursive and "-r, " or "",common.quote_param(path)))
                else:#clic sur un chemin à exclure...
                    pass
            else:
                #dialogaddonscan était en cours d'utilisation, on return
                return
        elif self.args.do=="scanall":
            if not(xbmc.getInfoLabel( "Window.Property(DialogAddonScan.IsAlive)" ) == "true"): #si dialogaddonscan n'est pas en cours d'utilisation...

                dialog = xbmcgui.Dialog()
                if True == dialog.yesno(common.getstring(30000), common.getstring(30214), common.getstring(30215), common.getstring(30216) ):
                    MPDB.Request('Update Files set sha = NULL')

                #xbmc.executebuiltin( "RunScript(%s,--database)"% join( home, "scanpath.py").encode("utf8") )
                common.run_script("%s,--database"% join( home, "scanpath.py"))
                return
            else:
                #dialogaddonscan était en cours d'utilisation, on return
                return
        elif self.args.do=="refreshpaths":
            pass

        if int(sys.argv[1]) >= 0:
            excludefolders=[]
            includefolders=[]
            for path,recursive,update,exclude in MPDB.RootFolders():
                if exclude:
                    excludefolders.append([path,recursive,update])
                else:
                    includefolders.append([path,recursive,update])


            # Add a path to database
            self.addAction(name      = common.getstring(30208),#add a root path
                        params    = [("do","addroot"),("viewmode","view"),("exclude","0")],#paramètres
                        action    = "rootfolders",#action
                        iconimage = join(PIC_PATH,"newsettings.png"),#icone
                        fanart    = join(PIC_PATH,"fanart-setting.png"),
                        contextmenu   = None)#menucontextuel

            # Scan all paths
            if len(includefolders) > 0:
                self.addAction(name      = common.getstring(30213),#scan all distinct root paths
                            params    = [("do","scanall"),("viewmode","view"),],#paramètres
                            action    = "rootfolders",#action
                            iconimage = join(PIC_PATH,"settings.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-setting.png"),
                            contextmenu   = None)#menucontextuel

            # Show included folders
            for path,recursive,update in includefolders:
                srec = recursive==1 and "ON" or "OFF"
                supd = update==1 and "ON" or "OFF"
                path = common.smart_unicode(path)

                self.addAction(name      = "[COLOR=FF66CC00][B][ + ][/B][/COLOR] "+path+" [COLOR=FFC0C0C0][recursive="+srec+" , update="+supd+"][/COLOR]",
                            params    = [("do","rootclic"),("rootpath",path),("viewmode","view"),("exclude","0")],#paramètres
                            action    = "rootfolders",#action
                            iconimage = join(PIC_PATH,"settings.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-setting.png"),
                            #menucontextuel
                            contextmenu   = [( common.getstring(30206),"Notification(TODO : scan folder,scan this folder now !,3000,%s)"%join(home,"icon.png").encode("utf8") ),
                                             ( common.getstring(30207),"Container.Update(\"%s?action='rootfolders'&do='delroot'&delpath='%s'&exclude='1'&viewmode='view'\",)"%(sys.argv[0],common.quote_param(path.encode('utf-8'))))
                                             ]
                            )
            #Add a folder to exclude
            if len(includefolders)>=0:
                self.addAction(name      = common.getstring(30211),#add a folder to exclude
                            params    = [("do","addroot"),("viewmode","view"),("exclude","1")],#paramètres
                            action    = "rootfolders",#action
                            iconimage = join(PIC_PATH,"newsettings.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-setting.png"),
                            contextmenu   = None)#menucontextuel

            #Show excluded folders
            for path,recursive,update in excludefolders:
                self.addAction(name      = "[COLOR=FFFF0000][B][ - ][/B][/COLOR] "+path,
                            params    = [("do","rootclic"),("rootpath",path),("viewmode","view"),("exclude","1")],#paramètres
                            action    = "rootfolders",#action
                            iconimage = join(PIC_PATH,"settings.png"),#icone
                            fanart    = join(PIC_PATH,"fanart-setting.png"),
                            #menucontextuel
                            contextmenu   = [( common.getstring(30210),"Container.Update(\"%s?action='rootfolders'&do='delroot'&delpath='%s'&exclude='0'&viewmode='view'\",)"%(sys.argv[0],common.quote_param(path.encode('utf-8'))))])

            if self.args.do=="delroot":
                xbmcplugin.endOfDirectory( int(sys.argv[1]), updateListing=True)
            else:
                xbmcplugin.endOfDirectory( int(sys.argv[1]))

    def show_map(self):
        """get a google map for the given place (place is a string for an address, or a couple of gps lat/lon datas"""
        import geomaps
        
        try:
            path = common.smart_unicode(self.args.path)
            filename = common.smart_unicode(self.args.filename)
            joined = common.smart_utf8(join(path,filename))
            showmap = geomaps.main(datapath = DATA_PATH, place =self.args.place, picfile = joined )
        except:
            try:
                path = common.smart_utf8(self.args.path)
                filename = common.smart_utf8(self.args.filename)
                joined = join(path,filename)
                showmap = geomaps.main(datapath = DATA_PATH, place =self.args.place, picfile = joined )
            except:
                return

        showmap.doModal()
        del showmap


    def prettydate(self,dateformat,datetuple):
        "Replace %a %A %b %B date string formater (see strftime format) by the day/month names for the given date tuple given"
        dateformat = dateformat.replace("%a",common.getstring(30005).split("|")[datetuple.tm_wday])      #replace %a marker by short day name
        dateformat = dateformat.replace("%A",common.getstring(30007).split("|")[datetuple.tm_wday])      #replace %A marker by long day name
        dateformat = dateformat.replace("%b",common.getstring(30006).split("|")[datetuple.tm_mon - 1])   #replace %b marker by short month name
        dateformat = dateformat.replace("%B",common.getstring(30008).split("|")[datetuple.tm_mon - 1])   #replace %B marker by long month name
        return dateformat


    ##################################
    #traitement des menus contextuels
    ##################################
    def remove_period(self):

        MPDB.delPeriode(self.args.periodname)
        xbmc.executebuiltin( "Container.Update(\"%s?action='showperiod'&viewmode='view'&period=''\" , replace)"%sys.argv[0]  )

    def rename_period(self):
        #TODO : test if 'datestart' is before 'dateend'
        periodname = self.args.periodname
        datestart,dateend = MPDB.RequestWithBinds( """SELECT DateStart,DateEnd FROM Periodes WHERE PeriodeName=? """, (periodname,) )[0]

        dialog = xbmcgui.Dialog()
        d = dialog.numeric(1, "Input start date for period" ,strftime("%d/%m/%Y",strptime(datestart,"%Y-%m-%d %H:%M:%S")) )
        datestart = strftime("%Y-%m-%d",strptime(d.replace(" ","0"),"%d/%m/%Y"))

        d = dialog.numeric(1, "Input end date for period" ,strftime("%d/%m/%Y",strptime(dateend,"%Y-%m-%d %H:%M:%S")) )
        dateend = strftime("%Y-%m-%d",strptime(d.replace(" ","0"),"%d/%m/%Y"))

        kb = xbmc.Keyboard(common.smart_unicode(periodname), common.getstring(30110), False)
        kb.doModal()
        if (kb.isConfirmed()):
            titreperiode = kb.getText()
        else:
            titreperiode = periodname

        MPDB.renPeriode(self.args.periodname,titreperiode,datestart,dateend)
        xbmc.executebuiltin( "Container.Update(\"%s?action='showperiod'&viewmode='view'&period=''\" , replace)"%sys.argv[0]  )

    def addTo_collection(self):
        listcollection = ["[[%s]]"%common.getstring(30157)]+[col[0] for col in MPDB.ListCollections()]

        dialog = xbmcgui.Dialog()
        rets = dialog.select(common.getstring(30156),listcollection)
        if rets==-1: #choix de liste annulé
            return
        if rets==0: #premier élément : ajout manuel d'une collection
            kb = xbmc.Keyboard("", common.getstring(30155), False)
            kb.doModal()
            if (kb.isConfirmed()):
                namecollection = kb.getText()
            else:
                #il faut traiter l'annulation
                return
            #2 créé la collection en base
            MPDB.NewCollection(namecollection)
        else: #dans tous les autres cas, une collection existente choisie
            namecollection = listcollection[rets]
        #3 associe en base l'id du fichier avec l'id de la collection
        namecollection = common.smart_unicode(namecollection)
        path     = common.smart_unicode(self.args.path)
        filename = common.smart_unicode(self.args.filename)

        MPDB.addPicToCollection( namecollection, path, filename )
        common.show_notification(common.getstring(30000), common.getstring(30154)+ ' ' + namecollection,3000,join(home,"icon.png"))
        #xbmc.executebuiltin( "Notification(%s,%s %s,%s,%s)"%(common.getstring(30000).encode('utf-8'),common.getstring(30154).encode('utf-8'),namecollection.encode('utf-8'),3000,join(home,"icon.png").encode('utf-8')))


    def add_folder_to_collection(self):
        listcollection = ["[[%s]]"%common.getstring(30157)]+[col[0] for col in MPDB.ListCollections()]

        dialog = xbmcgui.Dialog()
        rets = dialog.select(common.getstring(30156),listcollection)
        if rets==-1: #cancel
            return
        if rets==0: # new collection
            kb = xbmc.Keyboard("", common.getstring(30155), False)
            kb.doModal()
            if (kb.isConfirmed()):
                namecollection = kb.getText()
            else:
                # cancel
                return
            MPDB.NewCollection(namecollection)
        else: # existing collection
            namecollection = listcollection[rets]

        #3 associe en base l'id du fichier avec l'id de la collection
        filelist = self.show_pics() #on récupère les photos correspondantes à la vue
        namecollection = common.smart_unicode(namecollection)
        for path,filename in filelist: #on les ajoute une par une
            path           = common.smart_unicode(path)
            filename       = common.smart_unicode(filename)
            MPDB.addPicToCollection( namecollection,path,filename )
        common.show_notification(common.getstring(30000), common.getstring(30161)%len(filelist)+' '+namecollection,3000,join(home,"icon.png"))
        #xbmc.executebuiltin( "Notification(%s,%s %s,%s,%s)"%(common.getstring(30000).encode("utf8"), common.getstring(30161).encode("utf8")%len(filelist),namecollection.encode("utf8"), 3000,join(home,"icon.png").encode("utf8")) )

    def remove_collection(self):
        MPDB.delCollection(self.args.collect)
        xbmc.executebuiltin( "Container.Update(\"%s?action='showcollection'&viewmode='view'&collect=''&method='show'\" , replace)"%sys.argv[0] , )

    def rename_collection(self):
        kb = xbmc.Keyboard(self.args.collect, common.getstring(30153), False)
        kb.doModal()
        if (kb.isConfirmed()):
            newname = kb.getText()
        else:
            newname = self.args.collect
        MPDB.renCollection(self.args.collect,newname)
        xbmc.executebuiltin( "Container.Update(\"%s?action='showcollection'&viewmode='view'&collect=''&method='show'\" , replace)"%sys.argv[0] , )

    def del_pics_from_collection(self):
        MPDB.delPicFromCollection(self.args.collect,self.args.path,self.args.filename)
        xbmc.executebuiltin( "Container.Update(\"%s?action='showpics'&viewmode='view'&page='1'&collect='%s'&method='collection'\" , replace)"%(sys.argv[0],common.quote_param(self.args.collect)) , )

    def show_diaporama(self):
        #1- récupère la liste des images (en utilisant show_pics avec le bon paramètre
        self.args.viewmode="diapo"
        self.args.page=""
        self.show_pics()

    def show_lastshots(self):
        #récupère X dernières photos puis affiche le résultat
        pass

    # MikeBZH44 : Method to execute query
    def exec_query(self,query):
        # Execute query
        # Needed to store results if CommonCache cacheFunction is used
        _results = MPDB.Request( query )
        return _results

    # MikeBZH44 : Method to query database and store result in Windows properties and CommonCache table
    def set_properties(self):
        # Init variables
        _limit = m.args.limit
        _method = m.args.method
        _results = []
        _count = 0
        WINDOW = xbmcgui.Window( 10000 )
        START_TIME = time.time()
        # Get general statistics and set properties
        Count = MPDB.Request( """SELECT COUNT(*) FROM files WHERE ImageDateTime IS NOT NULL""" )[0]
        Collections = MPDB.Request( """SELECT COUNT(*) FROM collections""" )[0]
        Categories = MPDB.Request( """select count(distinct tf.idFile) from TagTypes tt, TagContents tc, TagsInFiles tf where tt.idTagType = tc.idTagType and tc.idTagContent = tf.idTagContent and tt.TagTranslation = ( select TagTranslation from TagTypes tti where tti.TagType = 'Category')""" )[0]
        Folders = MPDB.Request( """SELECT COUNT(*) FROM folders WHERE HasPics = 1""" )[0]
        WINDOW.clearProperty( "MyPicsDB%s.Count" %(_method))
        WINDOW.setProperty ( "MyPicsDB%s.Count" %(_method), str(Count[0]) )
        WINDOW.clearProperty( "MyPicsDB%s.Categories" %(_method))
        WINDOW.setProperty ( "MyPicsDB%s.Categories" %(_method), str(Categories[0]) )
        WINDOW.clearProperty( "MyPicsDB%s.Collections" %(_method))
        WINDOW.setProperty ( "MyPicsDB%s.Collections" %(_method), str(Collections[0]) )
        WINDOW.clearProperty( "MyPicsDB%s.Folders" %(_method))
        WINDOW.setProperty ( "MyPicsDB%s.Folders" %(_method), str(Folders[0]) )
        # Build query string
        _query = """SELECT b.FolderName, a.strPath, a.strFilename, ImageDateTime """
        _query += """FROM files AS a, folders AS b """
        _query += """WHERE ImageDateTime IS NOT NULL AND a.idFolder = b.idFolder """
        if _method == "Latest":
            # Get latest pictures based on shooted date time or added date time
            _sort = m.args.sort
            if _sort == "Shooted":
                _query += """ORDER BY ImageDateTime DESC LIMIT %s""" %(str(_limit))
            if _sort == "Added":
                _query += """ORDER BY "DateAdded" DESC LIMIT %s""" %(str(_limit))
        if _method == "Random":
            # Get random pictures from database
            _query += """ORDER BY RANDOM() LIMIT %s""" %(str(_limit))
        # Request database
        _results = self.exec_query( _query )
        cache.table_name = "MyPicsDB"
        # Go through results
        for _picture in _results:
            _count += 1
            # Clean and set properties
            _path = join( _picture[1], _picture[2])
            WINDOW.clearProperty( "MyPicsDB%s.%d.Folder" % ( _method, _count ) )
            WINDOW.setProperty( "MyPicsDB%s.%d.Folder" % ( _method, _count ), _picture[0] )
            WINDOW.clearProperty( "MyPicsDB%s.%d.Path" % ( _method, _count ) )
            WINDOW.setProperty( "MyPicsDB%s.%d.Path" % ( _method, _count ), _path )
            WINDOW.clearProperty( "MyPicsDB%s.%d.Name" % ( _method, _count ) )
            WINDOW.setProperty( "MyPicsDB%s.%d.Name" % ( _method, _count ), _picture[2] )
            WINDOW.clearProperty( "MyPicsDB%s.%d.Date" % ( _method, _count ) )
            WINDOW.setProperty( "MyPicsDB%s.%d.Date" % ( _method, _count ), _picture[3] )
            # Store path into CommonCache
            cache.set("MyPicsDB%s.%d" %( _method, _count ), ( _path ))
        # Store number of pictures fetched into CommonCache
        cache.set("MyPicsDB%s.Nb" %(_method), str(_count) )
        # Result contain less than _limit pictures, clean extra properties
        if _count < _limit:
            for _i in range (_count+1, _limit+1):
                WINDOW.clearProperty( "MyPicsDB%s.%d.Folder" % ( _method, _i ) )
                WINDOW.clearProperty( "MyPicsDB%s.%d.Path" % ( _method, _i ) )
                cache.set("MyPicsDB%s.%d" %( _method, _i ), "")
                WINDOW.clearProperty( "MyPicsDB%s.%d.Name" % ( _method, _i ) )
                WINDOW.clearProperty( "MyPicsDB%s.%d.Date" % ( _method, _i ) )
        # Display execution time
        t = ( time.time() - START_TIME )
        if t >= 60: return "%.3fm" % ( t / 60.0 )
        common.log("set_properties", "Function set_properties took %.3f s" % ( t ))

    # MikeBZH44 : Method to get pictures from CommonCache and start slideshow
    def set_slideshow(self):
        # Init variables
        _current = m.args.current
        _method = m.args.method
        START_TIME = time.time()
        # Clear current photo playlist
        _json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Clear", "params": {"playlistid": 2}, "id": 1}')
        _json_query = unicode(_json_query, 'utf-8', errors='ignore')
        _json_pl_response = simplejson.loads(_json_query)
        # Get number of picture to display from CommonCache
        cache.table_name = "MyPicsDB"
        _limit = int(cache.get("MyPicsDB%s.Nb" %(_method)))
        # Add pictures to slideshow, start from _current position
        for _i in range( _current,  _limit + 1 ):
            # Get path from CommonCache for current picture
            _path = cache.get("MyPicsDB%s.%d" %( _method, _i ))
            # Add current picture to slideshow
            _json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Add", "params": {"playlistid": 2, "item": {"file" : "%s"}}, "id": 1}' %(str(_path.encode('utf8')).replace("\\","\\\\")))
            _json_query = unicode(_json_query, 'utf-8', errors='ignore')
            _json_pl_response = simplejson.loads(_json_query)
        # If _current not equal 1 then add pictures from 1 to _current - 1
        if _current != 1:
            for _i in range( 1, _current ):
                # Get path from CommonCache for current picture
                _path = cache.get("MyPicsDB%s.%d" %( _method, _i ))
                # Add current picture to slideshow
                _json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Add", "params": {"playlistid": 2, "item": {"file" : "%s"}}, "id": 1}' %(str(_path.encode('utf8')).replace("\\","\\\\")))
                _json_query = unicode(_json_query, 'utf-8', errors='ignore')
                _json_pl_response = simplejson.loads(_json_query)
        # Start Slideshow
        _json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.Open", "params": {"item": {"playlistid": 2}}, "id": 1}' )
        _json_query = unicode(_json_query, 'utf-8', errors='ignore')
        _json_pl_response = simplejson.loads(_json_query)
        t = ( time.time() - START_TIME )
        # Display execution time
        if t >= 60: return "%.3fm" % ( t / 60.0 )
        common.log("set_slideshow", "Function set_slideshow took %.3f s" % ( t ))

    def show_pics(self):
        if not self.args.page: #0 ou "" ou None : pas de pagination ; on affiche toutes les photos de la requête sans limite
            limit = -1  # SQL 'LIMIT' statement equals to -1 returns all resulting rows
            offset = -1 # SQL 'OFFSET' statement equals to -1  : return resulting rows with no offset
            page = 0
        else: #do pagination stuff
            limit = int(common.getaddon_setting("picsperpage"))
            offset = (int(self.args.page)-1)*limit
            page = int(self.args.page)

        picfanart = None
        if self.args.method == "folder":#NON UTILISE : l'affichage par dossiers affiche de lui même les photos
            pass

        # we are showing pictures for a DATE selection
        elif self.args.method == "date":
            #   lister les images pour une date donnée
            picfanart = join(PIC_PATH,"fanart-date.png")
            formatstring = {"year":"%Y","month":"%Y-%m","date":"%Y-%m-%d","":"%Y","period":"%Y-%m-%d"}[self.args.period]
            if self.args.period=="year" or self.args.period=="":
                if self.args.value:
                    filelist = MPDB.pics_for_period('year',self.args.value)
                else:
                    filelist = MPDB.search_all_dates()

            elif self.args.period in ["month","date"]:
                filelist = MPDB.pics_for_period(self.args.period,self.args.value)

            elif self.args.period=="period":
                picfanart = join(PIC_PATH,"fanart-period.png")
                filelist = MPDB.search_between_dates(DateStart=(self.args.datestart,formatstring),
                                                     DateEnd=(self.args.dateend,formatstring))
            else:#period not recognized, show whole pics : TODO check if useful and if it can not be optimized for something better
                listyears=MPDB.get_years()
                amini=min(listyears)
                amaxi=max(listyears)
                if amini and amaxi:
                    filelist = MPDB.search_between_dates( ("%s"%(amini),formatstring) , ( "%s"%(amaxi),formatstring) )
                else:
                    filelist = []

        # we are showing pictures for a TAG selection
        elif self.args.method == "wizard":
            filelist = MPDB.search_filter_tags(self.args.kw.decode("utf8"), self.args.nkw.decode("utf8"), self.args.matchall)

        # we are showing pictures for a TAG selection
        elif self.args.method == "tag":
            picfanart = join(PIC_PATH,"fanart-keyword.png")
            if not self.args.tag:#p_category
                filelist = MPDB.search_tag(None)
            else:
                filelist = MPDB.search_tag(self.args.tag.decode("utf8"), self.args.tagtype.decode("utf8"))


        # we are showing pictures for a FOLDER selection
        elif self.args.method == "folders":
            #   lister les images du dossier self.args.folderid et ses sous-dossiers
            # BUG CONNU : cette requête ne récupère que les photos du dossier choisi, pas les photos 'filles' des sous dossiers
            #   il faut la modifier pour récupérer les photos filles des sous dossiers
            picfanart = join(PIC_PATH,"fanart-folder.png")
            listid = MPDB.all_children(self.args.folderid)
            filelist = [row for row in MPDB.Request( """SELECT p.FullPath,f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND p.ParentFolder in ('%s') ORDER BY ImageDateTime ASC LIMIT %s OFFSET %s"""%("','".join([str(i) for i in listid]),
                                                                                                                                                                                                                                    limit,
                                                                                                                                                                                                                                    offset) )]

        elif self.args.method == "collection":
            picfanart = join(PIC_PATH,"fanart-collection.png")
            filelist = MPDB.getCollectionPics(self.args.collect)

        elif self.args.method == "search":
            picfanart = join(PIC_PATH,"fanart-collection.png")
            filelist = MPDB.Searchfiles(self.args.field,self.args.searchterm,count=False)

        elif self.args.method == "lastmonth":
            #show pics taken within last month
            picfanart = join(PIC_PATH,"fanart-date.png")
            filelist = [row for row in MPDB.Request( """SELECT strPath,strFilename FROM files WHERE datetime(ImageDateTime) BETWEEN datetime('now','-1 months') AND datetime('now') ORDER BY ImageDateTime ASC LIMIT %s OFFSET %s"""%(limit,offset))]

        elif self.args.method == "recentpicsdb":#pictures added to database within x last days __OK
            picfanart = join(PIC_PATH,"fanart-date.png")
            numberofdays = common.getaddon_setting("recentnbdays")
            filelist = [row for row in MPDB.Request( """SELECT strPath,strFilename FROM files WHERE DateAdded IN (SELECT DISTINCT DateAdded FROM files WHERE DateAdded>=datetime('now','start of day','-%s days'))  ORDER BY DateAdded ASC LIMIT %s OFFSET %s"""%(numberofdays,limit,offset))]

        elif self.args.method =="lastpicsshooted":#X last pictures shooted __OK
            picfanart = join(PIC_PATH,"fanart-date.png")
            filelist = [row for row in MPDB.Request( """SELECT strPath,strFilename FROM files WHERE ImageDateTime IS NOT NULL ORDER BY ImageDateTime DESC LIMIT %s"""%common.getaddon_setting('lastpicsnumber') )]

        elif self.args.method =="videos":#show all videos __OK
            picfanart = join(PIC_PATH,"fanart-videos.png")
            filelist = [row for row in MPDB.Request( """SELECT strPath,strFilename FROM files WHERE ftype="video" ORDER BY ImageDateTime DESC LIMIT %s OFFSET %s"""%(limit,offset) )]

        #on teste l'argumen 'viewmode'
            #si viewmode = view : on liste les images
            #si viewmode = scan : on liste les photos qu'on retourne
            #si viewmode = zip  : on liste les photos qu'on zip
            #si viewmode = diapo: on liste les photos qu'on ajoute au diaporama
        if self.args.viewmode=="scan":
            return filelist
        if self.args.viewmode=="diapo":
            pDialog = xbmcgui.DialogProgress()
            pDialog.create(common.getstring(30000), 'Preparing SlideShow :','')
            from urllib import urlopen
            HTTP_API_url = "http://%s/xbmcCmds/xbmcHttp?command="%xbmc.getIPAddress()
            urlopen(HTTP_API_url + "ClearSlideshow" )
            c=0
            for path,filename in filelist:
                c=c+1
                pDialog.update(int(100*(float(c)/len(filelist))) , "Adding pictures to the slideshow",filename)
                if pDialog.iscanceled():break
                urlopen(HTTP_API_url + "AddToSlideshow(%s)" % common.quote_param(join(path,filename)))
            if not pDialog.iscanceled(): xbmc.executebuiltin( "SlideShow(,,notrandom)" )
            pDialog.close()
            return

        if self.args.viewmode=="zip":
            from tarfile import open as taropen
            #TODO : enable user to select the destination
            destination = join(DATA_PATH,self.args.name.decode("utf8")+".tar.gz")
            destination = common.smart_unicode(xbmc.translatePath(destination))

            if isfile(destination):
                dialog = xbmcgui.Dialog()
                ok = dialog.yesno(common.getstring(30000).encode('utf-8'),common.getstring(30064).encode('utf-8')%basename(destination),dirname(destination), common.getstring(30065).encode('utf-8'))#Archive already exists, overwrite ?
                if not ok:
                    #todo, ask for another name and if cancel, cancel the zip process as well
                    common.show_notification(common.getstring(30000),common.getstring(30066),3000,join(home,"icon.png"))
                    #xbmc.executebuiltin( "Notification(%s,%s,%s,%s)"%(common.getstring(30000).encode('utf-8'),common.getstring(30066).encode('utf-8'),3000,join(home,"icon.png").encode('utf-8')) )
                    return
                else:
                    pass #user is ok to overwrite, let's go on

            tar = taropen(destination.encode(sys.getfilesystemencoding()),mode="w:gz")#open a tar file using gz compression
            error = 0
            pDialog = xbmcgui.DialogProgress()
            pDialog.create(common.getstring(30000), common.getstring(30063),'')
            compte=0
            msg=""
            for (path,filename) in filelist:
                path     = common.smart_unicode(path)
                filename = common.smart_unicode(filename)
                compte=compte+1
                picture = common.smart_unicode(join(path,filename))
                arcroot = common.smart_unicode(path.replace( dirname( picture ), "" ))
                arcname = common.smart_unicode(join( arcroot, filename ).replace( "\\", "/" ))
                if common.smart_unicode(picture) == common.smart_unicode(destination): # sert à rien de zipper le zip lui même :D
                    continue
                pDialog.update(int(100*(compte/float(len(filelist)))),common.getstring(30067),picture)#adding picture to the archive
                try:
                    # Dirty hack for windows. 7Zip uses codepage cp850
                    if RunningOS == 'win32':
                        enc='cp850'
                    else:
                        enc='utf-8'
                    tar.add( common.smart_unicode(picture).encode(sys_encoding) , common.smart_unicode(arcname).encode(enc) )
                except:
                    common.log("show_pics >> zip",  "tar.gz compression error :", xbmc.LOGERROR)
                    error += 1
                    common.log("show_pics >> zip",  "Error  %s" % common.smart_unicode(arcname).encode(sys_encoding), xbmc.LOGERROR)
                    print_exc()
                if pDialog.iscanceled():
                    msg = common.getstring(30068) #Zip file has been canceled !
                    break
            tar.close()
            if not msg:
                if error: msg = common.getstring(30069)%(error,len(filelist))   #"%s Errors while zipping %s files"
                else: msg = common.getstring(30070)%len(filelist)               #%s files successfully Zipped !!
            common.show_notification(common.getstring(30000),msg,3000,join(home,"icon.png"))
            #xbmc.executebuiltin( "Notification(%s,%s,%s,%s)"%(common.getstring(30000).encode('utf-8'),msg.encode('utf-8'),3000,join(home,"icon.png").encode('utf-8')) )
            return

        if self.args.viewmode=="export":
            #1- ask for destination
            dialog = xbmcgui.Dialog()
            dstpath = dialog.browse(3, common.getstring(30180),"files" ,"", True, False, "")#Choose the destination for exported pictures
            dstpath = common.smart_unicode(dstpath)
            #pour créer un dossier dans la destination, on peut utiliser le nom  self.args.name
            if dstpath == "":
                return
            #3- use the  name to export to that folder
            #   a- ask the user if subfolder has to be created
            #   a-1/ yes : show the keyboard for a possible value for a folder name (using m.args.name as base name)
            #               repeat as long as input value is not correct for a folder name or dialog has been canceled
            #   a-2/ no : simply go on with copy ...
            ok = dialog.yesno(common.getstring(30000),common.getstring(30181),"(%s)"%self.args.name)#do you want to create a folder for exported pictures ?
            if ok:
                dirok=False
                while not dirok:
                    kb = xbmc.Keyboard(self.args.name, common.getstring(30182).encode('utf-8'), False)#Input subfolder name
                    kb.doModal()

                    if (kb.isConfirmed()):
                        subfolder = common.smart_unicode(kb.getText())
                        try:
                            os.mkdir(join(dstpath,subfolder))
                            dstpath = join(dstpath,subfolder)
                            dirok = True
                        except Exception,msg:
                            print_exc()
                            dialog.ok(common.getstring(30000),"Error#%s : %s"%msg.args)
                    else:
                        common.show_notification(common.getstring(30000),common.getstring(30183),3000,join(home,"icon.png"))
                        #xbmc.executebuiltin( "Notification(%s,%s,%s,%s )"%(common.getstring(30000).encode('utf-8'),common.getstring(30183).encode('utf-8'),3000,join(home,"icon.png").encode('utf-8')) )
                        return


            #browse(type, heading, shares[, mask, useThumbs, treatAsFolder, default])
            from shutil import copy
            pDialog = xbmcgui.DialogProgress()
            pDialog.create(common.getstring(30000),common.getstring(30184))# 'Copying files...')
            i=0.0
            cpt=0
            for path,filename in filelist:

                path     = common.smart_unicode(path)
                filename = common.smart_unicode(filename)

                pDialog.update(int(100*i/len(filelist)),common.getstring(30185)%join(path,filename),dstpath)#"Copying '%s' to :"
                i=i+1.0
                #2- does the destination have the file ? shall we overwrite it ?
                #TODO : rename a file if it already exists, rather than asking to overwrite it
                if isfile(join(dstpath,filename)):
                    ok = dialog.yesno(common.getstring(30000),common.getstring(30186)%filename,dstpath,common.getstring(30187))#File %s already exists in... overwrite ?
                    if not ok:
                        continue
                copy(join(path,filename), dstpath)
                cpt = cpt+1
            pDialog.update(100,common.getstring(30188),dstpath)#"Copying Finished !
            xbmc.sleep(1000)
            common.show_notification(common.getstring(30000),common.getstring(30189)%(cpt,dstpath),3000,join(home,"icon.png"))
            #xbmc.executebuiltin( "Notification(%s,%s,%s,%s )"%(common.getstring(30000).encode('utf-8'),(common.getstring(30189)%(cpt,dstpath)).encode('utf-8'),3000,join(home,"icon.png").encode('utf-8')) )
            dialog.browse(2, common.getstring(30188).encode('utf-8'),"files" ,"", True, False, dstpath.encode('utf-8'))#show the folder which contain pictures exported
            return

        #ajout des boutons de pagination
        if len(filelist)>=limit:#alors on ajoute les paginations
            #faire un menu contextuel afin de régler le nombre d'items par pages
            if int(page)>1:#à partir de la page 2
                #on affiche un bouton page précédente
##                self.addDir(name      = "page precedente",
##                            params    = [("do","rootclic"),("rootpath",path),("viewmode","view"),("exclude","1")],#paramètres
##                            action    = "showpics",#action
##                            iconimage = join(PIC_PATH,"settings.png"),#icone
##                            fanart    = join(PIC_PATH,"fanart-setting.png"),
##                            #menucontextuel
##                            contextmenu   = [( common.getstring(30210),"Container.Update(\"%s?action='rootfolders'&do='delroot'&delpath='%s'&exclude='0'&viewmode='view'\",)"%(sys.argv[0],common.quote_param(path)))
##                                             ]
##                            )
                #print "self.args"
                #print type(self.args.__dict__)
                #print list(self.args.__dict__.iteritems())
                common.log("show_pics >> pagination",  "TODO  : display previous page item")
            if (page*limit)<(len(filelist)):
                common.log("show_pics >> pagination",  "TODO  : display next page item")
                #on affiche un bouton page suivante

        # fill the pictures list
        for path,filename in filelist:
            path     = common.smart_unicode(path)
            filename = common.smart_unicode(filename)        
            #création du menu contextuel selon les situasions
            context=[]
            # - diaporama
            #context.append( (common.getstring(30303),"SlideShow(%s%s,recursive,notrandom)"%(sys.argv[0],common.quote_param(self.parm)) ) )
            # - add to collection
            context.append( ( common.getstring(30152),"XBMC.RunPlugin(\"%s?action='addtocollection'&viewmode='view'&path='%s'&filename='%s'\")"%(sys.argv[0],
                                                                                                                         common.quote_param(path.encode('utf-8')),
                                                                                                                         common.quote_param(filename.encode('utf-8')))
                              )
                            )
            # - del pic from collection : seulement les images des collections
            if self.args.method=="collection":
                context.append( ( common.getstring(30151),"XBMC.RunPlugin(\"%s?action='delfromcollection'&viewmode='view'&collect='%s'&path='%s'&filename='%s'\")"%(sys.argv[0],
                                                                                                                                             common.quote_param(self.args.collect),
                                                                                                                                             common.quote_param(path.encode('utf-8')),
                                                                                                                                             common.quote_param(filename.encode('utf-8')))
                                  )
                                )

            #3 - montrer où est localisé physiquement la photo
            context.append( (common.getstring(30060),"XBMC.RunPlugin(\"%s?action='locate'&filepath='%s'&viewmode='view'\" ,)"%(sys.argv[0],common.quote_param(join(path,filename).encode('utf-8')) ) ) )


            #5 - les infos de la photo
            #context.append( ( "paramètres de l'addon","XBMC.ActivateWindow(virtualkeyboard)" ) )
            self.addPic(filename,
                        path,
                        contextmenu = context,
                        fanart = xbmcplugin.getSetting(int(sys.argv[1]),'usepicasfanart')=='true' and join(path,filename) or picfanart
                        )
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE )#SORT_METHOD_NONE)SORT_METHOD_TITLE
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL )
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED )
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_FILE )

        #xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="photos" )
        xbmcplugin.endOfDirectory(int(sys.argv[1]))


GlobalFilterTrue  = []
GlobalFilterFalse  = []
GlobalMatchAll = False
Handle        = 0
def filterwizard_delegate(ArrayTrue, ArrayFalse, MatchAll = False):
    global GlobalFilterTrue, GlobalFilterFalse, GlobalMatchAll, Handle
    GlobalFilterTrue  = ArrayTrue
    GlobalFilterFalse  = ArrayFalse
    GlobalMatchAll = MatchAll
    Handle        = int(sys.argv[ 1 ] )



if __name__=="__main__":

    m=Main()
    #print common.getaddon_setting("ratingmini")
    #print "Handle = " + str(sys.argv[1])
    #print "Action = " + m.args.action

    if not sys.argv[ 2 ]: #pas de paramètres : affichage du menu principal
        #set the debugging for the library
        MPDB.DEBUGGING = False
        # initialisation de la base :
        MPDB.pictureDB = pictureDB
        #   - efface les tables et les recréés
        if common.getaddon_setting("initDB") == "true":
            MPDB.Make_new_base(pictureDB, True)
            common.setaddon_setting("initDB","false")
        else:
            MPDB.VersionTable()
            #MPDB.Make_new_base(pictureDB, False)
        #scan les répertoires lors du démarrage (selon setting)
        if common.getaddon_setting('bootscan')=='true':
            if not(xbmc.getInfoLabel( "Window.Property(DialogAddonScan.IsAlive)" ) == "true"):
                #si un scan n'est pas en cours, on lance le scan
                common.run_script("%s,--database"%join( home, "scanpath.py") )
                #xbmc.executebuiltin( "RunScript(%s,--database) "%join( home, "scanpath.py").encode("utf8") )
                #puis on rafraichi le container sans remplacer le contenu, avec un paramètre pour dire d'afficher le menu
                xbmc.executebuiltin( "Container.Update(\"%s?action='showhome'&viewmode='view'\" ,)"%(sys.argv[0]) , )
        else:
            m.show_home()


    elif m.args.action=='showhome':
        #display home menu
        m.show_home()
    #les sélections sur le menu d'accueil :
    #   Tri par dates
    elif m.args.action=='showdate':
        m.show_date()
    #   Tri par dossiers
    elif m.args.action=='showfolder':
        m.show_folders()
    #   Tri par mots clés
    elif m.args.action=='showkeywords':
        m.show_keywords()
    # tags submenu
    elif m.args.action=="showtranslationeditor":
        m.show_translationeditor()
    elif m.args.action=="help":
        m.show_help()
    elif m.args.action=='showwizard':
        m.show_wizard()
    elif m.args.action=='showtagtypes':
        m.show_tagtypes()
    elif m.args.action=='showtags':
        m.show_tags()
    #   Affiche les images
    elif m.args.action=='showpics':
        m.show_pics()
    #affiche la sélection de période
    elif m.args.action=='showperiod':
        m.show_period()
    elif m.args.action=='removeperiod':
        m.remove_period()
    elif m.args.action=='renameperiod':
        m.rename_period()
    elif m.args.action=='showcollection':
        m.show_collection()
    elif m.args.action=='addtocollection':
        m.addTo_collection()
    elif m.args.action=='removecollection':
        m.remove_collection()
    elif m.args.action=='delfromcollection':
        m.del_pics_from_collection()
    elif m.args.action=='renamecollection':
        m.rename_collection()
    elif m.args.action=='globalsearch':
        m.global_search()
    elif m.args.action=='addfolder':
        m.add_folder_to_collection()
    elif m.args.action=='rootfolders':
        m.show_roots()
    elif m.args.action=='locate':
        dialog = xbmcgui.Dialog()
        dstpath = dialog.browse(2, common.getstring(30071),"files" ,"", True, False, m.args.filepath)
    elif m.args.action=='geolocate':
        m.show_map()
    elif m.args.action=='diapo':
        m.show_diaporama()
    elif m.args.action=='alea':
        #TODO : afficher une liste aléatoire de photos
        pass
    elif m.args.action=='lastshot':
        #TODO : afficher une liste des X dernières photos prise selon la date de prise de vue
        m.show_lastshots()
    elif m.args.action=='request':
        #TODO : afficher le résultat d'une requête
        pass
    # MikeBZH44 : Method to query database and store result in Windows properties and CommonCache table
    elif m.args.action=='setproperties':
        m.set_properties()
    # MikeBZH44 : Method to get pictures from CommonCache and start slideshow
    elif m.args.action=='slideshow':
        m.set_slideshow()
    else:
        m.show_home()
    del MPDB



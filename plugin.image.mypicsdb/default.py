#!/usr/bin/python
# -*- coding: utf8 -*-

import os,sys
try:
    import xbmc
    makepath=xbmc.translatePath(os.path.join)
except:
    makepath=os.path.join
home = os.getcwd().replace(';','')
#these few lines are taken from AppleMovieTrailers script
# Shared resources
BASE_RESOURCE_PATH = makepath( home, "resources" )
DATA_PATH = xbmc.translatePath( "special://profile/addon_data/plugin.image.mypicsdb/")
DB_PATH = xbmc.translatePath( "special://database/")
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
# append the proper platforms folder to our path, xbox is the same as win32
env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )


import urllib
import re
import xbmcplugin,xbmcgui,xbmc
import os.path

sys_enc = sys.getfilesystemencoding()
   
if sys.modules.has_key("MypicsDB"):
    del sys.modules["MypicsDB"]
import MypicsDB as MPDB
    
global pictureDB
pictureDB = os.path.join(DB_PATH,"MyPictures.db")
##else:
##    #on utilise pas la DB principale, alors quel est la base à utiliser ?
##    #   si choix d'une DB existante
##    if xbmcplugin.getSetting(int(sys.argv[1]),'whatDB')=="0":
##        print "Il faut ouvrir une base existante"
##        #A FAIRE : tester que la base est correcte ou alors le faire depuis les paramètres
##        pictureDB = xbmcplugin.getSetting(int(sys.argv[1]),'selectDB')
##    #   sinon création d'une nouvelle DB 
##    elif xbmcplugin.getSetting(int(sys.argv[1]),'whatDB')=="1":
##        print "Il faut créer une nouvelle base"
##        #assurons nous que le chemin configuré existe
##        if not os.path.exists( xbmc.translatePath ( xbmcplugin.getSetting(int(sys.argv[1]),'selectpath') ) ):
##            print "le chemin de création de la base n'existe pas"
##            dialog = xbmcgui.Dialog()
##            ok = dialog.ok("MyPictureDB","Création d'une nouvelle base","Le chemin configuré n'existe pas !")
##        else:
##            pictureDB = "%s%s.db"%( xbmc.translatePath ( xbmcplugin.getSetting(int(sys.argv[1]),'selectpath') ) ,
##                                   xbmcplugin.getSetting(int(sys.argv[1]),'nameDB')
##                                   )
##print "la base à utiliser est :"
##print pictureDB
                               
        

def clean2(s): # remove \\uXXX
    """credit : sfaxman"""
    pat = re.compile(r'\\u(....)')
    def sub(mo):
        return unichr(int(mo.group(1), 16))
    return pat.sub(sub, smart_unicode(s))

def smart_unicode(s):
    """credit : sfaxman"""
    if not s:
        return ''
    try:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'UTF-8')
        elif not isinstance(s, unicode):
            s = unicode(s, 'UTF-8')
    except:
        if not isinstance(s, basestring):
            if hasattr(s, '__unicode__'):
                s = unicode(s)
            else:
                s = unicode(str(s), 'ISO-8859-1')
        elif not isinstance(s, unicode):
            s = unicode(s, 'ISO-8859-1')
    return s

def unescape(text):
    u"""
    credit : Fredrik Lundh
    found : http://effbot.org/zone/re-sub.htm#unescape-html"""
    import htmlentitydefs
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)





class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )
    def has_key(key):
        return key in self.__dict__

class Main:
    def __init__(self):
        self.get_args()

    def get_args(self):
        exec "self.args = _Info(%s)" % ( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ), )

    def Title(self,title):
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=urllib.unquote_plus(title.encode("utf-8")) )
        
    def addDir(self,name,params,action,iconimage,contextmenu=None,total=0,info="*"):
        #params est une liste de tuples [(nomparametre,valeurparametre),]
        #contitution des paramètres
        try:
            parameter="&".join([param+"="+repr(urllib.quote_plus(valeur.encode("utf-8"))) for param,valeur in params])
        except:
            parameter=""
        #création de l'url
        u=sys.argv[0]+"?"+parameter+"&action="+repr(str(action))+"&name="+repr(urllib.quote_plus(name.encode("utf8")))
        ok=True
        #création de l'item de liste
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        #adjonction d'informations
        #liz.setInfo( type="Pictures", infoLabels={ "Title": name } )
        #menu contextuel
        if contextmenu :
            liz.addContextMenuItems(contextmenu)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True,totalItems=total)
        return ok
    
    def addPic(self,picname,picpath,info="*"):
        ok=True
        liz=xbmcgui.ListItem(picname,info)
        liz.setLabel2(info)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=os.path.join(picpath,picname),listitem=liz,isFolder=False)
        
    def show_home(self):
        # par années
        self.addDir(unescape("Sort by Date"),[("period","year"),("value","")],"showdate","")
        # par dossiers
        self.addDir(unescape("Sort by Folders"),[("method","folders"),("folderid",""),("onlypics","non")],"showfolder","")
        # par mots clés
        self.addDir(unescape("Sort by Keywords"),[("kw",""),],"showkeywords","")
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=urllib.unquote_plus("My Pictures Library".encode("utf-8")) )
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_date(self):
        #period = year|month|date
        #value  = "2009"|"12/2009"|"25/12/2009"
        action="showdate"
        if self.args.period=="year":
            #TODO : interroger la base pour obtenir la liste des années disponibles
            #   (self.args.value sera inutile)
            listperiod=MPDB.get_years()#["2006","2007","2009"]
            nextperiod="month"
            allperiod =""
            action="showdate"
        elif self.args.period=="month":
            #TODO : interroger la base pour obtenir la liste des mois disponibles
            #   (self.args.value contiendra l'année dont on veut les mois)
            listperiod=MPDB.get_months(self.args.value)#[self.args.value+"-02",self.args.value+"-05",self.args.value+"-06"]
            nextperiod="date"
            allperiod="year"
            action="showdate"
        elif self.args.period=="date":
            #TODO : interroger la base pour obtenir la liste des dates disponibles
            #   (self.args.value contiendra le mois/jour dont on veut les dates
            listperiod=MPDB.get_dates(self.args.value)#[self.args.value+"-06",self.args.value+"-07",self.args.value+"-08",self.args.value+"-14"]
            nextperiod="date"#None
            allperiod = "month"
            action="showpics"
        else:
            listperiod=[]
            nextperiod=None

        if not None in listperiod:
            self.addDir(name      = "All the period %s"%self.args.value, #libellé
                        params    = [("method","date"),("period",allperiod),("value",self.args.value)],#paramètres
                        action    = "showpics",#action
                        iconimage = "",#icone
                        contextmenu   = None)#menucontextuel
            total=len(listperiod)
            for period in listperiod:
                if period:
                    self.addDir(name      = period, #libellé
                                params    = [("method","date"),("period",nextperiod),("value",period)],#paramètres
                                action    = action,#action
                                iconimage = "",#icone
                                contextmenu   = None,#menucontextuel
                                total = total)#nb total d'éléments
                
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="Display by date : %s"%urllib.unquote_plus(self.args.value.encode("utf-8")) )
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_folders(self):
        #on récupère les sous dossiers si il y en a
        if not self.args.folderid: #pas d'id on affiche les dossiers racines
            childrenfolders=[row for row in MPDB.Request("SELECT idFolder,FolderName FROM folders WHERE ParentFolder is null")]
        else:#sinon on affiche les sous dossiers du dossier sélectionné
            childrenfolders=[row for row in MPDB.Request("SELECT idFolder,FolderName FROM folders WHERE ParentFolder='%s'"%self.args.folderid)]
        total = len(childrenfolders)
##        if total>0: #on a des sous dossiers...
##            #il faut afficher un item pour lister toutes les photos de ce dossier et des sous dossiers
##            self.addDir(name      = "Tous les dossiers enfants", #libellé
##                        params    = [("method","folders"),("folderid",str(self.args.folderid)),("onlypics","oui")],#paramètres
##                        action    = "showpics",#action
##                        iconimage = "",#icone
##                        contextmenu   = None)#menucontextuel

        #on ajoute les dossiers 
        for idchildren, childrenfolder in childrenfolders:
            self.addDir(name      = childrenfolder, #libellé
                        params    = [("method","folders"),("folderid",str(idchildren)),("onlypics","non")],#paramètres
                        action    = "showfolder",#action
                        iconimage = "",#icone
                        contextmenu   = None,#menucontextuel
                        total = total)#nb total d'éléments
        
        #maintenant, on liste les photos si il y en a, du dossier en cours
        picsfromfolder = [row for row in MPDB.Request("SELECT p.FullPath,f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%self.args.folderid)]
        for path,filename in picsfromfolder:
            self.addPic(filename,path)
            
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="Display by folders : %s"%urllib.unquote_plus(self.args.folderid.encode("utf-8")) )
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def show_keywords(self):
        # affiche les mots clés
        listkw = [u"%s"%k.decode("utf8")  for k in MPDB.list_KW()]
        if MPDB.search_keyword(None): #si il y a des photos sans mots clés
            self.addDir(name      = "No keywords pictures", #libellé
                        params    = [("method","keyword"),("kw","")],#paramètres
                        action    = "showpics",#action
                        iconimage = "",#icone
                        contextmenu   = None)#menucontextuel
        total = len(listkw)
        for kw in listkw:
            #on alimente le plugin en mots clés
            self.addDir(name      = kw, #libellé
                        params    = [("method","keyword"),("kw",kw)],#paramètres
                        action    = "showpics",#action
                        iconimage = "",#icone
                        contextmenu   = None,#menucontextuel
                        total = total)#nb total d'éléments
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="Display by Keywords : %s"%urllib.unquote_plus(self.args.kw.encode("utf-8")) )
        xbmcplugin.endOfDirectory(int(sys.argv[1]))



    def show_pics(self):
        if self.args.method == "folder":#NON UTILISE : l'affichage par dossiers affiche de lui même les photos
            pass

        elif self.args.method == "date":
            #   lister les images pour une date donnée
            format = {"year":"%Y","month":"%Y-%m","date":"%Y-%m-%d","":"%Y"}[self.args.period]
            if self.args.period=="year" or self.args.period=="":
                if self.args.value:
                    filelist = MPDB.search_between_dates( (self.args.value,format) , ( str( int(self.args.value) +1 ),format) )
                else:
                    filelist = MPDB.search_all_dates()
                    
            elif self.args.period=="month":
                a,m=self.args.value.split("-")
                if m=="12":
                    aa=int(a)+1,
                    mm=1
                else:
                    aa=a
                    mm=int(m)+1
                filelist = MPDB.search_between_dates( ("%s-%s"%(a,m),format) , ( "%s-%s"%(aa,mm),format) )
                
            elif self.args.period=="date":
                #BUG CONNU : trouver un moyen de trouver le jour suivant en prenant en compte le nb de jours par mois
                a,m,j=self.args.value.split("-")              
                filelist = MPDB.search_between_dates( ("%s-%s-%s"%(a,m,j),format) , ( "%s-%s-%s"%(a,m,int(j)+1),format) )
                
            else:
                #pas de periode, alors toutes les photos du 01/01 de la plus petite année, au 31/12 de la plus grande année
                listyears=MPDB.get_years()
                amini=min(listyears)
                amaxi=max(listyears)
                if amini and amaxi:
                    filelist = MPDB.search_between_dates( ("%s"%(amini),format) , ( "%s"%(amaxi),format) )
                else:
                    filelist = []
                
                    
        elif self.args.method == "keyword":
            #   lister les images correspondant au mot clé
            if not self.args.kw: #le mot clé est vide '' --> les photos sans mots clés
                filelist = MPDB.search_keyword(None)
            else:
                filelist = MPDB.search_keyword(urllib.unquote_plus(self.args.kw.encode("utf8")))

        elif self.args.method == "folders":
            #   lister les images du dossier self.args.folderid et ses sous-dossiers
            # BUG CONNU : cette requête ne récupère que les photos du dossier choisi, pas les photos 'filles' des sous dossiers
            #   il faut la modifier pour récupérer les photos filles des sous dossiers
            listid = MPDB.all_children(self.args.folderid)
            filelist = [row for row in MPDB.Request( "SELECT p.FullPath,f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND p.ParentFolder in ('%s')"%"','".join([str(i) for i in listid]))]

        #alimentation de la liste
        for path,filename in filelist:
            self.addPic(filename,path)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category="photos" )
        xbmcplugin.endOfDirectory(int(sys.argv[1]))           
            
##    def show_videos(self):
##        #on pourrait lancer directement la lecture des vidéos
##        # étant donné que ca risque d'être long, envisager d'utiliser un script séparé
##        # qui chargera les url et crééra une playliste, puis lancera le player
##        # pendant ce temps les vidéos de la playliste s'afficheront
##
##        #Affichons maintenant les vidéos
##        for video in getPlaylistContent(self.args.plsID):
##            contextmenu = [ (
##                            "Enregistrer",
##                            'XBMC.RunScript(%s,%s,%s,%s,%s)'%(os.path.join(os.getcwd(),"VideoDownload.py").encode("utf8"),
##                                                        video['user_uri'],
##                                                        video["video_id"],
##                                                        os.path.join(DOWNLOADDIR.encode("utf8"),xbmc.makeLegalFilename(video['video_title'].replace('\\',''))),
##                                                        video['preview_uri']
##                                                        ),
##                                                    ),
##                            ]
##            self.addDir(video['video_title'].replace('\\','').decode("utf8"),
##                        [("user_uri",video['user_uri']),("video_id",video["video_id"]),("title",video['video_title'].replace('\\','').decode("utf8"))],
##                        "play",
##                        video['preview_uri'],
##                        contextmenu)
##
##        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_NONE)
##        xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=urllib.unquote_plus(self.args.title.encode("utf-8")) )
##        xbmcplugin.endOfDirectory(int(sys.argv[1]))




        
global pDialog
def pupdate(percent, line1="", line2="", line3=""):
    pDialog.update(percent, line1,line2,line3)
    
def scan_my_pics():
    global pictureDB,pDialog
    #dialog = xbmcgui.Dialog()
    #ok = dialog.ok("scan","scan préalable")
    pDialog = xbmcgui.DialogProgress()
    ret = pDialog.create('MyPicsDB', 'Database opening :',pictureDB)


    # initialisation de la base :
    MPDB.pictureDB = pictureDB
    #   - efface les tables et les recréés
    MPDB.Make_new_base(pictureDB,
                       ecrase= xbmcplugin.getSetting(int(sys.argv[1]),"initDB") == "true")
    picpath=[]
    if xbmcplugin.getSetting(int(sys.argv[1]),'scanfolder'):
        picpath.append(xbmcplugin.getSetting(int(sys.argv[1]),'scanfolder'))
    else:
        # A FAIRE : voir ce qu'on peut prendre comme dossier si aucun n'est configuré
        dialog = xbmcgui.Dialog()
        ok = dialog.ok("MyPicsDB","No folder to scan is set !","Please edit plugin parameters to set a folder to scan")
        return False
        
    print "Scan folder :"
    print picpath
    
    import time
    t=time.time()
    
    # parcours récursif du dossier 'picpath'
    total = 0
    n=0
    for chemin in picpath:
        pDialog.update(n*100/len(picpath), 'Scan path :',chemin)
        MPDB.compte = 0
        MPDB.browse_folder(chemin,parentfolderID=None,recursive=xbmcplugin.getSetting(int(sys.argv[1]),'recursive')=="true",update=False,updatefunc = pupdate)
        total = total + MPDB.compte
        n=n+1

    if xbmcplugin.getSetting(int(sys.argv[1]),'updateDB')=="true":
        # traitement des dossiers supprimés/renommés physiquement --> on supprime toutes les entrées de la base
        lp = MPDB.list_path()
        i = 0
        for path in lp:#on parcours tous les dossiers distinct en base de donnée
            if not os.path.isdir(path): #si le chemin en base n'est pas réellement un dossier,...
                pDialog.update(i*100/len(lp), 'Deleted folders update',path)
                MPDB.DB_del_pic(path)#... on supprime toutes les entrées s'y rapportant
                #print "%s n'est pas un chemin. Les entrées s'y rapportant dans la base sont supprimées."%path 
            i=i+1
    return True
    

if __name__=="__main__":

    m=Main()
    if not sys.argv[ 2 ]: #pas de paramètres : affichage du menu principal
        #creation d'un log
        MPDB.razlog()
        ok = scan_my_pics()#scan lorsque le plugin n'a pas de paramètres
        if not ok: #on peut traiter un retour erroné du scan
            print "erreur lors du scan"
            
            pass
        else:#sinon on affiche le menu d'accueil
            m.args.action=''
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
    elif m.args.action=='showpics':
        m.show_pics()
    elif m.args.action=='scan':
        #un scan simple est demandé...
        ok = scan_my_pics()
    else:
        m.show_home()
    del MPDB
##    m=Main()
##    m.display()
    

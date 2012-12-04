#!/usr/bin/python
# -*- coding: utf8 -*-
 
usagestr = """
requires : MyPictures Database library
requires : XBMC mediacenter (at least Dharma version)

Scans silently folders for feeding the database with IPTC/EXIF pictures metadatas

usage :
    scan_path (--database|--rootpath) [--recursive] [--update] %database_path% [%folder to scan%]
        --database
            Use the database given as first argument. Browse all root path found in the database
      OR
        --rootpath
            Scan a path for pictures (does not create the root folder in the database)
        --recursive
            If given, in addition to -p, indicates a recursive scan
        --update
            if given, remove pictures that does not exists anymore in the given path

        -h or --help : show the usage info

      arguments :
          1- full path to the database
          2- if --rootpath, the path to scan for pictures
"""

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

from sys import path as syspath,modules as sysmodules
from os import stat,listdir as oslistdir
from os import walk as oswalk
from os.path import join,splitext,walk,basename,normpath,isdir,sep as separator,dirname as osdirname

import xbmc,xbmcgui,xbmcaddon
Addon = xbmcaddon.Addon(id='plugin.image.mypicsdb')

#home = getcwd().replace(';','')
home = Addon.getAddonInfo('path')

#these few lines are taken from AppleMovieTrailers script
# Shared resources
BASE_RESOURCE_PATH = join( home, "resources" )
#DATA_PATH = xbmc.translatePath( "special://profile/addon_data/plugin.image.mypicsdb/")
DATA_PATH = Addon.getAddonInfo('profile')
PIC_PATH = join( BASE_RESOURCE_PATH, "images")
DB_PATH = xbmc.translatePath( "special://database/")
syspath.append( join( BASE_RESOURCE_PATH, "lib" ) )



__language__ = Addon.getLocalizedString

from urllib import unquote_plus
from traceback import print_exc,format_tb
if sysmodules.has_key("MypicsDB"):
    del sysmodules["MypicsDB"]
import MypicsDB as MPDB
import CharsetDecoder as decoder

global pictureDB
pictureDB = join(DB_PATH,"MyPictures.db")

from time import strftime,gmtime

from DialogAddonScan import AddonScan
from file_item import Thumbnails
global Exclude_folders #TODO
Exclude_folders = []
for path,recursive,update,exclude in MPDB.RootFolders():
    if exclude:
        #print path
        Exclude_folders.append(smart_unicode(normpath(path)))

global listext,vidsext
listext=[]
picsext=[]
vidsext=[]
for ext in Addon.getSetting("picsext").split("|"):#on récupère les extensions photo
    picsext.append("." + ext.replace(".","").upper())
for ext in Addon.getSetting("vidsext").split("|"):#on récupère les extensions vidéos
    vidsext.append("." + ext.replace(".","").upper())
listext=picsext+vidsext



def get_unicode( to_decode ):
    final = []
    try:
        temp_string = to_decode.encode('utf8')
        return to_decode
    except:
        while True:
            try:
                final.append(to_decode.decode('utf8'))
                break
            except UnicodeDecodeError, exc:
                # everything up to crazy character should be good
                final.append(to_decode[:exc.start].decode('utf8'))
                # crazy character is probably latin1
                final.append(to_decode[exc.start].decode('latin1'))
                # remove already encoded stuff
                to_decode = to_decode[exc.start+1:]
        return "".join(final)

def main2():
    #get active window
    import optparse
    global cptroots,iroots
    parser = optparse.OptionParser()
    parser.enable_interspersed_args()
    parser.add_option("--database","-d",action="store_true", dest="database",default=False)
    #parser.add_option("--help","-h")
    parser.add_option("-p","--rootpath",action="store", type="string", dest="rootpath")
    parser.add_option("-r","--recursive",action="store_true", dest="recursive", default=False)
    parser.add_option("-u","--update",action="store_true", dest="update", default=True)
    (options, args) = parser.parse_args()

    #dateadded = strftime("%Y-%m-%d %H:%M:%S")#pour inscrire la date de scan des images dans la base
    if options.rootpath:
        options.rootpath = decoder.smart_utf8(unquote_plus( options.rootpath)).replace("\\\\", "\\").replace("\\\\", "\\").replace("\\'", "\'")
        #print "options.rootpath = " + smart_unicode(options.rootpath).encode('utf-8')
        scan = AddonScan()
        scan.create( __language__(30000) )
        cptroots = 1
        iroots = 1
        scan.update(0,0,
                    __language__(30000)+" ["+__language__(30241)+"]",#MyPicture Database [preparing]
                    __language__(30247))#please wait...
        count_files(unquote_plus(options.rootpath),recursive = options.recursive)
        try:
            #browse_folder(dirname,parentfolderID=None,recursive=True,updatepics=False,addpics=True,delpics=True,rescan=False,updatefunc=None)
            #browse_folder(unquote_plus(options.rootpath),parentfolderID=None,recursive=options.recursive,updatepics=options.update,addpics=True,delpics=True,rescan=False,updatefunc=scan,dateadded = dateadded )
            browse_folder(unquote_plus(options.rootpath),parentfolderID=None,recursive=options.recursive,updatepics=True,addpics=True,delpics=True,rescan=False,updatefunc=scan,dateadded = strftime("%Y-%m-%d %H:%M:%S"))#dateadded )
        except:
            print_exc()
        scan.close()


    if options.database:
        #print "options.database"
        listofpaths = MPDB.RootFolders()
        if listofpaths:
            scan = AddonScan()#xbmcgui.getCurrentWindowId()
            scan.create( __language__(30000) )#MyPicture Database
            scan.update(0,0,
                        __language__(30000)+" ["+__language__(30241)+"]",#MyPicture Database [preparing]
                        __language__(30247))#please wait...
            #comptage des fichiers et des dossiers à parcourir
            for path,recursive,update,exclude in listofpaths:
                if exclude==0:
                    cptroots = cptroots + 1
                    count_files(unquote_plus(path),False)
            #print "cptroots"
            #print cptroots
            for path,recursive,update,exclude in listofpaths:
                if exclude==0:
                    #count_files(unquote_plus(path))
                    try:
                        #browse_folder(dirname,parentfolderID=None,recursive=True,updatepics=False,rescan=False,updatefunc=None)
                        iroots=iroots+1
                        browse_folder(unquote_plus(path),parentfolderID=None,recursive=recursive==1,updatepics=update==1,addpics=True,delpics=True,rescan=False,updatefunc=scan,dateadded = strftime("%Y-%m-%d %H:%M:%S"))#dateadded)
                    except:
                        print_exc()

            scan.close()




global compte,comptenew,cptscanned,cptdelete,cptchanged,cptroots,iroots
compte=comptenew=cptscanned=cptdelete=cptchanged=cptroots=iroots=0
global totalfiles,totalfolders
totalfiles=totalfolders=0

def processDirectory ( args, dirname, filenames ):

    #print "processDirectory "
    if smart_unicode(dirname) in Exclude_folders:#si le dirname est un chemin exclu, on sort
        #print "processDirectory( %s) in Exclude_folders"%smart_unicode(dirname).encode('utf-8')
        return
    global totalfolders,totalfiles
    totalfolders=totalfolders+1
    for filename in filenames:
        #print smart_unicode(filename).encode('utf-8')
        if splitext(filename)[1].upper() in listext:
            totalfiles=totalfiles+1

def count_files ( path, reset = True, recursive = True ):
    global totalfiles,totalfolders
    
    #path = smart_unicode(path)
    
    #print "In count_files(%s)"%path.encode('utf-8')
    if reset:
        totalfiles=totalfolders=0
    if smart_unicode(path) in Exclude_folders: #si le path est un chemin exclu, on sort
        return
    if recursive:
        try:
            walk(path, processDirectory, None )
        except:
            walk(path.encode('utf-8'), processDirectory, None)
    else:
        try:
            path,folders,files = oswalk(path).next()
        except:
            # new in 0.7.1.3
            path,folders,files = oswalk(path.encode('utf-8')).next()
        totalfiles=totalfiles+len(files)
        totalfolders=totalfolders+int(len(files)>=1)



def browse_folder(dirname,parentfolderID=None,recursive=True,updatepics=False,addpics=True,delpics=True,rescan=False,updatefunc=None,dateadded = strftime("%Y-%m-%d %H:%M:%S")):
    """Browse the root folder 'dirname'
    - 'recursive' : the scan is recursive. all the subfolders of 'dirname' are traversed for pics
    - 'updatepics' : enable to modify a picture entry if metas changed
    - 'rescan' : force the scan wheter pictures are already inside DB or not
    - 'addpics' :
    - 'delpics' :
    - 'dateadded' : the date when the pictures are scanned (useful for subfolders calls to keep the same date as the main root folder)
    - 'updatefunc' is a function called to show the progress of the scan. The parameters are : pourcentage(int),[ line1(str),line2(str),line3(str) ] )
    """
    global compte,comptenew,cptscanned,cptdelete,cptchanged,cptroots,iroots
    cpt=0
    #on liste les fichiers jpg du dossier
    listfolderfiles=[]
    sys_enc = sys.getfilesystemencoding()
    dirname = smart_unicode(dirname)

    print "In browse_folder"
    print decoder.smart_utf8(dirname)

    #######
    # Pre STEP: cleanup keywords in database
    #######
    MPDB.DB_cleanup_keywords()

    #######
    # STEP 0 : dirname should not be one of those which are excluded from scan !
    #######
    # TODO : if the path was already scanned before, we need to remove previously added pictures AND subfolders
    if dirname in Exclude_folders:
        #print "dirname in Exclude_folders"
        cptdelete = cptdelete + MPDB.RemovePath(dirname)
        return
    #######
    # STEP 1 : list all files in directory
    #######

    # This conversion is important for windows to get filenames in utf-8 encoding!
    if type(dirname).__name__ == "str":
        dirname = unicode(dirname, 'utf-8')
    try:
        dirname = smart_unicode(dirname)
        try:
            listdir = oslistdir(dirname)
        except:
            listdir = oslistdir(dirname.encode('utf-8'))
        # pretty stupid, but is a must.
        for index in range(len(listdir)):
            listdir[index] = smart_unicode(listdir[index])

    except:
        print_exc()
        MPDB.log( "Error while trying to get directory content", MPDB.LOGERROR )
        listdir=[]



    #######
    # STEP 2 : Keep only the files with extension...
    #######
    for f in listdir:
        if splitext(f)[1].upper() in listext:
            listfolderfiles.append(f)


    #on récupère la liste des fichiers entrées en BDD pour le dossier en cours
    listDBdir = MPDB.DB_listdir(dirname)# --> une requête pour tout le dossier

    #######
    # STEP 3 : If folder contains pictures, create folder in database
    #######
    #on ajoute dans la table des chemins le chemin en cours
    PFid = MPDB.DB_folder_insert(basename(dirname) or osdirname(dirname).split(separator)[-1],
                            dirname,
                            parentfolderID,
                            listfolderfiles and "1" or "0"#i
                            )
    if listfolderfiles:#si le dossier contient des fichiers jpg...
        #######
        # STEP 4 : browse all pictures
        #######
        #puis on parcours toutes les images du dossier en cours
        for picfile in listfolderfiles:#... on parcours tous les jpg du dossier
            extension = splitext(picfile)[1].upper()
            if extension in vidsext and Addon.getSetting("usevids") == "false":#si une video mais qu'on ne prend pas les vidéos
                if picfile in listDBdir:
                    listDBdir.pop(listDBdir.index(picfile))
                continue #alors on ne fait rien et on reprend la boucle

            if file_is_accessible(dirname, picfile):
                cptscanned = cptscanned+1
                cpt = cpt + 1
            else:
                MPDB.DB_del_pic(dirname,picfile)
                cptdelete=cptdelete+1

            ###if updatefunc and updatefunc.iscanceled(): return#dialog progress has been canceled
            #on enlève l'image traitée de listdir
            if len(listdir) > 0:
                listdir.pop(listdir.index(picfile))
            if not rescan: #si pas de rescan
                #les images ne sont pas à scanner de force
                if picfile in listDBdir: #si l'image est déjà en base
                    #l'image est déjà en base de donnée
                    if updatepics: #si le paramètre est configuré pour mettre à jour les metas d'une photo
                        #Il faut mettre à jour les images...
                        if extension in vidsext:
                            DoScan = True
                            update = True
                            straction = __language__(30242)#Updating
                            if file_is_accessible(dirname, picfile):
                                cptchanged = cptchanged + 1
                        elif not (MPDB.fileSHA(join(dirname,picfile))==MPDB.getFileSha(dirname,picfile)): #si l'image a changé depuis qu'elle est en base
                            #Scan les metas et ajoute l'image avec un paramètre de mise à jour = true
                            DoScan = True
                            update = True
                            straction = __language__(30242)#Updating
                            if file_is_accessible(dirname, picfile):
                                cptchanged = cptchanged + 1                        
                        else:
                            DoScan = False
                            straction = __language__(30243)#"Passing"
                            #mais l'image n'a pas changée. Donc on passe
                    else:
                        DoScan = False
                        straction = __language__(30243)#"Passing"
                        #mais on ne met pas à jour les photos. Donc on passe
                else:
                    DoScan = True
                    update = False
                    straction = __language__(30244)#"Adding"
                    if file_is_accessible(dirname, picfile):
                        comptenew = comptenew + 1
                    #l'image n'est pas dans la base. On l'ajoute maintenant avec paramètre de mise à jour = false
            else:
                DoScan = True
                update = True
                straction = __language__(30245)#"Rescan"
                #on rescan les photos donc on ajoute l'image avec paramètre de mise à jour = true


            if updatefunc and totalfiles!=0 and cptroots!=0:
                updatefunc.update(int(100*float(cptscanned)/float(totalfiles)),#cptscanned-(cptscanned/100)*100,
                                  #cptscanned/100,
                                  int(100*float(iroots)/float(cptroots)),
                                  __language__(30000)+"[%s] (%0.2f%%)"%(straction,100*float(cptscanned)/float(totalfiles)),#"MyPicture Database [%s] (%0.2f%%)"
                                  picfile)
            if DoScan and file_is_accessible(dirname, picfile):
                try:
                    modifiedtime = str(stat(join(dirname,picfile)).st_mtime)
                except:
                    modifiedtime = str(stat(join(dirname.encode('utf-8'),picfile.encode('utf-8'))).st_mtime)

                picentry = { "idFolder":PFid,
                             "strPath":dirname,
                             "strFilename":picfile,
                             "UseIt":1,
                             "sha": extension in picsext and str(MPDB.fileSHA(join(dirname,picfile))) or extension in vidsext and "1" ,
                             #"DateAdded":dateadded,
                             "DateAdded":strftime("%Y-%m-%d %H:%M:%S"),
                             "mtime":modifiedtime,
                             "ftype": extension in picsext and "picture" or extension in vidsext and "video" or ""}




                # get the meta tags
                try:
                    if not extension in vidsext:
                        picentry.update(get_metas(dirname,picfile))
                    # insert picture into table files
                    try:
                        for index in picentry:
                            if isinstance(picentry[index], str) == False        \
                              and isinstance(picentry[index], unicode) == False \
                              and isinstance(picentry[index], int) == False     \
                              and isinstance(picentry[index], long) == False    \
                              and isinstance(picentry[index], float) == False:
                                    picentry[index] = ""

                        #if isinstance(picentry['EXIF ExifVersion'], str) == False:
                            #picentry['EXIF ExifVersion'] = ""

                        MPDB.DB_file_insert(dirname,picfile,picentry,update)
                    except MPDB.MyPictureDB:
                        print "Error in " + smart_unicode(dirname).encode('utf-8') + "  File:" + smart_unicode(picfile).encode('utf-8')
                        print "Parameter set start"
                        print picentry
                        print "Parameter set end"
                        pass
                except:
                    print_exc()




            if picfile in listDBdir:
                listDBdir.pop(listDBdir.index(picfile))

        #Now if the database contain some more pictures assign for this folder, we need to delete them if 'update' setting is true
        if listDBdir :#and updatepics: #à l'issu si listdir contient encore des fichiers, c'est qu'ils sont en base mais que le fichier n'existe plus physiquement.
            for f in listDBdir: #on parcours les images en DB orphelines
                cptdelete=cptdelete+1
                if updatefunc and totalfiles!=0 and cptroots!=0:
                    updatefunc.update(int(100*float(cptscanned)/float(totalfiles)),#cptscanned-(cptscanned/100)*100,
                                      #cptscanned/100,
                                      int(100*float(iroots)/float(cptroots)),
                                      __language__(30000)+"["+__language__(30246)+"]",#MyPicture Database [Removing]
                                      f)
                MPDB.DB_del_pic(dirname,f)
                MPDB.log( "\t%s has been deleted from database because the file does not exists in this folder. "%f)#f.decode(sys_enc))
            MPDB.log("")


    else:
        MPDB.log( "This folder does not contain any picture :")
        MPDB.log( dirname )
        MPDB.log( "" )

    if cpt:
        MPDB.log( "%s new pictures found in %s"%(str(cpt),dirname), MPDB.LOGNOTICE )
        #unicode(info.data[k].encode("utf8").__str__(),"utf8")
        compte=compte+cpt
        cpt=0
    if recursive: #gestion de la recursivité. On rappel cette même fonction pour chaque dossier rencontré
        MPDB.log( "scan the subfolders of :", MPDB.LOGNOTICE)
        MPDB.log( dirname, MPDB.LOGNOTICE )
        for item in listdir:
            try:
                joineddir = join(dirname,item)
            except:
                joineddir = join(dirname.encode('utf-8'),item.encode('utf-8'))
                
            joineddir = smart_unicode(joineddir)

            try:
                isjoineddir = isdir(joineddir)
            except:
                isjoineddir = isdir(joineddir.encode('utf-8'))

            if isjoineddir :#un directory
                #browse_folder(dirname,parentfolderID=None,recursive=True,updatepics=False,rescan=False,updatefunc=None)
                browse_folder(joineddir,PFid,recursive,updatepics,addpics,delpics,rescan,updatefunc,dateadded)
            else:
                #listdir contenait un fichier mais pas un dossier
                # inutilisé... on passe pour le moment
                pass

def file_is_accessible(dirname, picfile):
    dirname = smart_unicode(dirname)
    picfile = smart_unicode(picfile)

    filename = smart_unicode(join(dirname,picfile))

    try:
        a=str(stat(filename).st_mtime)
    except:
        try:
            a=str(stat(filename.encode('utf-8')).st_mtime)
        except:
            return False
    try:
        f = open(filename , 'rb')
        f.close()
    except:
        try:
            f = open(filename.encode('utf-8') , 'rb')
            f.close()
        except:
            return False

    return True




def get_metas(dirname,picfile):
    picentry = {}
    ### chemin de la miniature
    extension = splitext(picfile)[1].upper()

    #si le fichier est une vidéo,
    if extension in vidsext:
        picentry.update({"EXIF DateTimeOriginal":strftime("%Y-%m-%d %H:%M:%S",gmtime(stat(join(dirname,picfile)).st_mtime))})
    #si le fichier est une image
    elif extension in picsext:
        thumbnails = Thumbnails()
        #picentry["Thumb"]=thumbnails.get_cached_picture_thumb( join(dirname,picfile) ).decode("utf8")

        ###############################
        #    getting  EXIF  infos     #
        ###############################
        #reading EXIF infos
        #   (file fields are creating if needed)

        try:
            exif = MPDB.get_exif(join(dirname,picfile))

            #EXIF infos are added to a dictionnary
            picentry.update(exif)
        except:
            print "Exception thrown from MPDB.get_exif"

        ###############################
        #    getting  IPTC  infos     #
        ###############################
        try:
            iptc = MPDB.get_iptc(dirname,picfile)
 
            #IPTC infos are added to a dictionnary
            picentry.update(iptc)
        except:
            print "Exception thrown from MPDB.get_iptc"

        ###############################
        #    getting  XMP infos       #
        ###############################
        try:
            xmp = MPDB.get_xmp(dirname, picfile)
            picentry.update(xmp)
        except:
            print "Exception thrown from MPDB.get_xmp"

        
    else:
        picentry={}
        #this should never happen
        MPDB.log( "file was neither of video type, nor picture type... Check the extensions in settings", LOGNOTICE )

    return picentry

def usage():
    print usagestr

if __name__=="__main__":
    #commande dos de test :
    #F:\Apps\Python24>python scanpath.py --rootpath --recursive --update 'c:\path to database\db.db' 'path to scan'
    #récupération des chemins à exclure TODO


    #1- récupérer le paramètre
    main2()

    xbmc.executebuiltin( "Notification(%s,%s)"%(__language__(30000).encode("utf8"),
                                                __language__(30248).encode("utf8")%(cptscanned,comptenew,cptdelete,cptchanged)
                                                )
                         )

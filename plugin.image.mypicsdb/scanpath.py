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
#import sys
from sys import path as syspath,modules as sysmodules
from os import stat,listdir as oslistdir
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
    
global pictureDB
pictureDB = join(DB_PATH,"MyPictures.db")

from time import strftime

from DialogAddonScan import AddonScan
from file_item import Thumbnails  
global Exclude_folders #TODO
Exclude_folders = []
for path,recursive,update,exclude in MPDB.RootFolders():
    if exclude:
        print path
        Exclude_folders.append(normpath(path))

global listext
listext=[]
for ext in Addon.getSetting("picsext").split("|"):
    listext.append("." + ext.replace(".","").upper())

def main2():
    #get active window
    import optparse
    global cptroots,iroots
    parser = optparse.OptionParser()
    parser.enable_interspersed_args()  
    parser.add_option("--database","-d",action="store_true", dest="database",default=False)
    #parser.add_option("--help","-h")
    parser.add_option("-p","--rootpath",action="store", type="string", dest="rootpath")
    parser.add_option("-r","--recursive",action="store_true", dest="recursive", default=True)
    parser.add_option("-u","--update",action="store_true", dest="update", default=True)
    (options, args) = parser.parse_args()
    print "option,args"
    print options
    print args
    print dir(parser)
    dateadded = strftime("%Y-%m-%d %H:%M:%S")#pour inscrire la date de scan des images dans la base
    if options.rootpath:
        print unquote_plus(options.rootpath)
        scan = AddonScan()#xbmcgui.getCurrentWindowId()
        scan.create( __language__(30000) )
        print options.recursive
        print options.update
        cptroots = 1
        iroots = 1
        scan.update(0,0,
                    __language__(30000)+" ["+__language__(30241)+"]",#MyPicture Database [preparing]
                    __language__(30247))#please wait...
        count_files(unquote_plus(options.rootpath))
        try:
            #browse_folder(dirname,parentfolderID=None,recursive=True,updatepics=False,addpics=True,delpics=True,rescan=False,updatefunc=None)
            #browse_folder(unquote_plus(options.rootpath),parentfolderID=None,recursive=options.recursive,updatepics=options.update,addpics=True,delpics=True,rescan=False,updatefunc=scan,dateadded = dateadded )
            browse_folder(unquote_plus(options.rootpath),parentfolderID=None,recursive=options.recursive,updatepics=True,addpics=True,delpics=True,rescan=False,updatefunc=scan,dateadded = dateadded )
        except:
            print_exc()
        scan.close()
        
        
    if options.database:
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
            print "cptroots"
            print cptroots
            for path,recursive,update,exclude in listofpaths:
                if exclude==0:
                    #count_files(unquote_plus(path))
                    try:
                        #browse_folder(dirname,parentfolderID=None,recursive=True,updatepics=False,rescan=False,updatefunc=None)
                        iroots=iroots+1
                        browse_folder(unquote_plus(path),parentfolderID=None,recursive=recursive==1,updatepics=update==1,addpics=True,delpics=True,rescan=False,updatefunc=scan,dateadded = dateadded)
                    except:
                        print_exc()
                else:
                    print "Exclude path"
                    print path
            scan.close()
            



global compte,comptenew,cptscanned,cptdelete,cptchanged,cptroots,iroots
compte=comptenew=cptscanned=cptdelete=cptchanged=cptroots=iroots=0
global totalfiles,totalfolders
totalfiles=totalfolders=0

def processDirectory ( args, dirname, filenames ):
    print dirname
    if dirname in Exclude_folders:#si le dirname est un chemin exclu, on sort
        return
    global totalfolders,totalfiles
    totalfolders=totalfolders+1
    for filename in filenames:
        if splitext(filename)[1].upper() in listext:
            totalfiles=totalfiles+1

def count_files ( path, reset = True ):
    global totalfiles,totalfolders
    if reset:
        totalfiles=totalfolders=0
    if path in Exclude_folders: #si le path est un chemin exclu, on sort
        return
    walk(path, processDirectory, None )

    
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

    #######
    # STEP 0 : dirname should not be one of those which are excluded from scan !
    #######
    # TODO : if the path was already scanned before, we need to remove previously added pictures AND subfolders
    if dirname in Exclude_folders:
        cptdelete = cptdelete + MPDB.RemovePath(dirname)
        return
    #######
    # STEP 1 : list all files in directory
    #######
    try:
        listdir = oslistdir(dirname)
    except:
        print_exc()
        MPDB.log( "Error while trying to get directory content" )
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
##        #on ajoute dans la table des chemins le chemin en cours
##        PFid = DB_folder_insert(basename(dirname) or osdirname(dirname).split(separator)[-1],
##                                dirname,
##                                parentfolderID,
##                                i#"1" if listfolderfiles else "0"
##                                )
        #######
        # STEP 4 : browse all pictures
        #######
        #puis on parcours toutes les images du dossier en cours
        for picfile in listfolderfiles:#... on parcours tous les jpg du dossier
            cptscanned = cptscanned+1
            cpt = cpt + 1
            ###if updatefunc and updatefunc.iscanceled(): return#dialog progress has been canceled
            #on enlève l'image traitée de listdir
            listdir.pop(listdir.index(picfile))
            if not rescan: #si pas de rescan
                #les images ne sont pas à scanner de force
                if picfile in listDBdir: #si l'image est déjà en base
                    #l'image est déjà en base de donnée
                    if updatepics: #si le paramètre est configuré pour mettre à jour les metas d'une photo
                        #Il faut mettre à jour les images...
                        if not (MPDB.fileSHA(join(dirname,picfile))==MPDB.getFileSha(dirname,picfile)): #si l'image a changé depuis qu'elle est en base
                            #Scan les metas et ajoute l'image avec un paramètre de mise à jour = true
                            DoScan = True
                            update = True
                            straction = __language__(30242)#Updating
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
                    comptenew = comptenew + 1
                    #l'image n'est pas dans la base. On l'ajoute maintenant avec paramètre de mise à jour = false
            else:
                DoScan = True
                update = True
                straction = __language__(30245)#"Rescan"
                #on rescan les photos donc on ajoute l'image avec paramètre de mise à jour = true


            if updatefunc:
                updatefunc.update(int(100*float(cptscanned)/float(totalfiles)),#cptscanned-(cptscanned/100)*100,
                                  #cptscanned/100,
                                  int(100*float(iroots)/float(cptroots)),
                                  __language__(30000)+"[%s] (%0.2f%%)"%(straction,100*float(cptscanned)/float(totalfiles)),#"MyPicture Database [%s] (%0.2f%%)"
                                  picfile)
            if DoScan:
                
                picentry = { "idFolder":PFid,
                             "strPath":dirname.decode("utf8"),
                             "strFilename":picfile.decode("utf8"),
                             "UseIt":1,
                             "sha":str(MPDB.fileSHA(join(dirname,picfile))),
                             "DateAdded":dateadded,
                             "mtime":str(stat(join(dirname,picfile)).st_mtime)}

                #récupère les infos EXIF/IPTC
                picentry.update(get_metas(dirname,picfile))

                #insertion des données de la photo dans la table 'files'
                try:
                    MPDB.DB_file_insert(dirname,picfile,picentry,update)
                except MPDB.MyPictureDB:
                    pass

                
            if picfile in listDBdir:
                listDBdir.pop(listDBdir.index(picfile))
                
        #Now if the database contain some more pictures assign for this folder, we need to delete them if 'update' setting is true
        if listDBdir :#and updatepics: #à l'issu si listdir contient encore des fichiers, c'est qu'ils sont en base mais que le fichier n'existe plus physiquement.
            for f in listDBdir: #on parcours les images en DB orphelines
                cptdelete=cptdelete+1
                if updatefunc:
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
        MPDB.log( "%s new pictures found in %s"%(str(cpt),dirname) )
        #unicode(info.data[k].encode("utf8").__str__(),"utf8")
        compte=compte+cpt
        cpt=0
    if recursive: #gestion de la recursivité. On rappel cette même fonction pour chaque dossier rencontré
        MPDB.log( "scan the subfolders of :")
        MPDB.log( dirname )
        for item in listdir:
            if isdir(join(dirname,item)):#un directory
                #browse_folder(dirname,parentfolderID=None,recursive=True,updatepics=False,rescan=False,updatefunc=None)
                browse_folder(join(dirname,item),PFid,recursive,updatepics,addpics,delpics,rescan,updatefunc,dateadded)
            else:
                #listdir contenait un fichier mais pas un dossier
                # inutilisé... on passe pour le moment
                pass
            
def get_metas(dirname,picfile):
    picentry = {}
    ### chemin de la miniature
    thumbnails = Thumbnails()
    picentry["Thumb"]=thumbnails.get_cached_picture_thumb( join(dirname,picfile) ).decode("utf8")

    ###############################
    #    getting  EXIF  infos     #
    ###############################
    #reading EXIF infos
    #   (file fields are creating if needed)
    try:
        exif = MPDB.get_exif(join(dirname,picfile).encode('utf8'))
    except UnicodeDecodeError:
        exif = MPDB.get_exif(join(dirname,picfile))
    #EXIF infos are added to a dictionnary
    picentry.update(exif)

    ###############################
    #    getting  IPTC  infos     #
    ###############################
    iptc = MPDB.get_iptc(dirname,picfile)
    #IPTC infos are added to a dictionnary
    picentry.update(iptc)
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

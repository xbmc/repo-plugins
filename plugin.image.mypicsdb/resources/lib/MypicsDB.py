# -*- coding: utf8 -*-
"""
Todo :
* ability to remove a file from database
* use smb file access to browse smb share pictures:
    http://sourceforge.net/projects/pysmb/
* Input .avi files inside DB because many camera can make videos
    and it can be interesting to play diaporama including videos
* Use XMP standard (input or output ?) as it replaces IPTC
    http://www.adobe.com/products/xmp/
    http://www.iptc.org/IPTC4XMP/
* 

    
"""
import os,sys
from os.path import join, exists, isfile, isdir
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

DEBUGGING = True
#import time
#import fnmatch
#import os.path
from time import strftime,strptime

#traitement EXIF
##import EXIF
#traitement IPTC
##if sys.modules.has_key("iptcinfo"):
##    del sys.modules['iptcinfo']
##from iptcinfo import IPTCInfo 
##from iptcinfo import c_datasets as IPTC_FIELDS

#base de donnée SQLITE
try:
    from pysqlite2 import dbapi2 as sqlite
    print "using pysqlite2"
except:
    from sqlite3 import dbapi2 as sqlite
    print "using sqlite3"
    pass

from traceback import print_exc
global pictureDB
pictureDB = join(DB_PATH,"MyPictures.db")
sys_enc = sys.getfilesystemencoding()

lists_separator = "||"

class MyPictureDB(Exception):
    pass
    
def log(msg):
    if DEBUGGING:
        print str("MyPicsDB >> %s"%msg.__str__())

#net use z: \\remote\share\ login /USER:password
#mount -t cifs //ntserver/download -o username=vivek,password=myPassword /mnt/ntserver
def mount(mountpoint="z:",path="\\",login=None,password=""):
    import os
    print "net use %s %s %s /USER:%s"%(mountpoint,path,login,password)
    if not exists(mountpoint):
        log( "Mounting %s as %s..."%(path,mountpoint) )
        if login:
            os.system("net use %s %s %s /USER:%s"%(mountpoint,path,login,password))
        else:
            os.system("net use %s %s"%(mountpoint,path))
    else:
        log( "%s is already mounted !"%mountpoint )
    return exists(mountpoint)

def Make_new_base(DBpath,ecrase=True):
##    if not(isfile(DBpath)):
##        f=open("DBpath","w")
##        f.close()
    log( "Creating a new picture database\n%s\n"%DBpath)
    conn = sqlite.connect(DBpath)
    cn=conn.cursor()
    if ecrase:
        #drop table
        try:
            cn.execute("""DROP TABLE files""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE files" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
        try:
            cn.execute("""DROP TABLE keywords""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE keywords" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
        try:
            cn.execute("""DROP TABLE folders""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE folders" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
        try:
            cn.execute("""DROP TABLE KeywordsInFiles""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE KeywordsInFiles" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
        try:
            cn.execute("""DROP TABLE Collections""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE Collections" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
        try:
            cn.execute("""DROP TABLE FilesInCollections""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE FilesInCollections" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
        try:
            cn.execute("""DROP TABLE Periodes""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE Periodes" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
        try:
            cn.execute("""DROP TABLE Rootpaths""")
        except Exception,msg:
            log( ">>> Make_new_base - DROP TABLE Rootpaths" )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )


    #table 'files'
    try:
        cn.execute("""CREATE TABLE files ( idFile integer primary key, idFolder integer, strPath text, strFilename text, DateAdded DATETIME, mtime text, UseIt integer , sha text, Thumb text,
                    CONSTRAINT UNI_FILE UNIQUE ("strPath","strFilename")
                                   )""")
    except Exception,msg:
        if msg.args[0].startswith("table 'files' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE files ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    #table 'keywords'
    try:
        cn.execute("""CREATE TABLE "keywords" ("idKW" INTEGER primary key, "keyword" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'keywords' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE keywords ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    #table 'KeywordsInFiles'
    try:
        cn.execute("""CREATE TABLE "KeywordsInFiles" ("idKW" INTEGER NOT NULL, "idFile" INTEGER NOT NULL);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'KeywordsInFiles' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE KeywordsInFiles ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    #table 'folders'
    try:
        cn.execute("""CREATE TABLE "folders" ("idFolder" INTEGER  primary key not null, "FolderName" TEXT, "ParentFolder" INTEGER, "FullPath" TEXT UNIQUE,"HasPics" INTEGER);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'folders' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE folders ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    #table 'Collections'
    try:
        cn.execute("""CREATE TABLE "Collections" ("idCol" INTEGER PRIMARY KEY, "CollectionName" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Collections' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE Collections ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    #table 'FilesInCollections'
    try:
        cn.execute("""CREATE TABLE "FilesInCollections" ("idCol" INTEGER NOT NULL,
                                   "idFile" INTEGER NOT NULL,
                                   CONSTRAINT UNI_COLLECTION UNIQUE ("idCol","idFile")
                                   );""")
    except Exception,msg:
        if msg.args[0].startswith("table 'FilesInCollections' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE FilesInCollections ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    #table 'periodes'
    try:
        cn.execute("""CREATE TABLE "periodes" 
  ("idPeriode" INTEGER  PRIMARY KEY NOT NULL,
   "PeriodeName" TEXT UNIQUE NOT NULL,
   "DateStart" DATETIME NOT NULL,
   "DateEnd" DATETIME NOT NULL,
   CONSTRAINT UNI_PERIODE UNIQUE ("PeriodeName","DateStart","DateEnd")
   )""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Periodes' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE Periodes ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    #table 'Rootpaths'
    try:
        cn.execute("""CREATE TABLE "Rootpaths" 
  ("idRoot" INTEGER  PRIMARY KEY NOT NULL,
   "path" TEXT UNIQUE NOT NULL,
   "recursive" INTEGER NOT NULL,
   "remove" INTEGER NOT NULL,
   "exclude" INTEGER DEFAULT 0)""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Rootpaths' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE Rootpaths ..." )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
    conn.commit()
    cn.close()



def addColumn(table,colheader,format="text"):
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    try:
        cn.execute("""ALTER TABLE %s ADD "%s" %s"""%(table,colheader,format))
    except Exception,msg:
        if not msg.args[0].startswith("duplicate column name"):
            log( 'EXCEPTION >> addColums %s,%s,%s'%(table,colheader,format) )
            log( "\t%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
   
    conn.commit()
    cn.close()
 
##def getColumns(table):
##    conn = sqlite.connect(pictureDB)
##    cn=conn.cursor()
##    cn.execute("select * from files")
##    retour= "\n".join([field[0] for field in cn.description])
##    print retour
##    conn.commit()
##    cn.close()
##    return retour


def DB_exists(picpath,picfile): 
    """
    Check wether or not a file exists in the DB
    """
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    try:
        cn.execute("""SELECT strPath, strFilename FROM "main"."files" WHERE strPath = (?) AND strFilename = (?);""",(picpath.decode("utf8"),picfile.decode("utf8"),) )
    except Exception,msg:
        log( "EXCEPTION >> DB_exists %s,%s"%(picpath,picfile) )
        log( "\t%s - %s"%(Exception,msg) )
        log( "~~~~" )
        log( "" )
        raise Exception, msg   
    if len(cn.fetchmany())==0:
        
        retour= False
    else:
        retour= True
    cn.close()
    return retour

def DB_listdir(path):
    """
    List files from DB where path
    """
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    conn.text_factory = str #sqlite.OptimizedUnicode
    log( path )
    try:
        cn.execute( """SELECT f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND p.FullPath=(?)""",(path,))
    except Exception,msg:
        log( "ERROR : DB_listdir ..." )
        log( "%s - %s"%(Exception,msg) )
        cn.close()
        raise
        
    retour = [row[0] for row in cn]
    cn.close()
    return retour
 
def DB_file_insert(path,filename,dictionnary,update=False):
    """
    insert into file database the dictionnary values into the dictionnary keys fields
    keys are DB fields ; values are DB values
    """

    if update :#si update alors on doit updater et non pas insert
        if DB_exists(path,filename):
            print "file exists in database and rescan is set to true..."
            print Request("""DELETE FROM files WHERE idFolder = (SELECT idFolder FROM folders WHERE FullPath='%s') AND strFilename='%s'"""%(path,filename))
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    #méthode dajout d'une ligne d'un coup
    conn.text_factory = str#sqlite.OptimizedUnicode
    try:
        cn.execute( """INSERT INTO files('%s') values (%s)""" % ( "','".join(dictionnary.keys()), ",".join(["?"]*len(dictionnary.values())) ) ,
                                                                     dictionnary.values()
                    )
    except Exception,msg:
        log( ">>> DB_file_insert ..." )
        log(filename)
        log( "%s - %s"%(Exception,msg) )
        log( """INSERT INTO files('%s') values (%s)""" % ( "','".join(dictionnary.keys()) , ",".join(["?"]*len(dictionnary.values())) ) )
        log( "" )
        conn.commit()
        cn.close()
        raise MyPictureDB
    
    # TRAITEMENT DES MOTS CLES (base keywords)
    if dictionnary.has_key("keywords"):
        kwl = dictionnary["keywords"].split(lists_separator)
        for mot in kwl:
            if mot: #on ajoute que les mots clés non vides
                #First for keywords, create an entry for this keyword in keywords table
                try:
                    cn.execute("""INSERT INTO keywords(keyword) VALUES("%s")"""%mot.encode("utf8"))
                except Exception,msg:
                    if str(msg)=="column keyword is not unique":
                        pass
                    else:
                        log( 'EXCEPTION >> keywords' )
                        log( "\t%s - %s"%(Exception,msg) )
                        log( "~~~~" )
                        log( "" )
                #Then, add the corresponding id of file and id of keyword inside the KeywordsInFiles database
                try:
                    cn.execute("""INSERT INTO KeywordsInFiles(idKW,idFile) SELECT k.idKW,f.idFile FROM keywords k, files f WHERE k.keyword="%s" AND f.strPath="%s" AND f.strFilename="%s";"""%(mot.encode("utf8"),
                                                                                                                                                                                               path,
                                                                                                                                                                                               filename))
                except Exception,msg:
                    log("Error while adding KeywordsInFiles")
                    log("\t%s - %s"% (Exception,msg) )

##    # TRAITEMENT DES FOLDERS
##    try:
##        haspic = "1" if True else "0"
##        cn.execute("""INSERT INTO folders(FolderName,ParentFolder,FullPath,HasPics) VALUES (?,?,?,?)""",('nom du dossier',999,path,haspic))
##    except sqlite.IntegrityError:
##        print "ERROR ERROR ERROR !!!"
##        pass
    conn.commit()
    cn.close()
    return True

def DB_folder_insert(foldername,folderpath,parentfolderID,haspic):
    """insert into folders database, the folder name, folder parent, full path and if has pics
        Return the id of the folder inserted"""
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    conn.text_factory = sqlite.OptimizedUnicode
    #insert in the folders database
    try:
        cn.execute("""INSERT INTO folders(FolderName,ParentFolder,FullPath,HasPics) VALUES (?,?,?,?);""",(foldername.decode("utf8"),parentfolderID,folderpath.decode("utf8"),haspic))
    except sqlite.IntegrityError:
        pass
    conn.commit()
    #return the id of the folder inserted
    cn.execute("""SELECT idFolder FROM folders where FullPath= ?""",(folderpath.decode("utf8"),))
    try:
        retour = [row for (row,) in cn][0]
    except:
        retour = 0
    cn.close()
    return retour


##def DB_del_path(path):
##    #recup l'id du path donné
##    idpath = Request("SELECT idPath from folders where FullPath like '%?'",(path,))
##    deletelist=[]# listera les id des dossiers à supprimer
##    deletelist.append(idpath)#le dossier en paramètres est aussi à supprimer
##    deletelist.extend(get_children(idpath))#on ajoute tous les enfants en sous enfants du dossier

def get_children(folderid):
    """search all children folders ids for the given folder id"""
    childrens=[c[0] for c in Request("SELECT idFolder FROM folders WHERE ParentFolder='%s'"%folderid)]
    log( childrens )
    list_child=[]
    list_child.extend(childrens)
    for idchild in childrens:
        list_child.extend(get_children(idchild))
    return list_child

def DB_del_pic(picpath,picfile=None): #TODO : revoir la vérif du dossier inutile
    """Supprime le chemin/fichier de la base. Si aucun fichier n'est fourni, toutes les images du chemin sont supprimées de la base"""
    if picfile:
        #on supprime le fichier de la base
        Request("""DELETE FROM files WHERE idFolder = (SELECT idFolder FROM folders WHERE FullPath='%s') AND strFilename='%s'"""%(picpath,picfile))
        #puis maintenant on vérifie que le chemin dossier est toujours utile ou alors on le supprime
        #1- on récupère l'ID du dossier de l'image supprimée
        #2- on cherche si il y a des images avec cet id
        #3- si oui : on laisse / si non : on supprime le dossier
##        Request("""DELETE FROM folders 
##    WHERE 
##      (SELECT DISTINCT idFolder FROM files 
##          WHERE idFolder=(
##              SELECT DISTINCT idFolder FROM folders WHERE FullPath='%s'
##                         )
##      )
##   or FullPath='%s'""" %(picpath,picpath) )
    else:
        idpath = Request("SELECT idFolder FROM folders WHERE FullPath = '%s'"%picpath)[0][0]#le premier du tuple à un élément
        log( idpath )
        deletelist=[]#va lister les id des dossiers à supprimer
        deletelist.append(idpath)#le dossier en paramètres est aussi à supprimer
        deletelist.extend(get_children(str(idpath)))#on ajoute tous les enfants en sous enfants du dossier
        Request( "DELETE FROM files WHERE idFolder in ('%s')"%"','".join([str(i) for i in deletelist]) )
        Request( "DELETE FROM folders WHERE idFolder in ('%s')"%"','".join([str(i) for i in deletelist]) )

    return

def fileSHA ( filepath ) :
    #found here : http://sebsauvage.net/python/doublesdetector.py
    #thanks sebsauvage for all its snippets !
    """ Compute SHA (Secure Hash Algorythm) of a file.
        Input : filepath : full path and name of file (eg. 'c:\windows\emm386.exe')
        Output : string : contains the hexadecimal representation of the SHA of the file.
                          returns '0' if file could not be read (file not found, no read rights...)
    """
    import md5#sha
    try:
        file = open(filepath,'rb')
        digest = md5.new()#sha.new()
        data = file.read(65536)
        while len(data) != 0:
            digest.update(data)
            data = file.read(65536)
        file.close()
    except:
        print_exc()
        return '0'
    else:
        return digest.hexdigest()

def getFileSha (path,filename):
    #return the SHA in DB for the given picture
    try:
        return [row for row in Request( """select sha from files where strPath="%s" and strFilename="%s";"""%(path,filename))][0][0]
    except:
        return "0"

def getFileMtime(path,filename):
    #return the modification time 'mtime' in DB for the given picture
    return [row for row in Request( """select mtime from files where strPath="%s" and strFilename="%s";"""%(path,filename))][0][0]

def DB_deltree(picpath):
    pass

def getRating(path,filename):
    try:
        return [row for row in Request( """SELECT files."Image Rating" FROM files WHERE strPath="%s" AND strFilename="%s";"""%(path,filename) )][0][0]
    except IndexError:
        return None

def RequestOnList(request,picturelist):
    """applique la requête sur la liste d'images """
    request = """select * from files where strPath||"\"||strFilename in (
"c:\Users\alexsolex\Documents\python\images_test\aussi\avec photos\IMG_2463.jpg",
"c:\Users\alexsolex\Documents\python\images_test\autres\IMG_2404.jpg",
"c:\Users\alexsolex\Documents\python\images_test\autres\tarlak2.jpg"
) 
AND
UseIt = 1
AND
idFolder = 6"""



###################################
# Collection functions
#####################################
def ListCollections():
    """List all available collections"""
    return [row for row in Request( """SELECT CollectionName FROM Collections""")]

def NewCollection(Colname):
    """Add a new collection"""
    if Colname :
        Request( """INSERT INTO Collections(CollectionName) VALUES ("%s")"""%Colname )
    else:
        log( """NewCollection : User did not specify a name for the collection.""")
def delCollection(Colname):
    """delete a collection"""
    if Colname:
        Request( """DELETE FROM FilesInCollections WHERE idCol=(SELECT idCol FROM Collections WHERE CollectionName="%s");"""%Colname )
        Request( """DELETE FROM Collections WHERE CollectionName="%s";"""%Colname )
    else:
        log( """delCollection : User did not specify a name for the collection""" )
def getCollectionPics(Colname):
    """List all pics associated to the Collection given as Colname"""
    return [row for row in Request( """SELECT strPath,strFilename FROM Files WHERE idFile IN (SELECT idFile FROM FilesInCollections WHERE idCol IN (SELECT idCol FROM Collections WHERE CollectionName='%s')) ORDER BY "EXIF DateTimeOriginal" ASC;"""%Colname)]

def renCollection(Colname,newname):
    """rename give collection"""
    if Colname:
        Request( """UPDATE Collections SET CollectionName = "%s" WHERE CollectionName="%s";"""%(newname,Colname) )
    else:
        log( """renCollection : User did not specify a name for the collection""")
        
def addPicToCollection(Colname,filepath,filename):
    #cette requête ne vérifie pas si :
    #   1- le nom de la collection existe dans la table Collections
    #   2- si l'image est bien une image en base de donnée Files
    #ces points sont solutionnés partiellement car les champs ne peuvent être NULL
    #   3- l'association idCol et idFile peut apparaitre plusieurs fois...
    print """(SELECT idFile FROM files WHERE strPath="%s" AND strFilename="%s")"""%(filepath,filename)
    Request( """INSERT INTO FilesInCollections(idCol,idFile) VALUES ( (SELECT idCol FROM Collections WHERE CollectionName="%s") , (SELECT idFile FROM files WHERE strPath="%s" AND strFilename="%s") )"""%(Colname,filepath,filename) )

def delPicFromCollection(Colname,filepath,filename):
    Request( """DELETE FROM FilesInCollections WHERE idCol=(SELECT idCol FROM Collections WHERE CollectionName="%s") AND idFile=(SELECT idFile FROM files WHERE strPath="%s" AND strFilename="%s")"""%(Colname,filepath,filename) )
    
####################
# Periodes functions
#####################
def ListPeriodes():
    """List all periodes"""
    return [row for row in Request( """SELECT PeriodeName,DateStart,DateEnd FROM Periodes""")]

def addPeriode(periodname,datestart,dateend):
    #datestart et dateend doivent être au format string ex.: "datetime('2009-07-12')" ou "strftime('%Y',now)"
    Request( """INSERT INTO Periodes(PeriodeName,DateStart,DateEnd) VALUES ('%s',%s,%s)"""%(periodname,datestart,dateend) )
    return

def delPeriode(periodname):
    Request( """DELETE FROM Periodes WHERE PeriodeName="%s" """%periodname )
    return

def renPeriode(periodname,newname,newdatestart,newdateend):
    Request( """UPDATE Periodes SET PeriodeName = "%s",DateStart = datetime("%s") , DateEnd = datetime("%s") WHERE PeriodeName="%s" """%(newname,newdatestart,newdateend,periodname) )
    return

def PicsForPeriode(periodname):
    """Get pics for the given period name"""
    period = Request( """SELECT DateStart,DateEnd FROM Periodes WHERE PeriodeName='%s'"""%periodname )
    return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN %s AND %s ORDER BY "EXIF DateTimeOriginal" ASC"""%period )]

def Searchfiles(column,searchterm,count=False):
    if count:
        return [row for row in Request( """SELECT count(*) FROM files WHERE files.'%s' LIKE "%%%s%%";"""%(column,searchterm))][0][0]
    else:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE files.'%s' LIKE "%%%s%%";"""%(column,searchterm))]
###
def getGPS(filepath,filename):
    coords = Request( """SELECT files.'GPS GPSLatitudeRef',files.'GPS GPSLatitude' as lat,files.'GPS GPSLongitudeRef',files.'GPS GPSLongitude' as lon FROM files WHERE lat NOT NULL AND lon NOT NULL AND strPath="%s" AND strFilename="%s";"""%(filepath,filename) )
    try:
        coords=coords[0]
    except IndexError:
        return None
    if not coords: return None
    latR,lat,lonR,lon=coords
        
    lD,lM,lS = lat.replace(" ","").replace("[","").replace("]","").split(",")
    LD,LM,LS = lon.replace(" ","").replace("[","").replace("]","").split(",")
    exec("LS=%s"%LS)
    exec("lS=%s"%lS)
    latitude =  (int(lD)+(int(lM)/60.0)+(int(lS)/3600.0)) * (latR=="S" and -1 or 1)
    longitude = (int(LD)+(int(LM)/60.0)+(int(LS)/3600.0)) * (lonR=="W" and -1 or 1)
    return (latitude,longitude)

######################################"
#  Fonctions pour les dossiers racines
######################################"

def RootFolders():
    "return folders which are root for scanning pictures"
    return [row for row in Request( """SELECT path,recursive,remove,exclude FROM Rootpaths""")]

def AddRoot(path,recursive,remove,exclude):
    "add the path root inside the database. Recursive is 0/1 for recursive scan, remove is 0/1 for removing files that are not physically in the place"
    Request( """INSERT INTO Rootpaths(path,recursive,remove,exclude) VALUES ("%s",%s,%s,%s)"""%(path,recursive,remove,exclude) )

def getRoot(path):
    return [row for row in Request( """SELECT path,recursive,remove,exclude FROM Rootpaths WHERE path='%s'"""%path )][0]

def RemoveRoot(path):
    "remove the given rootpath, remove pics from this path, ..."
    #first remove the path with all its pictures / subfolders / keywords / pictures in collections...
    RemovePath(path)
    #then remove the rootpath itself
    Request( """DELETE FROM Rootpaths WHERE path="%s" """%path )    
    
def RemovePath(path):
    "remove the given rootpath, remove pics from this path, ..."
    cptremoved = 0
    #récupère l'id de ce chemin
    try:
        idpath = Request( """SELECT idFolder FROM folders WHERE FullPath = "%s";"""%path )[0][0]
    except:
        #le chemin n'est sans doute plus en base
        return 0
    #1- supprime les images situées directement sous la racine du chemin à supprimer
    cptremoved = Request( """SELECT count(*) FROM files WHERE idFolder='%s'"""%idpath )[0][0]
    Request( """DELETE FROM files WHERE idFolder='%s'"""%idpath)
    #parcours tous les sous dossiers
    for idchild in all_children(idpath):
        #supprime les keywordsinfiles
        Request( """DELETE FROM KeywordsInFiles WHERE idKW in (SELECT idKW FROM KeywordsInFiles WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s'))"""%idchild )
        #supprime les photos de files in collection
        Request( """DELETE FROM FilesInCollections WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s')"""%idchild )        
        #2- supprime toutes les images
        cptremoved = cptremoved + Request( """SELECT count(*) FROM files WHERE idFolder='%s'"""%idchild)[0][0]
        Request( """DELETE FROM files WHERE idFolder='%s'"""%idchild)
        #3 - supprime ce sous dossier
        Request( """DELETE FROM folders WHERE idFolder='%s'"""%idchild)
    #4- supprime le dossier
    Request( """DELETE FROM folders WHERE idFolder='%s'"""%idpath)
    #5- supprime les 'périodes' si elles ne contiennent plus de photos (TODO : voir si on supprime les périodes vides ou pas)
    for periodname,datestart,dateend in ListPeriodes():
        if Request( """SELECT count(*) FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN '%s' AND '%s'"""%(datestart,dateend) )[0][0]==0:
            Request( """DELETE FROM Periodes WHERE PeriodeName='%s'"""%periodname )
    return cptremoved

##########################################
##########################################

def hook_directory ( filepath,filename,filecount, nbfiles ):
    import sys
    log( "%s/%s - %s"%(filecount,nbfiles,join(filepath,filename)) )
    
class dummy_update:#TODO : check if this is usefull
    def __init__(self):
        self.cancel=False
        pass
    def update(self,percent, line1=None, line2=None, line3=None):
        log( "%s\t%s\n\t%s\n\t%s"%(percent,line1,line2,line3) )
    def iscanceled(self):
        return self.cancel


def get_exif(picfile):
    """
    get EXIF fields in the picture and return datas as key:value dictionnary
    """
    from EXIF import process_file as EXIF_file
    #définition des champs EXIF que nous souhaitons utiliser
    EXIF_fields =[
                "Image Model",
                "Image Orientation",
                "Image Rating",
                #"Image ResolutionUnit",
                #"Image XResolution",
                #"Image YResolution",
                #"Image Make",
                "Image DateTime",
                "EXIF DateTimeOriginal",
                "EXIF DateTimeDigitized",
                "EXIF ExifImageWidth",
                "EXIF ExifImageLength",
                #"EXIF FileSource",
                #"EXIF Flash",
                "EXIF SceneCaptureType",
                #"EXIF DigitalZoomRatio",
                "GPS GPSLatitude",
                "GPS GPSLatitudeRef",
                "GPS GPSLongitude",
                "GPS GPSLongitudeRef",
                #"EXIF ExifVersion"]
                  ]
    #ouverture du fichier
    f=open(picfile,"rb")
    #   et lecture des tags EXIF (on ne prend pas les makernotes, données constructeurs)
    #tags = EXIF.process_file(f,details=False)
    tags = EXIF_file(f,details=False)
    #fermeture du fichier
    f.close()
    #pré-initialisation des champs à  mettre en base
    picentry={}    
    #on parcours les infos EXIF qu'on souhaite récupérer
    for tag in EXIF_fields:
    #for tag in tags:
        #mais on ne traite que les tags présents dans la photo
        if tag in tags.keys():
            if tag in ["EXIF DateTimeOriginal","EXIF DateTimeDigitized","Image DateTime"]:
                tagvalue=None
                for datetimeformat in ["%Y:%m:%d %H:%M:%S","%Y.%m.%d %H.%M.%S","%Y-%m-%d %H:%M:%S"]:
                    try:
                        tagvalue = strftime("%Y-%m-%d %H:%M:%S",strptime(tags[tag].__str__(),datetimeformat))
                        break
                    except:
                        log( "Datetime (%s) did not match for '%s' format... trying an other one..."%(tags[tag].__str__(),datetimeformat) )
                if not tagvalue:
                    log( "ERROR : the datetime format is not recognize (%s)"%tags[tag].__str__() )
                
            else:
                tagvalue = tags[tag].__str__()
            try:
                #on créé un champ dans la base pour une info exif
                if tag in ["EXIF DateTimeOriginal","EXIF DateTimeDigitized","Image DateTime"]:
                    addColumn("files",tag,"DATETIME")
                else:
                    addColumn("files",tag)
                picentry[tag]=tagvalue
            except Exception, msg:
                log(">> get_exif %s"%picfile )
                log( "%s - %s"%(Exception,msg) )
                log( "~~~~" )
                log( "" )
    return picentry

def get_iptc(path,filename):
    """
    Get IPTC datas from picfile and return a dictionnary where keys are DB fields and values are DB values
    """
    if sys.modules.has_key("iptcinfo"):
        del sys.modules['iptcinfo']
    from iptcinfo import IPTCInfo 
    from iptcinfo import c_datasets as IPTC_FIELDS

    try:
        info = IPTCInfo(join(path,filename))
    except Exception,msg:
        if not type(msg.args[0])==type(int()):
            if msg.args[0].startswith("No IPTC data found."):
                #print "No IPTC data found."
                return {}
            else:
                log( "EXCEPTION >> get_iptc %s"%join(path,filename) )
                log( "%s - %s"%(Exception,msg) )
                log( "~~~~" )
                log( "" )
                return {}
        else:
            log( "EXCEPTION >> get_iptc %s"%join(path,filename) )
            log( "%s - %s"%(Exception,msg) )
            log( "~~~~" )
            log( "" )
            return {}
    iptc = {}
    
    #il faudrait peut être gérer les infos suivantes de manière particulière:
    #   "supplemental category"
    #   "keywords"
    #   "contact"
    #en effet ces 3 infos contiennent des listes
    for k in info.data.keys():
        if k in IPTC_FIELDS:
            if IPTC_FIELDS[k] in ["supplemental category","keywords","contact"]:
                #Those 3 IPTC infos may need special work as they are lists
                #print "|".join(info.data[k])
                #unicode(info.data[k].encode("utf8").__str__(),"utf8")
                pass
            elif IPTC_FIELDS[k] in ["date created","time created"]:
                #ces champs sont au format date
                #a voir si il faut les traiter différemment
                pass
            addColumn("files",IPTC_FIELDS[k])
            
            if isinstance(info.data[k],unicode):
                try:
                    #iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode(sys_enc).__str__(),"utf8")
                    iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode("utf8").__str__(),"utf8")
                except UnicodeDecodeError:
                    iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode(sys_enc).__str__(),sys_enc)
            elif isinstance(info.data[k],list):
                #iptc[IPTC_FIELDS[k]] = info.data[k].__str__()
                iptc[IPTC_FIELDS[k]] = lists_separator.join(info.data[k])
                #print lists_separator.join(info.data[k])
            elif isinstance(info.data[k],str):
                iptc[IPTC_FIELDS[k]] = info.data[k].decode(sys_enc)
            else:
                log( "%s,%s"%(path,filename) )
                log( "WARNING : type returned by iptc field is not handled :" )
                log( repr(type(info.data[k])) )
                log( "" )
        else:
            log("\nIPTC problem with file :")
            try:
                log( "WARNING : '%s' IPTC field is not handled (data for this field : \n%s)"%(k,info.data[k][:80]) )
            except:
                log( "WARNING : '%s' IPTC field is not handled (unreadable data for this field)"%k )
            log( "" )
    
    return iptc

def MakeRequest(field,comparator,value):
    return Request( """SELECT p.FullPath,f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND %s %s %s """%(field,comparator,value))

def get_fields(table="files"):
    tableinfo = Request( """pragma table_info("%s")"""%table)
    return [(name,typ) for cid,name,typ,notnull,dflt_value,pk in tableinfo]        

def Request(SQLrequest):
    log( "SQL > %s"%SQLrequest)
    conn = sqlite.connect(pictureDB)
    conn.text_factory = str #sqlite.OptimizedUnicode
    cn=conn.cursor()
    try:
        cn.execute( SQLrequest )
        conn.commit()
        retour = [row for row in cn]
    except Exception,msg:
        log( "The request failed :" )
        log( "%s - %s"%(Exception,msg) )
        log( "---" )     
        retour= []
    cn.close()
    return retour

def search_keyword(kw=None):
    """Look for given keyword and return the list of pictures.
If keyword is not given, pictures with no keywords are returned"""
    if kw is not None: #si le mot clé est fourni
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT idFile FROM KeywordsInFiles WHERE idKW =(SELECT idKW FROM keywords WHERE keyword="%s"))"""%kw.encode("utf8"))]
    else: #sinon, on retourne toutes les images qui ne sont pas associées à des mots clés
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT DISTINCT idFile FROM KeywordsInFiles)""" )]

def list_KW():
    """Return a list of all keywords in database"""
    return [row for (row,) in Request( """SELECT keyword FROM keywords ORDER BY LOWER(keyword) ASC""" )]

def countKW(kw):
    if kw is not None:
        return Request("""SELECT count(*) FROM files WHERE idFile in (SELECT idFile FROM KeywordsInFiles WHERE idKW =(SELECT idKW FROM keywords WHERE keyword="%s"))"""%kw.encode("utf8"))[0][0]
    else:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM KeywordsInFiles)""" )[0][0]

def countPicsFolder(folderid):
    log("TEST : tous les enfants de %s"%folderid)
    log(all_children(folderid))
    log("fin du test")
    cpt = Request("SELECT count(*) FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%folderid)[0][0]
    for idchild in all_children(folderid):
        cpt = cpt+Request("SELECT count(*) FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%idchild)[0][0]
    return cpt#Request("SELECT count(*) FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%folderid)[0][0]

def countPeriod(period,value):
    #   lister les images pour une date donnée
    format = {"year":"%Y","month":"%Y-%m","date":"%Y-%m-%d","":"%Y"}[period]
    if period=="year" or period=="":
        if value:
            #filelist = search_between_dates( (value,format) , ( str( int(value) +1 ),format) )
            filelist = pics_for_period('year',value)
        else:
            filelist = search_all_dates()
    elif period in ["month","date"]:
        filelist = pics_for_period(period,value)
        
    else:
        #pas de periode, alors toutes les photos du 01/01 de la plus petite année, au 31/12 de la plus grande année
        listyears=get_years()
        amini=min(listyears)
        amaxi=max(listyears)
        if amini and amaxi:
            filelist = search_between_dates( ("%s"%(amini),format) , ( "%s"%(amaxi),format) )
        else:
            filelist = []
    return len(filelist)

def list_cam_models():
    """retourne la liste des modèles d'appareils photos"""
    return [row for (row,) in Request("""SELECT DISTINCT "Image Model" FROM files WHERE "Image Model" NOT NULL""")]


def list_path():
    """retourne la liste des chemins en base de données"""
    #print Request( """SELECT DISTINCT strPath FROM files""" )
    return [row for (row,) in Request( """SELECT DISTINCT strPath FROM files""" )]


##
##def all_children(rootid):
##    """liste les id des dossiers enfants"""
##    #A REVOIR : Ne fonctionne pas correctement !
##    enfants=[]
##    childrens=[rootid]
##    continu = False
##    while True:
##        for ch in childrens:#1
##            print ch
##            chlist = [row for (row,) in Request( """SELECT idFolder FROM folders WHERE ParentFolder='%s'"""%ch )]#2,10,17
##            print chlist
##            if chlist: continu = True
##        print "*****"
##        childrens = chlist#2,10,17
##        enfants = enfants + chlist#2,10,17
##        if not continu: break
##        continu = False
##    return enfants

def all_children(rootid):
    """liste les id des dossiers enfants"""
    #A REVOIR : Ne fonctionne pas correctement !
    enfants=[]
    childrens=[rootid]
    continu = False
    while True:
        try:
            id = childrens.pop(0)
        except:
            #fin
            break
        chlist = [row for (row,) in Request( """SELECT idFolder FROM folders WHERE ParentFolder='%s'"""%id )]#2,10,17
        childrens=childrens+chlist
        enfants=enfants+chlist

    return enfants
    
        

#def search_between_dates(datestart='2007-01-01 00:00:01',dateend='2008-01-01 00:00:01'):
def search_between_dates(DateStart=("2007","%Y"),DateEnd=("2008","%Y")):
    """Cherche les photos qui ont été prises entre 'datestart' et 'dateend'."""
    log(DateStart)
    log(DateEnd)
    DS = strftime("%Y-%m-%d %H:%M:%S",strptime(DateStart[0],DateStart[1]))
    DE = strftime("%Y-%m-%d %H:%M:%S",strptime(DateEnd[0],DateEnd[1]))
    if DateEnd[1]=="%Y-%m-%d":
        Emodifier = "'start of day','+1 days','-1 minutes'"
        Smodifier = "'start of day'"
    elif DateEnd[1]=="%Y-%m":
        Emodifier = "'start of month','+1 months','-1 minutes'"
        Smodifier = "'start of month'"
    elif DateEnd[1]=="%Y":
        Emodifier = "'start of year','+1 years',-1 minutes'"
        Smodifier = "'start of year'"
    else:
        Emodifier = "''"
        Smodifier = "''"
    
    #SELECT strPath,strFilename FROM files WHERE strftime('%Y-%m-%d %H:%M:%S', "EXIF DateTimeOriginal") BETWEEN strftime('%Y-%m-%d %H:%M:%S','2007-01-01 00:00:01') AND strftime('%Y-%m-%d %H:%M:%S','2007-12-31 23:59:59') ORDER BY "EXIF DateTimeOriginal" ASC
    request = """SELECT strPath,strFilename FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN datetime('%s',%s) AND datetime('%s',%s) ORDER BY "EXIF DateTimeOriginal" ASC"""%(DS,Smodifier,DE,Emodifier)
    return [row for row in Request(request)]

def pics_for_period(periodtype,date):
    print periodtype,date
    try:
        sdate,modif1,modif2 = {'year' :['%s-01-01'%date,'start of year','+1 years'],
                               'month':['%s-01'%date,'start of month','+1 months'],
                               'date' :['%s'%date,'start of day','+1 days']}[periodtype]
    except:
        print_exc()
        log ("pics_for_period ( periodtype = ['date'|'month'|'year'] , date = corresponding to the period (year|year-month|year-month-day)")    
    request = """SELECT strPath,strFilename FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN datetime('%s','%s') AND datetime('%s','%s','%s') ORDER BY "EXIF DateTimeOriginal" ASC;"""%(sdate,modif1,
                                                                                                                                                                                                  sdate,modif1,modif2)
    return [row for row in Request(request)]

def get_years():
    #print "\n".join(get_years())
    return [t for (t,) in Request("""SELECT DISTINCT strftime("%Y","EXIF DateTimeOriginal") FROM files where "EXIF DateTimeOriginal" NOT NULL ORDER BY "EXIF DateTimeOriginal" ASC""")]
def get_months(year):
    #print "\n".join(get_months("2006"))
    return [t for (t,) in Request("""SELECT distinct strftime("%%Y-%%m","EXIF DateTimeOriginal") FROM files where strftime("%%Y","EXIF DateTimeOriginal") = '%s' ORDER BY "EXIF DateTimeOriginal" ASC"""%year)]
def get_dates(year_month):
    #print "\n".join(get_dates("2006-07"))
    return [t for (t,) in Request("""SELECT distinct strftime("%%Y-%%m-%%d","EXIF DateTimeOriginal") FROM files where strftime("%%Y-%%m","EXIF DateTimeOriginal") = '%s' ORDER BY "EXIF DateTimeOriginal" ASC"""%year_month)]
def search_all_dates():# TODO check if it is really usefull (check 'get_pics_dates' to see if it is not the same)
    """return all files from database sorted by 'EXIF DateTimeOriginal' """
    return [t for t in Request("""SELECT strPath,strFilename FROM files ORDER BY "EXIF DateTimeOriginal" ASC""")]
def get_pics_dates():
    """return all different dates from 'EXIF DateTimeOriginal'"""
    return [t for (t,) in Request("""SELECT DISTINCT strftime("%Y-%m-%d","EXIF DateTimeOriginal") FROM files WHERE "EXIF DateTimeOriginal"  NOT NULL ORDER BY "EXIF DateTimeOriginal" ASC""")]

def getDate(path,filename):
    try:
        return [row for row in Request( """SELECT files."EXIF DateTimeOriginal" FROM files WHERE strPath="%s" AND strFilename="%s";"""%(path,filename) )][0][0]
    except IndexError:
        return None

if __name__=="__main__":
    # initialisation de la base :
    pictureDB = join(DATA_PATH,"MyPictures.db")
    #   - efface les tables et les recréés
    Make_new_base(pictureDB,ecrase=True)
    #mount(mountpoint="y:",path="\\\\192.168.0.1\\photos",login="titi",password="toto")

    picpath = [r"Y:"]
    #picpath = [r"C:\Users\alexsolex\Documents\python\images_test"]
    #picpath=[home]
    from time import time
    t=time()
    
    # parcours récursif du dossier 'picpath'
    global compte
    total = 0
    for chemin in picpath:
        compte = 0
        #os.path.walk(chemin, processDirectory, (hook_directory,False) )
        browse_folder(chemin,parentfolderID=None,recursive=True,update=False)
        log( "  - %s nouvelles images trouvées dans le répertoire %s et ses sous-dossiers."%(compte,chemin) )
        total = total + compte
    log( u"%s images ajoutées à la base en %s secondes!".encode("utf8")%(total,str(time()-t)) )

    # traitement des dossiers supprimés/renommés physiquement --> on supprime toutes les entrées de la base
    for path in list_path():#on parcours tous les dossiers distinct en base de donnée
        if not isdir(path): #si le chemin en base n'est pas réellement un dossier,...
            DB_del_pic(path)#... on supprime toutes les entrées s'y rapportant
            print "%s n'est pas un chemin. Les entrées s'y rapportant dans la base sont supprimées."%path
    print
    print
    print "Demo de GESTION PAR MOTS CLES"
    print
    print
    print "liste des mots cles"
    print list_KW()
    print
    print "Les photos correspondants au mot clef 'Animaux'"
    c = search_keyword(u"Musée".encode("utf8"))
    for path,filename in c:
        fichier = join(path,filename)
        if isfile(fichier):
            print "\t%s"%fichier
        else:
            print "'%s' n'est pas un fichier valide"%fichier        
    print
    print "Les photos entre le 2006-07-13 00:00:01 et le 2007-06-30 23:59:59"
    c = search_between_dates(("2006-07-13 00:00:01","%Y-%m-%d %H:%M:%S"),("2007-06-30 23:59:59","%Y-%m-%d %H:%M:%S"))
    c=search_between_dates(("2006-07","%Y-%m"),("2006-08","%Y-%m"))
    c=search_between_dates(("2006-06-26","%Y-%m-%d"),("2006-08-15","%Y-%m-%d"))
    for path,filename in c:
        fichier = join(path,filename)
        if isfile(fichier):
            print "\t%s"%fichier
        else:
            print "'%s' n'est pas un fichier valide"%fichier
    print
    print
    #print "\n".join(get_years())
    print "\n".join([t for (t,) in Request("""SELECT DISTINCT strftime("%Y","EXIF DateTimeOriginal") FROM files where "EXIF DateTimeOriginal" NOT NULL""")])
    #print "\n".join(get_months("2006"))
    print "\n".join([t for (t,) in Request("""SELECT distinct strftime("%%Y-%%m","EXIF DateTimeOriginal") FROM files where strftime("%%Y","EXIF DateTimeOriginal") = '%s'"""%2007)])
    #print "\n".join(get_dates("2006-07"))
    print "\n".join([t for (t,) in Request("""SELECT distinct strftime("%%Y-%%m-%%d","EXIF DateTimeOriginal") FROM files where strftime("%%Y-%%m","EXIF DateTimeOriginal") = '%s'"""%"2006-07")])
    print
    print u"Les modèles d'appareils photos".encode("utf8")
    print u"\n".join([u"\t%s"%k.decode("utf8") for k in list_cam_models()]).encode("utf8")
    print
    print u"Les mots clés différents".encode("utf8")
    print u"\n".join([u"\t%s"%k.decode("utf8")  for k in list_KW()]).encode("utf8")

    print
    print "suppression des images du dossier 'C:\images_test'"
    DB_del_pic(r"C:\images_test")


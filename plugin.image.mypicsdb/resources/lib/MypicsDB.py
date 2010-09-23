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


import time
import fnmatch
import os.path
import traceback

#traitement EXIF
import EXIF
#traitement IPTC
if sys.modules.has_key("iptcinfo"):
    del sys.modules['iptcinfo']
from iptcinfo import IPTCInfo 
from iptcinfo import c_datasets as IPTC_FIELDS
#base de donnée SQLITE
try:
    from pysqlite2 import dbapi2 as sqlite
    print "using pysqlite2"
except:
    from sqlite3 import dbapi2 as sqlite
    print "using sqlite3"
    pass

global pictureDB
pictureDB = os.path.join(DB_PATH,"MyPictures.db")
sys_enc = sys.getfilesystemencoding()

lists_separator = "||"


    
def log(msg):
    print str("MyPicsDB >> %s"%msg.__str__())
    
def mount(mountpoint="z:",path="\\",login=None,password=""):
    import os
    if not os.path.exists(mountpoint):
        log( "Mounting %s as %s..."%(path,mountpoint) )
        if login:
            os.system("net use %s %s %s /USER:%s"%(mountpoint,path,login,password))
        else:
            os.system("net use %s %s"%(mountpoint,path))
    else:
        log( "%s is already mounted !"%mountpoint )
    return os.path.exists(mountpoint)

def Make_new_base(DBpath,ecrase=True):
##    if not(os.path.isfile(DBpath)):
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


    #table 'files'
    try:
        cn.execute("""CREATE TABLE files ( idFile integer primary key, idFolder integer, strPath text, strFilename text, UseIt integer )""")
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
    #table 'c'
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
 
def getColumns(table):
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    cn.execute("select * from files")
    retour= "\n".join([field[0] for field in cn.description])
   
    conn.commit()
    cn.close()
    return retour


def DB_exists(picpath,picfile):
    """
    Check wether or not a file exists in the DB
    """
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    try:
        cn.execute("""SELECT strPath, strFilename FROM "main"."files" WHERE strPath = (?) AND strFilename = (?);""",(picpath,picfile,) )
    except Exception,msg:
        log( "EXCEPTION >> DB_exists %s,%s"%(picpath,picfile) )
        log( "\t%s - %s"%(Exception,msg) )
        log( "~~~~" )
        log( "" )
        raise Exception, msg

    cn.close()    
    if len(cn.fetchmany())==0:
        return False
    else:
        return True    

def DB_listdir(path):
    """
    List files from DB where path
    """
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    conn.text_factory = str #sqlite.OptimizedUnicode
    #attention path doit être unicode !!
    log( path )
    try:
        #cn.execute( """SELECT strFilename FROM "files" WHERE strPath = (?);""",(path,))
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

    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    #méthode dajout d'une ligne d'un coup
    conn.text_factory = sqlite.OptimizedUnicode      
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
    # TRAITEMENT DES MOTS CLES (base keywords)
    if dictionnary.has_key("keywords"):
        kwl = dictionnary["keywords"].split(lists_separator)
        for mot in kwl:
            if mot: #on ajoute que les mots clés non vides
                #First for keywords, create an entry for this keyword in keywords table
                try:
                    cn.execute("""INSERT INTO keywords(keyword) VALUES("%s")"""%mot.encode("utf8","replace"))##
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
                    print type(mot)
                    cn.execute("""INSERT INTO KeywordsInFiles(idKW,idFile) SELECT k.idKW,f.idFile FROM keywords k, files f WHERE k.keyword=? AND f.strPath=? AND f.strFilename=?""",(mot.decode("utf8"),
                                                                                                                                                                                     path.encode("utf8"),
                                                                                                                                                                                     filename.encode("utf8")))
                except Exception,msg:
                    log("Error while adding KeywordsInFiles")
                    print Exception,msg
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
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    conn.text_factory = sqlite.OptimizedUnicode      
    try:
        cn.execute("""INSERT INTO folders(FolderName,ParentFolder,FullPath,HasPics) VALUES (?,?,?,?);""",(foldername.decode("utf8"),parentfolderID,folderpath.decode("utf8"),haspic))
    except sqlite.IntegrityError:
        pass
    conn.commit()
    cn.execute("""SELECT idFolder FROM folders where FullPath= ?""",(folderpath.decode("utf8"),))
    try:
        retour = [row for (row,) in cn][0]
    except:
        retour = 0
    cn.close()
    return retour


def DB_del_path(path):
    #recup l'id du path donné
    idpath = Request("SELECT idPath from folders where FullPath like '%?'",(path,))
    deletelist=[]# listera les id des dossiers à supprimer
    deletelist.append(idpath)#le dossier en paramètres est aussi à supprimer
    deletelist.extend(get_children(idpath))#on ajoute tous les enfants en sous enfants du dossier

def get_children(folderid):
    childrens=[c[0] for c in Request("SELECT idFolder FROM folders WHERE ParentFolder='%s'"%folderid)]
    log( childrens )
    list_child=[]
    list_child.extend(childrens)
    for idchild in childrens:
        list_child.extend(get_children(idchild))
    return list_child

def DB_del_pic(picpath,picfile=None):
    """Supprime le chemin/fichier de la base. Si aucun fichier n'est fourni, toutes les images du chemin sont supprimées de la base"""
    if picfile:
        #on supprime le fichier de la base
        Request("""DELETE FROM files WHERE idFolder = (SELECT idFolder FROM folders WHERE FullPath=%s) AND strFilename=%s"""%(picpath,picfile))
        #puis maintenant on vérifie que le chemin dossier est toujours utile ou alors on le supprime
        Request("""DELETE FROM folders 
    WHERE 
      (SELECT DISTINCT idFolder FROM files 
          WHERE idFolder=(
              SELECT DISTINCT idFolder FROM folders WHERE FullPath=%s
                         )
      )
   or FullPath=%s""" %(picpath,picpath) )
    else:
        idpath = Request("SELECT idFolder FROM folders WHERE FullPath = '%s'"%picpath)[0][0]#le premier du tuple à un élément
        log( idpath )
        deletelist=[]#va lister les id des dossiers à supprimer
        deletelist.append(idpath)#le dossier en paramètres est aussi à supprimer
        deletelist.extend(get_children(str(idpath)))#on ajoute tous les enfants en sous enfants du dossier
        Request( "DELETE FROM files WHERE idFolder in ('%s')"%"','".join([str(i) for i in deletelist]) )
        Request( "DELETE FROM folders WHERE idFolder in ('%s')"%"','".join([str(i) for i in deletelist]) )

    return

def DB_deltree(picpath):
    pass

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
    return [row for row in Request( """SELECT strPath,strFilename FROM Files WHERE idFile IN (SELECT idFile FROM FilesInCollections WHERE idCol IN (SELECT idCol FROM Collections WHERE CollectionName='%s'))"""%Colname)]

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

def renPeriode(periodname,newname):
    Request( """UPDATE Periodes SET PeriodeName = "%s" WHERE PeriodeName="%s" """%(newname,periodname) )
    return

def PicsForPeriode(periodname):
    """Get pics for the given period name"""
    period = Request( """SELECT DateStart,DateEnd FROM Periodes WHERE PeriodeName=%s"""%periodname )
    return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN %s AND %s ORDER BY "EXIF DateTimeOriginal" ASC"""%period )]

###
    
def hook_directory ( filepath,filename,filecount, nbfiles ):
    import sys
    log( "%s/%s - %s"%(filecount,nbfiles,os.path.join(filepath,filename)) )
    
def dummy_update(percent, line1=None, line2=None, line3=None):
    log( "%s\t%s\n\t%s\n\t%s"%(percent,line1,line2,line3) )
    
def browse_folder(dirname,parentfolderID=None,recursive=True,update=False,updatefunc=dummy_update):
    """parcours le dossier racine 'dirname'
    - 'recursive' pour traverser récursivement les sous dossiers de 'dirname'
    - 'update' pour forcer le scan des images qu'elles soient déjà en base ou pas
    - 'updatefunc' est une fonction appelée pour indiquer la progression. Les paramètres sont (pourcentage(int),[ line1(str),line2(str),line3(str) ] )
"""
    try:
        listdir = os.listdir(dirname)
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + \
                str(sys.exc_type)+ ": " + str(sys.exc_value) + "\n"
        log( pymsg )
        listdir=[]
        
    global compte
    cpt=0
    #on liste les fichiers jpg du dossier
    listfolderfiles=[]
##    import imghdr
    for f in listdir:
        if os.path.splitext(f)[1].upper() in [".JPG",".TIF",".PNG",".GIF",".BMP"]:
            listfolderfiles.append(f)
###other technic using imghdr but many jpg pictures are not handled..... why ??
##        print ""
##        print "** %s"%f
##        try:
##            if os.path.isfile(os.path.join(dirname,f)) and imghdr.what(os.path.join(dirname,f)) in ['jpeg','gif','tiff','bmp','png']:
##                listfolderfiles.append(f)
##                print imghdr.what(os.path.join(dirname,f))
##            else:
##                print imghdr.what(os.path.join(dirname,f))
##        except:
##            print "passing ...\n"
##            pass
    
    #listfolderfiles = fnmatch.filter(listdir,"*.jpg")
    #on récupère la liste des fichiers entrées en BDD pour le dossier en cours
    listDBdir = DB_listdir(dirname)# --> une requête pour tout le dossier
    if listfolderfiles: i="1"
    else: i="0"
    #"1" if listfolderfiles else "0"

    #on ajoute dans la table des chemins le chemin en cours
    PFid = DB_folder_insert(os.path.basename(dirname) or os.path.dirname(dirname).split(os.path.sep)[-1],
                            dirname,
                            parentfolderID,
                            i#"1" if listfolderfiles else "0"
                            )
    #si le dossier contient des fichiers jpg...
    if listfolderfiles:
        #alors on parcours toutes les images du dossier en cours
        for picfile in listfolderfiles:#... on parcours tous les jpg
            #on enlève l'image traitée de listdir
            listdir.pop(listdir.index(picfile))
            #si l'image n'est pas déjà en base de donnée
            if not picfile in listDBdir or update:
                cpt = cpt + 1
                updatefunc(int(100 * float(cpt)%len(listfolderfiles)),"Adding from %s to Database :"%dirname,picfile)
                #préparation d'un dictionnaire pour les champs et les valeurs
                # c'est ce dictionnaire qui servira à  remplir la table fichiers
                ##picentry = { "strPath":dirname, "strFilename":picfile }
                picentry = { "idFolder":PFid, "strPath":dirname.decode("utf8"),"strFilename":picfile.decode("utf8"),"UseIt":1 }

                ###############################
                # récupération des infos EXIF #
                ###############################
                #lecture des infos EXIF
                #   (les colonnes nécessaires sont alors écrites)
                try:
                    exif = get_exif(os.path.join(dirname,picfile).encode('utf8'))
                except UnicodeDecodeError:
                    exif = get_exif(os.path.join(dirname,picfile))
                #on ajoute les infos exif au dictionnaire
                picentry.update(exif)

                ###############################
                # récupération des infos IPTC #
                ###############################
                iptc = get_iptc(dirname,picfile)
                #on ajoute les infos iptc au dictionnaire
                picentry.update(iptc)

                ###############################
                # Insertion en base de donnée #
                ###############################

                #insertion des données dans la table
                DB_file_insert(dirname,picfile,picentry,update)
            else: #file already in DB
                updatefunc(int(100 * float(cpt)%len(listfolderfiles)),"Already in Database :",picfile)
                pass
            if picfile in listDBdir:
                listDBdir.pop(listDBdir.index(picfile))
                
        #puis si la base contient encore des images pour ce dossier
        if listDBdir and update: #à l'issu si listdir contient encore des fichiers, c'est qu'ils sont en base mais que le fichier n'existe plus physiquement.
            co=0
            for f in listDBdir: #on parcours les images en DB orphelines
                compte=compte+1
                updatefunc(int(100 * float(co)%len(listDBdir)),"Removing from Database :",f)
                DB_del_pic(dirname,f)
                log( u"\t%s a été supprimé de la base car le fichier n'existe pas dans ce dossier. "%f.decode(sys_enc))
            log("")
            del co
            
    else:

        updatefunc(0,"No pictures in this folder :",dirname)
        log( "Ce dossier ne contient pas d'images :")
        log( dirname )
        log( "" )
    
    if cpt:
        log( "%s nouvelles images trouvees dans %s"%(str(cpt),dirname) )
        #unicode(info.data[k].encode("utf8").__str__(),"utf8")
        compte=compte+cpt
        cpt=0
    if recursive: #gestion de la recursivité. On rappel cette même fonction pour chaque dossier rencontré
        log( "traitement des sous dossiers de :")
        log( dirname )
        for item in listdir:
            if os.path.isdir(os.path.join(dirname,item)):#un directory
                browse_folder(os.path.join(dirname,item),PFid,recursive,update,updatefunc)
            else:
                #listdir contenait un fichier mais pas un dossier
                # inutilisé... on passe pour le moment
                pass
                


        

        

def get_exif(picfile):
    """
    get EXIF fields in the picture and return datas as key:value dictionnary
    """
    #définition des champs EXIF que nous souhaitons utiliser
    EXIF_fields =["Image DateTime",
                "Image Model",
                "Image Orientation",
                #"Image ResolutionUnit",
                #"Image XResolution",
                #"Image YResolution",
                #"Image Make",
                "EXIF DateTimeOriginal",
                "EXIF ExifImageWidth",
                #"EXIF FileSource",
                #"EXIF Flash",
                "EXIF SceneCaptureType",
                #"EXIF DigitalZoomRatio",
                "EXIF DateTimeDigitized",
                "GPS GPSLatitude",
                "GPS GPSLongitude",
                #"EXIF ExifVersion"]
                  ]
    #ouverture du fichier
    f=open(picfile,"rb")
    #   et lecture des tags EXIF (on ne prend pas les makernotes, données constructeurs)
    tags = EXIF.process_file(f,details=False)
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
                        tagvalue = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(tags[tag].__str__(),datetimeformat))
                        break
                    except:
                        log( "Datetime (%s) did not match for '%s' format... trying an other one..."%(tags[tag].__str__(),datetimeformat) )
                if not tagvalue:
                    log( "ERROR : the datetime format is not recognize (%s)"%tags[tag].__str__() )
                #tagvalue = time.mktime(time.strptime(tags[tag].__str__(),"%Y:%m:%d %H:%M:%S"))
                #tagvalue = tags[tag].__str__()
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
    try:
        info = IPTCInfo(os.path.join(path,filename))
    except Exception,msg:
        if not type(msg.args[0])==type(int()):
            if msg.args[0].startswith("No IPTC data found."):
                #print "No IPTC data found."
                return {}
            else:
                log( "EXCEPTION >> get_iptc %s"%os.path.join(path,filename) )
                log( "%s - %s"%(Exception,msg) )
                log( "~~~~" )
                log( "" )
                return {}
        else:
            log( "EXCEPTION >> get_iptc %s"%os.path.join(path,filename) )
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
        return Request("""SELECT count(*) FROM files WHERE idFile in (SELECT DISTINCT idFile FROM KeywordsInFiles)""" )[0][0]

def countPicsFolder(folderid):
    log("TEST : tous les enfants de %s"%folderid)
    log(all_children(folderid))
    log("fin du test")
    cpt = Request("SELECT count(*) FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%folderid)[0][0]
    for idchild in all_children(folderid):
        cpt = cpt+Request("SELECT count(*) FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%idchild)[0][0]
    return cpt#Request("SELECT count(*) FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%folderid)[0][0]

def countPeriod(period,value):
    print "countperiod(%s,%s)"%(period,value)
    #   lister les images pour une date donnée
    format = {"year":"%Y","month":"%Y-%m","date":"%Y-%m-%d","":"%Y"}[period]
    if period=="year" or period=="":
        if value:
            filelist = search_between_dates( (value,format) , ( str( int(value) +1 ),format) )
        else:
            filelist = search_all_dates()
            
    elif period=="month":
        a,m=value.split("-")
        if m=="12":
            aa=int(a)+1
            mm=1
        else:
            aa=a
            mm=int(m)+1
        print mm,aa
        print
        filelist = search_between_dates( ("%s-%s"%(a,m),format) , ( "%s-%s"%(aa,mm),format) )
        
    elif period=="date":
        #BUG CONNU : trouver un moyen de trouver le jour suivant en prenant en compte le nb de jours par mois
        a,m,j=value.split("-")              
        filelist = search_between_dates( ("%s-%s-%s"%(a,m,j),format) , ( "%s-%s-%s"%(a,m,int(j)+1),format) )
        
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
    
        
def search_year(year):
    """retourne les photos de l'année fournie"""
    #TODO : utiliser un format date pour la variable year, et tester sa validité
    retour = search_between_dates((year,"%Y"),(str(int(year)+1),"%Y"))
    return retour

#def search_between_dates(datestart='2007-01-01 00:00:01',dateend='2008-01-01 00:00:01'):
def search_between_dates(DateStart=("2007","%Y"),DateEnd=("2008","%Y")):
    """Cherche les photos qui ont été prises entre 'datestart' et 'dateend'."""
    log(DateStart)
    log(DateEnd)
    DS = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(DateStart[0],DateStart[1]))#time.mktime(time.strptime(DateStart[0],DateStart[1]))
    DE = time.strftime("%Y-%m-%d %H:%M:%S",time.strptime(DateEnd[0],DateEnd[1]))#time.mktime(time.strptime(DateEnd[0],DateEnd[1]))
    #SELECT strPath,strFilename FROM files WHERE strftime('%Y-%m-%d %H:%M:%S', "EXIF DateTimeOriginal") BETWEEN strftime('%Y-%m-%d %H:%M:%S','2007-01-01 00:00:01') AND strftime('%Y-%m-%d %H:%M:%S','2007-12-31 23:59:59') ORDER BY "EXIF DateTimeOriginal" ASC
    request = """SELECT strPath,strFilename FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN datetime('%s') AND datetime('%s') ORDER BY "EXIF DateTimeOriginal" ASC"""%(DS,DE)
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
def search_all_dates():
    return [t for t in Request("""SELECT strPath,strFilename FROM files ORDER BY "EXIF DateTimeOriginal" ASC""")]
def get_pics_dates():
    return [t for (t,) in Request("""SELECT distinct strftime("%Y-%m-%d","EXIF DateTimeOriginal") FROM files where "EXIF DateTimeOriginal"  not null ORDER BY "EXIF DateTimeOriginal" ASC""")]
#Quelques requêtes SQLite
#
"""
SELECT strPath,strFilename,"EXIF DateTimeOriginal" FROM files
   WHERE strftime('%Y-%m-%d %H:%M:%S', "EXIF DateTimeOriginal") > datetime("2009-01-01","start of year","-1 year")
   ORDER BY "EXIF DateTimeOriginal" ASC
"""
#toutes les photos entre 2 dates/heures données
"""
SELECT strPath,strFilename,"EXIF DateTimeOriginal" FROM files
WHERE strftime('%Y-%m-%d %H:%M:%S', "EXIF DateTimeOriginal") BETWEEN strftime('%Y-%m-%d %H:%M:%S','2007-01-01 00:00:01') AND strftime('%Y-%m-%d %H:%M:%S','2007-12-31 23:59:59')
ORDER BY "EXIF DateTimeOriginal" ASC
"""
#toutes les photos d'un mois d'une date donnée
"""
SELECT strPath,strFilename,"EXIF DateTimeOriginal" FROM files
WHERE strftime('%Y-%m-%d %H:%M:%S', "EXIF DateTimeOriginal") BETWEEN date("2009-11-21","start of month") AND date("2009-11-21","start of month","+1 month")
ORDER BY "EXIF DateTimeOriginal" ASC
"""
#les dossiers racines :
"""select * from folders where ParentFolder is Null"""
#les dossiers enfants d'un dossier
"""select * from folders where ParentFolder = 78"""
if __name__=="__main__":
    # initialisation de la base :
    pictureDB = os.path.join(DATA_PATH,"MyPictures.db")
    #   - efface les tables et les recréés
    Make_new_base(pictureDB,ecrase=True)
    #mount(mountpoint="y:",path="\\\\192.168.0.1\\photos",login="titi",password="toto")

    picpath = [r"Y:"]
    #picpath = [r"C:\Users\alexsolex\Documents\python\images_test"]
    #picpath=[home]
    
    t=time.time()
    
    # parcours récursif du dossier 'picpath'
    global compte
    total = 0
    for chemin in picpath:
        compte = 0
        #os.path.walk(chemin, processDirectory, (hook_directory,False) )
        browse_folder(chemin,parentfolderID=None,recursive=True,update=False)
        log( "  - %s nouvelles images trouvées dans le répertoire %s et ses sous-dossiers."%(compte,chemin) )
        total = total + compte
    log( u"%s images ajoutées à la base en %s secondes!".encode("utf8")%(total,str(time.time()-t)) )

    # traitement des dossiers supprimés/renommés physiquement --> on supprime toutes les entrées de la base
    for path in list_path():#on parcours tous les dossiers distinct en base de donnée
        if not os.path.isdir(path): #si le chemin en base n'est pas réellement un dossier,...
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
        fichier = os.path.join(path,filename)
        if os.path.isfile(fichier):
            print "\t%s"%fichier
        else:
            print "'%s' n'est pas un fichier valide"%fichier        
    print
    print "Les photos entre le 2006-07-13 00:00:01 et le 2007-06-30 23:59:59"
    c = search_between_dates(("2006-07-13 00:00:01","%Y-%m-%d %H:%M:%S"),("2007-06-30 23:59:59","%Y-%m-%d %H:%M:%S"))
    c=search_year("2007")
    c=search_between_dates(("2006-07","%Y-%m"),("2006-08","%Y-%m"))
    c=search_between_dates(("2006-06-26","%Y-%m-%d"),("2006-08-15","%Y-%m-%d"))
    for path,filename in c:
        fichier = os.path.join(path,filename)
        if os.path.isfile(fichier):
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

##    IPaddress = "192.168.0.21"
##    HTTP_API_url = "http://%s/xbmcCmds/xbmcHttp?command="%IPaddress
##    import urllib
##    print "Suppression du diaporama en cours..."
##    print urllib.urlopen( HTTP_API_url + "ClearSlideshow()" ).read()
##    print "Diaporama supprime !"
##    print
##    print "Ajout des fichiers dans le diaporama..."
##    for path,filename in c:
##        fichier = os.path.join(path,filename)
##        print "\t%s"%fichier
##        if os.path.isfile(fichier):
##            html = urllib.urlopen(HTTP_API_url + "AddToSlideshow(%s)" % fichier).read()
##            print html
##        else:
##            print "'%s' n'est pas un fichier valide"%fichier
##    print "Lancement de la lecture..."
##    print urllib.urlopen( HTTP_API_url + "ExecBuiltIn(SlideShow(,,notrandom))" ).read()
##    print "Lecture démarrée !"
##    print

del xbmc
##Tags EXIF :
EXIF_tags =["Image YCbCrPositioning",
            "Image ExifOffset",
            "Image DateTime",
            "Image Model",
            "Image Orientation",
            "Image ResolutionUnit",
            "Image XResolution",
            "Image Make",
            "Image YResolution",
            "EXIF ComponentsConfiguration",
            "EXIF CustomRendered",
            "EXIF FlashPixVersion",
            "EXIF ShutterSpeedValue",
            "EXIF ColorSpace",
            "EXIF MeteringMode",
            "EXIF ExifVersion",
            "EXIF Flash",
            "EXIF DateTimeOriginal",
            "EXIF ApertureValue",
            "EXIF InteroperabilityOffset",
            "EXIF FNumber",
            "EXIF FileSource",
            "EXIF ExifImageLength",
            "EXIF CompressedBitsPerPixel",
            "EXIF ExposureBiasValue",
            "EXIF ExposureMode",
            "EXIF FocalPlaneYResolution",
            "EXIF ExifImageWidth",
            "EXIF FocalPlaneXResolution",
            "EXIF SceneCaptureType",
            "EXIF DigitalZoomRatio",
            "EXIF DateTimeDigitized",
            "EXIF FocalLength",
            "EXIF ExposureTime",
            "EXIF WhiteBalance",
            "EXIF FocalPlaneResolutionUnit",
            "EXIF MaxApertureValue",
            "EXIF SensingMethod",
            "JPEGThumbnail",
            "Thumbnail JPEGInterchangeFormat",
            "Thumbnail JPEGInterchangeFormatLength",
            "Thumbnail Compression",
            "Thumbnail ResolutionUnit",
            "Thumbnail XResolution",
            "Thumbnail YResolution"]


            

# -*- coding: utf8 -*-
"""
Todo :
* ability to remove a file from database
* use smb file access to browse smb share pictures:
    http://sourceforge.net/projects/pysmb/


"""
import os,sys,re
from os.path import join, exists, isfile, isdir
from urllib import unquote_plus

try:
    import xbmc
    makepath=xbmc.translatePath(os.path.join)
except:
    makepath=os.path.join

import  xbmcaddon
from XMP import XMP_Tags
 
Addon = xbmcaddon.Addon(id='plugin.image.mypicsdb')
home = Addon.getAddonInfo('path')

#these few lines are taken from AppleMovieTrailers script
# Shared resources
BASE_RESOURCE_PATH = makepath( home, "resources" )
DATA_PATH = Addon.getAddonInfo('profile')
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
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite
    pass


from traceback import print_exc
global pictureDB
pictureDB = join(DB_PATH,"MyPictures.db")
sys_enc = sys.getfilesystemencoding()

lists_separator = "||"

class MyPictureDB(Exception):
    pass

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
    
LOGDEBUG = 0
LOGDEBUG = 4
LOGFATAL = 6
LOGINFO = 1
LOGNONE = 7
LOGNOTICE = 2
LOGSEVERE = 5
LOGWARNING = 3
def log(msg, level=LOGINFO):

    if type(msg).__name__=="unicode":
        msg = msg.encode("utf-8")
    if DEBUGGING:
        #print str("MyPicsDB >> %s"%msg.__str__())
        xbmc.log(str("MyPicsDB >> %s"%msg.__str__()), level)

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
        for table in ['tags', 'TagContent', 'TagContents', 'TagsInFiles', 'TagTypes',"files","keywords","folders","KeywordsInFiles","Collections","FilesInCollections","Periodes","Rootpaths","CategoriesInFiles","Categories","SupplementalCategoriesInFiles","SupplementalCategories","CitiesInFile","Cities","CountriesInFiles","Countries"]:
            try:
                cn.execute("""DROP TABLE %s"""%table)
            except Exception,msg:
                log( ">>> Make_new_base - DROP TABLE %s"%table, LOGDEBUG )
                log( "%s - %s"%(Exception,msg), LOGDEBUG )
                log( "~~~~", LOGDEBUG )
                log( "", LOGDEBUG )


    #table 'files'
    try:
        cn.execute("""CREATE TABLE files ( idFile integer primary key, idFolder integer, strPath text, strFilename text, ftype text, DateAdded DATETIME, mtime text, UseIt integer , sha text, Thumb text,  "Image Rating" text, City text,
                    CONSTRAINT UNI_FILE UNIQUE ("strPath","strFilename")
                                   )""")
    except Exception,msg:
        if msg.args[0].startswith("table 'files' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE files ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'keywords'
    try:
        cn.execute("""CREATE TABLE "keywords" ("idKW" INTEGER primary key, "keyword" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'keywords' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE keywords ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'KeywordsInFiles'
    try:
        cn.execute("""CREATE TABLE "KeywordsInFiles" ("idKW" INTEGER NOT NULL, "idFile" INTEGER NOT NULL);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'KeywordsInFiles' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE KeywordsInFiles ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
# MDB
    #table 'Categories'
    try:
        cn.execute("""CREATE TABLE "Categories" ("idCategory" INTEGER NOT NULL primary key, "Category" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Categories' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Categories ..." )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'CategoriesInFiles'
    try:
        cn.execute("""CREATE TABLE "CategoriesInFiles" ("idCategory" INTEGER NOT NULL, "idFile" INTEGER NOT NULL);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'CategoriesInFiles' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE CategoriesInFiles ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'SupplementalCategories'
    try:
        cn.execute("""CREATE TABLE "SupplementalCategories" ("idSupplementalCategory" INTEGER NOT NULL primary key, "SupplementalCategory" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'SupplementalCategories' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE SupplementalCategories ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'SupplementalCategoriesInFiles'
    try:
        cn.execute("""CREATE TABLE "SupplementalCategoriesInFiles" ("idSupplementalCategory" INTEGER NOT NULL, "idFile" INTEGER NOT NULL);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'SupplementalCategoriesInFiles' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE SupplementalCategoriesInFiles ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'Countries'
    try:
        cn.execute("""CREATE TABLE "Countries" ("idCountry" INTEGER NOT NULL primary key, "Country" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Countries' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Countries ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'CountriesInFiles'
    try:
        cn.execute("""CREATE TABLE "CountriesInFiles" ("idCountry" INTEGER NOT NULL, "idFile" INTEGER NOT NULL);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'CountriesInFiles' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE CountriesInFiles ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )

    #table 'Persons'
    try:
        cn.execute("""CREATE TABLE "Persons" ("idPerson" INTEGER NOT NULL primary key, "Person" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Persons' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Persons ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'PersonsInFiles'
    try:
        cn.execute("""CREATE TABLE "PersonsInFiles" ("idPerson" INTEGER NOT NULL, "idFile" INTEGER NOT NULL);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'PersonsInFiles' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE PersonsInFiles ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )


    #table 'Cities'
    try:
        cn.execute("""CREATE TABLE "Cities" ("idCity" INTEGER NOT NULL primary key, "City" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Cities' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Cities ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'CitiesInFiles'
    try:
        cn.execute("""CREATE TABLE "CitiesInFiles" ("idCity" INTEGER NOT NULL, "idFile" INTEGER NOT NULL);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'CitiesInFiles' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE CitiesInFiles ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'folders'
    try:
        cn.execute("""CREATE TABLE "folders" ("idFolder" INTEGER  primary key not null, "FolderName" TEXT, "ParentFolder" INTEGER, "FullPath" TEXT UNIQUE,"HasPics" INTEGER);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'folders' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE folders ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
    #table 'Collections'
    try:
        cn.execute("""CREATE TABLE "Collections" ("idCol" INTEGER PRIMARY KEY, "CollectionName" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Collections' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE Collections ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
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
            log( ">>> Make_new_base - CREATE TABLE FilesInCollections ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
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
            log( ">>> Make_new_base - CREATE TABLE Periodes ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
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
            log( ">>> Make_new_base - CREATE TABLE Rootpaths ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG)
            log( "" , LOGDEBUG)


    #table 'TagTypes'
    try:
        cn.execute("""CREATE TABLE "TagTypes" ("idTagType" INTEGER NOT NULL primary key, "TagType" TEXT, "TagTranslation" TEXT, CONSTRAINT UNI_TAG UNIQUE("TagType") )""")
    except Exception,msg:
        if msg.args[0].startswith("table 'TagTypes' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Tags ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )

    #table 'TagContent'
    try:
        cn.execute("""CREATE TABLE "TagContents" ("idTagContent" INTEGER NOT NULL primary key, "idTagType" INTEGER, "TagContent" TEXT, CONSTRAINT UNI_TAG UNIQUE("idTagType", "TagContent") )""")
    except Exception,msg:
        if msg.args[0].startswith("table 'TagContents' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Tags ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )

    #table 'TagsInFiles'
    try:
        cn.execute("""CREATE TABLE "TagsInFiles" ("idTagContent" INTEGER NOT NULL, "idFile" INTEGER NOT NULL)""")
    except Exception,msg:
        if msg.args[0].startswith("table 'TagsInFiles' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE TagsInFiles ...", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~" , LOGDEBUG)
            log( "" , LOGDEBUG)

    # Index creation for old tag tables
    try:
        cn.execute("CREATE INDEX idxCategoriesInFiles1 ON CategoriesInFiles(idCategory)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxCitiesInFiles1 ON CitiesInFiles(idCity)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxCountriesInFiles1 ON CountriesInFiles(idCountry)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxFilesInCollections1 ON FilesInCollections(idCol)")
    except Exception,msg:
        pass


    try:
        cn.execute("CREATE INDEX idxKeywordsInFiles1 ON KeywordsInFiles(idKW)")
    except Exception,msg:
        pass


    try:
        cn.execute("CREATE INDEX idxPersonsInFiles1 ON PersonsInFiles(idPerson)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxSupplementalCategoriesInFiles1 ON SupplementalCategoriesInFiles(idSupplementalCategory)")
    except Exception,msg:
        pass


    # Index creation for new tag tables
    try:
        cn.execute("CREATE INDEX idxTagTypes1 ON TagTypes(idTagType)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxTagContent1 ON TagContents(idTagContent)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxTagsInFiles1 ON TagsInFiles(idTagContent)")
        cn.execute("CREATE INDEX idxTagsInFiles2 ON TagsInFiles(idFile)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxFiles ON Files (idFile)")
        cn.execute("CREATE INDEX idxFilesInCollections ON FilesInCollections (idFile)")
    except Exception,msg:
        pass

    conn.commit()


    # test table files for column city
    try:
        cn.execute("select City from files where idfile = -1")
    except Exception,msg:
        if msg.args[0].startswith("no such column: City"):
            addColumn('files', 'City')

    cn.close()

columnList = []
def addColumn(table,colheader,format="text"):
    global columnList
    key = table + '||' + colheader + '||' + format
    try:
        columnList.index(key);
        return
    except:
        conn = sqlite.connect(pictureDB)
        cn=conn.cursor()
        try:
            cn.execute("""ALTER TABLE %s ADD "%s" %s"""%(table,colheader,format))
        except Exception,msg:
            if not msg.args[0].startswith("duplicate column name"):
                log( 'EXCEPTION >> addColums %s,%s,%s'%(table,colheader,format), LOGDEBUG )
                log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                log( "~~~~", LOGDEBUG )
                log( "", LOGDEBUG )

        conn.commit()
        cn.close()
        columnList.append(key)

##def getColumns(table):
##    conn = sqlite.connect(pictureDB)
##    cn=conn.cursor()
##    cn.execute("select * from files")
##    retour= "\n".join([field[0] for field in cn.description])
##    print retour
##    conn.commit()
##    cn.close()
##    return retour

def DB_cleanup_keywords():
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    conn.text_factory = unicode #sqlite.OptimizedUnicode

    # if complete path was removed/renamed on hard disk then delete them
    for path in list_path():
        try:
            if not isdir(path):
                DB_del_pic(path)
        except:
            if not isdir(path.encode('utf-8')):
                DB_del_pic(path)

    try:
        # in old version something went wrong with deleteing old unused folders
        for i in range(1,10):
            cn.execute('delete from folders where ParentFolder not in (select idFolder from folders) and ParentFolder is not null')

        cn.execute('delete from files where idFolder not in( select idFolder from folders)')

        cn.execute( "delete from keywordsInFiles where idFile not in(select idFile from Files )")
        cn.execute( "delete from keywords where idKW not in (select idKW from keywordsInFiles)")
        cn.execute( "delete from categoriesInFiles where idFile not in(select idFile from Files )")
        cn.execute( "delete from Categories where idCategory not in (select idCategory from categoriesInFiles)")
        cn.execute( "delete from supplementalCategoriesInFiles where idFile not in(select idFile from Files )")
        cn.execute( "delete from SupplementalCategories where idSupplementalCategory not in (select idSupplementalCategory from supplementalCategoriesInFiles)")
        cn.execute( "delete from countriesInFiles where idFile not in(select idFile from Files )")
        cn.execute( "delete from Countries where idCountry not in (select idCountry from countriesInFiles)")
        cn.execute( "delete from citiesInFiles where idFile not in(select idFile from Files )")
        cn.execute( "delete from Cities where idCity not in (select idCity from citiesInFiles)")
        cn.execute( "delete from personsInFiles where idFile not in(select idFile from Files )")
        cn.execute( "delete from Persons where idPerson not in (select idPerson from personsInFiles)")

        cn.execute( "delete from TagsInFiles where idFile not in(select idFile from Files )")
        cn.execute( "delete from TagContents where idTagContent not in (select idTagContent from TagsInFiles)")
        # Only delete tags which are not translated!
        cn.execute( "delete from TagTypes where idTagType not in (select idTagType from TagContents) and TagType = TagTranslation")

    except Exception,msg:
        log( "ERROR : DB_cleanup_keywords ...", LOGSEVERE )
        log( "%s - %s"%(Exception,msg), LOGSEVERE )
        cn.close()
        raise

    conn.commit()
    cn.close()

def DB_exists(picpath,picfile):
    """
    Check wether or not a file exists in the DB
    """
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    try:
        cn.execute("""SELECT strPath, strFilename FROM "main"."files" WHERE strPath = (?) AND strFilename = (?);""",(picpath,picfile,) )
    except Exception,msg:
        log( "EXCEPTION >> DB_exists %s,%s"%(picpath,picfile), LOGDEBUG )
        log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
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
    conn.text_factory = unicode #sqlite.OptimizedUnicode
    log( path )
    try:
        cn.execute( """SELECT f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND p.FullPath=(?)""",(path,))
    except Exception,msg:
        log( "ERROR : DB_listdir ...", LOGDEBUG )
        log( "%s - %s"%(Exception,msg), LOGDEBUG )
        cn.close()
        raise

    retour = [row[0] for row in cn]
    #print retour
    cn.close()
    return retour
    
tagTypeDBKeys = {}
def DB_file_insert(path,filename,dictionnary,update=False):
    """
    insert into file database the dictionnary values into the dictionnary keys fields
    keys are DB fields ; values are DB values
    """
    global tagTypeDBKeys
    
    if update :#si update alors on doit updater et non pas insert
        if DB_exists(path,filename):
            #print "file exists in database and rescan is set to true..."
            Request("DELETE FROM files WHERE idFolder = (SELECT idFolder FROM folders WHERE FullPath='%s') AND strFilename='%s'"%(path,filename))
            DB_cleanup_keywords()
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()

    conn.text_factory = unicode#sqlite.OptimizedUnicode
    try:
        cn.execute( """INSERT INTO files('%s') values (%s)""" % ( "','".join(dictionnary.keys()), ",".join(["?"]*len(dictionnary.values())) ) ,
                                                                     dictionnary.values()
                    )
        conn.commit()
    except Exception,msg:
        log( ">>> DB_file_insert ...", LOGDEBUG )
        log(filename)
        log( "%s - %s"%(Exception,msg), LOGDEBUG )
        log( """INSERT INTO files('%s') values (%s)""" % ( "','".join(dictionnary.keys()) , ",".join(["?"]*len(dictionnary.values())) ), LOGDEBUG )
        log( "", LOGDEBUG )
        conn.commit()
        cn.close()
        raise MyPictureDB


    # meta table inserts
    cn.execute("SELECT idFile FROM files WHERE strPath = (?) AND strFilename = (?);",(path,filename,) )
    idFile = [row[0] for row in cn][0]

    # loop over tags dictionary
    for tagType, value in dictionnary.iteritems():

        if isinstance(value, basestring) and dictionnary[tagType]:

            # exclude the following tags
            if tagType not in ['sha', 'strFilename', 'strPath',
                               'mtime', 'ftype',
                               'source', 'urgency', 'time created', 'date created']:

                #['EXIF DateTimeDigitized', 'DateAdded', #, 'EXIF DateTimeOriginal'
                #'EXIF ExifImageLength', 'EXIF SceneCaptureType','EXIF ExifImageWidth',
                #'Image DateTime', 'Image Model', 'Image Orientation',
                
                tagValues = dictionnary[tagType].split(lists_separator)

                tagType = tagType[0].upper() + tagType[1:]

                for value in tagValues:

                    # change dates
                    if tagType == 'EXIF DateTimeOriginal':
                        value = value[:10]
                        
                    # first make sure that the tag exists in table TagTypes
                    # is it already in our list?
                    if not tagType in tagTypeDBKeys:
                  
                        # not in list therefore insert into table TagTypes
                        try:
                            cn.execute("INSERT INTO TagTypes(TagType, TagTranslation) VALUES('%s','%s')"%(tagType,tagType))
                        except Exception,msg:
                            if str(msg)=="column TagType is not unique":
                                pass
                            else:
                                log( 'EXCEPTION >> tags', LOGDEBUG )
                                log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                                log( "~~~~" , LOGDEBUG)
                                log( "", LOGDEBUG )

                         # select the key of the tag from table TagTypes
                        cn.execute("SELECT min(idTagType) FROM TagTypes WHERE TagType = (?) ",(tagType,) )
                        idTagType= [row[0] for row in cn][0]
                        tagTypeDBKeys[tagType] = idTagType
                    else :
                        idTagType = tagTypeDBKeys[tagType]
                            
                    try:
                        cn.execute("INSERT INTO TagContents(idTagType,TagContent) VALUES(%d,'%s')"%(idTagType,value))
                    except Exception,msg:
                        if str(msg)=="columns idTagType, TagContent are not unique":
                            pass
                        else:
                            log( 'EXCEPTION >> tags', LOGDEBUG )
                            log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                            log( "~~~~", LOGDEBUG )
                            log( "", LOGDEBUG )
                    #Then, add the corresponding id of file and id of tag inside the TagsInFiles database
                    try:
                        cn.execute("INSERT INTO TagsInFiles(idTagContent,idFile) SELECT t.idTagContent, %d FROM TagContents t WHERE t.idTagType=%d AND t.TagContent = '%s' "%(idFile,idTagType,value))


                    # At first column was named idTag then idTagContent
                    except Exception,msg:
                        if str(msg)=="table TagsInFiles has no column named idTagContent":
                            try:
                                cn.execute("DROP TABLE TagsInFiles")
                                cn.execute('CREATE TABLE "TagsInFiles" ("idTagContent" INTEGER NOT NULL, "idFile" INTEGER NOT NULL)')

                                cn.execute("INSERT INTO TagsInFiles(idTagContent,idFile) SELECT t.idTagContent, %d FROM TagContents t WHERE t.idTagType=%d AND t.TagContent = '%s' "%(idFile,idTagType,value))
                            except:
                                log("Error while ALTER TABLE TagsInFiles ", LOGDEBUG)
                                log("\t%s - %s"% (Exception,msg), LOGDEBUG )
                        else:
                            log("Error while adding TagsInFiles")
                            log("\t%s - %s"% (Exception,msg) )


    # XMP Person tags
    if dictionnary.has_key("persons"):
        kwl = dictionnary["persons"].split(lists_separator)
        for mot in kwl:
            if mot:
                #First for persons, create an entry for this persons in persons table
                try:
                    cn.execute("""INSERT INTO persons(person) VALUES("%s")"""%mot)
                except Exception,msg:
                    if str(msg)=="column Person is not unique":
                        pass
                    else:
                        log( 'EXCEPTION >> persons', LOGDEBUG )
                        log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                        log( "~~~~", LOGDEBUG )
                        log( "", LOGDEBUG )
                #Then, add the corresponding id of file and id of keyword inside the KeywordsInFiles database
                try:
                    cn.execute("""INSERT INTO personsInFiles(idPerson,idFile) SELECT k.idPerson,f.idFile FROM Persons k, files f WHERE k.person="%s" AND f.strPath="%s" AND f.strFilename="%s";"""%(mot,
                                                                                                                                                                                               path,
                                                                                                                                                                                               filename))
                except Exception,msg:
                    log("Error while adding PersonsInFiles", LOGDEBUG)
                    log("\t%s - %s"% (Exception,msg), LOGDEBUG )



    # TRAITEMENT DES MOTS CLES (base keywords)
    if dictionnary.has_key("keywords"):
        kwl = dictionnary["keywords"].split(lists_separator)
        for mot in kwl:
            if mot: #on ajoute que les mots clés non vides
                #First for keywords, create an entry for this keyword in keywords table
                try:
                    cn.execute("""INSERT INTO keywords(keyword) VALUES("%s")"""%mot)
                except Exception,msg:
                    if str(msg)=="column keyword is not unique":
                        pass
                    else:
                        log( 'EXCEPTION >> keywords', LOGDEBUG )
                        log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                        log( "~~~~", LOGDEBUG )
                        log( "", LOGDEBUG )
                #Then, add the corresponding id of file and id of keyword inside the KeywordsInFiles database
                try:
                    cn.execute("""INSERT INTO KeywordsInFiles(idKW,idFile) SELECT k.idKW,f.idFile FROM keywords k, files f WHERE k.keyword="%s" AND f.strPath="%s" AND f.strFilename="%s";"""%(mot,
                                                                                                                                                                                               path,
                                                                                                                                                                                               filename))

                except Exception,msg:
                    log("Error while adding KeywordsInFiles", LOGDEBUG)
                    log("\t%s - %s"% (Exception,msg), LOGDEBUG )
    # TRAITEMENT DE SUPPLEMENTAL CATEGORY (base Categories)
    if dictionnary.has_key("supplemental category"):
        catl = dictionnary["supplemental category"].split(lists_separator)
        for cat in catl:
            if cat: #to add only category name that are not empty
                #create first an entry for this category in Categories table
                try:
                    cn.execute("""INSERT INTO SupplementalCategories(SupplementalCategory) VALUES("%s")"""%cat)
                except Exception,msg:
                    if str(msg)=="column SupplementalCategory is not unique":
                        pass
                    else:
                        log( 'EXCEPTION >> SupplementalCategory', LOGDEBUG )
                        log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                        log( "~~~~" , LOGDEBUG)
                        log( "", LOGDEBUG )
                #then, add the corresponding id of file and id of category inside the CategoriesInFiles database
                try:
                    cn.execute("""INSERT INTO SupplementalCategoriesInFiles(idSupplementalCategory,idFile) SELECT c.idSupplementalCategory,f.idFile FROM SupplementalCategories c, files f WHERE c.SupplementalCategory="%s" AND f.strPath="%s" AND f.strFilename="%s";"""%(cat,
                                                                                                                                                                                               path,
                                                                                                                                                                                               filename))
                except Exception,msg:
                    log("Error while adding SupplementalCategoriesInFiles", LOGDEBUG)
                    log("\t%s - %s"% (Exception,msg), LOGDEBUG )


    # TRAITEMENT DE CATEGORY (base Categories)

    if dictionnary.has_key("category"):
        if dictionnary["category"]: #to add only category name that are not empty
            #create first an entry for this category in Categories table
            try:
                cn.execute("""INSERT INTO Categories(Category) VALUES("%s")"""%dictionnary["category"])
            except Exception,msg:
                if str(msg)=="column Category is not unique":
                    pass
                else:
                    log( 'EXCEPTION >> Category', LOGDEBUG )
                    log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                    log( "~~~~", LOGDEBUG )
                    log( "", LOGDEBUG )
            #then, add the corresponding id of file and id of category inside the CategoriesInFiles database
            try:
                cn.execute("""INSERT INTO CategoriesInFiles(idCategory,idFile) SELECT c.idCategory,f.idFile FROM Categories c, files f WHERE c.Category="%s" AND f.strPath="%s" AND f.strFilename="%s";"""%(dictionnary["category"],
                                                                                                                                                                                           path,
                                                                                                                                                                                           filename))
            except Exception,msg:
                log("Error while adding CategoriesInFiles", LOGDEBUG)
                log("\t%s - %s"% (Exception,msg), LOGDEBUG )

    # TRAITEMENT DES PAYS (base Country)
    if dictionnary.has_key("country/primary location name"):
        if dictionnary["country/primary location name"]:
            try:
                cn.execute("""INSERT INTO Countries(Country) VALUES("%s")"""%dictionnary["country/primary location name"])
            except Exception,msg:
                if str(msg)=="column Country is not unique":
                    pass
                else:
                    log( 'EXCEPTION >> Country', LOGDEBUG )
                    log( "\t%s - %s"%(Exception,msg), LOGDEBUG )
                    log( "~~~~", LOGDEBUG )
                    log( "", LOGDEBUG )
            try:
                cn.execute("""INSERT INTO CountriesInFiles(idCountry,idFile) SELECT c.idCountry,f.idFile FROM Countries c, files f WHERE c.Country="%s" AND f.strPath="%s" AND f.strFilename="%s";"""%(dictionnary["country/primary location name"],
                                                                                                                                                                                           path,
                                                                                                                                                                                           filename))
            except Exception,msg:
                log("Error while adding CountriesInFiles", LOGDEBUG)
                log("\t%s - %s"% (Exception,msg), LOGDEBUG )

    # TRAITEMENT DES VILLES ( base City)
    if dictionnary.has_key("city"):
        if dictionnary["city"]:
            try:
                cn.execute("""INSERT INTO Cities(City) VALUES("%s")"""%dictionnary["city"])
            except Exception,msg:
                if str(msg)=="column City is not unique":
                    pass
                else:
                    log( 'EXCEPTION >> Country', LOGDEBUG )
                    log( "\%s - %s"%(Exception,msg), LOGDEBUG )
                    log( "~~~~", LOGDEBUG )
                    log( "", LOGDEBUG )
            try:
                cn.execute("""INSERT INTO CitiesInFiles(idCity,idFile) SELECT c.idCity,f.idFile FROM Cities c, files f WHERE c.City="%s" AND f.strPath="%s" AND f.strFilename="%s";"""%(dictionnary["city"],
                                                                                                                                                                                           path,
                                                                                                                                                                                           filename))
            except Exception,msg:
                log("Error while adding CountriesInFiles", LOGDEBUG)
                log("\t%s - %s"% (Exception,msg), LOGDEBUG )
##    # TRAITEMENT DES FOLDERS
##    try:
##        haspic = "1" if True else "0"
##        cn.execute("""INSERT INTO folders(FolderName,ParentFolder,FullPath,HasPics) VALUES (?,?,?,?)""",('nom du dossier',999,path,haspic))
##    except sqlite.IntegrityError:
##        print "ERROR ERROR ERROR !!!"
##        pass
    conn.commit()
    cn.close()
    
    # Set default translation for tag types
    DefaultTagTypesTranslation()

    return True

def DB_folder_insert(foldername,folderpath,parentfolderID,haspic):
    """insert into folders database, the folder name, folder parent, full path and if has pics
        Return the id of the folder inserted"""
    conn = sqlite.connect(pictureDB)
    cn=conn.cursor()
    conn.text_factory = sqlite.OptimizedUnicode
    #insert in the folders database
    try:
        cn.execute("""INSERT INTO folders(FolderName,ParentFolder,FullPath,HasPics) VALUES (?,?,?,?);""",(foldername,parentfolderID,folderpath,haspic))
    except sqlite.IntegrityError:
        pass
    conn.commit()
    #return the id of the folder inserted
    cn.execute("""SELECT idFolder FROM folders where FullPath= ?""",(folderpath,))
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
    
    try:
        import hashlib
        digest = hashlib.md5()
    except ImportError:
        # for Python << 2.5
        import md5
        digest = md5.new()    
        
    filepath = smart_unicode(filepath)
    try:
        try:
            file = open(filepath,'rb')
        except:
            file = open(filepath.encode('utf-8'),'rb')

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
    #print """(SELECT idFile FROM files WHERE strPath="%s" AND strFilename="%s")"""%(filepath,filename)
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
    if not coords: 
        return None
        
    latR,lat,lonR,lon=coords
    tuplat = lat.replace(" ","").replace("[","").replace("]","").split(",")
    tuplon = lon.replace(" ","").replace("[","").replace("]","").split(",")
    lD,lM,lS = lat.replace(" ","").replace("[","").replace("]","").split(",")[:3]
    LD,LM,LS = lon.replace(" ","").replace("[","").replace("]","").split(",")[:3]
    exec("lD=%s"%lD)
    exec("lM=%s"%lM)
    exec("lS=%s"%lS)
    exec("LD=%s"%LD)
    exec("LM=%s"%LM)
    exec("LS=%s"%LS)
    latitude =  (int(lD)+(int(lM)/60.0)+(int(lS)/3600.0)) * (latR=="S" and -1 or 1)
    longitude = (int(LD)+(int(LM)/60.0)+(int(LS)/3600.0)) * (lonR=="W" and -1 or 1)
    return (latitude,longitude)

######################################"
#  Fonctions pour les dossiers racines
######################################"

def RootFolders():
    "return folders which are root for scanning pictures"
    return [row for row in Request( """SELECT path,recursive,remove,exclude FROM Rootpaths ORDER BY path""")]

def AddRoot(path,recursive,remove,exclude):
    "add the path root inside the database. Recursive is 0/1 for recursive scan, remove is 0/1 for removing files that are not physically in the place"
    DB_cleanup_keywords()
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
        #supprime les Categoriesinfiles
        Request( """DELETE FROM CategoriesInFiles WHERE idCategory in (SELECT idCategory FROM CategoriesInFiles WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s'))"""%idchild )
        #supprime les photos de files in collection
        Request( """DELETE FROM FilesInCollections WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s')"""%idchild )
        #2- supprime toutes les images
        cptremoved = cptremoved + Request( """SELECT count(*) FROM files WHERE idFolder='%s'"""%idchild)[0][0]
        Request( """DELETE FROM files WHERE idFolder='%s'"""%idchild)
        #3 - supprime ce sous dossier
        Request( """DELETE FROM folders WHERE idFolder='%s'"""%idchild)
        #supprime les SupplementalCategoriesInFiles
        Request( """DELETE FROM SupplementalCategoriesInFiles WHERE idSupplementalCategory in (SELECT idSupplementalCategory FROM SupplementalCategoriesInFiles WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s'))"""%idchild )
    #4- supprime le dossier
    Request( """DELETE FROM folders WHERE idFolder='%s'"""%idpath)
    #5- supprime les 'périodes' si elles ne contiennent plus de photos (TODO : voir si on supprime les périodes vides ou pas)
    for periodname,datestart,dateend in ListPeriodes():
        if Request( """SELECT count(*) FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN '%s' AND '%s'"""%(datestart,dateend) )[0][0]==0:
            Request( """DELETE FROM Periodes WHERE PeriodeName='%s'"""%periodname )
    DB_cleanup_keywords()
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
                "GPS GPSLatitude",
                "GPS GPSLatitudeRef",
                "GPS GPSLongitude",
                "GPS GPSLongitudeRef",
                "Image DateTime",
                "EXIF DateTimeOriginal",
                "EXIF DateTimeDigitized",
                "EXIF ExifImageWidth",
                "EXIF ExifImageLength",
                "EXIF Flash",

                #
                "Image ResolutionUnit",
                "Image XResolution",
                "Image YResolution",
                "Image Make",
                "EXIF FileSource",
                "EXIF SceneCaptureType",
                "EXIF DigitalZoomRatio",
                "EXIF ExifVersion"
                  ]
    #ouverture du fichier
    try:
        f=open(picfile,"rb")
    except:
        f=open(picfile.encode('utf-8'),"rb")

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
                        log( "Datetime (%s) did not match for '%s' format... trying an other one..."%(tags[tag].__str__(),datetimeformat), LOGDEBUG )
                if not tagvalue:
                    log( "ERROR : the datetime format is not recognize (%s)"%tags[tag].__str__(), LOGDEBUG )

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
                log(">> get_exif %s"%picfile , LOGDEBUG)
                log( "%s - %s"%(Exception,msg), LOGDEBUG )
                log( "~~~~", LOGDEBUG )
                log( "", LOGDEBUG )
    return picentry

        
def get_xmp(dirname, picfile):
    ###############################
    #    getting  XMP   infos     #
    ###############################
   
   
    
    xmpclass = XMP_Tags()
    tags = xmpclass.get_xmp(dirname, picfile)
    
    for k in tags:
        addColumn("files", k)
    
    return tags
    
    tags = xmpclass.get_xmp(dirname, picfile, tagname)
    xmp = {}    
    if tags.has_key(tagname) and tagname == 'MPReg:PersonDisplayName':
        xmp['persons'] = tags[tagname]
        addColumn("files", 'persons')
    elif tags.has_key(tagname):
        xmp[tagname]   = tags[tagname]
        addColumn("files", tagname)
    else:
        xmp[tagname] = ''
    return xmp
    
    



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
                log( "EXCEPTION 1 >> get_iptc %s"%join(path,filename), LOGDEBUG )
                log( "%s - %s"%(Exception,msg), LOGDEBUG )
                log( "~~~~", LOGDEBUG )
                log( "", LOGDEBUG )
                return {}
        else:
            log( "EXCEPTION 2>> get_iptc %s"%join(path,filename), LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "~~~~", LOGDEBUG )
            log( "", LOGDEBUG )
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
                pass
            elif IPTC_FIELDS[k] in ["date created","time created"]:
                pass
            addColumn("files",IPTC_FIELDS[k])
            #print IPTC_FIELDS[k]
            if isinstance(info.data[k],unicode):
                #print "unicode"
                try:
                    #iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode(sys_enc).__str__(),"utf8")
                    iptc[IPTC_FIELDS[k]] = info.data[k]#unicode(info.data[k].encode(sys_enc).__str__(),sys_enc)
                except UnicodeDecodeError:
                    iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode("utf8").__str__(),"utf8")
            elif isinstance(info.data[k],list):
                #print "list"
                iptc[IPTC_FIELDS[k]] = lists_separator.join([i for i in info.data[k]])
            elif isinstance(info.data[k],str):
                #print "str"
                iptc[IPTC_FIELDS[k]] = info.data[k].decode("utf8")
            else:
                #print "other"
                log( "%s,%s"%(path,filename) )
                log( "WARNING : type returned by iptc field is not handled :" )
                log( repr(type(info.data[k])) )
                log( "" )
            #print type(iptc[IPTC_FIELDS[k]])
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
    #log( "SQL > %s"%SQLrequest, LOGINFO)
    conn = sqlite.connect(pictureDB)
    conn.text_factory = unicode #sqlite.OptimizedUnicode
    cn=conn.cursor()
    try:
        cn.execute( SQLrequest )
        conn.commit()
        retour = [row for row in cn]
    except Exception,msg:
        if msg.args[0].startswith("no such column: files.GPS GPSLatitudeRef"):
            pass
        else:
            log( "The request failed :", LOGDEBUG )
            log( "%s - %s"%(Exception,msg), LOGDEBUG )
            log( "---", LOGDEBUG )
        retour= []
    cn.close()
    return retour

def search_filter_tags(FilterInlineArrayTrue, FilterInlineArrayFalse, MatchAll):

    if len(FilterInlineArrayTrue) == 0 and len(FilterInlineArrayFalse) == 0:
        return
        
    FilterInlineArrayTrue = unquote_plus(FilterInlineArrayTrue)
    FilterArrayTrue = FilterInlineArrayTrue.split("|||")

    FilterInlineArrayFalse = unquote_plus(FilterInlineArrayFalse)
    FilterArrayFalse = FilterInlineArrayFalse.split("|||")    
    
    OuterSelect = "SELECT distinct strPath,strFilename FROM FILES WHERE 1=1 "
    # These selects are joined with IN clause
    InnerSelect = "SELECT tif.idfile FROM TagContents tc, TagsInFiles tif , TagTypes tt WHERE tif.idTagContent = tc.idTagContent AND tc.idTagType = tt.idTagType "
    # Build the conditions
    if MatchAll == "1":
        if len(FilterInlineArrayTrue) > 0:
            for Filter in FilterArrayTrue:

                KeyValue = Filter.split("||")
                Key = KeyValue[0]
                Value = KeyValue[1]
                
                Condition = "AND tt.TagTranslation = '"+Key+"' AND tc.TagContent = '"+Value+"' "
                OuterSelect += " AND idFile in ( " + InnerSelect + Condition + " ) "

        if len(FilterInlineArrayFalse) > 0:
            for Filter in FilterArrayFalse:

                KeyValue = Filter.split("||")
                Key = KeyValue[0]
                Value = KeyValue[1]
                
                Condition = "AND tt.TagTranslation = '"+Key+"' AND tc.TagContent = '"+Value+"' "
                OuterSelect += " AND idFile not in ( " + InnerSelect + Condition + " ) "            
                
    else:
        OldKey = ""
        OldValue = ""

        if len(FilterInlineArrayTrue) > 0:        
            for Filter in FilterArrayTrue:

                KeyValue = Filter.split("||")
                Key = KeyValue[0]
                Value = KeyValue[1]
                
                if Key != OldKey:
                    if len(OldKey) > 0:
                        Condition = "AND tt.TagTranslation = '"+OldKey+"' AND tc.TagContent in( "+OldValue+" ) "
                        OuterSelect += " AND idFile in ( " + InnerSelect + Condition + " ) "
                    OldKey = Key
                    OldValue = "'" + Value + "'"
                else:
                    OldValue += ", '" + Value + "'"
            Condition = "AND tt.TagTranslation = '"+OldKey+"' AND tc.TagContent in( "+OldValue+" ) "
            OuterSelect += " AND idFile in ( " + InnerSelect + Condition + " ) "
        
        
        if len(FilterInlineArrayFalse) > 0:
            for Filter in FilterArrayFalse:

                KeyValue = Filter.split("||")
                Key = KeyValue[0]
                Value = KeyValue[1]
                
                if Key != OldKey:
                    if len(OldKey) > 0:
                        Condition = "AND tt.TagTranslation = '"+OldKey+"' AND tc.TagContent in( "+OldValue+" ) "
                        OuterSelect += " AND idFile not in ( " + InnerSelect + Condition + " ) "
                    OldKey = Key
                    OldValue = "'" + Value + "'"
                else:
                    OldValue += ", '" + Value + "'"
                    
            Condition = "AND tt.TagTranslation = '"+OldKey+"' AND tc.TagContent in( "+OldValue+" ) "
            OuterSelect += " AND idFile in ( " + InnerSelect + Condition + " ) "

    return [row for row in Request(OuterSelect)]

def search_tag(tag=None,tagtype='a',limit=-1,offset=-1):
    """Look for given keyword and return the list of pictures.
If tag is not given, pictures with no keywords are returned"""
    if tag is not None: #si le mot clé est fourni
        return [row for row in Request( """SELECT distinct strPath,strFilename FROM files f, TagContents tc, TagsInFiles tif, TagTypes tt WHERE f.idFile = tif.idFile AND tif.idTagContent = tc.idTagContent AND tc.TagContent = '%s' and tc.idTagType = tt.idTagType  and length(trim(tt.TagTranslation))>0 and tt.TagTranslation = '%s' LIMIT %s OFFSET %s"""%(tag.encode("utf8"),tagtype.encode("utf8"),limit,offset))]
    else: #sinon, on retourne toutes les images qui ne sont pas associées à des mots clés
        return [row for row in Request( """SELECT distinct strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM TagsInFiles) LIMIT %s OFFSET %s"""%(limit,offset) )]


def DefaultTagTypesTranslation():
    """Return a list of all keywords in database """
    Request("update TagTypes set TagTranslation = 'State' where TagTranslation =  'Province/state'")
    Request("update TagTypes set TagTranslation = 'State' where TagTranslation =  'Photoshop:State'")
    Request("update TagTypes set TagTranslation = 'City' where TagTranslation = 'Photoshop:City'")
    
    Request("update TagTypes set TagTranslation = 'Country' where TagTranslation =  'Country/primary location name'")
    Request("update TagTypes set TagTranslation = 'Country' where TagTranslation =  'Photoshop:Country'")
    
    Request("update TagTypes set TagTranslation = 'DateCreated' where TagTranslation =  'EXIF DateTimeOriginal'")
    Request("update TagTypes set TagTranslation = 'DateCreated' where TagTranslation =  'Photoshop:DateCreated'")
    Request("update TagTypes set TagTranslation = 'DateCreated' where TagTranslation =  'Image DateTime'")
    
    Request("update TagTypes set TagTranslation = 'Description' where TagTranslation =  'Photoshop:Headline'")
    Request("update TagTypes set TagTranslation = 'Description' where TagTranslation = 'Caption/abstract'")
    Request("update TagTypes set TagTranslation = 'Description' where TagTranslation = 'Dc:description'")
    
    Request("update TagTypes set TagTranslation = 'Creator' where TagTranslation = 'Writer/editor'")
    Request("update TagTypes set TagTranslation = 'Creator' where TagTranslation = 'By-line'")
    Request("update TagTypes set TagTranslation = 'Creator' where TagTranslation = 'Dc:creator'")
    Request("update TagTypes set TagTranslation = 'Creator Title' where TagTranslation = 'By-line title'")
    Request("update TagTypes set TagTranslation = 'Title' where TagTranslation = 'Object name'")
    Request("update TagTypes set TagTranslation = 'Title' where TagTranslation = 'Dc:title'")

    Request("update TagTypes set TagTranslation = 'Copyright' where TagTranslation = 'Dc:rights'")
    Request("update TagTypes set TagTranslation = 'Copyright' where TagTranslation = 'Copyright notice'")
    
    Request("update TagTypes set TagTranslation = 'Label' where TagTranslation =  'Xmp:Label'")
    Request("update TagTypes set TagTranslation = 'Image Rating' where TagTranslation =  'Xmp:Rating'")
    Request("update TagTypes set TagTranslation = 'Location' where TagTranslation =  'Iptc4xmpCore:Location'")
    
    Request("update TagTypes set TagTranslation = 'Keywords' where TagTranslation =  'MicrosoftPhoto:LastKeywordIPTC'")
    Request("update TagTypes set TagTranslation = 'Keywords' where TagTranslation =  'MicrosoftPhoto:LastKeywordXMP'")
    Request("update TagTypes set TagTranslation = 'Keywords' where TagTranslation =  'Dc:subject'")

    Request("update TagTypes set TagTranslation = 'Image Width' where TagTranslation =  'EXIF ExifImageWidth'")
    Request("update TagTypes set TagTranslation = 'Image Length' where TagTranslation =  'EXIF ExifImageLength'")
    Request("update TagTypes set TagTranslation = 'Orientation' where TagTranslation =  'EXIF SceneCaptureType'")
    Request("update TagTypes set TagTranslation = 'Flash' where TagTranslation =  'EXIF Flash'")
    
    # default to not visible
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'EXIF DateTimeDigitized'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'EXIF DigitalZoomRatio'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'EXIF ExifVersion'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'EXIF FileSource'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'Image Orientation'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'Image ResolutionUnit'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'Image XResolution'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'Image YResolution'")
    
    #Request("delete from TagTypes where idTagType not in (select distinct idTagType from TagContents)")
    
def list_TagTypes():
    DefaultTagTypesTranslation()
    return [row for (row,) in Request( """SELECT distinct TagTranslation FROM TagTypes where length(trim(TagTranslation))>0 ORDER BY LOWER(TagTranslation) ASC""" )]

def countTagTypes(kw,limit=-1,offset=-1):
    if kw is not None:
        return Request("""SELECT count(distinct TagContent) FROM tagsInFiles tif, TagContents tc, TagTypes tt WHERE tif.idTagContent = tc.idTagContent AND tc.idTagType = tt.idTagType and length(trim(tt.TagTranslation))>0 and tt.TagTranslation ='%s' """%kw.encode("utf8"))[0][0]
    else:
        return Request("""SELECT count(*) FROM TagTypes where length(trim(TagTranslation))>0""" )[0][0]
        
def setTranslatedTagType(TagType, TagTranslation):
    Request("Update TagTypes set TagTranslation = '%s' where TagType = '%s'"%(TagTranslation.encode('utf-8'), TagType.encode('utf-8')))
    
def getTagTypesForTranslation():
    return [row for row in Request('select TagType, TagTranslation from TagTypes order by 2,1')]

def list_Tags(tagType):
    """Return a list of all keywords in database"""
    return [row for (row,) in Request( """select distinct TagContent from TagContents tc, TagsInFiles tif, TagTypes tt  where tc.idTagContent = tif.idTagContent and tc.idTagType = tt.idTagType and tt.TagTranslation='%s' ORDER BY LOWER(TagContent) ASC"""%tagType.encode("utf8") )]

def countTags(kw,tagType, limit=-1,offset=-1):
    if kw is not None:
        return Request("""select count(distinct idFile) from  TagContents tc, TagsInFiles tif, TagTypes tt  where tc.idTagContent = tif.idTagContent and tc.TagContent = '%s' and tc.idTagType = tt.idTagType and tt.TagTranslation = '%s'"""%(kw.encode("utf8"), tagType.encode("utf8")))[0][0]
    else:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM TagsInFiles)""" )[0][0]


####
def search_person(person=None,limit=-1,offset=-1):
    """Look for given person and return the list of pictures.
If person is not given, pictures with no person are returned"""
    if person is not None: #si le mot clé est fourni
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT idFile FROM PersonsInFiles WHERE idPerson =(SELECT max(idPerson) FROM persons WHERE person="%s")) LIMIT %s OFFSET %s"""%(person.encode("utf8"),limit,offset))]
    else: #sinon, on retourne toutes les images qui ne sont pas associées à des mots clés
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM PersonsInFiles) LIMIT %s OFFSET %s"""%(limit,offset) )]

def list_person():
    """Return a list of all persons in database"""
    return [row for (row,) in Request( """SELECT person FROM persons ORDER BY LOWER(person) ASC""" )]

def count_person(person,limit=-1,offset=-1):
    if person is not None:
        return Request("""SELECT count(*) FROM files WHERE idFile in (SELECT idFile FROM PersonsInFiles WHERE idPerson =(SELECT idPerson FROM persons WHERE person="%s"))"""%person.encode("utf8"))[0][0]
    else:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM PersonsInFiles)""" )[0][0]

####

def search_keyword(kw=None,limit=-1,offset=-1):
    """Look for given keyword and return the list of pictures.
If keyword is not given, pictures with no keywords are returned"""
    if kw is not None: #si le mot clé est fourni
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT idFile FROM KeywordsInFiles WHERE idKW =(SELECT idKW FROM keywords WHERE keyword="%s")) LIMIT %s OFFSET %s"""%(kw.encode("utf8"),limit,offset))]
    else: #sinon, on retourne toutes les images qui ne sont pas associées à des mots clés
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM KeywordsInFiles) LIMIT %s OFFSET %s"""%(limit,offset) )]

def list_KW():
    """Return a list of all keywords in database"""
    return [row for (row,) in Request( """SELECT keyword FROM keywords ORDER BY LOWER(keyword) ASC""" )]

def countKW(kw,limit=-1,offset=-1):
    if kw is not None:
        return Request("""SELECT count(*) FROM files WHERE idFile in (SELECT idFile FROM KeywordsInFiles WHERE idKW =(SELECT idKW FROM keywords WHERE keyword="%s"))"""%kw.encode("utf8"))[0][0]
    else:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM KeywordsInFiles)""" )[0][0]

### MDB
def search_category(p_category=None):
    if p_category is not None:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT idFile FROM CategoriesInFiles WHERE idCategory =(SELECT idCategory FROM Categories WHERE Category="%s"))"""%p_category.encode("utf8"))]
    else:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM CategoriesInFiles)""" )]

def list_category():
    return [row for (row,) in Request( """SELECT Category FROM Categories ORDER BY LOWER(Category) ASC""" )]

def count_category(p_category):
    if p_category is not None:
        return Request("""SELECT count(*) FROM CategoriesInFiles WHERE idCategory =(SELECT idCategory FROM Categories WHERE Category="%s")"""%p_category.encode("utf8"))[0][0]
    else:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM CategoriesInFiles)""" )[0][0]

def search_supplementalcategory(p_supplementalcategory=None):
    if p_supplementalcategory is not None:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT idFile FROM SupplementalCategoriesInFiles WHERE idSupplementalCategory =(SELECT idSupplementalCategory FROM SupplementalCategories WHERE SupplementalCategory="%s"))"""%p_supplementalcategory.encode("utf8"))]
    else:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM SupplementalCategoriesInFiles)""" )]

def list_supplementalcategory():
    return [row for (row,) in Request( """SELECT SupplementalCategory FROM SupplementalCategories ORDER BY LOWER(SupplementalCategory) ASC""" )]

def count_supplementalcategory(p_supplementalcategory):
    if p_supplementalcategory is not None:
        return Request("""SELECT count(*) FROM SupplementalCategoriesInFiles WHERE idSupplementalCategory =(SELECT idSupplementalCategory FROM SupplementalCategories WHERE SupplementalCategory="%s")"""%p_supplementalcategory.encode("utf8"))[0][0]
    else:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM SupplementalCategoriesInFiles)""" )[0][0]

def list_country_old(): #USELESS ?
    return [row for (row,) in Request( """SELECT Country FROM Countries ORDER BY LOWER(Country) ASC""" )]

def list_country():
    return [row for row in Request( """SELECT ifnull("country/primary location name",""), count(*) FROM files  GROUP BY "country/primary location name"  ;""" )]

def search_country(p_country=None):
    if p_country is None:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM CountriesInFiles)""" )]
    else:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT idFile FROM CountriesInFiles WHERE idCountry =(SELECT idCountry FROM Countries WHERE Country="%s"))"""%p_country.encode("utf8"))]

def count_country(p_country): #USELESS ?
    if p_country is None:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM CountriesInFiles)""" )[0][0]
    else:
        return Request("""SELECT count(*) FROM CountriesInFiles WHERE idCountry=(SELECT idCountry FROM Countries WHERE Country="%s")"""%p_country.encode("utf8"))[0][0]

def list_city_old(): #USELESS ?
    return [row for (row,) in Request( """SELECT City FROM Cities ORDER BY LOWER(City) ASC""" )]

def list_city(country=None):
    if not country:
        return [row for row in Request( """SELECT ifnull(City,""), count(*) from files  GROUP BY city""" )]
    else:
        return [row for row in Request( """SELECT ifnull(City,""), count(*) from files where "country/primary location name" = "%s" GROUP BY city"""%country.encode("utf8") )]


def search_city4country(country,city=""):
    #if not country and not city (shouldn't happen) : display all pics
    #if not country but city (shouldn't happen)
    #if not city but country : show all pics for this country
    if city: citystmt = """ AND City = "%s" ORDER BY City ASC"""%city.encode("utf8")
    else: citystmt = """ AND City is Null or City = "" """
    return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE "country/primary location name" = "%s"%s"""%(country.encode("utf8"),citystmt))]

def search_city(p_city=None):
    if p_city is None:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM CitiesInFiles)""" )]
    else:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE idFile in (SELECT idFile FROM CitiesInFiles WHERE idCity =(SELECT idCity FROM Cities WHERE City="%s"))"""%p_city.encode("utf8"))]

def count_city(p_city):
    if p_city is None:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM CitiesInFiles)""" )[0][0]
    else:
        return Request("""SELECT count(*) FROM CitiesInFiles WHERE idCity=(SELECT idCity FROM Cities WHERE City="%s")"""%p_city.encode("utf8"))[0][0]


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
    #print periodtype,date
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
    
    print "Start"
    log("sadkfjask")
    
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


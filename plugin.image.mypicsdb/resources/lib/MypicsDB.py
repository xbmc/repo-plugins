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
from traceback import print_exc

import  xbmcaddon, xbmc
from XMP import XMP_Tags
import CharsetDecoder as decoder

from time import strftime,strptime

#base de donnée SQLITE
try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite
    pass



Addon = xbmcaddon.Addon(id='plugin.image.mypicsdb')
home = Addon.getAddonInfo('path')

#these few lines are taken from AppleMovieTrailers script
# Shared resources
BASE_RESOURCE_PATH = join( home, "resources" )
DATA_PATH = Addon.getAddonInfo('profile')
DB_PATH = xbmc.translatePath( "special://database/")
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
# append the proper platforms folder to our path, xbox is the same as win32
env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )

DEBUGGING = True

global pictureDB
pictureDB = join(DB_PATH,"MyPictures.db")
sys_enc = sys.getfilesystemencoding()

lists_separator = "||"

class MyPictureDB(Exception):
    pass


LOGDEBUG = 0
LOGINFO = 1
LOGNOTICE = 2
LOGWARNING = 3
LOGERROR = 4
LOGSEVERE = 5
LOGFATAL = 6
LOGNONE = 7

def log(msg, level=LOGDEBUG):

    if type(msg).__name__=="unicode":
        msg = msg.encode("utf-8")
    if DEBUGGING:
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

def CreateMissingIndexes(cn, strVersion):    
    try:
        cn.execute("drop index idxFiles")
    except:
        pass
    try:
        cn.execute("create index idxFiles1 on Files(idFile, idFolder)")
    except:
        pass
    try:
        cn.execute("CREATE INDEX idxFolders1 ON Folders(idFolder)")
    except:
        pass
    try:
        cn.execute("CREATE INDEX idxFolders2 ON Folders(ParentFolder)")
    except:
        pass
                    
def VersionTable():
    #table 'Version'
    conn = sqlite.connect(pictureDB)
    conn.text_factory = unicode #sqlite.OptimizedUnicode
    cn=conn.cursor()
  
    try:    
        cn.execute("CREATE TABLE DBVersion ( strVersion text primary key  )")
        cn.execute("insert into DBVersion (strVersion) values('1.2.7')")
        # Cause the table didn't exist the DB version is max 1.1.9
        CreateMissingIndexes(cn, '1.1.9')
        conn.commit() 
    except Exception,msg:
        if msg.args[0].startswith("table DBVersion already exists"):
            # Test Version of DB
            strVersion = Request("Select strVersion from DBVersion")[0][0];
            if strVersion == '1.1.9':
            # create missing indexes:
                try:
                    CreateMissingIndexes(cn, '1.1.9')
                    cn.execute("Update DBVersion set strVersion = '1.2.7'")
                    strVersion = '1.2.7'
                    conn.commit() 
                except Exception,msg:
                    log( "MyPicsDB database version could not be updated. ", LOGERROR )

            log( "MyPicsDB database version is %s"%str(strVersion), LOGDEBUG )
            
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> VersionTable - CREATE TABLE DBVersion ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )
    cn.close()
            
def Make_new_base(DBpath,ecrase=True):
##    if not(isfile(DBpath)):
##        f=open("DBpath","w")
##        f.close()
    log( "Creating a new picture database\n%s\n"%DBpath)
    conn = sqlite.connect(DBpath)
    cn=conn.cursor()
    if ecrase:
        #drop table
        for table in ['Persons', 'PersonsInFiles', 'tags', 'TagContent', 'TagContents', 'TagsInFiles', 'TagTypes',"files","keywords","folders","KeywordsInFiles","Collections","FilesInCollections","Periodes","CategoriesInFiles","Categories","SupplementalCategoriesInFiles","SupplementalCategories","CitiesInFiles","Cities","CountriesInFiles","Countries","DBVersion"]:
            try:
                cn.execute("""DROP TABLE %s"""%table)
            except Exception,msg:
                log( ">>> Make_new_base - DROP TABLE %s"%table, LOGERROR )
                log( "%s - %s"%(Exception,msg), LOGERROR )


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
            log( ">>> Make_new_base - CREATE TABLE files ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )

    #table 'folders'
    try:
        cn.execute("""CREATE TABLE "folders" ("idFolder" INTEGER  primary key not null, "FolderName" TEXT, "ParentFolder" INTEGER, "FullPath" TEXT UNIQUE,"HasPics" INTEGER);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'folders' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE folders ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )
    #table 'Collections'
    try:
        cn.execute("""CREATE TABLE "Collections" ("idCol" INTEGER PRIMARY KEY, "CollectionName" TEXT UNIQUE);""")
    except Exception,msg:
        if msg.args[0].startswith("table 'Collections' already exists"):
            #cette exception survient lorsque la table existe déjà.
            #   elle n'est pas une erreur, on la passe
            pass
        else: #sinon on imprime l'exception levée pour la traiter
            log( ">>> Make_new_base - CREATE TABLE Collections ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )
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
            log( ">>> Make_new_base - CREATE TABLE FilesInCollections ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )
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
            log( ">>> Make_new_base - CREATE TABLE Periodes ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )
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
            log( ">>> Make_new_base - CREATE TABLE Rootpaths ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )


    #table 'TagTypes'
    try:
        cn.execute("""CREATE TABLE "TagTypes" ("idTagType" INTEGER NOT NULL primary key, "TagType" TEXT, "TagTranslation" TEXT, CONSTRAINT UNI_TAG UNIQUE("TagType") )""")
    except Exception,msg:
        if msg.args[0].startswith("table 'TagTypes' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Tags ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )

    #table 'TagContent'
    try:
        cn.execute("""CREATE TABLE "TagContents" ("idTagContent" INTEGER NOT NULL primary key, "idTagType" INTEGER, "TagContent" TEXT, CONSTRAINT UNI_TAG UNIQUE("idTagType", "TagContent") )""")
    except Exception,msg:
        if msg.args[0].startswith("table 'TagContents' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE Tags ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )

    #table 'TagsInFiles'
    try:
        cn.execute("""CREATE TABLE "TagsInFiles" ("idTagContent" INTEGER NOT NULL, "idFile" INTEGER NOT NULL)""")
    except Exception,msg:
        if msg.args[0].startswith("table 'TagsInFiles' already exists"):
            pass
        else:
            log( ">>> Make_new_base - CREATE TABLE TagsInFiles ...", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )


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
        cn.execute("CREATE INDEX idxFolders1 ON Folders(idFolder)")
        cn.execute("CREATE INDEX idxFolders2 ON Folders(ParentFolder)")
    except Exception,msg:
        pass

    try:
        cn.execute("CREATE INDEX idxFiles1 ON Files(idFile, idFolder)")
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
                log( 'EXCEPTION >> addColums %s,%s,%s'%(table,colheader,format), LOGERROR )
                log( "\t%s - %s"%(Exception,msg), LOGERROR )

        conn.commit()
        cn.close()
        columnList.append(key)

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

        cn.execute('delete from files where sha is null')
        #cn.execute('delete from folders where haspics = 0')
        #cn.execute('delete from folders where idFolder not in (select idFolder from Files)')
        cn.execute('delete from files where idFolder not in( select idFolder from folders)')

        #cn.execute( "delete from keywordsInFiles where idFile not in(select idFile from Files )")
        #cn.execute( "delete from keywords where idKW not in (select idKW from keywordsInFiles)")
        #cn.execute( "delete from categoriesInFiles where idFile not in(select idFile from Files )")
        #cn.execute( "delete from Categories where idCategory not in (select idCategory from categoriesInFiles)")
        #cn.execute( "delete from supplementalCategoriesInFiles where idFile not in(select idFile from Files )")
        #cn.execute( "delete from SupplementalCategories where idSupplementalCategory not in (select idSupplementalCategory from supplementalCategoriesInFiles)")
        #cn.execute( "delete from countriesInFiles where idFile not in(select idFile from Files )")
        #cn.execute( "delete from Countries where idCountry not in (select idCountry from countriesInFiles)")
        #cn.execute( "delete from citiesInFiles where idFile not in(select idFile from Files )")
        #cn.execute( "delete from Cities where idCity not in (select idCity from citiesInFiles)")
        #cn.execute( "delete from personsInFiles where idFile not in(select idFile from Files )")
        #cn.execute( "delete from Persons where idPerson not in (select idPerson from personsInFiles)")

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
        log( "EXCEPTION >> DB_exists %s,%s"%(picpath,picfile), LOGERROR )
        log( "\t%s - %s"%(Exception,msg), LOGERROR )
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
    
    try:
        cn.execute( """SELECT f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND p.FullPath=(?)""",(path,))
    except Exception,msg:
        log( "ERROR : DB_listdir ...", LOGERROR )
        log( "DB_listdir(%s)"%path, LOGERROR )
        log( "%s - %s"%(Exception,msg), LOGERROR )
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
            RequestWithBinds(""" DELETE FROM files WHERE idFolder = (SELECT idFolder FROM folders WHERE FullPath=?) AND strFilename=? """,(path,filename))
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
        log( ">>> DB_file_insert ...", LOGERROR )
        log(decoder.smart_unicode(filename).encode('utf-8'), LOGERROR)
        log( "%s - %s"%(Exception,msg), LOGERROR )
        log( """INSERT INTO files('%s') values (%s)""" % ( "','".join(dictionnary.keys()) , ",".join(["?"]*len(dictionnary.values())) ), LOGERROR )
        log( "", LOGERROR )
        conn.commit()
        cn.close()
        raise MyPictureDB


    # meta table inserts
    cn.execute("SELECT idFile FROM files WHERE strPath = ? AND strFilename = ?",(path,filename,) )
    idFile = [row[0] for row in cn][0]

    # loop over tags dictionary
    for tagType, value in dictionnary.iteritems():

        if isinstance(value, basestring) and dictionnary[tagType]:

            # exclude the following tags
            if tagType not in ['sha', 'strFilename', 'strPath',
                               'mtime', 'ftype',
                               'source', 'urgency', 'time created', 'date created']:
                
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
                            cn.execute(""" INSERT INTO TagTypes(TagType, TagTranslation) VALUES(?, ?) """,(tagType,tagType))
                        except Exception,msg:
                            if str(msg)=="column TagType is not unique":
                                pass
                            else:
                                log( 'EXCEPTION >> tags', LOGERROR )
                                log( 'tagType = %s'%tagType, LOGERROR )
                                log( "\t%s - %s"%(Exception,msg), LOGERROR )

                         # select the key of the tag from table TagTypes
                        cn.execute("SELECT min(idTagType) FROM TagTypes WHERE TagType = ? ",(tagType,) )
                        idTagType= [row[0] for row in cn][0]
                        tagTypeDBKeys[tagType] = idTagType
                    else :
                        idTagType = tagTypeDBKeys[tagType]
                            
                    try:
                        cn.execute(""" INSERT INTO TagContents(idTagType,TagContent) VALUES(?,?) """,(idTagType,value))
                    except Exception,msg:
                        if str(msg)=="columns idTagType, TagContent are not unique":
                            pass
                        else:
                            log( 'EXCEPTION >> tags', LOGERROR )
                            log( 'tagType = %s'%tagType, LOGERROR )
                            log( 'tagValue = %s'%decoder.smart_utf8(value), LOGERROR )
                            log( "\t%s - %s"%(Exception,msg), LOGERROR )
                            log( "~~~~", LOGERROR )
                            log( "", LOGERROR )

                    # this block should be obsolet now!!!

                    #Then, add the corresponding id of file and id of tag inside the TagsInFiles database
                    try:
                        cn.execute(""" INSERT INTO TagsInFiles(idTagContent,idFile) SELECT t.idTagContent, %d FROM TagContents t WHERE t.idTagType=%d AND t.TagContent = ? """%(idFile,idTagType), (value,))


                    # At first column was named idTag then idTagContent
                    except Exception,msg:
                        if str(msg)=="table TagsInFiles has no column named idTagContent":
                            try:
                                cn.execute("DROP TABLE TagsInFiles")
                                cn.execute('CREATE TABLE "TagsInFiles" ("idTagContent" INTEGER NOT NULL, "idFile" INTEGER NOT NULL)')

                                cn.execute(""" INSERT INTO TagsInFiles(idTagContent,idFile) SELECT t.idTagContent, %d FROM TagContents t WHERE t.idTagType=%d AND t.TagContent = ? """%(idFile,idTagType), (value,))
                            except:
                                log("Error while ALTER TABLE TagsInFiles ", LOGERROR)
                                log("\t%s - %s"% (Exception,msg), LOGERROR )
                        else:
                            log("Error while adding TagsInFiles")
                            log("\t%s - %s"% (Exception,msg) )
                            log("%s %s - %s"%(idFile,idTagType,decoder.smart_utf8(value)))
                            #print """ INSERT INTO TagsInFiles(idTagContent,idFile) SELECT t.idTagContent, %d FROM TagContents t WHERE t.idTagType=%d AND t.TagContent = '%s' """%(idFile,idTagType,value)




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
        cn.execute("""INSERT INTO folders(FolderName,ParentFolder,FullPath,HasPics) VALUES (?,?,?,?) """,(foldername,parentfolderID,folderpath,haspic))
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

def get_children(folderid):
    """search all children folders ids for the given folder id"""
    childrens=[c[0] for c in RequestWithBinds("SELECT idFolder FROM folders WHERE ParentFolder=? ", (folderid,))]
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
        #print """DELETE FROM files WHERE idFolder = (SELECT idFolder FROM folders WHERE FullPath="%s") AND strFilename="%s" """%(picpath,picfile)
        RequestWithBinds("""DELETE FROM files WHERE idFolder = (SELECT idFolder FROM folders WHERE FullPath=?) AND strFilename=? """,(picpath,picfile))

    else:

        try:
            if picpath:
                idpath = RequestWithBinds("""SELECT idFolder FROM folders WHERE FullPath = ? """, (picpath,))[0][0]#le premier du tuple à un élément
            else:
                idpath = Request("""SELECT idFolder FROM folders WHERE FullPath is null""")[0][0]#le premier du tuple à un élément

            log( "DB_del_pic(%s,%s)"%( decoder.smart_utf8(picpath),decoder.smart_utf8(picfile)), LOGDEBUG )

            deletelist=[]#va lister les id des dossiers à supprimer
            deletelist.append(idpath)#le dossier en paramètres est aussi à supprimer
            deletelist.extend(get_children(str(idpath)))#on ajoute tous les enfants en sous enfants du dossier

            Request( """DELETE FROM files WHERE idFolder in ("%s")"""%""" "," """.join([str(i) for i in deletelist]) )
            Request( """DELETE FROM folders WHERE idFolder in ("%s") """%""" "," """.join([str(i) for i in deletelist]) )
        except:
            pass

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
        
    filepath = decoder.smart_unicode(filepath)
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
        return [row for row in RequestWithBinds( """select sha from files where strPath=? and strFilename=? """,(path,filename))][0][0]
    except:
        return "0"

def getFileMtime(path,filename):   
    #return the modification time 'mtime' in DB for the given picture
    return [row for row in RequestWithBinds( """select mtime from files where strPath=? and strFilename=? """%(path,filename))][0][0]

def DB_deltree(picpath):
    pass

def getRating(path,filename):   
    try:
        return [row for row in RequestWithBinds( """SELECT files."Image Rating" FROM files WHERE strPath=? AND strFilename=? """, (path,filename) )][0][0]
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
        RequestWithBinds( """INSERT INTO Collections(CollectionName) VALUES (?) """,(Colname, ))
    else:
        log( """NewCollection : User did not specify a name for the collection.""")
def delCollection(Colname):      
    """delete a collection"""
    if Colname:
        RequestWithBinds( """DELETE FROM FilesInCollections WHERE idCol=(SELECT idCol FROM Collections WHERE CollectionName=?)""", (Colname,))
        RequestWithBinds( """DELETE FROM Collections WHERE CollectionName=? """,(Colname,) )
    else:
        log( """delCollection : User did not specify a name for the collection""" )
        
def getCollectionPics(Colname):      
    """List all pics associated to the Collection given as Colname"""
    return [row for row in RequestWithBinds( """SELECT strPath,strFilename FROM Files WHERE idFile IN (SELECT idFile FROM FilesInCollections WHERE idCol IN (SELECT idCol FROM Collections WHERE CollectionName=?)) ORDER BY "EXIF DateTimeOriginal" ASC""",(Colname,))]

def renCollection(Colname,newname):   
    """rename give collection"""
    if Colname:
        RequestWithBinds( """UPDATE Collections SET CollectionName = ? WHERE CollectionName=? """, (newname,Colname) )
    else:
        log( """renCollection : User did not specify a name for the collection""")

def addPicToCollection(Colname,filepath,filename):    

    #cette requête ne vérifie pas si :
    #   1- le nom de la collection existe dans la table Collections
    #   2- si l'image est bien une image en base de donnée Files
    #ces points sont solutionnés partiellement car les champs ne peuvent être NULL
    #   3- l'association idCol et idFile peut apparaitre plusieurs fois...
    #print """(SELECT idFile FROM files WHERE strPath="%s" AND strFilename="%s")"""%(filepath,filename)
    RequestWithBinds( """INSERT INTO FilesInCollections(idCol,idFile) VALUES ( (SELECT idCol FROM Collections WHERE CollectionName=?) , (SELECT idFile FROM files WHERE strPath=? AND strFilename=?) )""",(Colname,filepath,filename) )

def delPicFromCollection(Colname,filepath,filename):
    RequestWithBinds( """DELETE FROM FilesInCollections WHERE idCol=(SELECT idCol FROM Collections WHERE CollectionName=?) AND idFile=(SELECT idFile FROM files WHERE strPath=? AND strFilename=?)""",(Colname,filepath,filename) )

####################
# Periodes functions
#####################
def ListPeriodes():
    """List all periodes"""
    return [row for row in Request( """SELECT PeriodeName,DateStart,DateEnd FROM Periodes""")]

def addPeriode(periodname,datestart,dateend):
    #datestart et dateend doivent être au format string ex.: "datetime('2009-07-12')" ou "strftime('%Y',now)"
    RequestWithBinds( """INSERT INTO Periodes(PeriodeName,DateStart,DateEnd) VALUES (?,%s,%s)"""%(datestart,dateend), (periodname,) )
    return

def delPeriode(periodname):
    RequestWithBinds( """DELETE FROM Periodes WHERE PeriodeName=? """,(periodname,) )
    return

def renPeriode(periodname,newname,newdatestart,newdateend):

    RequestWithBinds( """UPDATE Periodes SET PeriodeName = ?,DateStart = datetime(?) , DateEnd = datetime(?) WHERE PeriodeName=? """,(newname,newdatestart,newdateend,periodname) )
    return

def PicsForPeriode(periodname):    
    """Get pics for the given period name"""
    period = RequestWithBinds( """SELECT DateStart,DateEnd FROM Periodes WHERE PeriodeName=?""", (periodname,) )
    return [row for row in RequestWithBinds( """SELECT strPath,strFilename FROM files WHERE datetime("EXIF DateTimeOriginal") BETWEEN ? AND ? ORDER BY "EXIF DateTimeOriginal" ASC""",period )]

def Searchfiles(column,searchterm,count=False):
    searchterm = searchterm.replace("'", "''")      

    if count:
        return [row for row in Request( """SELECT count(*) FROM files WHERE files.'%s' LIKE "%%%s%%";"""%(column,searchterm))][0][0]
    else:
        return [row for row in Request( """SELECT strPath,strFilename FROM files WHERE files.'%s' LIKE "%%%s%%";"""%(column,searchterm))]
###
def getGPS(filepath,filename):
    coords = RequestWithBinds( """SELECT files.'GPS GPSLatitudeRef',files.'GPS GPSLatitude' as lat,files.'GPS GPSLongitudeRef',files.'GPS GPSLongitude' as lon FROM files WHERE lat NOT NULL AND lon NOT NULL AND strPath=? AND strFilename=?""",(filepath,filename) )
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
    RequestWithBinds( """INSERT INTO Rootpaths(path,recursive,remove,exclude) VALUES (?,?,?,?)""",(decoder.smart_unicode(path),recursive,remove,exclude) )

def getRoot(path):
    #print decoder.smart_utf8(path)
    return [row for row in RequestWithBinds( """SELECT path,recursive,remove,exclude FROM Rootpaths WHERE path=? """, (decoder.smart_unicode(path),) )][0]


def RemoveRoot(path):
    "remove the given rootpath, remove pics from this path, ..."
    #first remove the path with all its pictures / subfolders / keywords / pictures in collections...
    RemovePath(path)
    #then remove the rootpath itself
    RequestWithBinds( """DELETE FROM Rootpaths WHERE path=? """, (decoder.smart_unicode(path),) )


def RemovePath(path):
    "remove the given rootpath, remove pics from this path, ..."
    cptremoved = 0
    #récupère l'id de ce chemin
    try:
        idpath = RequestWithBinds( """SELECT idFolder FROM folders WHERE FullPath = ?""",(decoder.smart_unicode(path),) )[0][0]
    except:
        #le chemin n'est sans doute plus en base
        return 0
    #1- supprime les images situées directement sous la racine du chemin à supprimer
    cptremoved = Request( """SELECT count(*) FROM files WHERE idFolder='%s'"""%idpath )[0][0]
    Request( """DELETE FROM files WHERE idFolder='%s'"""%idpath)
    #parcours tous les sous dossiers
    for idchild in all_children(idpath):
        #supprime les keywordsinfiles
        #Request( """DELETE FROM KeywordsInFiles WHERE idKW in (SELECT idKW FROM KeywordsInFiles WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s'))"""%idchild )
        #supprime les Categoriesinfiles
        #Request( """DELETE FROM CategoriesInFiles WHERE idCategory in (SELECT idCategory FROM CategoriesInFiles WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s'))"""%idchild )
        #supprime les photos de files in collection
        Request( """DELETE FROM FilesInCollections WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s')"""%idchild )
        #2- supprime toutes les images
        cptremoved = cptremoved + Request( """SELECT count(*) FROM files WHERE idFolder='%s'"""%idchild)[0][0]
        Request( """DELETE FROM files WHERE idFolder='%s'"""%idchild)
        #3 - supprime ce sous dossier
        Request( """DELETE FROM folders WHERE idFolder='%s'"""%idchild)
        #supprime les SupplementalCategoriesInFiles
        #Request( """DELETE FROM SupplementalCategoriesInFiles WHERE idSupplementalCategory in (SELECT idSupplementalCategory FROM SupplementalCategoriesInFiles WHERE idFile in (SELECT idFile FROM files WHERE idFolder='%s'))"""%idchild )
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
                        log( "Datetime (%s) did not match for '%s' format... trying an other one..."%(tags[tag].__str__(),datetimeformat), LOGERROR )
                if not tagvalue:
                    log( "ERROR : the datetime format is not recognize (%s)"%tags[tag].__str__(), LOGERROR )

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
                log(">> get_exif %s"%picfile , LOGERROR)
                log( "%s - %s"%(Exception,msg), LOGERROR )
                log( "~~~~", LOGERROR )
                log( "", LOGERROR )
    return picentry

        
def get_xmp(dirname, picfile):
    ###############################
    #    getting  XMP   infos     #
    ###############################
   
   
    
    xmpclass = XMP_Tags()
    tags = xmpclass.get_xmp(dirname, picfile)
    
    for tagname in tags:
        if tagname == 'Iptc4xmpExt:PersonInImage':
            key = 'persons'
            
            if tags.has_key(key):
                tags[key] += '||' + tags[tagname]
            else:
                tags[key] = tags[tagname]
                MPDB.addColumn("files", key)
        else:           
            addColumn("files", tagname)
    if tags.has_key('Iptc4xmpExt:PersonInImage'):
        del(tags['Iptc4xmpExt:PersonInImage'])
    return tags


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
    
    if len(info.data) < 4:
        return iptc

        
    for k in info.data.keys():
        if k in IPTC_FIELDS:
            #if IPTC_FIELDS[k] in ["supplemental category","keywords","contact"]:
            #    pass
            #elif IPTC_FIELDS[k] in ["date created","time created"]:
            #    pass
            addColumn("files",IPTC_FIELDS[k])

            if isinstance(info.data[k],unicode):

                try:
                    #iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode(sys_enc).__str__(),"utf8")
                    iptc[IPTC_FIELDS[k]] = info.data[k]#unicode(info.data[k].encode(sys_enc).__str__(),sys_enc)
                except UnicodeDecodeError:
                    iptc[IPTC_FIELDS[k]] = unicode(info.data[k].encode("utf8").__str__(),"utf8")
            elif isinstance(info.data[k],list):

                iptc[IPTC_FIELDS[k]] = lists_separator.join([i for i in info.data[k]])
            elif isinstance(info.data[k],str):

                iptc[IPTC_FIELDS[k]] = info.data[k].decode("utf8")
            else:

                log( "%s,%s"%(path,filename) )
                log( "WARNING : type returned by iptc field is not handled :" )
                log( repr(type(info.data[k])) )
                log( "" )

        else:
            log("IPTC problem with file: %s"%join(path,filename), LOGERROR)
            try:
                log( " '%s' IPTC field is not handled. Data for this field : \n%s"%(k,info.data[k][:80]) , LOGERROR)
            except:
                log( " '%s' IPTC field is not handled (unreadable data for this field)"%k , LOGERROR)
            log( "IPTC data for picture %s will be ignored"%filename , LOGERROR)
            ipt = {}
            return ipt

    return iptc

def MakeRequest(field,comparator,value):
    return Request( """SELECT p.FullPath,f.strFilename FROM files f,folders p WHERE f.idFolder=p.idFolder AND %s %s %s """%(field,comparator,value))

def get_fields(table="files"):
    tableinfo = Request( """pragma table_info("%s")"""%table)
    return [(name,typ) for cid,name,typ,notnull,dflt_value,pk in tableinfo]

def Request(SQLrequest):
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
            log( "The request failed :", LOGERROR )
            log( "%s - %s"%(Exception,msg), LOGERROR )
            log( "SQL Request> %s"%SQLrequest, LOGERROR)
            log( "---", LOGERROR )
        retour= []
    cn.close()
    return retour

    
def RequestWithBinds(SQLrequest, bindVariablesOrg):
    conn = sqlite.connect(pictureDB)
    conn.text_factory = unicode #sqlite.OptimizedUnicode
    cn=conn.cursor()
    bindVariables = []
    for value in bindVariablesOrg:
        if type(value) == type('str'):
            bindVariables.append(decoder.smart_unicode(value))
        else:
            bindVariables.append(value)
    try:
        cn.execute( SQLrequest, bindVariables )
        conn.commit()
        retour = [row for row in cn]
    except Exception,msg:
        if msg.args[0].startswith("no such column: files.GPS GPSLatitudeRef"):
            pass
        else:
            try:
                log( "The request failed :", LOGERROR )
                log( "%s - %s"%(Exception,msg), LOGERROR )
                log( "SQL RequestWithBinds > %s"%SQLrequest, LOGERROR)
                i = 1
                for var in bindVariables:
                    log ("SQL RequestWithBinds %d> %s"%(i,var), LOGERROR)
                    i=i+1
                log( "---", LOGERROR )
            except:
                pass
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
                Value = KeyValue[1].replace("'", "''")
                
                Condition = "AND tt.TagTranslation = '"+Key+"' AND tc.TagContent = '"+Value+"' "
                OuterSelect += " AND idFile in ( " + InnerSelect + Condition + " ) "

        if len(FilterInlineArrayFalse) > 0:
            for Filter in FilterArrayFalse:

                KeyValue = Filter.split("||")
                Key = KeyValue[0]
                Value = KeyValue[1].replace("'", "''")
                
                Condition = "AND tt.TagTranslation = '"+Key+"' AND tc.TagContent = '"+Value+"' "
                OuterSelect += " AND idFile not in ( " + InnerSelect + Condition + " ) "            
                
    else:
        OldKey = ""
        OldValue = ""

        if len(FilterInlineArrayTrue) > 0:        
            for Filter in FilterArrayTrue:

                KeyValue = Filter.split("||")
                Key = KeyValue[0]
                Value = KeyValue[1].replace("'", "''")
                
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
                Value = KeyValue[1].replace("'", "''")
                
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
        return [row for row in RequestWithBinds( """SELECT distinct strPath,strFilename FROM files f, TagContents tc, TagsInFiles tif, TagTypes tt WHERE f.idFile = tif.idFile AND tif.idTagContent = tc.idTagContent AND tc.TagContent = ? and tc.idTagType = tt.idTagType  and length(trim(tt.TagTranslation))>0 and tt.TagTranslation = ? LIMIT %s OFFSET %s """%(limit,offset), (tag.encode("utf8"),tagtype.encode("utf8")) )]
    else: #sinon, on retourne toutes les images qui ne sont pas associées à des mots clés
        return [row for row in Request( """SELECT distinct strPath,strFilename FROM files WHERE idFile NOT IN (SELECT DISTINCT idFile FROM TagsInFiles) LIMIT %s OFFSET %s"""%(limit,offset) )]


def DefaultTagTypesTranslation():

    """Return a list of all keywords in database """
    Request("update TagTypes set TagTranslation = 'Country' where TagTranslation =  'Country/primary location name'")
    Request("update TagTypes set TagTranslation = 'Country' where TagTranslation =  'Photoshop:Country'")
    Request("update TagTypes set TagTranslation = 'Country' where TagTranslation =  'Iptc4xmpExt:CountryName'")
    Request("update TagTypes set TagTranslation = 'Country' where TagTranslation =  'Iptc4xmpCore:Country'")

    Request("update TagTypes set TagTranslation = 'Country Code' where TagTranslation =  'Country/primary location code'")
    Request("update TagTypes set TagTranslation = 'Country Code' where TagTranslation =  'Iptc4xmpCore:CountryCode'")
    
    Request("update TagTypes set TagTranslation = 'State' where TagTranslation =  'Province/state'")
    Request("update TagTypes set TagTranslation = 'State' where TagTranslation =  'Photoshop:State'")
    Request("update TagTypes set TagTranslation = 'State' where TagTranslation =  'Iptc4xmpExt:ProvinceState'")
    
    Request("update TagTypes set TagTranslation = 'City' where TagTranslation = 'Photoshop:City'")
    Request("update TagTypes set TagTranslation = 'City' where TagTranslation = 'Iptc4xmpExt:City'")
    Request("update TagTypes set TagTranslation = 'Location' where TagTranslation =  'Iptc4xmpCore:Location'")
    Request("update TagTypes set TagTranslation = 'Event' where TagTranslation = 'Iptc4xmpExt:Event'")
    
    Request("update TagTypes set TagTranslation = 'Date Added' where TagTranslation =  'DateAdded'")
    Request("update TagTypes set TagTranslation = 'Date Created' where TagTranslation =  'EXIF DateTimeOriginal'")
    Request("update TagTypes set TagTranslation = 'Date/Time Created' where TagTranslation =  'Photoshop:DateCreated'")
    Request("update TagTypes set TagTranslation = 'Date/Time Created' where TagTranslation =  'Image DateTime'")
    
    Request("update TagTypes set TagTranslation = 'Description' where TagTranslation = 'Caption/abstract'")
    Request("update TagTypes set TagTranslation = 'Description' where TagTranslation = 'Dc:description'")
    Request("update TagTypes set TagTranslation = 'Description' where TagTranslation = 'Iptc4xmpCore:Description'")

    Request("update TagTypes set TagTranslation = 'Headline' where TagTranslation = 'Iptc4xmpCore:Headline'")
    Request("update TagTypes set TagTranslation = 'Headline' where TagTranslation =  'Photoshop:Headline'")
    
    Request("update TagTypes set TagTranslation = 'Title' where TagTranslation = 'Object name'")
    Request("update TagTypes set TagTranslation = 'Title' where TagTranslation = 'Dc:title'")
    Request("update TagTypes set TagTranslation = 'Title' where TagTranslation = 'Iptc4xmpCore:Title'")
    
    Request("update TagTypes set TagTranslation = 'Creator' where TagTranslation = 'Writer/editor'")
    Request("update TagTypes set TagTranslation = 'Creator' where TagTranslation = 'By-line'")
    Request("update TagTypes set TagTranslation = 'Creator' where TagTranslation = 'Dc:creator'")
    Request("update TagTypes set TagTranslation = 'Creator Title' where TagTranslation = 'By-line title'")

    Request("update TagTypes set TagTranslation = 'Copyright' where TagTranslation = 'Dc:rights'")
    Request("update TagTypes set TagTranslation = 'Copyright' where TagTranslation = 'Copyright notice'")

    Request("update TagTypes set TagTranslation = 'Label' where TagTranslation =  'Xmp:Label'")
    Request("update TagTypes set TagTranslation = 'Image Rating' where TagTranslation =  'Xmp:Rating'")

    Request("update TagTypes set TagTranslation = 'Keywords' where TagTranslation =  'MicrosoftPhoto:LastKeywordIPTC'")
    Request("update TagTypes set TagTranslation = 'Keywords' where TagTranslation =  'MicrosoftPhoto:LastKeywordXMP'")
    Request("update TagTypes set TagTranslation = 'Keywords' where TagTranslation =  'Dc:subject'")
    Request("update TagTypes set TagTranslation = 'Keywords' where TagTranslation =  'Iptc4xmpCore:Keywords'")    

    Request("update TagTypes set TagTranslation = 'Category' where TagTranslation =  'Photoshop:Category'")
    Request("update TagTypes set TagTranslation = 'Supplemental Category' where TagTranslation =  'Photoshop:SupplementalCategories'")
    Request("update TagTypes set TagTranslation = 'Supplemental Category' where TagTranslation =  'Supplemental category'")

    Request("update TagTypes set TagTranslation = 'Persons' where TagTranslation =  'Iptc4xmpExt:PersonInImage'")

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
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'GPS GPSLatitude'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'GPS GPSLatitudeRef'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'GPS GPSLongitude'")
    Request("update TagTypes set TagTranslation = '' where TagTranslation =  'GPS GPSLongitudeRef'")
    
    
    #Request("delete from TagTypes where idTagType not in (select distinct idTagType from TagContents)")
    
def list_TagTypes():
    DefaultTagTypesTranslation()
    return [row for (row,) in Request( """SELECT distinct tt.TagTranslation FROM TagTypes tt, TagContents tc, TagsInFiles tif 
where length(trim(TagTranslation))>0 
and tt.idTagType = tc.idTagType
and tc.idTagContent = tif.idTagContent
ORDER BY LOWER(TagTranslation) ASC""" )]

def list_TagTypesAndCount():
    DefaultTagTypesTranslation()
    return [row for row in Request( """
SELECT tt.TagTranslation, count(distinct tagcontent)
  FROM TagTypes tt, TagContents tc
 where length(trim(TagTranslation)) > 0 
   and tt.idTagType                 = tc.idTagType
group by tt.tagtranslation """   )]

def countTagTypes(tagType,limit=-1,offset=-1):
    if tagType is not None:
        return RequestWithBinds("""SELECT count(distinct TagContent) FROM tagsInFiles tif, TagContents tc, TagTypes tt WHERE tif.idTagContent = tc.idTagContent AND tc.idTagType = tt.idTagType and length(trim(tt.TagTranslation))>0 and tt.idTagType =? """, (tagType,) )[0][0]
    else:
        return Request("""SELECT count(*) FROM TagTypes where length(trim(TagTranslation))>0""" )[0][0]
        
def setTranslatedTagType(TagType, TagTranslation):
    RequestWithBinds("Update TagTypes set TagTranslation = ? where TagType = ? ",(TagTranslation.encode('utf-8'), TagType.encode('utf-8')))
    
def getTagTypesForTranslation():
    return [row for row in Request('select TagType, TagTranslation from TagTypes order by 2,1')]

def list_Tags(tagType):
    """Return a list of all keywords in database"""
    return [row for (row,) in Request( """select distinct TagContent from TagContents tc, TagsInFiles tif, TagTypes tt  where tc.idTagContent = tif.idTagContent and tc.idTagType = tt.idTagType and tt.TagTranslation='%s' ORDER BY LOWER(TagContent) ASC"""%tagType.encode("utf8") )]

def list_TagsAndCount(tagType):
    """Return a list of all keywords in database"""
    return [row for row in RequestWithBinds( """
    select TagContent, count(distinct idfile) 
  from TagContents tc, TagsInFiles tif, TagTypes tt  
 where tc.idTagContent = tif.idTagContent
   and tc.idTagType = tt.idTagType 
   and tt.TagTranslation=? 
group BY LOWER(TagContent)""",(tagType.encode("utf8"),) )]
    
def countTags(kw,tagType, limit=-1,offset=-1):
    if kw is not None:
        return RequestWithBinds("""select count(distinct idFile) from  TagContents tc, TagsInFiles tif, TagTypes tt  where tc.idTagContent = tif.idTagContent and tc.TagContent = ? and tc.idTagType = tt.idTagType and tt.TagTranslation = ? """,(kw, tagType))[0][0]
    else:
        return Request("""SELECT count(*) FROM files WHERE idFile not in (SELECT DISTINCT idFile FROM TagsInFiles)""" )[0][0]


def countPicsFolder(folderid):
    # new part
    folderPath = RequestWithBinds("""Select FullPath from Folders where idFolder = ?""", (folderid,))[0][0]
    # mask the apostrophe
    folderPath = folderPath.replace("'", "''")
    count = Request("""select count(*) from files f, folders p where f.idFolder=p.idFolder and p.FullPath like '%s%%' """%folderPath)[0][0]
    return count

    # old part
    log("TEST : all children of folderid %s"%folderid)
    children = all_children(folderid)
    log(children)

    cpt = Request("SELECT count(*) FROM files f,folders p WHERE f.idFolder=p.idFolder AND f.idFolder='%s'"%folderid)[0][0]
    for idchild in children:
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
    return [row for (row,) in Request( """SELECT DISTINCT strPath FROM files""" )]


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
    return [t for (t,) in Request("""SELECT DISTINCT strftime("%Y","EXIF DateTimeOriginal") FROM files where "EXIF DateTimeOriginal" NOT NULL ORDER BY "EXIF DateTimeOriginal" ASC""")]
    
def get_months(year):
    return [t for (t,) in Request("""SELECT distinct strftime("%%Y-%%m","EXIF DateTimeOriginal") FROM files where strftime("%%Y","EXIF DateTimeOriginal") = '%s' ORDER BY "EXIF DateTimeOriginal" ASC"""%year)]

def get_dates(year_month):
    return [t for (t,) in Request("""SELECT distinct strftime("%%Y-%%m-%%d","EXIF DateTimeOriginal") FROM files where strftime("%%Y-%%m","EXIF DateTimeOriginal") = '%s' ORDER BY "EXIF DateTimeOriginal" ASC"""%year_month)]
    
def search_all_dates():# TODO check if it is really usefull (check 'get_pics_dates' to see if it is not the same)
    """return all files from database sorted by 'EXIF DateTimeOriginal' """
    return [t for t in Request("""SELECT strPath,strFilename FROM files ORDER BY "EXIF DateTimeOriginal" ASC""")]
    
def get_pics_dates():
    """return all different dates from 'EXIF DateTimeOriginal'"""
    return [t for (t,) in Request("""SELECT DISTINCT strftime("%Y-%m-%d","EXIF DateTimeOriginal") FROM files WHERE length(trim("EXIF DateTimeOriginal"))>0  ORDER BY "EXIF DateTimeOriginal" ASC""")]

def getDate(path,filename):
    try:
        return [row for row in RequestWithBinds( """SELECT files."EXIF DateTimeOriginal" FROM files WHERE strPath=? AND strFilename=? """,(path,filename) )][0][0]
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


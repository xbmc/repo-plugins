# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with XBMC; see the file COPYING. If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *

#imports
import xbmc
import xbmcplugin
import xbmcgui
import xbmcaddon
import os

# Minimal code to import bossanova808 common code
ADDON           = xbmcaddon.Addon()
CWD             = ADDON.getAddonInfo('path')
RESOURCES_PATH  = xbmc.translatePath( os.path.join( CWD, 'resources' ))
LIB_PATH        = xbmc.translatePath(os.path.join( RESOURCES_PATH, "lib" ))

sys.path.append( LIB_PATH )

from b808common import *
from XZenScreensaver import *

#uses zenapi by Scott Gorling (http://www.scottgorlin.com)
from zenapi import ZenConnection
from zenapi.snapshots import Photo, Group, PhotoSet


#kick this off
footprints()

################################################################################
################################################################################
# CONSTANTS AND INIT STUFF

#zero out core data between passes
mode = None
url = None
galleryid=None
group=None
category=None
categoryid=None
choice=None
AUTH = None
AUTHENTICATED = False
KEYRINGED = False

#entries per page (+1 for the next page entry)
LIMIT=14

#LIST MODES
MENU_ROOT = "MENU_ROOT"
CATEGORIES = "CATEGORIES"
CATEGORY_OPTIONS = "CATEGORY_OPTIONS"

#GALLERY MODES
MENU_USERGALLERIES = "MENU_USERGALLERIES"
POPPHOTOS = "POPPHOTOS"
POPGALLERIES = "POPGALLERIES"
POPCOLLECTIONS = "POPCOLLECTIONS"
DISPLAY_GALLERY = "DISPLAY_GALLERY"
DISPLAY_CATEGORY = "DISPLAY_CATEGORY"
RECENTPHOTOS = "RECENTPHOTOS"
RECENTGALLERIES = "RECENTGALLERIES"
RECENTCOLLECTIONS = "RECENTCOLLECTIONS"

#Zenfolio Quality Levels for Images
ZEN_DOWNLOAD_QUALITY = {
                    "ProtectXXLarge" : 6,
                    "ProtectExtraLarge" :5 ,
                    "ProtectLarge" :4,
                    "ProtectMedium" :3
}

ZEN_URL_QUALITY ={
                    "Small thumbnail" : 0,      #Small thumbnail (up to 80 x 80)
                    "Square thumbnail": 1,      #Square thumbnail (60 x 60, cropped square)
                    "Small": 2,                 #Small (up to 400 x 400)
                    "Medium": 3,                #Medium (up to 580 x 450)
                    "Large" : 4,                #Large (up to 800 x 630)
                    "X-Large" : 5,              #X-Large (up to 1100 x 850)
                    "XX-Large" : 6,             #XX-Large (up to 1550 x 960)
                    "Medium thumbnail" : 10,    #Medium thumbnail (up to 120 x 120)
                    "Large thumbnail" : 11      #Large thumbnail (up to 120 x 120)
}

#these modes use the thumbnail view (for playable items)
galleryModes = [\
                MENU_USERGALLERIES,\
                DISPLAY_GALLERY,\
                POPPHOTOS,\
                POPGALLERIES,\
                POPCOLLECTIONS,\
                RECENTPHOTOS,\
                RECENTGALLERIES,\
                RECENTCOLLECTIONS,\
                DISPLAY_CATEGORY \
              ]


#get the settings & parameters
USERNAME=ADDON.getSetting('username')
PASSWORD=ADDON.getSetting('password')
GALLERYPASS=ADDON.getSetting('passwordOriginals')

#there will be parameters if we're running as a plugin..
if sys.argv[0]=='':
    SCREENSAVER=True
else:    
    SCREENSAVER=False
    params=getParams()
    log("Parameters parsed: " + str(params))

#try and get data from the paramters
try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    galleryid=int(params["galleryid"])
except:
    pass
try:
    mode=params["mode"]
except:
    pass
try:
    group=int(params["group"])
except:
    pass
try:
    category=params["category"]
except:
    pass
try:
    categoryid=params["categoryid"]
except:
    pass
try:
    choice=params["choice"]
except:
    pass
#if we're paging groups of photos, what is the starting offset?
offset=0
try:
    offset=int(params["offset"])
except:
    pass



################################################################################
# Basic Util Functions

def frontPadTo9Chars(shortStr):
    while len(shortStr)<9:
        shortStr = "0" + shortStr
    return shortStr


################################################################################
# Zenfolio Connection & Authentication

def ConnectZen(mode):

    global AUTHENTICATED, AUTH, KEYRINGED, USERNAME, PADDSSWORD

    #connect to ZenFolio
    zen = ZenConnection(username = USERNAME, password = PASSWORD)

    #try and authenticate, although we can do a lot without this
    try:
        AUTH=zen.Authenticate()
        AUTHENTICATED=True
    except:
        print_exc()
        #if in the root menu the first time, let them know this is just a public browsing session....
        if mode==None:
            notify(LANGUAGE(30002),LANGUAGE(30003))

    return zen


################################################################################
# Photo/Set Loaders

#add a thumb for a group
def AddGroupThumb(group, numberOfItems=0):

    global zen

    try:
        titlePhoto = zen.LoadPhoto(group.TitlePhoto,'Level1')
        urlTitlePhoto = titlePhoto.getUrl(ZEN_URL_QUALITY['Large thumbnail'],auth=AUTH)

        if group.Title is None:
            title = LANGUAGE(30004)
        else:
            title = LANGUAGE(30005) + ": " + unquoteUni(group.Title)

        url = buildPluginURL({'mode':MENU_USERGALLERIES,'group':str(group.Id)})
        item=xbmcgui.ListItem(title,url,urlTitlePhoto,urlTitlePhoto)
        xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True,numberOfItems)

    except Exception as inst:
        log("AddPhotoSetThumb - Exception!", inst)


#add thumb that links to a set of photos
def AddPhotoSetThumb(photoSet, numberOfItems=0):

    global AUTH

    try:
        titlePhoto = zen.LoadPhoto(photoSet.TitlePhoto,'Level1')
        urlTitlePhoto = titlePhoto.getUrl(ZEN_URL_QUALITY['Large thumbnail'],auth=AUTH)

        if photoSet.Title is None:
            title="(" + LANGUAGE(30006) + ")"
        else:
            title = LANGUAGE(30007) + ": " + unquoteUni(photoSet.Title)

        url = buildPluginURL({"mode":DISPLAY_GALLERY, "galleryid":str(photoSet.Id)})
        item=xbmcgui.ListItem(title,url,urlTitlePhoto,urlTitlePhoto)
        xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True,numberOfItems)

    except Exception as inst:
        log("AddPhotoSetThumb - Exception!", inst)

#Add thumb that links to an individual photo

def AddPhotoThumb(photo, numberOfItems=0,downloadKey=""):

    global AUTH

    try:
        #get the highest quality url available
        for key, value in ZEN_DOWNLOAD_QUALITY.iteritems():
            if key not in photo.AccessDescriptor['AccessMask']:
                url = photo.getUrl(value, keyring=downloadKey, auth=AUTH)
                #log("Added url quality: " + key)
                break;

        urlThumb = photo.getUrl(ZEN_URL_QUALITY['Large thumbnail'],keyring=downloadKey, auth=AUTH)

        if photo.Title is None:
            title= LANGUAGE(30004)
        else:
            title = unquoteUni(photo.Title)

        log("AddPhotoThumb: [" + str(photo.Id) + "] title: [" + str(title) + "] url: [" +str(url) + "] urlThumb: [" + str(urlThumb) +"]")

        item=xbmcgui.ListItem(title,str(url),str(urlThumb),str(urlThumb))
        xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,False,numberOfItems)

    except Exception as inst:
        log("AddPhotoThumb - Exception!", inst)


def getKey(item):

    global GALLERYPASS

    if isinstance(item, PhotoSet):
        #is this a password protected gallery?
        if item.AccessDescriptor['AccessType'] == 'Password':
            downloadKey = zen.GetDownloadOriginalKey(item.Photos,GALLERYPASS)
            log("Download Key is: " + downloadKey)
            return downloadKey
        else:
            #no password needed
            return ''
    else:
        return ''

#Given a gallery ID, add all the thumbs
def AddGallery(galleryid):

    global zen

    photoset = zen.LoadPhotoSet(galleryid, 'Level1',includePhotos=True)
    downloadKey = getKey(photoset)
    for photo in photoset.Photos:
        AddPhotoThumb(photo,len(photoset.Photos),downloadKey)

#Given a category ID, add all the thumbs
def AddCategory(categoryid,choice,offset=0):

    global zen

    AddNextPageLink(DISPLAY_CATEGORY,offset+LIMIT,categoryid,choice)

    if choice=="Photos":
        searchResults = zen.SearchPhotoByCategory(0,'Popularity',categoryid,offset,LIMIT)
        log(str(searchResults))
        for photo in searchResults['Photos']:
            AddPhotoThumb(photo,len(searchResults['Photos']))
    elif choice=="Galleries":
        searchResults = zen.SearchSetByCategory(0,'Gallery','Popularity',categoryid,offset,LIMIT)
        log(str(searchResults))
        for photoset in searchResults['PhotoSets']:
            AddPhotoSetThumb(photoset,len(searchResults['PhotoSets']))
    elif choice=="Collections":
        searchResults = zen.SearchSetByCategory(0,'Collection','Popularity',categoryid,offset,LIMIT)
        log(str(searchResults))
        for photoset in searchResults['PhotoSets']:
            AddPhotoSetThumb(photoset,len(searchResults['PhotoSets']))
    else:
        false


#Add list entry for a next page link for the correct mode, and where to start
def AddNextPageLink(mode,startNumber=0,categoryid="",choice=""):
    urlNextPage=buildPluginURL({"mode":mode,"offset":startNumber,"categoryid":categoryid,"choice":choice})
    item=xbmcgui.ListItem("Next Page",urlNextPage,"","")
    xbmcplugin.addDirectoryItem(THIS_PLUGIN,urlNextPage,item,True)


################################################################################
# Menu Builders

def BuildMenuRootItem(mode, label):
    url = buildPluginURL({"mode":mode})
    item=xbmcgui.ListItem(label,url,'','',)
    xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True)

def BuildMenuRoot():

    global zen

    if AUTHENTICATED:
        BuildMenuRootItem(MENU_USERGALLERIES        ,LANGUAGE(30008)) #"User Galleries"
    BuildMenuRootItem(CATEGORIES                    ,LANGUAGE(30009)) #"Categories"
    BuildMenuRootItem(RECENTPHOTOS                  ,LANGUAGE(30010)) #"Recent Photos"
    BuildMenuRootItem(RECENTGALLERIES               ,LANGUAGE(30011)) #"Recent Galleries"
    BuildMenuRootItem(RECENTCOLLECTIONS             ,LANGUAGE(30012)) #"Recent Collections"
    BuildMenuRootItem(POPPHOTOS                     ,LANGUAGE(30013)) #"Popular Photos"
    BuildMenuRootItem(POPGALLERIES                  ,LANGUAGE(30014)) #"Popular Galleries"
    BuildMenuRootItem(POPCOLLECTIONS                ,LANGUAGE(30015)) #"Popular Collections"


def BuildUserGallery(group=None):

    global zen, KEYRINGED

    if group is None:
        #load the album hierchy for the user
        #load the cover photos
        #add the links
        h = zen.LoadGroupHierarchy()
##        log("$$$ H Access is " + str(h.AccessDescriptor))
##        if KEYRINGED == False and h.AccessDescriptor['AccessType'] == 'Password':
##            log("Global User Keyring")
##            zen.KeyringAddKeyPlain(realmId= h.AccessDescriptor['RealmId'],password="")
##            KEYRINGED=True

    else:
        #loading a specific group
        h = zen.LoadGroup(group, includeChildren=True)


    for element in h.Elements:
        log("Access is: " + str(element.AccessDescriptor))
        if isinstance(element,PhotoSet):
            log("Add PhotoSet Thumb: " + str(element.Id))
            AddPhotoSetThumb(element,len(h.Elements))
        elif isinstance(element,Group):
            log("Add Group Thumb: " + str(element.Id))
            AddGroupThumb(element)
        elif isinstance(element,Photo):
            log("Add Photo Thumb: " + str(element.Id))
            AddPhotoThumb(element)
        else:
            log("Did not add, not sure what this is: " + element.__name__)


def BuildMenuPopSets(type="Gallery",offset=0):

    global zen

    if type=="Gallery": AddNextPageLink(POPGALLERIES,offset+LIMIT)
    else: AddNextPageLink(POPCOLLECTIONS,offset+LIMIT)
    photosets = zen.GetPopularSets(type,offset,LIMIT)
    for photoset in photosets:
        AddPhotoSetThumb(photoset,len(photosets))

def ShowPopularPhotos(offset=0):

    global zen

    #first add a next page link for quick browsing
    AddNextPageLink(POPPHOTOS,offset+LIMIT)

    #now add the photos of this page
    photos = zen.GetPopularPhotos(offset,LIMIT)
    for photo in photos:
        AddPhotoThumb(photo,len(photos))

def BuildMenuRecentSets(type="Gallery",offset=0):

    global zen

    if type=="Gallery": AddNextPageLink(RECENTGALLERIES,offset+LIMIT)
    else: AddNextPageLink(RECENTCOLLECTIONS,offset+LIMIT)
    photosets = zen.GetRecentSets(type,offset,LIMIT)
    for photoset in photosets:
        AddPhotoSetThumb(photoset,len(photosets))


#build a list of categories or subcats or subsubcats
#category = XXX000000
# subcategory = XXXYYY000
#   subsubcategory = XXXYYYZZZ

def BuildMenuCategoryOptions(categoryid,numberOfItems=0):
    choices = ['Photos','Galleries','Collections']

    for choice in choices:
        url = buildPluginURL({'mode':DISPLAY_CATEGORY,'categoryid':categoryid, 'choice':choice})
        item=xbmcgui.ListItem(choice,url,'','')
        xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True,numberOfItems)

#Add list entries for categories
def BuildMenuCategoryItem(category,code,numberOfItems=0):
    newCode = frontPadTo9Chars(str(category['Code']))

    newName = category['DisplayName']
    #sub sub
    if newCode[-3:]!="000":
        newName = "    " + newName
    elif newCode[-6:-3]!="000":
        newName = "  " + newName
    else:
        pass

    url = buildPluginURL({'mode':CATEGORY_OPTIONS,'categoryid':newCode})
    item=xbmcgui.ListItem(newName,url,'','')
    xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True,numberOfItems)


def BuildMenuCategories(parentCode=None):

    global zen

    categoriesList = zen.GetCategories()
    log(str(categoriesList))
    if parentCode is None:
        log("Parent Code None")
    else:
        parentCode = frontPadTo9Chars(parentCode)
        log("Parent Code incoming is: " + parentCode)

    for category in categoriesList:
        BuildMenuCategoryItem(category,"")

##        #get the code as a string and pad it to the orignal 12 characters
##        strCode = str(category['Code'])
##        strCode = frontPadTo9Chars(strCode)
##
##        if parentCode is not None:
##            log("Seeing if we're adding " + category['DisplayName'] + " code is " + strCode + " and parentCode is: "+ parentCode)
##            log("PC " + parentCode[:3] + " SC " + strCode[:3] + " SCL3 " + strCode[-3:])
##        else:
##            log("Seeing if we're adding " + category['DisplayName'] + " code is " + strCode + " and parentCode is: None")
##
##        if parentCode is None and strCode[-6:]=="000000":
##            #this is a parent category as it ends  in 000000
##            AddCategory(category,strCode)
##        else:
##            if parentCode is not None and parentCode!=strCode and parentCode[:3] == strCode[:3] and strCode[-3:]!="000":
##            #we have a parent code and it is a category, so we are dealing with sub categories - check if all but the last three chars match
##                AddCategory(category,strCode)
##            else:
##                if parentCode is not None and parentCode!=strCode and parentCode[:6]==strCode[:6] and strCode[-3:]!="000":
##                    if parentCode[:3] == strCode[:3] and parentCode!=strCode and strCode[-6:]!="000000":
##                        #ok we have a sub-sub category
##                        AddCategory(category,strCode)



################################################################################
#Show's a group of recent photos between offset and limit

def ShowRecentPhotos(offset=0):

    global zen

    #first add a next page link for quick browsing
    AddNextPageLink(RECENTPHOTOS,offset+LIMIT)

    #now add the photos of this page
    photos = zen.GetRecentPhotos(offset,LIMIT)
    for photo in photos:
        AddPhotoThumb(photo,len(photos))


################################################################################
################################################################################
# MAIN
################################################################################
################################################################################

################################################################################
# ZenFolio Connection...after this:
# global AUTH holds the auth token
# global AUTHENTICATED holds a boolean of authentication state
# global KEYRINGED holds a boolen of keyringed state

if __name__ == '__main__':


    # Calles as a screensaver?  This will be blank
    if SCREENSAVER:
        log( "...therefore running as screensaver" )
        screensaver_gui = XZenScreensaver('XZenScreensaver.xml' , CWD, 'Default')
        screensaver_gui.doModal()
        #when we drop back here we're out of the screensaver...
        log ("Xzen Screensaver Exited")
        del screensaver_gui
        sys.modules.clear()
    # we're running as an image plugin...
    else:
        log( "Running as a Pictures addon" )
        zen = ConnectZen(mode)
        if zen is None:
            notify(LANGUAGE(30016))
            sys.exit()

        ################################################################################
        # Based on how the plugin was called (mdode) - do something

        try:
            if mode==None or mode==MENU_ROOT:
                log( "Display XZen Root Menu" )
                BuildMenuRoot()

            elif mode==MENU_USERGALLERIES:
                log( "Display XZen User Gallery" )
                BuildUserGallery(group)

            elif mode==POPPHOTOS:
                log( "Display XZen Popular Photos")
                ShowPopularPhotos(offset)

            elif mode==POPGALLERIES:
                log( "Display XZen Popular Galleries")
                BuildMenuPopSets("Gallery",offset)

            elif mode==POPCOLLECTIONS:
                log( "Display XZen Popular Collections")
                BuildMenuPopSets("Collection", offset)

            elif mode==RECENTPHOTOS:
                log( "Display XZen Recent Photos")
                ShowRecentPhotos(offset)

            elif mode==RECENTGALLERIES:
                log( "Display XZen Recent Galleries")
                BuildMenuRecentSets("Gallery",offset)

            elif mode==RECENTCOLLECTIONS:
                log( "Display XZen Recent Collections")
                BuildMenuRecentSets("Collection", offset)

            elif mode==CATEGORIES:
                log( "Display XZen Categories")
                BuildMenuCategories(category)

            elif mode==CATEGORY_OPTIONS:
                log( "Display XZen Category Options (Photos/Galleries/Collections)")
                BuildMenuCategoryOptions(categoryid)

            elif mode==DISPLAY_CATEGORY:
                log( "Display XZen Category id: " + str (categoryid) )
                AddCategory(categoryid,choice,offset)

            elif mode==DISPLAY_GALLERY:
                log( "Display XZen Gallery id: " + str (galleryid) )
                AddGallery(galleryid)

            else:
                notify(LANGUAGE(30017))
                sys.exit()


        except:
            print_exc()


        ################################################################################
        # FINISH OFF - set display mode appropriately, tell XBMC we're done, exit.

        #if we've just built a list of albums, force thumbnail mode
        if mode in galleryModes:
          log("Playable Items -> Trying to set thumnbnail mode...")
          xbmc.executebuiltin('Container.SetViewMode(500)')
        else:
          log("List Items -> Trying to set list mode...")
          xbmc.executebuiltin('Container.SetViewMode(50)')

        #and tell XBMC we're done...
        xbmcplugin.endOfDirectory(THIS_PLUGIN)

        #and power this puppy down....
        footprints(startup=False)





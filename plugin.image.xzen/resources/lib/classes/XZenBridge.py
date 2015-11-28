#uses zenapi by Scott Gorling (http://www.scottgorlin.com)
#imports

from b808common import *
from XZenConstants import *
from zenapi import ZenConnection
from zenapi.snapshots import Photo, Group, PhotoSet


class XZenBridge():

    AUTH = None
    AUTHENTICATED = False
    KEYRINGED = False

    #get the settings & parameters
    USERNAME=ADDON.getSetting('username')
    PASSWORD=ADDON.getSetting('password')
    GALLERYPASS=ADDON.getSetting('passwordOriginals')


    def __init__(self, mode=None):

        self.zen = self.ConnectZen(mode)
        if self.zen is None:
            notify(LANGUAGE(30016))
            sys.exit()


    ################################################################################
    # Basic Util Functions



    ################################################################################
    # ZenFolio Connection...after this:
    # global AUTH holds the auth token
    # global AUTHENTICATED holds a boolean of authentication state
    # global KEYRINGED holds a boolen of keyringed state

    def ConnectZen(self, mode):

        #connect to ZenFolio
        local_zen = ZenConnection(username = self.USERNAME, password = self.PASSWORD)

        #try and authenticate, although we can do a lot without this
        try:
            self.AUTH=local_zen.Authenticate()
            self.AUTHENTICATED=True
        except:
            print_exc()
            #if in the root menu the first time, let them know this is just a public browsing session....
            if mode==None:
                notify(LANGUAGE(30002),LANGUAGE(30003))

        return local_zen


    ################################################################################
    # Photo/Set Loaders

    #add a thumb for a group
    def AddGroupThumb(self, group, numberOfItems=0):


        try:
            titlePhoto = self.zen.LoadPhoto(group.TitlePhoto,'Level1')
            urlTitlePhoto = titlePhoto.getUrl(ZEN_URL_QUALITY['Large thumbnail'],auth=self.AUTH)

            if group.Title is None:
                title = LANGUAGE(30004)
            else:
                title = LANGUAGE(30005) + ": " + unquoteUni(group.Title)

            url = buildPluginURL({'mode':MENU_USERGALLERIES,'group':str(group.Id)})
            item=xbmcgui.ListItem(title,url,urlTitlePhoto,urlTitlePhoto)

            cmi = "XBMC.RunPlugin(" + buildPluginURL({'mode':SET_SS_ROOT_GROUP,'group':str(group.Id)}) + ")"
            item.addContextMenuItems([('Set as XZenScreensaver Root', cmi)])

            xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True,numberOfItems)

        except Exception as inst:
            log("AddPhotoSetThumb - Exception!", inst)


    #add thumb that links to a set of photos
    def AddPhotoSetThumb(self, photoSet, numberOfItems=0):

        try:
            titlePhoto = self.zen.LoadPhoto(photoSet.TitlePhoto,'Level1')
            urlTitlePhoto = titlePhoto.getUrl(ZEN_URL_QUALITY['Large thumbnail'],auth=self.AUTH)

            if photoSet.Title is None:
                title="(" + LANGUAGE(30006) + ")"
            else:
                title = LANGUAGE(30007) + ": " + unquoteUni(photoSet.Title)

            url = buildPluginURL({"mode":DISPLAY_GALLERY, "galleryid":str(photoSet.Id)})
            item=xbmcgui.ListItem(title,url,urlTitlePhoto,urlTitlePhoto)
            
            cmi = "XBMC.RunPlugin(" + buildPluginURL({'mode':SET_SS_ROOT_SET,'set':str(photoSet.Id)}) + ")"
            item.addContextMenuItems([('Set as XZenScreensaver Root', cmi)])
            
            xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True,numberOfItems)

        except Exception as inst:
            log("AddPhotoSetThumb - Exception!", inst)

    #Add thumb that links to an individual photo

    def AddPhotoThumb(self, photo, numberOfItems=0,downloadKey=""):

        try:
            #get the highest quality url available
            for key, value in ZEN_DOWNLOAD_QUALITY.iteritems():
                if key not in photo.AccessDescriptor['AccessMask']:
                    url = photo.getUrl(value, keyring=downloadKey, auth=self.AUTH)
                    #log("Added url quality: " + key)
                    break;

            urlThumb = photo.getUrl(ZEN_URL_QUALITY['Large thumbnail'],keyring=downloadKey, auth=self.AUTH)

            if photo.Title is None:
                title= LANGUAGE(30004)
            else:
                title = unquoteUni(photo.Title)

            log("AddPhotoThumb: [" + str(photo.Id) + "] title: [" + str(title) + "] url: [" +str(url) + "] urlThumb: [" + str(urlThumb) +"]")

            item=xbmcgui.ListItem(title,str(url),str(urlThumb),str(urlThumb))
            xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,False,numberOfItems)

        except Exception as inst:
            log("AddPhotoThumb - Exception!", inst)


    def getKey(self, item):

        if isinstance(item, PhotoSet):
            #is this a password protected gallery?
            if item.AccessDescriptor['AccessType'] == 'Password':
                downloadKey = self.zen.GetDownloadOriginalKey(item.Photos,self.GALLERYPASS)
                log("Download Key is: " + downloadKey)
                return downloadKey
            else:
                #no password needed
                return ''
        else:
            return ''

    #Given a gallery ID, add all the thumbs
    def AddGallery(self, galleryid):

        photoset = self.zen.LoadPhotoSet(galleryid, 'Level1',includePhotos=True)
        downloadKey = self.getKey(photoset)
        for photo in photoset.Photos:
            self.AddPhotoThumb(photo,len(photoset.Photos),downloadKey)

    #Given a category ID, add all the thumbs
    def AddCategory(self, categoryid,choice,offset=0):


        self.AddNextPageLink(DISPLAY_CATEGORY,offset+LIMIT,categoryid,choice)

        if choice=="Photos":
            searchResults = self.zen.SearchPhotoByCategory(0,'Popularity',categoryid,offset,LIMIT)
            log(str(searchResults))
            for photo in searchResults['Photos']:
                self.AddPhotoThumb(photo,len(searchResults['Photos']))
        elif choice=="Galleries":
            searchResults = self.zen.SearchSetByCategory(0,'Gallery','Popularity',categoryid,offset,LIMIT)
            log(str(searchResults))
            for photoset in searchResults['PhotoSets']:
                self.AddPhotoSetThumb(photoset,len(searchResults['PhotoSets']))
        elif choice=="Collections":
            searchResults = self.zen.SearchSetByCategory(0,'Collection','Popularity',categoryid,offset,LIMIT)
            log(str(searchResults))
            for photoset in searchResults['PhotoSets']:
                self.AddPhotoSetThumb(photoset,len(searchResults['PhotoSets']))
        else:
            false


    #Add list entry for a next page link for the correct mode, and where to start
    def AddNextPageLink(self, mode,startNumber=0,categoryid="",choice=""):
        urlNextPage=buildPluginURL({"mode":mode,"offset":startNumber,"categoryid":categoryid,"choice":choice})
        item=xbmcgui.ListItem("Next Page",urlNextPage,"","")
        xbmcplugin.addDirectoryItem(THIS_PLUGIN,urlNextPage,item,True)


    ################################################################################
    # Menu Builders



    def BuildUserGallery(self, group=None):

        if group is None:
            #load the album hierchy for the user
            #load the cover photos
            #add the links
            h = self.zen.LoadGroupHierarchy()
    ##        log("$$$ H Access is " + str(h.AccessDescriptor))
    ##        if KEYRINGED == False and h.AccessDescriptor['AccessType'] == 'Password':
    ##            log("Global User Keyring")
    ##            zen.KeyringAddKeyPlain(realmId= h.AccessDescriptor['RealmId'],password="")
    ##            KEYRINGED=True

        else:
            #loading a specific group
            h = self.zen.LoadGroup(group, includeChildren=True)


        for element in h.Elements:
            log("Access is: " + str(element.AccessDescriptor))
            if isinstance(element,PhotoSet):
                log("Add PhotoSet Thumb: " + str(element.Id))
                self.AddPhotoSetThumb(element,len(h.Elements))
            elif isinstance(element,Group):
                log("Add Group Thumb: " + str(element.Id))
                self.AddGroupThumb(element)
            elif isinstance(element,Photo):
                log("Add Photo Thumb: " + str(element.Id))
                self.AddPhotoThumb(element)
            else:
                log("Did not add, not sure what this is: " + element.__name__)


    def BuildMenuPopSets(self, type="Gallery",offset=0):

        if type=="Gallery": self.AddNextPageLink(POPGALLERIES,offset+LIMIT)
        else: self.AddNextPageLink(POPCOLLECTIONS,offset+LIMIT)
        photosets = self.zen.GetPopularSets(type,offset,LIMIT)
        for photoset in photosets:
            self.AddPhotoSetThumb(photoset,len(photosets))

    def ShowPopularPhotos(self, offset=0):

        #first add a next page link for quick browsing
        self.AddNextPageLink(POPPHOTOS,offset+LIMIT)

        #now add the photos of this page
        photos = self.zen.GetPopularPhotos(offset,LIMIT)
        for photo in photos:
            self.AddPhotoThumb(photo,len(photos))

    def BuildMenuRecentSets(self, type="Gallery",offset=0):

        if type=="Gallery": self.AddNextPageLink(RECENTGALLERIES,offset+LIMIT)
        else: self.AddNextPageLink(RECENTCOLLECTIONS,offset+LIMIT)
        photosets = self.zen.GetRecentSets(type,offset,LIMIT)
        for photoset in photosets:
            self.AddPhotoSetThumb(photoset,len(photosets))


    #build a list of categories or subcats or subsubcats
    #category = XXX000000
    # subcategory = XXXYYY000
    #   subsubcategory = XXXYYYZZZ

    def BuildMenuCategoryOptions(self, categoryid,numberOfItems=0):
        choices = ['Photos','Galleries','Collections']

        for choice in choices:
            url = buildPluginURL({'mode':DISPLAY_CATEGORY,'categoryid':categoryid, 'choice':choice})
            item=xbmcgui.ListItem(choice,url,'','')
            xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True,numberOfItems)

    #Add list entries for categories
    def BuildMenuCategoryItem(self, category,code,numberOfItems=0):
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


    def BuildMenuCategories(self, parentCode=None):

        categoriesList = self.zen.GetCategories()
        log(str(categoriesList))
        if parentCode is None:
            log("Parent Code None")
        else:
            parentCode = frontPadTo9Chars(parentCode)
            log("Parent Code incoming is: " + parentCode)

        for category in categoriesList:
            self.BuildMenuCategoryItem(category,"")

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

    def ShowRecentPhotos(self, offset=0):

        #first add a next page link for quick browsing
        self.AddNextPageLink(RECENTPHOTOS,offset+LIMIT)

        #now add the photos of this page
        photos = self.zen.GetRecentPhotos(offset,LIMIT)
        for photo in photos:
            self.AddPhotoThumb(photo,len(photos))

    def BuildMenuRootItem(self, mode, label):
        url = buildPluginURL({"mode":mode})
        item=xbmcgui.ListItem(label,url,'','',)
        cmi = "XBMC.RunPlugin(" + buildPluginURL({'mode':SET_SS_ROOT_ROOT,'root':mode}) + ")"
        item.addContextMenuItems([('Set as XZenScreensaver Root', cmi)])
        xbmcplugin.addDirectoryItem(THIS_PLUGIN,url,item,True)

    def BuildMenuRoot(self):

        if self.AUTHENTICATED:
            self.BuildMenuRootItem(MENU_USERGALLERIES        ,LANGUAGE(30008)) #"User Galleries"
        self.BuildMenuRootItem(CATEGORIES                    ,LANGUAGE(30009)) #"Categories"
        self.BuildMenuRootItem(RECENTPHOTOS                  ,LANGUAGE(30010)) #"Recent Photos"
        self.BuildMenuRootItem(RECENTGALLERIES               ,LANGUAGE(30011)) #"Recent Galleries"
        self.BuildMenuRootItem(RECENTCOLLECTIONS             ,LANGUAGE(30012)) #"Recent Collections"
        self.BuildMenuRootItem(POPPHOTOS                     ,LANGUAGE(30013)) #"Popular Photos"
        self.BuildMenuRootItem(POPGALLERIES                  ,LANGUAGE(30014)) #"Popular Galleries"
        self.BuildMenuRootItem(POPCOLLECTIONS                ,LANGUAGE(30015)) #"Popular Collections"

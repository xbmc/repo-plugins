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

#SET SCREENSAVER MODES
SET_SS_ROOT_ROOT = "SET_SS_ROOT_ROOT"
SET_SS_ROOT_SET = "SET_SS_ROOT_SET"
SET_SS_ROOT_GROUP = "SET_SS_ROOT_GROUP"

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

#Zenfolio Quality Levels for Images
ZEN_DOWNLOAD_QUALITY = {
                    "ProtectXXLarge" : 6,
                    "ProtectExtraLarge" :5 ,
                    "ProtectLarge" :4,
                    "ProtectMedium" :3
}

ZEN_URL_QUALITY = {
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

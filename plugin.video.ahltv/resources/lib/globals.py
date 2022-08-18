import re
import sys
import json
import xbmc, xbmcplugin, xbmcgui, xbmcaddon
import random
import time

addon_url = sys.argv[0]
addon_handle = int(sys.argv[1])

# Addon Info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
XBMC_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString
ROOTDIR = xbmcaddon.Addon().getAddonInfo('path')

# Settings
settings = xbmcaddon.Addon()
USERNAME = json.dumps(str(settings.getSetting(id="username")))
PASSWORD = json.dumps(str(settings.getSetting(id="password")))

# API values
API_URL = 'https://api.watchtheahl.com'
APP_ID = str(random.randint(1,100000)) + ".KODI." + str(int(time.time()))
APP_KEY = "f33d78736fd12b3c1e30a9dafa5d3980"
API_KEY = None
PRODUCT_ID = "2"
VERIFY = True

COLOR_FREE = 'green'

# Images
ICON = ROOTDIR + "/icon.png"
AHL_LOGO = ROOTDIR + "/ahl_logo.png"
FANART = ROOTDIR + "/fanart.jpg"
CLEARLOGO = ROOTDIR + "/resources/media/clear_logo.png"

TEAM_FANART = {
    60000: "https://www.bakersfieldcondors.com/wp-content/uploads/2019/11/2019_11_24_Post-495x300.jpg", # Bakersfield
    60001: "https://s3.amazonaws.com/ahl-uploads/app/uploads/belleville/2019/12/13220526/BSens-4054-1024x681.jpg", # Belleville
    60002: "https://149345975.v2.pressablecdn.com/wp-content/uploads/191004-ROSTER-RELEASE-WEB.png", # Binghamton
    60003: "https://www.soundtigers.com/assets/img/celly-autos-b39c3e38bc.jpg", # Bridgeport
    60004: "https://www.gocheckers.com/images/19-20/Brian_Gibbons_121619.jpg", # Charlotte
    60005: "https://www.chicagowolves.com/wp-content/uploads/2019/06/celly-frontpage-gallery-1024x683.jpg", # Chicago
    60006: "https://www.clevelandmonsters.com/assets/img/W4S_0806-7bac3bd869.png", # Cleveland
    60030: "https://www.coloradoeagles.com/assets/img/1180x440-GameRecap-121719-2c0cd0f381.jpg", # Colorado
    60007: "https://griffinshockey.com/imager/general/189530/55-ford-white-jersey-1_191218_153138_87b984c08ea1e9642840dd02102af27c.jpg", # Grand
    60008: "http://www.hartfordwolfpack.com/assets/img/Dmowski-Action-Shot-2-c102424c5f.jpg", # Hartford
    60036: "https://www.hendersonsilverknights.com/wp-content/uploads/51037803332_d7a84d658a_k.jpg", # Henderson
    60009: "https://gocheckers.com/images/Division_Preview_Hershey.jpg", # Hershey
    60010: "https://www.iowawild.com/assets/img/ROT_IAvsONT_121419-a046a71eed.png", # Iowa
    60011: "https://www.rocketlaval.com/wp-content/uploads/2019/12/49236067966_40ff74a7cc_h.jpg", # Laval
    60012: "http://www.phantomshockey.com/wp-content/uploads/2019/12/Aube-Kubel-10_18_19-vs-BNG-3-Cut.jpg", # Lehigh
    60013: "https://moosehockey.com/wp-content/uploads/2019/12/recapSAdec14.jpg", # Manitoba
    60014: "https://farm66.staticflickr.com/65535/49391830453_e964db6ab0_c.jpg", # Milwaukee
    60015: "https://www.ontarioreign.com/assets/img/Moulson-BAK-Web-413-68af5a4817.jpg", # Ontario
    60016: "https://pbs.twimg.com/media/EMHgfRmXYAUGjJg?format=jpg&name=small", # Providence
    60017: "https://www.amerks.com/assets/img/202102010MV0103-a2f885f781.JPG", # Rochester
    60018: "https://www.icehogs.com/imager/general/images/56887/26675183548_fe811a1358_o_c98a7ad80693ecadd28d6db983184f6b.jpg", # Rockford
    60019: "https://www.oursportscentral.com/graphics/pictures/md20181113-159863.jpg", # San Antonio
    60020: "https://www.sandiegogulls.com/assets/img/49236474651_f20b716fe0_o-0e0bd9e650.jpg", # San Diego
    60021: "http://www.sjbarracuda.com/assets/img/20191004_Knights_vs_Sharks_0048-043f42ccbb.jpg", # San Jose
    60022: "http://www.springfieldthunderbirds.com/assets/img/Final-12-13-19-slideshow-f56650b6d8.jpg", # Springfield
    60023: "https://stocktonheat.com/wp-content/uploads/2019/12/Philp-SJ-Front.jpg", # Stockton
    60024: "https://syracusecrunch.com/images/2020/1/9/Alexey_Lipanov.jpg?width=1080&height=608&mode=crop&format=jpg&quality=80", # Syracuse
    60025: "http://www.texasstars.com/assets/img/StarsSweepMoose-5a58cecd54.png", # Texas
    60026: "http://ahl-uploads.s3.amazonaws.com/app/uploads/toronto_marlies/2018/05/28222440/tix-smith-huddle-1024x680.jpg", # Toronto
    60027: "https://www.tucsonroadrunners.com/wp-content/uploads/2019/12/12.14.19-Web-Recap.png", # Tucson
    60028: "http://www.uticacomets.com/assets/img/1218-feature-5450f98f05.jpg", # Utica
    60029: "http://www.wbspenguins.com/wp-content/uploads/2019/12/1000_Larmi.jpg", # Wilkes
    194381: "https://api.abbotsford.canucks.com/uploads/Homepage_5583e2b396.jpg", # Abbotsford
    194382: "https://www.bridgeportislanders.com/assets/img/weekly5-17502d478f.jpg", # Bridgeport Islanders
}

# User Agents
UA_IPHONE = 'AppleCoreMedia/1.0.0.15B202 (iPhone; U; CPU OS 11_1_2 like Mac OS X; en_us)'
UA_PC = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36'

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

import sys
import urllib
import re
import os

import xbmc
import xbmcaddon


############################################################################
# ADDON INFO
############################################################################

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = xbmc.translatePath(ADDON.getAddonInfo('path'))
ADDON_PATH_PROFILE = xbmc.translatePath(ADDON.getAddonInfo('profile'))
XBMC_VERSION = float(re.findall(r'\d{2}\.\d{1}', xbmc.getInfoLabel("System.BuildVersion"))[0])
LOCAL_STRING = ADDON.getLocalizedString


############################################################################
# SETTINGS
############################################################################

#Main settings
USERNAME = ADDON.getSetting('username')
PASSWORD = ADDON.getSetting('password')
QUALITY = int(ADDON.getSetting('quality'))
QUALITY_CLASSIC = int(ADDON.getSetting('quality_classic'))
USERAGENT = urllib.quote(ADDON.getSetting('useragent'))
ROGERSLOGIN = ADDON.getSetting(id="rogerslogin")
SHOWSCORE = ADDON.getSetting(id="show_score")
SHOW_SCORE_UPDATES = 0

#Visual settings
SHOWDIALOGQUALITY = 'true'
if QUALITY != 5:
    SHOWDIALOGQUALITY = 'false'

#Visual settings
TEAMNAME = int(ADDON.getSetting(id="team_names"))
HIDELIVEGAMES = ADDON.getSetting(id="hide_live_games")
USETHUMBNAILS = ADDON.getSetting(id="use_thumbnails")
USEADDONICON = ADDON.getSetting(id="use_addon_icon")


#if (USEADDONICON == 'true') and (USETHUMBNAILS == 'true'):
ICON = ADDON_PATH+"/icon.png"
#else:
#ICON = ''
FANART = ADDON_PATH+"/fanart.jpg"
    
thumbnail = ["square","cover","169"]
background = ["black","ice","transparent"]


THUMBFORMAT = thumbnail[int(ADDON.getSetting(id="thumb_format"))]
THUMBFORMATOSD = thumbnail[int(ADDON.getSetting(id="thumb_format_osd"))]
BACKGROUND = background[int(ADDON.getSetting(id="background"))]
BACKGROUNDOSD = background[int(ADDON.getSetting(id="background_osd"))]
GENERATETHUMBNAILS = ADDON.getSetting(id="generate_thumbnails")
DELETETHUMBNAILS = ADDON.getSetting(id="delete_thumbnails")
SHOWHADIALOG = "false" #ADDON.getSetting(id="showhadialog")
SHOWHADIALOGLIVE = "false"#ADDON.getSetting(id="showhadialoglive")
ALTERNATIVEVS = ADDON.getSetting(id="alternativevs")

############################################################################
# TEAM NAMES
############################################################################

def getTeams():
    allTeams = {'MIN': ['Minnesota', 'Wild', 'Minnesota Wild', 'MIN', 'Wild'], 
                'NYR': ['NY Rangers', 'Rangers', 'New York Rangers', 'NYR', 'Rangers'],
                'CAR': ['Carolina', 'Hurricanes', 'Carolina Hurricanes', 'CAR', 'Hurricanes'], 
                'BOS': ['Boston', 'Bruins', 'Boston Bruins', 'BOS', 'Bruins'], 
                'DET': ['Detroit', 'Red Wings', 'Detroit Red Wings', 'DET', 'RedWings'], 
                'CMB': ['Columbus', 'Blue Jackets', 'Columbus Blue Jackets', 'CMB', 'BlueJackets'], 
                'LOS': ['Los Angeles', 'Kings', 'Los Angeles Kings', 'LOS', 'Kings'], 
                'NYI': ['NY Islanders', 'Islanders', 'New York Islanders', 'NYI', 'Islanders'], 
                'FLA': ['Florida', 'Panthers', 'Florida Panthers', 'FLA', 'Panthers'], 
                'COL': ['Colorado', 'Avalanche', 'Colorado Avalanche', 'COL', 'Avalanche'], 
                'NSH': ['Nashville', 'Predators', 'Nashville Predators', 'NSH', 'Predators'], 
                'SAN': ['San Jose', 'Sharks', 'San Jose Sharks', 'SAN', 'Sharks'], 
                'NJD': ['New Jersey', 'Devils', 'New Jersey Devils', 'NJD', 'Devils'], 
                'DAL': ['Dallas', 'Stars', 'Dallas Stars', 'DAL', 'Stars'], 
                'CGY': ['Calgary', 'Flames', 'Calgary Flames', 'CGY', 'Flames'], 
                'TOR': ['Toronto', 'Maple Leafs', 'Toronto Maple Leafs', 'TOR', 'MapleLeafs'], 
                'WSH': ['Washington', 'Capitals', 'Washington Capitals', 'WSH', 'Capitals'], 
                'TAM': ['Tampa Bay', 'Lightning', 'Tampa Bay Lightning', 'TAM', 'Lightning'], 
                'WPG': ['Winnipeg', 'Jets', 'Winnipeg Jets', 'WPG', 'Jets'], 
                'BUF': ['Buffalo', 'Sabres', 'Buffalo Sabres', 'BUF', 'Sabres'], 
                'VAN': ['Vancouver', 'Canucks', 'Vancouver Canucks', 'VAN', 'Canucks'], 
                'STL': ['St. Louis', 'Blues', 'St. Louis Blues', 'STL', 'Blues'], 
                'CHI': ['Chicago', 'Blackhawks', 'Chicago Blackhawks', 'CHI', 'Blackhawks'], 
                'PHI': ['Philadelphia', 'Flyers', 'Philadelphia Flyers', 'PHI', 'Flyers'], 
                'ANA': ['Anaheim', 'Ducks', 'Anaheim Ducks', 'ANA', 'Ducks'], 
                'PIT': ['Pittsburgh', 'Penguins', 'Pittsburgh Penguins', 'PIT', 'Penguins'], 
                'EDM': ['Edmonton', 'Oilers', 'Edmonton Oilers', 'EDM', 'Oilers'], 
                'PHX': ['Phoenix', 'Coyotes', 'Phoenix Coyotes', 'PHX', 'Coyotes'], 
                'MON': ['Montreal', 'Canadiens', 'Montreal Canadiens', 'MON', 'Canadiens'], 
                'OTT': ['Ottawa', 'Senators', 'Ottawa Senators', 'OTT', 'Senators'],
                'ATL': ['Atlanta', 'Thrashers', 'Atlanta Thrashers', 'ATL', 'Thrashers'],
                'ARI': ['Arizona', 'Coyotes', 'Arizona Coyotes', 'ARI', 'Coyotes']}
    return allTeams
#   Copyright (C) 2017 Lunatixz
#
#
# This file is part of filmriseTV.
#
# filmriseTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# filmriseTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with filmriseTV.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding: utf-8 -*-

import os, sys
import xbmc, xbmcaddon, xbmcgui, xbmcplugin

# Plugin Info
ADDON_ID = 'plugin.video.filmrisetv'
REAL_SETTINGS = xbmcaddon.Addon(id=ADDON_ID)
ADDON_NAME = REAL_SETTINGS.getAddonInfo('name')
ADDON_PATH = (REAL_SETTINGS.getAddonInfo('path').decode('utf-8'))
ADDON_VERSION = REAL_SETTINGS.getAddonInfo('version')
SETTINGS_LOC = REAL_SETTINGS.getAddonInfo('profile')
ICON = REAL_SETTINGS.getAddonInfo('icon')
FANART = REAL_SETTINGS.getAddonInfo('fanart')

def start():
    addDir(
        title="TV",
        url="plugin://plugin.video.youtube/user/FilmRiseTV/")
    addDir(
        title="True Crime",
        url="plugin://plugin.video.youtube/user/FilmRiseTrueCrime/")
    addDir(
        title="Forensic Files",
        url="plugin://plugin.video.youtube/user/ForensicFilesChannel/")
    addDir(
        title="Documentary",
        url="plugin://plugin.video.youtube/user/FilmRiseDocumentary/")
    addDir(
        title="Movies",
        url="plugin://plugin.video.youtube/user/FilmRiseMovies/")
    addDir(
        title="Crime",
        url="plugin://plugin.video.youtube/channel/UCyG3mbSm4z6SyGPNvkgx_Yg/")
    addDir(
        title="Television",
        url="plugin://plugin.video.youtube/channel/UCVVXDVee0JZ2dlPYtpdTZVg/")
    addDir(
        title="Features",
        url="plugin://plugin.video.youtube/channel/UCtAddMIPhKMbLED3KEQiJGw/")
    addDir(
        title="Paranormal",
        url="plugin://plugin.video.youtube/channel/UCyCEMUGV8gtXeIQBwQiemyQ/")
    addDir(
        title="History",
        url="plugin://plugin.video.youtube/channel/UCq9rBa-YDHXfjl9t-I423Vw/")
    addDir(
        title="Horror",
        url="plugin://plugin.video.youtube/channel/UCv60jacPSiFH49SAT6nu7hQ/")
    addDir(
        title="Releasing",
        url="plugin://plugin.video.youtube/channel/UCigBBfWRC05eW9_5DjJLq_Q/")
    addDir(
        title="Kids",
        url="plugin://plugin.video.youtube/user/FilmRiseKids/")
    addDir(
        title="Cinema",
        url="plugin://plugin.video.youtube/channel/UCWzaMLuoZUNjsrCrTirABQA/")
    addDir(
        title="Cinema",
        url="plugin://plugin.video.youtube/channel/UCWzaMLuoZUNjsrCrTirABQA/")
    addDir(
        title="Fear",
        url="plugin://plugin.video.youtube/channel/UCCT0cBYnHaDXZwuPz-V14hg/")
    addDir(
        title="Queer Cinema",
        url="plugin://plugin.video.youtube/channel/UC974nyZIokgx0kI9NMFDisg/")
    addDir(
        title="Real",
        url="plugin://plugin.video.youtube/channel/UC0xciG7DZx9NO0FfKtA2Zvw/")
    addDir(
        title="World Wide Wrestling",
        url="plugin://plugin.video.youtube/channel/UCJOFMMpxU9_2jHn71wb6wDw/")
    addDir(
        title="Flicks",
        url="plugin://plugin.video.youtube/channel/UCSfjlqO4QWh2sfSO35utWBA/")
    addDir(
        title="Drive-In",
        url="plugin://plugin.video.youtube/channel/UCBxvJ1mDHiZ76KAI-PXPm2Q/")
    addDir(
        title="Nature",
        url="plugin://plugin.video.youtube/channel/UC-1z78NyBDIrBTpEVrceMuw/")
    addDir(
        title="Comedy",
        url="plugin://plugin.video.youtube/channel/UCIjpMIY_pDPK96VpV_4XAXA/")
    addDir(
        title="Wrestling Superstars",
        url="plugin://plugin.video.youtube/channel/UCTkOB7nYQjqwxg7UMuzAlqQ/")
    addDir(
        title="Pictures",
        url="plugin://plugin.video.youtube/channel/UCEU_963MKFlRQIMKg4vrnUw/")
    addDir(
        title="British Drama",
        url="plugin://plugin.video.youtube/channel/UC3wfGEkNESWBIMihGihJ7Gg/")
    addDir(
        title="LGBT",
        url="plugin://plugin.video.youtube/channel/UCCcJon4R7TbJZo6488Av2RQ/")
    addDir(
        title="Gay and Lesbian",
        url="plugin://plugin.video.youtube/channel/UCfjYVzUfwVXd3u6zoKDh8xw/")
    addDir(
        title="Classic Wrestling Network",
        url="plugin://plugin.video.youtube/channel/UCLLrvuagBVm0F5K3X74tnGg/")
    addDir(
        title="Cinematheque",
        url="plugin://plugin.video.youtube/channel/UCqbIomfUnB-LpP7xlBxMWJQ/")
    addDir(
        title="Unsolved Mysteries",
        url="plugin://plugin.video.youtube/channel/UCzirOgADPOz0eapgwBcX9Gw/")
    addDir(
        title="Presents Troma",
        url="plugin://plugin.video.youtube/channel/UCb5YfCigbb6iDRD8Im544Rw/")
    addDir(
        title="Outdoor Life",
        url="plugin://plugin.video.youtube/channel/UCwdimbkWdtqs9PRgkZFU61w/")
    addDir(
        title="Medical Detectives",
        url="plugin://plugin.video.youtube/user/MedicalDetectivesTV/")
    
def addDir(title, url):
    liz=xbmcgui.ListItem(title)
    liz.setProperty('IsPlayable', 'false')
    liz.setInfo(type="Video", infoLabels={"label":title,"title":title} )
    liz.setArt({'thumb':ICON,'fanart':FANART})
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=True)
    
start()
xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)
# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# The Heritage Channnel - video addon for Kodi Helix / Isengard. Videos from cultural, natural, scientific, academic, technical and other heritage organisations from across the world.
# This addon was modified from the BBQ Pit Boys plugin (http://addons.tvaddons.ag/show/plugin.video.barbecueweb/)
# These addons depends upon the Youtube addon by Bromix (http://kodi.wiki/view/Add-on:YouTube), so install that as well
#
# Version 1.0.1 with 35 channels / 9-8-2015 by ookgezellig@gmail.com
#
# ------------------------------------------------------------
# License: GPL (http://www.gnu.org/licenses/gpl-3.0.html)
# ------------------------------------------------------------

# TODO in next release: Derive icons from Twitter, this is a good source for square icons. Needs resizing to 256x256 and converting from .jpg to .png . Checkout Python Image Library

import os
import sys
import plugintools
import xbmcaddon
from addon.common.addon import Addon

addonID = 'plugin.video.heritagechannel'
addon = Addon(addonID, sys.argv)
local = xbmcaddon.Addon(id=addonID)
path = local.getAddonInfo('path')

localfilepath = os.path.join(path, 'resources', 'data', "institutions.csv")  # local csv = data/institutions.csv

# Name of institution, City, Countrycode, Youtube channel ID, abbreviation of institute (for icons and fanart)
# Put in in list chi[]
chi = []
chi = plugintools.read_local_csv(localfilepath)
# Break down chi[]. Set OrganisationName, city, countrycode,YoutubeChannel-ID, abbreviation, local thumb and local fanart for every CH institution
chi_name, chi_city, chi_countrycode, chi_countryname, chi_YOUTUBE_CHANNEL, chi_abbrev, chi_twitterHandle, chi_thumb, chi_fanart = (
    [] for i in range(9))

# Strip leading and traling blanks from list entries, as well as multiple inner spaces
# See http://bytes.com/topic/python/answers/590441-how-strip-mulitiple-white-spaces
for i in range(len(chi)):
    chi_name.append(" ".join(chi[i][0].split()))
    chi_city.append(" ".join(chi[i][1].split()))
    chi_countrycode.append(chi[i][2].strip())
    chi_countryname.append(
        plugintools.lookup_countryname("countrydata.csv", chi_countrycode[i].strip()))
    chi_YOUTUBE_CHANNEL.append(chi[i][3].strip())
    chi_abbrev.append(chi[i][4].strip())
    chi_thumb.append(
        os.path.join(path, 'resources', 'media', 'icons', "icon_" + chi_abbrev[i] + ".png"))
    chi_fanart.append(os.path.join(path, 'resources', 'media', 'fanarts',
                                   "fanart_" + chi_abbrev[i] + ".jpg"))


# Entry point
def run():
    plugintools.log("heritagechannel.run")
    # Get params
    params = plugintools.get_params()
    # if params.get("action") is None:
    main_list(params)
    # else:
    #    action = params.get("action")
    #    exec action + "(params)"
    plugintools.close_item_list()


# Main menu
def main_list(params):
    plugintools.log("heritagechannel.main_list " + repr(params))
    for j in range(len(chi)):
        plugintools.add_item(
            title=chi_name[j] + ", " + chi_city[j] + ", " + chi_countryname[j],
            url="plugin://plugin.video.youtube/user/" + chi_YOUTUBE_CHANNEL[j] + "/",
            thumbnail=chi_thumb[j],
            fanart=chi_fanart[j],
            folder=True)
run()

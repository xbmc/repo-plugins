#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import sys

import simplejson as json
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib import api_scraper as scraper
from resources.lib import livePlayer as livePlayer

from resources.lib.app_common import log
from resources.lib.base import addItemsToKodi, play_video
from resources.lib.utils import parameters_string_to_dict, unquoteUrl


def router(paramstring):
    params = parameters_string_to_dict(paramstring)
    mode = params.get('mode')
    link = params.get('link')
    showID = params.get('showID')
    if link:
        link = unquoteUrl(link)

    log(mode)
    if mode:
        if mode == 'getContentGrid':
            scraper.parseJsonGridVideoContent(link)
            addItemsToKodi(False)
        elif mode == 'getShowByID':
            scraper.getJsonShowById(link)
            addItemsToKodi(False)
        elif mode == 'getShowByUrl':
            scraper.getJsonShowByUrl(link)
            # if the previous call provides videos AND folders
            # try to fetch also videos
            if showID:
                scraper.getJsonShowById(showID)
            addItemsToKodi(False)
        elif mode == 'getFormatSliderForce':
            scraper.parseJsonFormatSliderContent(link, True)
            addItemsToKodi(False)
        elif mode == 'getFormatSlider':
            scraper.parseJsonFormatSliderContent(link)
            addItemsToKodi(False)
        elif mode == 'Play':
            # we just have a video ID fetch full video link
            if str(link).isdigit():
                link = scraper.getJsonVideoLink(link)
            play_video(link)
        elif mode == 'playlive':
            livePlayer.play_livestream("")
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        scraper.getMainMenu()
        addItemsToKodi(False)


if __name__ == '__main__':
    router(sys.argv[2])

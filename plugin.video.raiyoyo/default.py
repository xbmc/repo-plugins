# -*- coding: utf-8 -*-
import xbmcaddon
import xbmc
import xbmcplugin
import xbmcgui
import os
import sys
import re 
from resources.lib.raiyoyo import Raiyoyo
from phate89lib import kodiutils, staticutils

HANDLE=int(sys.argv[1])

raiyoyo = Raiyoyo()
raiyoyo.log = kodiutils.log

def stamp_ep(ep):
    ep['mediatype'] = 'video'
    xbmc.log("STAMP_EP:")
    xbmc.log(str(ep))
    kodiutils.addListItem("[COLOR blue]"+ep["title"]+"[/COLOR]", {'mode':'playRaiyoyo', 'url': ep["url"]}, thumb=ep["thumbs"],videoInfo=ep,isFolder=False)

def root():
    kodiutils.addListItem("Programmi",{'mode':'elenco_video'})
    kodiutils.endScript()

def elenco_video_groupList():
    for group in raiyoyo.get_url_groupList():
      kodiutils.addListItem(group["title"], {'mode':'elenco_puntate', 'id': group["id"]})
    kodiutils.endScript()

def elenco_puntate(id):
    kodiutils.setContent('videos')
    for pun in raiyoyo.get_url_punList(id):
      stamp_ep(pun)
    kodiutils.endScript()


def playRaiyoyo(streamUrl):
    kodiutils.setResolvedUrl(streamUrl)
#    kodiutils.setResolvedUrl(solved=False)
#    xbmc.executebuiltin('XBMC.PlayerControl(Play)')
  

# parameter values
params = staticutils.getParams()

if 'mode' in params:
  if params['mode'] == "elenco_video":
    elenco_video_groupList()
  elif params['mode'] == "elenco_puntate":
    if 'id' in params:
      elenco_puntate(params['id'])
  elif params['mode'] == "playRaiyoyo":
    playRaiyoyo(params['url'])

else:
  root()


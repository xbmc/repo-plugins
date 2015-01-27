#!/usr/bin/python
import os
from neverwise import Util

# http://resetdiretta.ns0.it:8000 # URL alternativo.
# Ho tentato di inserire il nome della radio tra le informazioni della canzone ma dallo stream ricevo le informazioni della canzone corrente che cancellano il nome della radio.
li = Util.createListItem(Util._addonName, thumbnailImage = '{0}/icon.png'.format(os.path.dirname(os.path.abspath(__file__))), streamtype = 'music', infolabels = { 'title' : Util._addonName })
xbmc.Player(xbmc.PLAYER_CORE_PAPLAYER).play('http://resetradiolive.ns0.it:8000', li)

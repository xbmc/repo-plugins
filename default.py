#!/usr/bin/python
import neverwise as nw, os#, datetime


class itvrs_radio_ice(object):

  def __init__(self):

    li = nw.createListItem(nw.addonName, thumbnailImage = '{0}/icon.png'.format(os.path.dirname(os.path.abspath(__file__))), streamtype = 'music', infolabels = { 'title' : nw.addonName })
    xbmc.Player().play('http://stream.zenolive.com/2m26re3dpg5tv', li)

# Entry point.
#startTime = datetime.datetime.now()
rr = itvrs_radio_ice()
del rr
#xbmc.log('{0} azione {1}'.format(nw.addonName, str(datetime.datetime.now() - startTime)))

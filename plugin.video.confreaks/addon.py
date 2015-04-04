#!/usr/bin/env python
from xbmcswift2 import Plugin
from xbmcswift2 import download_page
from api.router import Router

PLUGIN_NAME = 'Confreaks'
PLUGIN_ID = 'plugin.video.confreaks'

plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)


@plugin.route('/')
def index():
  return [{
    'label': event.name() + '  [COLOR mediumslateblue]' + event.pretty_range() + '[/COLOR]',
    'path': plugin.url_for('show_videos', event_code=event.code()),
    #'icon': ''
  } for event in Router.events()]


@plugin.route('/events/<event_code>/')
def show_videos(event_code):
  return [{
    'label': video.title + '  [COLOR mediumslateblue]' + video.presenter_names() + '[/COLOR]',
    'path': video.url(),
    'is_playable': True
  } for video in Router.videos(event_code)]


if __name__ == '__main__':
    plugin.run()
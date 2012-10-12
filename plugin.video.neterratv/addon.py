#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 mr.olix@gmail.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#    I'm a starter on XBMC and Python and I have to thank you all the people 
#    who post examples and code on the internet. 
#    Many thanks goes to Tristan Fischer who wrote the myvideo.de XBMC plugin
#    I started my the plugin code based on his code.
# 


from xbmcswift import Plugin, xbmc, xbmcplugin, xbmcgui, clean_dict


import resources.lib.neterratv as neterratv
import sys

DEBUG = False
REMOTE_DBG = False

print 'Start neterratv plugin'

# append pydev remote debugger
if REMOTE_DBG:
    # Make pydev debugger works for auto reload.
    # Note pydevd module need to be copied in XBMC\system\python\Lib\pysrc
    try:
        import pysrc.pydevd as pydevd
    # stdoutToServer and stderrToServer redirect stdout and stderr to eclipse console
        pydevd.settrace('localhost', stdoutToServer=True, stderrToServer=True)
    except ImportError:
        sys.stderr.write("Error: " +
            "You must add org.python.pydev.debug.pysrc to your PYTHONPATH.")
        sys.exit(1)

__addon_name__ = 'Neterra.TV'
__id__ = 'plugin.video.neterratv'

username = ""
password = ""
   
thisPlugin = int(sys.argv[1])

THUMBNAIL_VIEW_IDS = {'skin.confluence': 500,
                      'skin.aeon.nox': 551,
                      'skin.confluence-vertical': 500,
                      'skin.jx720': 52,
                      'skin.pm3-hd': 53,
                      'skin.rapier': 50,
                      'skin.simplicity': 500,
                      'skin.slik': 53,
                      'skin.touched': 500,
                      'skin.transparency': 53,
                      'skin.xeebo': 55}


class Plugin_mod(Plugin):

    def add_items(self, iterable, is_update=False, sort_method_ids=[],
                  override_view_mode=False):
        items = []
        urls = []
        for i, li_info in enumerate(iterable):
            items.append(self._make_listitem(**li_info))
            if self._mode in ['crawl', 'interactive', 'test']:
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'),
                                            '', li_info.get('url'))
                urls.append(li_info.get('url'))
        if self._mode is 'xbmc':
            if override_view_mode:
                skin = xbmc.getSkinDir()
                thumbnail_view = THUMBNAIL_VIEW_IDS.get(skin)
                if thumbnail_view:
                    cmd = 'Container.SetViewMode(%s)' % thumbnail_view
                    xbmc.executebuiltin(cmd)
            xbmcplugin.addDirectoryItems(self.handle, items, len(items))
            for id in sort_method_ids:
                xbmcplugin.addSortMethod(self.handle, id)
            xbmcplugin.endOfDirectory(self.handle, updateListing=is_update)
        return urls

    def _make_listitem(self, label, label2='', iconImage='', thumbnail='',
                       path='', **options):
        li = xbmcgui.ListItem(label, label2=label2, iconImage=iconImage,
                              thumbnailImage=thumbnail, path=path)
        cleaned_info = clean_dict(options.get('info'))
        if cleaned_info:
            li.setInfo('video', cleaned_info)
        if options.get('is_playable'):
            li.setProperty('IsPlayable', 'true')
        if options.get('context_menu'):
            li.addContextMenuItems(options['context_menu'])
        return options['url'], li, options.get('is_folder', True)

plugin = Plugin_mod(__addon_name__, __id__, __file__)

'''
default method route to /
called when the script starts 
'''
@plugin.route('/', default=True)
def main_menu():
    __log('main_menu start')
    #get a list with the TV stations
    stations = neterratv.showTVStations(plugin.get_setting('username'), plugin.get_setting('password'))
    items=[]
    for item in stations:
        items.append({'label': item[0],
                      'url': plugin.url_for('select_recordorlive',tvstation_name=item[0],tvstation_code=item[1])})
    return plugin.add_items(items)

'''
display TV live stream or recorded streams
'''
@plugin.route('/select_recordorlive/<tvstation_name>,<tvstation_code>')
def select_recordorlive(tvstation_name,tvstation_code):
    __log('select_recordorlive start')
    items=[]
    items.append({'label': 'TV ' + tvstation_name,
            'url': plugin.url_for('tvstation_playtv',tvstation_code=tvstation_code)})
    #append all others
    items.append({'label': 'Recorded ' + tvstation_name,
                  'url': plugin.url_for('show_recordedlist',tvstation_code=tvstation_code)})
    __log('select_recordorlive')
    return plugin.add_items(items)

'''
display list with the available TV streams from the selected TV station
'''
@plugin.route('/tvstation_playtv/<tvstation_code>')
def tvstation_playtv(tvstation_code):
    
    __log('tvstation_playtv started with string=%s' % tvstation_code)
       
    username = plugin.get_setting('username')
    password = plugin.get_setting('password')
    
    stations = neterratv.getTVStationsStreams(tvstation_code, username, password)
    
    items=[]
    i=0
    for station in stations:
        if i==0:
            items=[{'label': 'TV ' + station[0],
                    'url': plugin.url_for('tvstation_play',tvstation_code=station[1])}]
            i=i+1
        else:
            items.append({'label': 'TV ' + station[0],
                    'url': plugin.url_for('tvstation_play',tvstation_code=station[1])})

    __log('tvstation_playtv finished with string=%s' % tvstation_code)
    return plugin.add_items(items)

'''
show available recorded streams for select TV station
'''
@plugin.route('/show_recordedlist/<tvstation_code>')
def show_recordedlist(tvstation_code):
    
    __log('select_recordedstreams start')

    username = plugin.get_setting('username')
    password = plugin.get_setting('password')
    
    stations = neterratv.showTVStationRecorded(tvstation_code, username, password)
    
    items=[]
    i=0
    for station in stations:
        if i==0:
            items=[{'label': station[0],
                    'url': plugin.url_for('show_recordedstreams',tvstation_code=station[1])}]
            i=i+1
        else:
            items.append({'label': station[0],
                    'url': plugin.url_for('show_recordedstreams',tvstation_code=station[1])})

    __log('select_recordedstreams finished with string=%s' % tvstation_code)
    return plugin.add_items(items)

'''
shows available recorded streams for selected stream
'''
@plugin.route('/show_recordedstreams/<tvstation_code>')
def show_recordedstreams(tvstation_code):
    
    __log('show_recordedstreams start')

    username = plugin.get_setting('username')
    password = plugin.get_setting('password')
    
    stations = neterratv.showTVStationRecordedStreams(tvstation_code, username, password)
    
    items=[]
    i=0
    for station in stations:
        if i==0:
            items=[{'label': station[0],
                    'url': plugin.url_for('tvstation_play',tvstation_code=station[1])}]
            i=i+1
        else:
            items.append({'label': station[0],
                    'url': plugin.url_for('tvstation_play',tvstation_code=station[1])})

    __log('show_recordedstreams with string=%s' % tvstation_code)
    return plugin.add_items(items)

'''
returns the play link for the given URL
'''
@plugin.route('/tvstation_play/<tvstation_code>')
def tvstation_play(tvstation_code):
    
    __log('tvstation_play started with string=%s' % tvstation_code)
    
    username = plugin.get_setting('username')
    password = plugin.get_setting('password')
    
    url = neterratv.getTVPlayLink(tvstation_code,username,password)
    
    '''    
    items=[{'label': plugin.get_string(30002),
                  'url': url,'is_folder':False,'title':'Play','video_id':'0'}]
    '''
    
    #try to call the player with the link 

    #listitem = xbmcgui.ListItem(label='Play TV', path=url)

    #listitem.setInfo(type='Video',infoLabels={ "Label": "TV" })
    #xbmc.Player(xbmc.PLAYER_CORE_MPLAYER)
    #xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=listitem)
    
    xbmc.Player().play(url)
    print 'URL: ' + url
    __log('tvstation_play end')
    
    #return __add_items(items)

'''
private methods
'''
def __add_items(entries):
    items = []
    sort_methods = [xbmcplugin.SORT_METHOD_UNSORTED, ]
    force_viewmode = plugin.get_setting('force_viewmode') == 'true'
    update_on_pageswitch = plugin.get_setting('update_on_pageswitch') == 'true'
    has_icons = False
    is_update = False
    for e in entries:
        if force_viewmode and not has_icons and e.get('thumb', False):
            has_icons = True
        if e.get('pagenination', False):
            if e['pagenination'] == 'PREV':
                if update_on_pageswitch:
                    is_update = True
                title = '<< %s %s <<' % (plugin.get_string(30000), e['title'])
            elif e['pagenination'] == 'NEXT':
                title = '>> %s %s >>' % (plugin.get_string(30000), e['title'])
            items.append({'label': title,
                          'iconImage': 'DefaultFolder.png',
                          'is_folder': True,
                          'is_playable': False,
                          'url': plugin.url_for('show_path',
                                                path=e['path'])})
        elif e['is_folder']:
            items.append({'label': e['title'],
                          'iconImage': e.get('thumb', 'DefaultFolder.png'),
                          'is_folder': True,
                          'is_playable': False,
                          'url': plugin.url_for('show_path',
                                                path=e['path'])})
        else:
            items.append({'label': e['title'],
                          'iconImage': e.get('thumb', 'DefaultVideo.png'),
                          'info': {'duration': e.get('length', '0:00'),
                                   'plot': e.get('description', ''),
                                   'studio': e.get('username', ''),
                                   'date': e.get('date'),
                                   'year': e.get('year'),
                                   'rating': e.get('rating'),
                                   'votes': e.get('votes'),
                                   'views': e.get('views')},
                          'is_folder': False,
                          'is_playable': True,
                          'url':e['url']})
                        
                        #'url': plugin.url_for('watch_video',
                        #                       video_id=e['video_id'])})
                                                
                                
    sort_methods.extend((xbmcplugin.SORT_METHOD_VIDEO_RATING,
                         xbmcplugin.SORT_METHOD_VIDEO_RUNTIME,))
    __log('__add_items end')
    return plugin.add_items(items, is_update=is_update,
                            sort_method_ids=sort_methods,
                            override_view_mode=has_icons)

def __log(text):
    xbmc.log('%s addon: %s' % (__addon_name__, text))

if __name__ == '__main__':
    plugin.run()

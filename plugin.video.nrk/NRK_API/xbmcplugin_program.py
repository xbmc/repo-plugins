#xbmcplugin_program.py
#
#
#   NRK plugin for XBMC Media center
#
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#


import os, sys,re
import api_nrk as nrk
import utils
from utils import Key, PluginError, Log, Plugin
import xbmc, xbmcgui, xbmcplugin
from xbmcgui import ListItem
import connection_manager as datamanager
from connection_manager import Session, ImageArchiver, DataHandle


Log.notice( "PLUGIN::LOADED -> '%s'" % __name__)


ITERABLE = 1; PLAYABLE = 2; INPUT_SEARCH = 4
lang = xbmc.getLocalizedString

class WebTV(Plugin):
    
    stack_catalog = []
    merge_counter = 0
    
    catbase = 'Nett-tv'
    content = 'files'
    
    type_dict = { 
            nrk.PLAYLIST:        'Spilleliste',
            nrk.PLAYLIST_CLIP:   'Spilleliste klipp',
            nrk.PLAYLIST_ITEM:   'Spilleliste utvalg',
            nrk.SHOW:            'Program',
            nrk.SHOW_CLIP:       'Program klipp',
            nrk.SHOW_FOLDER:     'mappe',
            nrk.SHOW_CLIP_INDEX: 'Program klipp indeks',
            nrk.VIGNETE:         'Vignett',
            nrk.PROGRAM:         'Program',
            nrk.SEARCH:          'soek'
        }
    
    
    
    def _handle_playlist_clip(self):
        self.item = self.api.get_playlist_item(self.state.id)
        return PLAYABLE
    # - EOM -    
                       
    
    
    def _handle_playlist(self):
        
        
        ident, view, argument = self.state.id, self.state.view, self.state.arg
        
        if ident is nrk.REGION and not argument:
            regions = nrk.views.regions()
            self.stack.extend(regions)
            
        elif not view:
            self.stack.extend(nrk.views.playlist(self.state))
            if self.state.id is nrk.REGION:
                self.stack.append(nrk.views.archive)
           
        elif view != nrk.RELEVANT:
            plist = self.api.get_playlist_from_view(ident, view, argument)
            self.stack.extend(plist)
            
        else:
            plist = self.api.get_playlist(ident, argument)
            self.stack.extend(plist)

        return ITERABLE
    # - EOM -	
    
 
        
    def _handle_program_list(self):
        
        ident, view, argument = self.state.id, self.state.view, self.state.arg
        
        Log.notice('PLUGIN::SPAM -> program listing requested..')
        
        #Manage the different views and glue this shit together
        if not ident and not view:
            #Just throw the search in here for now
            self.stack.append( nrk.views.search )
            views = nrk.views.program( self.state )
            self.stack.extend( views )

        # View by character
        elif view is nrk.BY_CHAR and not ident:
            self.category = '%s - %s' % ( self.catbase, lang(30210) )
            shows = nrk.views.by_char()
            if not shows:
                return
            self.stack.extend(shows)

        # View by theme
        elif view == nrk.BY_THEME and not ident:
            self.category = '%s - %s' % ( self.catbase, lang(30211) )
            themes = nrk.views.by_theme()
            self.stack.extend( themes )
        
        # View all
        elif view is nrk.VIEW_ALL:
            self.category = '%s - %s' % ( self.catbase, lang(30212) )
            shows = self.api.get_all_shows()
            if not shows:
                return
            self.stack.extend( shows )
        
        # View by character    
        elif view is nrk.BY_CHAR:
            self.content = 'tvshows'
            self.category = '%s - %s' % ( self.catbase, ident )
            shows = self.api.get_shows_by_character(ident)
            if not shows:
                return
            self.stack.extend( shows )
        
        # View top total    
        elif (view is nrk.TOP_TOTAL      or 
              view is nrk.TOP_THIS_MONTH or 
              view is nrk.TOP_THIS_WEEK  or 
              view is nrk.TOP_BY_INPUT):
            
            if ident == 0:
                input = keyboard(heading=lang(30501))
                try:
                    input = int( input )
                except:
                    raise PluginError(lang(30502), lang(30502))
                else:
                    if not input > 0 and not input < 9999:
                        raise PluginError(lang(30502), lang(30502))  
                    else:
                        ident = input
            try:
                top = {7: lang(30213), 31: lang(30214), 3600: lang(30215)}[ident]
            except:
                top = lang(30216) % ident
                
            self.category = '%s - %s' % ( self.catbase, top )
            self.content  = 'tvshows'
            shows         = self.api.get_most_viewed_shows(ident)
            if not shows: return
            self.stack.extend(shows)
        
        # View live shows
        elif view is nrk.LIVE:
            self.category = lang(30350)
            self.content  = 'episodes'
            shows         = self.api.get_live_shows()
            if not shows: return
            self.stack.extend(shows)
            
        elif view is nrk.RECOMMENDED:
            self.category = lang(30217)
            self.content  = 'tvshows'
            shows         = self.api.get_recommended_shows()
            if not shows: return
            self.stack.extend(shows)
        
        elif view is nrk.ARTICLES:
            self.category = lang(30219)
            self.content  = 'tvshows'
            shows         = self.api.get_articles()
            if not shows: return
            self.stack.extend(shows)
                
        else:
            theme         = nrk.views.theme_title[ident]
            self.category = '%s - %s' % ( self.catbase, theme )
            self.content  = 'tvshows'
            shows         = self.api.get_shows_by_theme(ident)
            self.stack.extend(shows)

        return ITERABLE
    # - EOM -
    
    
    def _handle_search(self):

        if not self.state.arg:
            self.state.arg = keyboard('', 30500)
            if not self.state.arg:
                return
                
        if not self.state.id: 
            self.state.id = 1
                
        result = self.api.get_search_result(self.state.arg, self.state.id)
        self.stack.extend(result)

        return ITERABLE
    # - EOM -
    
    
    def _handle_show(self, data=None):
        
        shows = self.api.get_show(self.state.id, self.state.type)
        self.stack.extend(shows)
        self.content = 'episodes'
        return ITERABLE
    # - EOM -
    
    
    def _handle_show_clip(self, time=None):
        
        if self.platform == utils.XBOX:
            self.item = self.api.get_show_clip(
                                self.state.id, self.state.parent, True
                            )
        else: 
            self.item = self.api.get_show_clip(
                                self.state.id, self.state.parent
                            )    
        if time: self.item.time = time
        return PLAYABLE
    # - EOM -

    
    
    def _handle_show_clip_index(self):
        videoid, time = self.api.get_video_id(self.state.id)
        self.state.id = videoid
        return self._handle_show_clip(time)
    # - EOM -
   
    def _handle_live_show(self):
        shows = self.api.get_live_shows()
        self.stack.extend(shows)
        return ITERABLE
    
    
    
class Main(WebTV):

    def __init__(self):
        Plugin.__init__(self)
        
        if self.state.refresh == True:
            self.state.refresh = False
            key = Key.build_url('program', words=self.state.__dict__)
            xbmc.executebuiltin("ReplaceWindow(Programs,%s)" % key)
            return
            
        self.stack = []
        self.__set_settings()
        self.__map_functions()
        
        self.open()
        self.close()
        
        Session().close()
    # - EOM -


    def open(self):

        if not self.state.transparent:
            self._setup_session()
            
        #used for the watched/unwatched info
        if not self.session.data_objects.has_key('watched'):
            self.session.manage(watched={})
            
        self.mode = self.mapping[self.state.type]()
        
        if self.mode == ITERABLE:
            if self._pre_iter():
                self.create_directory()
        elif self.mode == PLAYABLE:
            self.play()
            
        return
    # - EOM -
    
    
    def _setup_session(self):

        if not self.session_key:
            Log.debug('Session key not set')
            self.session_key = str( hash( self.state ) )
            
        sdata = {
                'cache-time': self.settings['cache_time'], 
                'cache':      self.settings['cache_files'] and self.cache,
                'cache-path': self.cachepath,
                'key':        self.session_key
            }
            
        self.session     = Session(sdata)
        self.session_key = self.session.session_key
        
        cache = self.settings['cache_files'] and self.cache
        self.api  = nrk.Api(self.settings['connection_speed'], cache)
        self.imga = ImageArchiver(cache)
    # - EOM -
       
        
    def play(self):

        item = self.item
        li = ListItem(item.title, thumbnailImage=item.thumbnail, path=item.url)
        Log.notice('PLUGIN::SPAM -> play url %s' % item.url)
        self.player = utils.PluginPlayer()
            
        if self.state.playable: 
            self.dir.resolve_url(li, True)
        else:
            self.player.play(item.url, li)
        

        if not self.session.data_objects['watched'].has_key(item.id):
            Log.notice('PLUGIN::SPAM -> mark video as watched')
            self.session.update_object('watched')[item.id] = 1

        
        
    def create_directory(self):

        if self.state.type == nrk.PLAYLIST:
            self.player = utils.PluginPlayer()
        
        Log.notice('PLUGIN::SPAM -> Set plugin dir content "%s"' % self.content)
        self.dir.set_content(self.content)
        
        if self.settings['fetch_path']:
            if (self.state.type == nrk.SHOW 
            or self.state.type == nrk.SHOW_FOLDER):
                self.category = self.api.get_path(self.state.id, self.state.type)
                self.set_category()
        else:
            self.set_category()
        
        
        for i in self:
            li = ListItem(i.title, thumbnailImage=i.thumbnail)
            
            overlay = (
                    xbmcgui.ICON_OVERLAY_UNWATCHED,
                    xbmcgui.ICON_OVERLAY_WATCHED,)[
                        self.session.data_objects['watched'].has_key(i.key.id)]

                
            if i.isPlayable is True:
                li.setProperty('IsPlayable', 'true')

            li.setInfo( 'video', {
                            'plot':    i.plot, 
                            'title':   i.title, 
                            'overlay': overlay
                        }
                    )
            
            try:    
              li.setLabel2(self.type_dict[i.key.type])
            except:
              pass
              
            if self.state.type == nrk.PLAYLIST and self.state.view:
                self.player.queue(i.url, li)
            
            
            commands = []
            commands.append(( lang(30300), 
                                  'XBMC.RunPlugin(%s)' % (
                                        Key.build_url(
                                              'program',
                                              words = self.state.__dict__,
                                              refresh = True
                                        )), 
                                ))
                                
            if i.key.type == nrk.SHOW:                
                commands.append(( lang(30301), 
                                  'XBMC.RunPlugin(%s)' % (
                                        Key.build_url(
                                              'favorites',
                                              action = 'add', 
                                              name  = i.title, 
                                              thumb = i.thumbnail, 
                                              id    = i.key.id
                                        )), 
                                ))
                
            
            elif i.defntion == 'video/mp4':
                commands.append(( lang(30302), 
                                  'XBMC.RunPlugin(%s)' % (
                                        Key.build_url(
                                              'nogui',
                                              action = 'download', 
                                              name  = i.title, 
                                              thumb = i.thumbnail, 
                                              url   = i.url
                                        )), 
                                ))
                
            
            li.addContextMenuItems( commands )  
            
    
            if i.key.type != nrk.VIGNETE:
                ok = self.dir.add(i.url, li, i.isFolder, int(sys.argv[1]))
                if ok == False:
                    break
                
        if self.state.type == nrk.PLAYLIST and self.state.view:
            if self.settings.autoplay_playlist == True:
                self.player.playQueue()
        
        
    def __set_settings(self):
    
        self.settings = utils.PluginSettings()

        self.settings.add('fetch_subtitles')
        self.settings.add('transparency')
        self.settings.add('transparent_media')
        self.settings.add('fetch_chapters')
        self.settings.add('test_images')
        self.settings.add('cache_files')
        self.settings.add('fetch_path')
        self.settings.add('autoplay_playlist')
        
        #Connection speed
        options = ( 600, 1000, 1800, ); index = 11
        self.settings.add('connection_speed', 'values', options, index)
        #Cache time
        options = ( 999, 1, 2, 12, 24, ); index = 21
        self.settings.add('cache_time', 'values', options, index)
    # - EOM -


    
    def __map_functions(self):
        #Use a dict to map types against methods to
        #avoid some messy nested loops
        self.mapping = {
                nrk.PLAYLIST_ALT_CLIP:  self._handle_playlist_clip,
                nrk.SHOW_CLIP_INDEX:    self._handle_show_clip_index,
                nrk.PLAYLIST_CLIP:      self._handle_playlist_clip,
                nrk.SHOW_FOLDER:        self._handle_show,
                nrk.SHOW_CLIP:          self._handle_show_clip,
                nrk.PLAYLIST:           self._handle_playlist,
                nrk.PROGRAM:            self._handle_program_list,
                nrk.SEARCH:             self._handle_search,
                nrk.SHOW:               self._handle_show,
                nrk.LIVE:               self._handle_live_show
            }
    # - EOM -
    
    
    #Used for iteration
    def __iter__(self):
        return self.next()
    # - EOM -
    
    
    def next(self):
        Log.notice('PLUGIN -> Stack contains %d elements' % len(self.stack))
        for item in self.stack:
            return_object = self._iter_handler(item)
            if return_object is not None:
                yield return_object
                #item.update(return_object)
        self._post_iter()
    # - EOM -
    
    
    def _pre_iter(self):
        """ Actions done before iterating through the stack """
        
        if len(self.stack) == 1 and self.settings['transparency']:
            # Got only one item, so if transparent folder is enabled in
            # settings, do transparent..
            if ( (self.stack[0].key.type == nrk.SHOW_CLIP) and 
                  self.settings('transparent_media') == False ):
                return True
                 
            Log.debug('PLUGIN::SPAM -> Create transparent transparency')
            item = self.stack.pop(0)
            item.key.transparent = True
            return_object = self._iter_handler(item)
            self.state    = item.key
            self.session.swap_session(self.state.parent_session)
            self.dir.is_open = True
            self.open()
            return
        return True
    # - EOM -

    
    def _test_image(self, item):
        """ Takes care of xbmc's lack of support for thumbnails
            without file extension. Done by getting mime type from header
        """
        
        ext = self.imga.archive_image(self.state, item.thumbnail, item.key.id)
        if ext:
            match  = re.search(nrk.regex.image_identity, item.thumbnail)
            if match:
                item.thumbnail = nrk.uri.content_image(match.group('id'), ext)
                Log.debug('PLUGIN::THUMBNAIL -> new url: "%s"' % item.thumbnail)
                
        return item
    # - EOM -
    
    
    def _iter_handler(self, item):
        
        if self.settings['test_images'] is True:
            item = self._test_image(item)
            
        if item.key.type == nrk.SHOW:
            item.key.image = item.thumbnail
            
        elif item.key.type == nrk.SHOW_CLIP:
            if self.state.image is not None:
                item.thumbnail = item.key.image = self.state.image
            item = self.__set_playable(item)
            
        elif item.key.type == nrk.SHOW_FOLDER:
            if self.state.image is not None:
                item.key.image = self.state.image
            
        elif item.key.type == nrk.PLAYLIST_CLIP:
            item = self.__set_playable(item)
            
        elif item.key.type == nrk.SHOW_CLIP_INDEX:
            item = self.__set_playable(item)

            
        item.key.parent_session = self.session_key 
        
        if not item.url:
            item.url = item.key.geturl(nrk.PROGRAM)
                
        return item
    # - EOM -
   
   
    def _post_iter(self):
        self.imga.save_image_archive()
    # - EOM - 
    
   
    def __set_playable(self, item):
        item.isFolder = False
        if not item.key.transparent:
            item.isPlayable   = True
            item.key.playable = True
            
        item.key.sessionkey = self.session.session_key
        return item
    # - EOM -
    
    
    def search(self, search_string=None):
        if search_string is None:
            return
        self.key.arg = search_string
        return self.open(self.key)
    # - EOM -
    
    
# - End Of Class   

      



      
def keyboard(default="", heading="", hidden=False ):
    """ shows a keyboard and returns a value """
    
    # localize heading if it's an integer
    try:
        heading = xbmc.getLocalizedString(int(heading))
    except:
        pass
        
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return unicode(keyboard.getText(), "utf-8")           
            
            

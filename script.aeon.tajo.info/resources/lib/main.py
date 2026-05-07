#!/usr/bin/python
# coding: utf-8

########################

import sys
import xbmc
import xbmcgui

from resources.lib.helper import *
from resources.lib.tmdb import *
from resources.lib.person import *
from resources.lib.video import *
from resources.lib.season import *
from resources.lib.localdb import *

########################

class TheMovieDB(object):
    def __init__(self,call,params):
        self.monitor = xbmc.Monitor()
        self.window_stack = []
        self.dialog_cache = {}
        self.call = call
        self.tmdb_id = params.get('tmdb_id')
        self.season = params.get('season')
        self.query = remove_quotes(params.get('query'))
        self.query_year = params.get('year')
        self.exact_search = True if params.get('exact') == 'true' else False
        self.external_id = params.get('external_id')
        self.dbid = params.get('dbid')

        if self.call == 'tv':
            self.dbtype = 'tvshow'
        elif self.call == 'movie':
            self.dbtype = 'movie'

        winprop('script.aeon.tajo.info-language_code', DEFAULT_LANGUAGE)
        winprop('script.aeon.tajo.info-country_code', COUNTRY_CODE)

        busydialog()

        if self.dbid and self.dbtype:
            self.tmdb_id = self.find_id(method='dbid')
        elif self.external_id:
            self.tmdb_id = self.find_id(method='external_id')
        elif self.query:
            self.tmdb_id = self.find_id(method='query')

        if self.tmdb_id:
            self.call_params = {}

            local_media = get_local_media()
            self.call_params['local_shows'] = local_media['shows']
            self.call_params['local_movies'] = local_media['movies']

            self.entry_point()

        busydialog(close=True)


    ''' Search for tmdb_id based one a query string or external ID (IMDb or TVDb)
    '''
    def find_id(self,method):
        if method == 'dbid':
            method_details = 'VideoLibrary.Get%sDetails' % self.dbtype
            param = '%sid' % self.dbtype
            key_details = '%sdetails' % self.dbtype

            dbinfo = json_call(method_details,
                               properties=['uniqueid', 'year', 'title'],
                               params={param: int(self.dbid)}
                               )
            try:
                dbinfo = dbinfo['result'][key_details]
            except KeyError:
                return

            uniqueid = dbinfo.get('uniqueid', {})

            result = None
            for item in uniqueid:
                if uniqueid[item].startswith('tt'):
                    result = tmdb_find(self.call, uniqueid[item])
                    break

                elif self.dbtype == 'tvshow' and item.lower() == 'tvdb' and uniqueid[item]:
                    result = tmdb_find(self.call, uniqueid[item])
                    break

            if not result:
                self.query = dbinfo.get('title')
                self.query_year = dbinfo.get('year', '')

                tmdb_id = self.find_id(method='query')
                return tmdb_id

        elif method == 'external_id':
            result = tmdb_find(self.call, self.external_id)

            if not result and self.query:
                self.find_id(method='query')

        elif method == 'query':
            if ' / ' in self.query:
                query_values = self.query.split(' / ')
                position = tmdb_select_dialog_small(query_values)
                if position < 0:
                    return ''
                else:
                    self.query = query_values[position]

            result = tmdb_search(self.call, self.query, self.query_year)

            if self.exact_search:
                exact_results = []

                for item in result:
                    title = item.get('title') or item.get('name') or ''
                    original_title = item.get('original_title') or item.get('original_name') or ''

                    if title.lower() == self.query.lower() or original_title.lower() == self.query.lower():
                        if self.query_year:
                            premiered = item.get('first_air_date', '') if self.call == 'tv' else item.get('release_date', '')
                            if self.query_year == premiered[:-6]:
                                exact_results.append(item)
                        else:
                            exact_results.append(item)

                if exact_results:
                    result = exact_results
                else:
                    return ''

        try:
            if len(result) > 1:
                position = tmdb_select_dialog(result, self.call)
                if position < 0:
                    raise Exception
            else:
                position = 0

            tmdb_id = result[position]['id']

        except Exception:
            return ''

        return tmdb_id


    ''' Collect all data by the tmdb_id and build the dialogs.
    '''
    def entry_point(self):
        self.call_params['call'] = self.call
        self.call_params['tmdb_id'] = self.tmdb_id
        self.call_params['season'] = self.season
        self.request = self.call + str(self.tmdb_id)

        busydialog()

        if self.call == 'person':
            dialog = self.fetch_person()
        elif self.call == 'tv' and self.season:
            dialog = self.fetch_season()
        elif self.call == 'movie' or self.call == 'tv':
            dialog = self.fetch_video()

        busydialog(close=True)

        ''' Open next dialog if information has been found. If not open the previous dialog again.
        '''
        if dialog:
            self.dialog_cache[self.request] = dialog
            self.dialog_manager(dialog)

        elif self.window_stack:
            self.dialog_history()

        else:
            self.quit()

    def fetch_person(self):
        data = TMDBPersons(self.call_params)
        if not data['person']:
            return

        dialog = DialogPerson('script-aeon-tajo-person.xml', ADDON_PATH, 'default', '1080i',
                              person=data['person'],
                              movies=data['movies'],
                              tvshows=data['tvshows'],
                              combined=data['combined'],
                              images=data['images'],
                              tmdb_id=self.tmdb_id
                              )
        return dialog

    def fetch_video(self):
        data = TMDBVideos(self.call_params)
        if not data['details']:
            return

        dialog = DialogVideo('script-aeon-tajo-video.xml', ADDON_PATH, 'default', '1080i',
                             details=data['details'],
                             cast=data['cast'],
                             crew=data['crew'],
                             similar=data['similar'],
                             youtube=data['youtube'],
                             backdrops=data['backdrops'],
                             posters=data['posters'],
                             collection=data['collection'],
                             seasons=data['seasons'],
                             tmdb_id=self.tmdb_id
                             )
        return dialog

    def fetch_season(self):
        data = TMDBSeasons(self.call_params)
        if not data['details']:
            return

        dialog = DialogSeason('script-aeon-tajo-video.xml', ADDON_PATH, 'default', '1080i',
                              details=data['details'],
                              cast=data['cast'],
                              gueststars=data['gueststars'],
                              posters=data['posters'],
                              tmdb_id=self.tmdb_id
                              )
        return dialog


    ''' Dialog handler. Creates the window history, reopens dialogs from a stack
        or cache and is responsible for keeping the script alive.
    '''
    def dialog_manager(self,dialog):
        dialog.doModal()

        try:
            next_id = dialog['id']
            next_call = dialog['call']
            next_season = dialog['season']

            if next_call == 'youtube':
                while condition('Player.HasMedia | Window.IsVisible(busydialog) | Window.IsVisible(busydialognocancel) | Window.IsVisible(okdialog)') and not self.monitor.abortRequested():
                    self.monitor.waitForAbort(1)

                # reopen dialog after playback ended
                self.dialog_manager(dialog)

            if next_call == 'back':
                self.dialog_history()

            if next_call == 'close':
                raise Exception

            if not next_id or not next_call:
                raise Exception

            self.window_stack.append(dialog)
            self.tmdb_id = next_id
            self.call = next_call
            self.season = next_season
            self.request = next_call + str(next_id) + str(next_season)

            if self.dialog_cache.get(self.request):
                dialog = self.dialog_cache[self.request]
                self.dialog_manager(dialog)
            else:
                self.entry_point()

        except Exception:
            self.quit()

    def dialog_history(self):
        if self.window_stack:
            dialog = self.window_stack.pop()
            self.dialog_manager(dialog)
        else:
            self.quit()

    def quit(self):
        del self.call_params
        del self.window_stack
        del self.dialog_cache
        quit()


''' Person dialog
'''
class DialogPerson(xbmcgui.WindowXMLDialog):
    def __init__(self,*args,**kwargs):
        self.first_load = True
        self.action = {}

        self.tmdb_id = kwargs['tmdb_id']
        self.person = kwargs['person']
        self.movies = kwargs['movies']
        self.tvshows = kwargs['tvshows']
        self.combined = kwargs['combined']
        self.images = kwargs['images']

    def __getitem__(self,key):
        return self.action[key]

    def __setitem__(self,key,value):
        self.action[key] = value

    def onInit(self):
        execute('ClearProperty(script.aeon.tajo.info-nextcall,home)')

        if self.first_load:
            self.add_items()

    def add_items(self):
        self.first_load = False

        index = 10051
        li = [self.person, self.movies, self.tvshows, self.images, self.combined]

        for items in li:
            try:
                clist = self.getControl(index)
                clist.addItems(items)
            except RuntimeError as error:
                log('Control with id %s cannot be filled. Error --> %s' % (str(index), error), DEBUG)
                pass
            index += 1

    def onAction(self,action):
        if action.getId() in [92,10]:
            self.action['id'] = ''
            self.action['season'] = ''
            self.action['call'] = 'back' if action.getId() == 92 else 'close'
            self.quit()

    def onClick(self,controlId):
        next_id = xbmc.getInfoLabel('Container(%s).ListItem.Property(id)' % controlId)
        next_call = xbmc.getInfoLabel('Container(%s).ListItem.Property(call)' % controlId)

        if next_call in ['person','movie','tv'] and next_id:
            self.action['id'] = next_id
            self.action['call'] = next_call
            self.action['season'] = ''
            self.quit()

        elif next_call == 'image':
            FullScreenImage(controlId)

    def quit(self):
        close_action = self.getProperty('onclose')
        onnext_action = self.getProperty('onnext')
        onback_action = self.getProperty('onback_%s' % self.getFocusId())

        if self.action.get('call') and self.action.get('id'):
            execute('SetProperty(tmdb_next_call,true,home)')
            if onnext_action:
                execute(onnext_action)

        if self.action.get('call') == 'back' and onback_action:
            execute(onback_action)

        else:
            if close_action:
                execute(close_action)
            self.close()


''' Show & movie dialog
'''
class DialogVideo(xbmcgui.WindowXMLDialog):
    def __init__(self,*args,**kwargs):
        self.first_load = True
        self.action = {}

        self.tmdb_id = kwargs['tmdb_id']
        self.details = kwargs['details']
        self.cast = kwargs['cast']
        self.crew = kwargs['crew']
        self.similar = kwargs['similar']
        self.youtube = kwargs['youtube']
        self.backdrops = kwargs['backdrops']
        self.posters = kwargs['posters']
        self.seasons = kwargs['seasons']
        self.collection = kwargs['collection']

    def __getitem__(self,key):
        return self.action[key]

    def __setitem__(self,key,value):
        self.action[key] = value

    def onInit(self):
        execute('ClearProperty(script.aeon.tajo.info-nextcall,home)')

        if self.first_load:
            self.add_items()

    def add_items(self):
        self.first_load = False

        index = 10051
        li = [self.details, self.cast, self.similar, self.youtube, self.backdrops, self.crew, self.collection, self.seasons, self.posters]

        for items in li:
            try:
                clist = self.getControl(index)
                clist.addItems(items)
            except RuntimeError as error:
                log('Control with id %s cannot be filled. Error --> %s' % (str(index), error), DEBUG)
                pass
            index += 1

    def onAction(self,action):
        if action.getId() in [92,10]:
            self.action['id'] = ''
            self.action['season'] = ''
            self.action['call'] = 'back' if action.getId() == 92 else 'close'
            self.quit()

    def onClick(self,controlId):
        next_id = xbmc.getInfoLabel('Container(%s).ListItem.Property(id)' % controlId)
        next_call = xbmc.getInfoLabel('Container(%s).ListItem.Property(call)' % controlId)
        next_season = xbmc.getInfoLabel('Container(%s).ListItem.Property(call_season)' % controlId)

        if next_call in ['person','movie','tv'] and next_id:
            if next_id != str(self.tmdb_id) or next_season:
                self.action['id'] = next_id
                self.action['call'] = next_call
                self.action['season'] = next_season
                self.quit()

        elif next_call == 'image':
            FullScreenImage(controlId)

        elif next_call == 'youtube':
            self.action['id'] = ''
            self.action['season'] = ''
            self.action['call'] = 'youtube'
            xbmc.Player().play('plugin://plugin.video.youtube/play/?video_id=%s' % xbmc.getInfoLabel('Container(%s).ListItem.Property(ytid)' % controlId))
            self.quit()

    def quit(self):
        close_action = self.getProperty('onclose')
        onnext_action = self.getProperty('onnext')
        onback_action = self.getProperty('onback_%s' % self.getFocusId())

        if self.action.get('call') and self.action.get('id'):
            execute('SetProperty(script.aeon.tajo.info-nextcall,true,home)')
            if onnext_action:
                execute(onnext_action)

        if self.action.get('call') == 'back' and onback_action:
            execute(onback_action)

        else:
            if close_action:
                execute(close_action)
            self.close()


''' Season dialog
'''
class DialogSeason(xbmcgui.WindowXMLDialog):
    def __init__(self,*args,**kwargs):
        self.first_load = True
        self.action = {}

        self.tmdb_id = kwargs['tmdb_id']
        self.details = kwargs['details']
        self.cast = kwargs['cast']
        self.gueststars = kwargs['gueststars']
        self.posters = kwargs['posters']

    def __getitem__(self,key):
        return self.action[key]

    def __setitem__(self,key,value):
        self.action[key] = value

    def onInit(self):
        execute('ClearProperty(script.aeon.tajo.info-nextcall,home)')

        if self.first_load:
            self.add_items()

    def add_items(self):
        self.first_load = False

        index = [10051, 10052, 10056, 10059]
        li = [self.details, self.cast, self.gueststars, self.posters]

        for items in li:
            try:
                clist = self.getControl(index[li.index(items)])
                clist.addItems(items)
            except RuntimeError as error:
                log('Control with id %s cannot be filled. Error --> %s' % (str(index[li.index(items)]), error), DEBUG)
                pass

    def onAction(self,action):
        if action.getId() in [92,10]:
            self.action['id'] = ''
            self.action['season'] = ''
            self.action['call'] = 'back' if action.getId() == 92 else 'close'
            self.quit()

    def onClick(self,controlId):
        next_id = xbmc.getInfoLabel('Container(%s).ListItem.Property(id)' % controlId)
        next_call = xbmc.getInfoLabel('Container(%s).ListItem.Property(call)' % controlId)

        if next_call in ['person'] and next_id:
            self.action['id'] = next_id
            self.action['call'] = next_call
            self.action['season'] = ''
            self.quit()

        elif next_call == 'image':
            FullScreenImage(controlId)

    def quit(self):
        close_action = self.getProperty('onclose')
        onnext_action = self.getProperty('onnext')
        onback_action = self.getProperty('onback_%s' % self.getFocusId())

        if self.action.get('call') and self.action.get('id'):
            execute('SetProperty(script.aeon.tajo.info-nextcall,true,home)')
            if onnext_action:
                execute(onnext_action)

        if self.action.get('call') == 'back' and onback_action:
            execute(onback_action)

        else:
            if close_action:
                execute(close_action)
            self.close()


''' Slideshow dialog
'''
class FullScreenImage(object):
    def __init__(self,controlId):
        slideshow = []
        for i in range(int(xbmc.getInfoLabel('Container(%s).NumItems' % controlId))):
            slideshow.append(xbmc.getInfoLabel('Container(%s).ListItemAbsolute(%s).Art(thumb)' % (controlId,i)))

        dialog = self.ShowImage('script-aeon-tajo-image.xml', ADDON_PATH, 'default', '1080i', slideshow=slideshow, position=xbmc.getInfoLabel('Container(%s).CurrentItem' % controlId))
        dialog.doModal()
        del dialog

    class ShowImage(xbmcgui.WindowXMLDialog):
        def __init__(self,*args,**kwargs):
            self.position = int(kwargs['position']) - 1
            self.slideshow = list()
            for item in kwargs['slideshow']:
                list_item = xbmcgui.ListItem(label='')
                list_item.setArt({'icon': item})
                self.slideshow.append(list_item)

        def onInit(self):
            self.cont = self.getControl(1)
            self.cont.addItems(self.slideshow)
            self.cont.selectItem(self.position)
            self.setFocusId(2)
import re
import xbmc
import xbmcgui
import xbmcvfs
import datetime
import resources.lib.utils as utils
from json import loads
from string import Formatter
from collections import defaultdict
from resources.lib.plugin import Plugin
from resources.lib.kodilibrary import KodiLibrary
from resources.lib.traktapi import TraktAPI
from resources.lib.listitem import ListItem
try:
    from urllib.parse import quote_plus, quote  # Py3
except ImportError:
    from urllib import quote_plus, quote  # Py2


def string_format_map(fmt, d):
    try:
        str.format_map
    except AttributeError:
        parts = Formatter().parse(fmt)
        return fmt.format(**{part[1]: d[part[1]] for part in parts})
    else:
        return fmt.format(**d)


class Player(Plugin):
    def __init__(self):
        super(Player, self).__init__()
        self.traktapi = TraktAPI()
        self.search_movie, self.search_episode, self.play_movie, self.play_episode = [], [], [], []
        self.item = defaultdict(lambda: '+')
        self.itemlist, self.actions, self.players, self.identifierlist = [], [], {}, []
        self.is_local = None
        self.dp_local = self.addon.getSettingBool('default_player_local')
        self.dp_movies = self.addon.getSettingString('default_player_movies')
        self.dp_episodes = self.addon.getSettingString('default_player_episodes')
        self.dp_movies_id = None
        self.dp_episodes_id = None
        self.fallbacks = {}

    def setup_players(self, tmdbtype=None, details=False, clearsetting=False, assertplayers=True):
        self.build_players(tmdbtype)
        if details:
            self.build_details()
        self.build_selectbox(clearsetting, assertplayers)

    def get_fallback(self, dp_file, dp_action):
        fallback = self.players.get(dp_file, {}).get('fallback', {}).get(dp_action)
        if not fallback:  # No fallback so prompt dialog
            utils.kodi_log(u'Player -- {} {}\nFallback not set!'.format(dp_file, dp_action), 2)
            return xbmcgui.Dialog().select(self.addon.getLocalizedString(32042), self.itemlist)
        if fallback in self.identifierlist:  # Found a fallback in list so play that
            utils.kodi_log(u'Player -- {} {}\nFallback found: {}'.format(dp_file, dp_action, fallback), 2)
            return self.identifierlist.index(fallback)
        fb_file, fb_action = fallback.split()
        utils.kodi_log(u'Player -- {} {}\nFallback NOT found!\n{}'.format(dp_file, dp_action, fallback), 2)
        return self.get_fallback(fb_file, fb_action)  # Fallback not in list so let's check fallback's fallback

    def get_playerindex(self, force_dialog=False):
        if force_dialog or (self.itemtype == 'movie' and not self.dp_movies) or (self.itemtype == 'episode' and not self.dp_episodes):
            idx = xbmcgui.Dialog().select(self.addon.getLocalizedString(32042), self.itemlist)  # Ask user to select player
            if self.itemtype == 'movie':
                self.dp_movies = self.itemlist[idx].getLabel()
                self.dp_movies_id = self.identifierlist[idx]
                utils.kodi_log(u'Player -- User selected {}\n{}'.format(self.dp_movies, self.dp_movies_id), 2)
            elif self.itemtype == 'episode':
                self.dp_episodes = self.itemlist[idx].getLabel()
                self.dp_episodes_id = self.identifierlist[idx]
                utils.kodi_log(u'Player -- User selected {}\n{}'.format(self.dp_episodes, self.dp_episodes_id), 2)
            return idx

        for i in range(0, len(self.itemlist)):
            label = self.itemlist[i].getLabel()
            if (
                    (label == self.dp_movies and self.itemtype == 'movie') or
                    (label == self.dp_episodes and self.itemtype == 'episode') or
                    (label == u'{0} {1}'.format(self.addon.getLocalizedString(32061), 'Kodi') and self.dp_local)):
                utils.kodi_log(u'Player -- Attempting to Play with Default Player:\n {}'.format(label), 2)
                return i  # Play local or with default player if found

        # Check for fallbacks
        utils.kodi_log(u'Player -- Checking for Fallbacks', 2)
        if self.itemtype == 'movie' and self.dp_movies_id:
            dp_file, dp_action = self.dp_movies_id.split()
            return self.get_fallback(dp_file, dp_action)
        if self.itemtype == 'episode' and self.dp_episodes_id:
            dp_file, dp_action = self.dp_episodes_id.split()
            return self.get_fallback(dp_file, dp_action)

        return -1

    def play_external(self, force_dialog=False, playerindex=-1):
        if playerindex > -1:  # Previous iteration didn't find an item to play so remove it and retry
            xbmcgui.Dialog().notification(self.itemlist[playerindex].getLabel(), self.addon.getLocalizedString(32040))
            del self.actions[playerindex]  # Item not found so remove the player's action list
            del self.itemlist[playerindex]  # Item not found so remove the player's select dialog entry
            del self.identifierlist[playerindex]  # Item not found so remove the player's index

        playerindex = self.get_playerindex(force_dialog=force_dialog)

        # User cancelled dialog
        if not playerindex > -1:
            utils.kodi_log(u'Player -- User cancelled', 2)
            return False

        player = self.actions[playerindex]
        if not player or not player[1]:
            utils.kodi_log(u'Player -- Player not found!', 2)
            return False

        # External player has list of actions so let's iterate through them to find our item
        resolve_url = False
        if isinstance(player[1], list):
            actionlist = player[1]
            player = (False, actionlist[0])
            for d in actionlist[1:]:
                if player[0]:
                    break  # Playable item was found in last action so let's break and play it

                with utils.busy_dialog():
                    folder = KodiLibrary().get_directory(string_format_map(player[1], self.item))  # Get the next folder from the plugin

                if d.get('dialog'):  # Special option to show dialog of items to select from
                    d_items = []
                    for f in folder:  # Create our list of items
                        if not f.get('label') or f.get('label') == 'None':
                            continue
                        lb_list = []
                        label_a = f.get('label')
                        if f.get('year') and f.get('year') != 1601:
                            label_a = u'{} ({})'.format(label_a, f.get('year'))
                        if utils.try_parse_int(f.get('season', 0)) > 0 and utils.try_parse_int(f.get('episode', 0)) > 0:
                            label_a = u'{}x{}. {}'.format(f.get('season'), f.get('episode'), label_a)
                        if f.get('streamdetails'):
                            sdv_list = f.get('streamdetails', {}).get('video', [{}]) or [{}]
                            sda_list = f.get('streamdetails', {}).get('audio', [{}]) or [{}]
                            sdv, sda = sdv_list[0], sda_list[0]
                            if sdv.get('width') or sdv.get('height'):
                                lb_list.append(u'{}x{}'.format(sdv.get('width'), sdv.get('height')))
                            if sdv.get('codec'):
                                lb_list.append(u'{}'.format(sdv.get('codec', '').upper()))
                            if sda.get('codec'):
                                lb_list.append(u'{}'.format(sda.get('codec', '').upper()))
                            if sda.get('channels'):
                                lb_list.append(u'{} CH'.format(sda.get('channels', '')))
                            for i in sda_list:
                                if i.get('language'):
                                    lb_list.append(u'{}'.format(i.get('language', '').upper()))
                            if sdv.get('duration'):
                                lb_list.append(u'{} mins'.format(utils.try_parse_int(sdv.get('duration', 0)) // 60))
                        if f.get('size'):
                            lb_list.append(u'{}'.format(utils.normalise_filesize(f.get('size', 0))))
                        label_b = ' | '.join(lb_list) if lb_list else ''
                        d_items.append(ListItem(label=label_a, label2=label_b, icon=f.get('thumbnail')).set_listitem())
                    if d_items:
                        idx = 0
                        if d.get('dialog', '').lower() != 'auto' or len(d_items) != 1:
                            idx = xbmcgui.Dialog().select('Select Item', d_items, useDetails=True)
                        if idx == -1:  # User exited the dialog so return and do nothing
                            return
                        resolve_url = True if folder[idx].get('filetype') == 'file' else False  # Set true for files so we can play
                        player = (resolve_url, folder[idx].get('file'))  # Set the folder path to open/play
                        break  # Move onto next action
                    else:  # Ask user to select a different player if no items in dialog
                        return self.play_external(force_dialog=force_dialog, playerindex=playerindex)

                x = 0
                utils.kodi_log('Player -- Retrieved Folder\n{}'.format(string_format_map(player[1], self.item)), 2)
                for f in folder:  # Iterate through plugin folder looking for a matching item
                    x += 1  # Keep an index for position matching
                    for k, v in d.items():  # Iterate through our key (infolabel) / value (infolabel must match) pairs of our action
                        if k == 'position':  # We're looking for an item position not an infolabel
                            if utils.try_parse_int(string_format_map(v, self.item)) != x:  # Format our position value
                                break  # Not the item position we want so let's go to next item in folder
                        elif not f.get(k) or not re.match(string_format_map(v, self.item), u'{}'.format(f.get(k, ''))):  # Format our value and check if it regex matches the infolabel key
                            break  # Item's key value doesn't match value we are looking for so let's got to next item in folder
                    else:  # Item matched our criteria so let's open it up
                        utils.kodi_log('Player -- Found Match!\n{}'.format(f), 2)
                        resolve_url = True if f.get('filetype') == 'file' else False  # Set true for files so we can play
                        player = (resolve_url, f.get('file'))  # Get ListItem.FolderPath for item
                        break  # Move onto next action (either open next folder or play file)
                else:
                    utils.kodi_log('Player -- Failed to find match!\n{}'.format(d), 2)
                    return self.play_external(force_dialog=force_dialog, playerindex=playerindex)  # Ask user to select a different player

        # Play/Search found item
        if player and player[1]:
            action = string_format_map(player[1], self.item)
            if player[0] and action.endswith('.strm'):  # Action is play and is a strm so PlayMedia
                utils.kodi_log(u'Player -- Found strm.\nAttempting PLAYMEDIA({})'.format(action), 2)
                xbmc.executebuiltin(utils.try_decode_string(u'PlayMedia({0})'.format(action)))
            elif player[0]:  # Action is play and not a strm so play with player
                utils.kodi_log(u'Player -- Found file.\nAttempting to PLAY: {}'.format(action), 2)
                xbmc.Player().play(action, ListItem(library='video', **self.details).set_listitem())
            else:
                action = u'Container.Update({0})'.format(action) if xbmc.getCondVisibility("Window.IsMedia") else u'ActivateWindow(videos,{0},return)'.format(action)
                utils.kodi_log(u'Player -- Found folder.\nAttempting to OPEN: {}'.format(action), 2)
                xbmc.executebuiltin(utils.try_decode_string(action))
            return action

    def play(self, itemtype, tmdb_id, season=None, episode=None, force_dialog=False):
        """ Entry point for player method """
        if not tmdb_id or not itemtype:
            return

        with utils.busy_dialog():
            # Get the details for the item
            self.itemtype, self.tmdb_id, self.season, self.episode = itemtype, tmdb_id, season, episode
            self.tmdbtype = 'tv' if self.itemtype in ['episode', 'tv'] else 'movie'
            self.details = self.tmdb.get_detailed_item(self.tmdbtype, tmdb_id, season=season, episode=episode)
            self.item['tmdb_id'] = self.tmdb_id
            self.item['imdb_id'] = self.details.get('infoproperties', {}).get('tvshow.imdb_id') or self.details.get('infoproperties', {}).get('imdb_id')
            self.item['tvdb_id'] = self.details.get('infoproperties', {}).get('tvshow.tvdb_id') or self.details.get('infoproperties', {}).get('tvdb_id')
            self.item['originaltitle'] = self.details.get('infolabels', {}).get('originaltitle')
            self.item['title'] = self.details.get('infolabels', {}).get('tvshowtitle') or self.details.get('infolabels', {}).get('title')
            self.item['year'] = self.details.get('infolabels', {}).get('year')

            # Check if we have a local file
            # TODO: Add option to auto play local
            if self.details and self.itemtype == 'movie':
                self.is_local = self.localmovie()
            if self.details and self.itemtype == 'episode':
                self.is_local = self.localepisode()

            self.setup_players(details=True)

        if not self.itemlist:
            return False

        return self.play_external(force_dialog=force_dialog)

    def build_details(self):
        self.item['id'] = self.tmdb_id
        self.item['tmdb'] = self.tmdb_id
        self.item['imdb'] = self.details.get('infolabels', {}).get('imdbnumber')
        self.item['name'] = u'{0} ({1})'.format(self.item.get('title'), self.item.get('year'))
        self.item['firstaired'] = self.details.get('infolabels', {}).get('premiered')
        self.item['premiered'] = self.details.get('infolabels', {}).get('premiered')
        self.item['released'] = self.details.get('infolabels', {}).get('premiered')
        self.item['showname'] = self.item.get('title')
        self.item['clearname'] = self.item.get('title')
        self.item['tvshowtitle'] = self.item.get('title')
        self.item['title'] = self.item.get('title')
        self.item['thumbnail'] = self.details.get('thumb')
        self.item['poster'] = self.details.get('poster')
        self.item['fanart'] = self.details.get('fanart')
        self.item['now'] = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')

        if self.traktapi:
            slug_type = utils.type_convert(self.tmdbtype, 'trakt')
            trakt_details = self.traktapi.get_details(slug_type, self.traktapi.get_traktslug(slug_type, 'tmdb', self.tmdb_id))
            self.item['trakt'] = trakt_details.get('ids', {}).get('trakt')
            self.item['imdb'] = self.details.get('infoproperties', {}).get('tvshow.imdb_id') or trakt_details.get('ids', {}).get('imdb')
            self.item['tvdb'] = self.details.get('infoproperties', {}).get('tvshow.tvdb_id') or trakt_details.get('ids', {}).get('tvdb')
            self.item['slug'] = trakt_details.get('ids', {}).get('slug')

        if self.itemtype == 'episode':  # Do some special episode stuff
            self.item['id'] = self.item.get('tvdb')
            self.item['title'] = self.details.get('infolabels', {}).get('title')  # Set Episode Title
            self.item['name'] = u'{0} S{1:02d}E{2:02d}'.format(self.item.get('showname'), int(utils.try_parse_int(self.season)), int(utils.try_parse_int(self.episode)))
            self.item['season'] = self.season
            self.item['episode'] = self.episode

        if self.traktapi and self.itemtype == 'episode':
            trakt_details = self.traktapi.get_details(slug_type, self.item.get('slug'), season=self.season, episode=self.episode)
            self.item['epid'] = self.details.get('infoproperties', {}).get('tvdb_id') or trakt_details.get('ids', {}).get('tvdb')
            self.item['epimdb'] = trakt_details.get('ids', {}).get('imdb')
            self.item['eptmdb'] = self.details.get('infoproperties', {}).get('tmdb_id') or trakt_details.get('ids', {}).get('tmdb')
            self.item['eptrakt'] = trakt_details.get('ids', {}).get('trakt')

        utils.kodi_log(u'Player Details - Item:\n{}'.format(self.item), 2)

        for k, v in self.item.copy().items():
            if k not in ['name', 'showname', 'clearname', 'tvshowtitle', 'title', 'thumbnail', 'poster', 'fanart', 'originaltitle']:
                continue
            v = u'{0}'.format(v)
            self.item[k] = v.replace(',', '')
            self.item[k + '_+'] = v.replace(' ', '+')
            self.item[k + '_-'] = v.replace(' ', '-')
            self.item[k + '_escaped'] = quote(quote(utils.try_encode_string(v)))
            self.item[k + '_escaped+'] = quote(quote_plus(utils.try_encode_string(v)))
            self.item[k + '_url'] = quote(utils.try_encode_string(v))
            self.item[k + '_url+'] = quote_plus(utils.try_encode_string(v))

    def build_players(self, tmdbtype=None):
        basedirs = ['special://profile/addon_data/plugin.video.themoviedb.helper/players/']
        if self.addon.getSettingBool('bundled_players'):
            basedirs.append('special://home/addons/plugin.video.themoviedb.helper/resources/players/')
        for basedir in basedirs:
            files = [x for x in xbmcvfs.listdir(basedir)[1] if x.endswith('.json')]
            for file in files:
                vfs_file = xbmcvfs.File(basedir + file)
                try:
                    content = vfs_file.read()
                    meta = loads(content) or {}
                finally:
                    vfs_file.close()

                self.players[file] = meta
                if not meta.get('plugin') or not xbmc.getCondVisibility(u'System.HasAddon({0})'.format(meta.get('plugin'))):
                    continue  # Don't have plugin so skip

                tmdbtype = tmdbtype or self.tmdbtype
                priority = utils.try_parse_int(meta.get('priority')) or 1000
                if tmdbtype == 'movie' and meta.get('search_movie'):
                    self.search_movie.append((file, priority))
                if tmdbtype == 'movie' and meta.get('play_movie'):
                    self.play_movie.append((file, priority))
                if tmdbtype == 'tv' and meta.get('search_episode'):
                    self.search_episode.append((file, priority))
                if tmdbtype == 'tv' and meta.get('play_episode'):
                    self.play_episode.append((file, priority))

    def build_playeraction(self, playerfile, action, assertplayers=True):
        player = self.players.get(playerfile, {})
        isplay = True if action.startswith('play_') else False
        prefix = self.addon.getLocalizedString(32061) if action.startswith('play_') else xbmc.getLocalizedString(137)
        label = u'{0} {1}'.format(prefix, player.get('name', ''))

        # Check if matches default player and set default player id
        if label == self.dp_movies:
            self.dp_movies_id = '{} {}'.format(playerfile, action)
        if label == self.dp_episodes:
            self.dp_episodes_id = '{} {}'.format(playerfile, action)

        # Check that asserted values exist
        if assertplayers:
            for i in player.get('assert', {}).get(action, []):
                if i.startswith('!'):
                    if self.item.get(i[1:]) and self.item.get(i[1:]) != 'None':
                        return  # inverted assert - has value but we don't want it so don't build that player
                else:
                    if not self.item.get(i) or self.item.get(i) == 'None':
                        return  # missing / empty asserted value so don't build that player

        # Add player action to list for dialog
        self.append_playeraction(
            label=label, action=player.get(action, ''), isplay=isplay,
            identifier='{} {}'.format(playerfile, action))

    def append_playeraction(self, label, action, isplay=True, identifier=''):
        self.itemlist.append(xbmcgui.ListItem(label))
        self.actions.append((isplay, action))
        self.identifierlist.append(identifier)

    def build_selectbox(self, clearsetting=False, assertplayers=True):
        self.itemlist, self.actions = [], []
        if clearsetting:
            self.itemlist.append(xbmcgui.ListItem(xbmc.getLocalizedString(13403)))  # Clear Default
        if self.is_local:
            self.append_playeraction(u'{0} {1}'.format(self.addon.getLocalizedString(32061), 'Kodi'), self.is_local, identifier='play_kodi')
        for i in sorted(self.play_movie, key=lambda x: x[1]):
            self.build_playeraction(i[0], 'play_movie', assertplayers=assertplayers)
        for i in sorted(self.search_movie, key=lambda x: x[1]):
            self.build_playeraction(i[0], 'search_movie', assertplayers=assertplayers)
        for i in sorted(self.play_episode, key=lambda x: x[1]):
            self.build_playeraction(i[0], 'play_episode', assertplayers=assertplayers)
        for i in sorted(self.search_episode, key=lambda x: x[1]):
            self.build_playeraction(i[0], 'search_episode', assertplayers=assertplayers)
        utils.kodi_log(u'Player -- Built {} Players!\n{}'.format(
            len(self.itemlist), self.identifierlist), 2)

    def localfile(self, file):
        if not file:
            return
        if file.endswith('.strm'):
            f = xbmcvfs.File(file)
            contents = f.read()
            f.close()
            if contents.startswith('plugin://plugin.video.themoviedb.helper'):
                return
        return file

    def localmovie(self):
        # fuzzy_match = self.addon.getSettingBool('fuzzymatch_movie')
        return self.localfile(KodiLibrary(dbtype='movie').get_info(
            'file', fuzzy_match=False,
            tmdb_id=self.item.get('tmdb_id'),
            imdb_id=self.item.get('imdb_id')))

    def localepisode(self):
        # fuzzy_match = self.addon.getSettingBool('fuzzymatch_tv')
        dbid = KodiLibrary(dbtype='tvshow').get_info(
            'dbid', fuzzy_match=False,
            tmdb_id=self.item.get('tmdb_id'),
            tvdb_id=self.item.get('tvdb_id'),
            imdb_id=self.item.get('imdb_id'))
        return self.localfile(KodiLibrary(dbtype='episode', tvshowid=dbid).get_info(
            'file', season=self.season, episode=self.episode))

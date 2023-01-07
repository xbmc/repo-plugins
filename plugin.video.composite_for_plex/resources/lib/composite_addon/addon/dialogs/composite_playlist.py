# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import os
import random
from itertools import chain
from itertools import groupby

import pyxbmct.addonwindow as pyxbmct  # pylint: disable=import-error
from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error
from six import PY3
from six.moves import zip_longest

from ...addon.constants import CONFIG
from ...addon.containers import Item
from ...addon.items.episode import create_episode_item
from ...addon.items.movie import create_movie_item
from ...addon.logger import Logger
from ...addon.strings import i18n
from .progress_dialog import ProgressDialog

ACTION_STOP = 13

ACTIVE_DIALOG_PROPERTY = '-'.join([CONFIG['id'], 'dialog_active'])

LOG = Logger('composite_playlist')


class AlreadyActiveException(Exception):
    pass


class CompositePlaylistWindow(pyxbmct.AddonFullWindow):  # pylint: disable=too-many-instance-attributes

    def __init__(self, context=None, window=None):
        self.title = i18n('Composite Playlist')
        self.description_label = i18n('Generate a playlist from the information below')

        super(CompositePlaylistWindow, self).__init__(self.title)  # pylint: disable=super-with-arguments

        self._context = context
        self.window = window

        self.player = xbmc.Player()

        self.playlist_data = {
            'content': 'tvshows',
            'item_count': 50,
            'servers': [(i18n('All Servers'), None)],
            'source': (i18n('On Deck'), 'on_deck'),
            'shuffle': False
        }

        self._servers = []
        self._sources = [
            (i18n('All'), 'all'),
            (i18n('On Deck'), 'on_deck'),
            (i18n('Recently Added'), 'recent_added'),
            (i18n('Recently Released'), 'recent_released'),
        ]
        self._item_counts = ['1', '5', '10', '25', '50', '100', '250', '500', '1000']

        self.description = pyxbmct.Label(self.description_label, alignment=0)

        self.movies_radio = pyxbmct.RadioButton(self.bold(i18n('Movies')))
        self.tvshows_radio = pyxbmct.RadioButton(self.bold(i18n('TV Shows')))
        self.mixed_radio = pyxbmct.RadioButton(self.bold(i18n('Mixed')))

        self.item_count_label = pyxbmct.Label(self.bold(i18n('Item Count')), alignment=0)
        self.item_count = pyxbmct.Label(str(self.playlist_data['item_count']), alignment=1)
        self.item_count_list = pyxbmct.List()

        self.server_label = pyxbmct.Label(self.bold(i18n('Server(s)')), alignment=0)
        self.server_choice_label = pyxbmct.FadeLabel()
        self.server_list = pyxbmct.List()

        self.source_label = pyxbmct.Label(self.bold(i18n('Source')))
        self.source_choice_label = pyxbmct.FadeLabel()
        self.source_list = pyxbmct.List()

        self.shuffle_radio = pyxbmct.RadioButton(self.bold(i18n('Shuffle')))

        self.cancel_button = pyxbmct.Button(i18n('Cancel'))
        self.play_button = pyxbmct.Button(i18n('Play'))

        self.generated = False

    def __enter__(self):
        if self.window.getProperty(ACTIVE_DIALOG_PROPERTY) == 'true':
            raise AlreadyActiveException

        self.window.setProperty(ACTIVE_DIALOG_PROPERTY, 'true')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.window.clearProperty(ACTIVE_DIALOG_PROPERTY)

    @staticmethod
    def bold(value):
        return value.join(['[B]', '[/B]'])

    @staticmethod
    def color(string_color, value):
        return value.join(['[COLOR=%s]' % string_color, '[/COLOR]'])

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, value):
        self._context = value

    def start(self):
        xbmc.executebuiltin('Dialog.Close(all,true)')

        self.setGeometry(690, 550, 55, 69)

        self.set_controls()

        self.set_navigation()

        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)
        self.connect(ACTION_STOP, self.close)

        self.doModal()

        return self.generated

    def set_controls(self):
        self.placeControl(self.description, 3, 3, columnspan=64)

        self.placeControl(self.movies_radio, 9, 3, columnspan=18, rowspan=5)
        self.movies_radio.setSelected(self.playlist_data['content'] == 'movies')
        self.connect(self.movies_radio, self.c_movies_radio)

        self.placeControl(self.tvshows_radio, 13, 3, columnspan=18, rowspan=5)
        self.tvshows_radio.setSelected(self.playlist_data['content'] == 'tvshows')
        self.connect(self.tvshows_radio, self.c_tvshows_radio)

        self.placeControl(self.mixed_radio, 17, 3, columnspan=18, rowspan=5)
        self.mixed_radio.setSelected(self.playlist_data['content'] == 'mixed')
        self.connect(self.mixed_radio, self.c_mixed_radio)

        self.placeControl(self.item_count_label, 24, 3, columnspan=15)
        self.placeControl(self.item_count, 24, 15, columnspan=7)
        self.placeControl(self.item_count_list, 27, 3, columnspan=18, rowspan=25)
        self.item_count_list.addItems(self._item_counts)
        self.connect(self.item_count_list, self.c_select_count)

        self.placeControl(self.server_label, 9, 25, columnspan=12)
        self.placeControl(self.server_list, 12, 25, columnspan=31, rowspan=15)
        self.server_list.addItems(self.g_servers())
        self.connect(self.server_list, self.c_select_server)

        self.placeControl(self.source_label, 24, 25, columnspan=12)
        self.placeControl(self.source_choice_label, 24, 37, columnspan=19)
        self.source_choice_label.addLabel(self.playlist_data['source'][0])
        self.placeControl(self.source_list, 27, 25, columnspan=31, rowspan=17)
        self.source_list.addItems([name for name, _ in self._sources])
        self.connect(self.source_list, self.c_select_source)

        self.placeControl(self.shuffle_radio, 43, 25, columnspan=18, rowspan=5)
        self.shuffle_radio.setSelected(self.playlist_data['shuffle'])
        self.connect(self.shuffle_radio, self.c_shuffle_radio)

        self.placeControl(self.play_button, 12, 59, columnspan=12, rowspan=5)
        self.connect(self.play_button, self.c_play)

        self.placeControl(self.cancel_button, 17, 59, columnspan=12, rowspan=5)
        self.connect(self.cancel_button, self.close)

    def c_play(self):
        playlist_generator = PlaylistGenerator(context=self.context, data=self.playlist_data)
        item = playlist_generator.generate()
        self.generated = False
        if item:
            self.generated = True
            self.close()

    def c_movies_radio(self):
        self.playlist_data.update({
            'content': 'movies'
        })
        self.movies_radio.setSelected(True)
        self.tvshows_radio.setSelected(False)
        self.mixed_radio.setSelected(False)

    def c_tvshows_radio(self):
        self.playlist_data.update({
            'content': 'tvshows'
        })
        self.tvshows_radio.setSelected(True)
        self.mixed_radio.setSelected(False)
        self.movies_radio.setSelected(False)

    def c_mixed_radio(self):
        self.playlist_data.update({
            'content': 'mixed'
        })
        self.mixed_radio.setSelected(True)
        self.movies_radio.setSelected(False)
        self.tvshows_radio.setSelected(False)

    def c_shuffle_radio(self):
        self.playlist_data.update({
            'shuffle': self.shuffle_radio.isSelected()
        })

    def c_select_count(self):
        self.playlist_data.update({
            'item_count': int(self._item_counts[self.item_count_list.getSelectedPosition()])
        })
        self.item_count.setLabel(str(self.playlist_data['item_count']))

    def c_select_server(self):
        if self.server_list.getSelectedPosition() == 0:
            servers = [(i18n('All Servers'), None)]
        else:
            servers = self.playlist_data.get('servers', [])
            try:
                servers.remove((i18n('All Servers'), None))
            except ValueError:
                pass
            selected_server = self._servers[self.server_list.getSelectedPosition()]
            if selected_server in servers:
                if len(servers) > 1:
                    try:
                        servers.remove(selected_server)
                    except ValueError:
                        pass
            else:
                servers.append(self._servers[self.server_list.getSelectedPosition()])

        self.playlist_data.update({
            'servers': servers
        })
        self.server_list.reset()
        server_labels = [self.color('cyan', name)
                         if (name, uuid) in self.playlist_data.get('servers', [])
                         else name
                         for name, uuid in self._servers]
        self.server_list.addItems(server_labels)
        self.server_list.selectItem(self.server_list.getSelectedPosition())

    def g_servers(self):
        server_list = self.context.plex_network.get_server_list()
        self._servers = [(i18n('All Servers'), None)]
        for server in server_list:
            server_name = server.get_name()
            server_uuid = server.get_uuid()
            if server_name and server_uuid:
                self._servers += [(server_name, server_uuid)]
        return [self.color('cyan', name) if uuid is None else name
                for name, uuid in self._servers]

    def c_select_source(self):
        self.playlist_data.update({
            'source': self._sources[self.source_list.getSelectedPosition()]
        })
        self.source_choice_label.reset()
        self.source_choice_label.addLabel(str(self.playlist_data['source'][0]))

    def set_navigation(self):
        self.movies_radio.setNavigation(self.play_button, self.tvshows_radio,
                                        self.play_button, self.server_list)

        self.tvshows_radio.setNavigation(self.movies_radio, self.mixed_radio,
                                         self.movies_radio, self.server_list)

        self.mixed_radio.setNavigation(self.tvshows_radio, self.item_count_list,
                                       self.tvshows_radio, self.server_list)

        self.item_count_list.setNavigation(self.mixed_radio, self.server_list,
                                           self.mixed_radio, self.source_list)

        self.server_list.setNavigation(self.item_count_list, self.source_list,
                                       self.movies_radio, self.play_button)

        self.source_list.setNavigation(self.server_list, self.shuffle_radio,
                                       self.item_count_list, self.play_button)

        self.shuffle_radio.setNavigation(self.source_list, self.play_button,
                                         self.item_count_list, self.play_button)

        self.play_button.setNavigation(self.cancel_button, self.cancel_button,
                                       self.server_list, self.movies_radio)

        self.cancel_button.setNavigation(self.play_button, self.play_button,
                                         self.server_list, self.movies_radio)

        self.setFocus(self.movies_radio)


class PlaylistGenerator:

    def __init__(self, context, data):
        self.context = context
        self.data = data

        self.plex_network = context.plex_network

        self._content = data['content']
        self._item_count = data['item_count']
        self._servers = data['servers']
        self._source = data['source'][1]
        self._shuffle = data['shuffle']
        LOG.debug('PlaylistGenerator initialized: content=%s, item_count=%d, '
                  'servers=%s, source=%s, shuffle=%s' %
                  (self.content, self.item_count, self.servers,
                   self.source, str(self.shuffle)))

    @property
    def content(self):
        return self._content

    @property
    def item_count(self):
        return int(self._item_count)

    @property
    def servers(self):
        return self._servers

    @property
    def source(self):
        return self._source

    @property
    def shuffle(self):
        return bool(self._shuffle)

    @property
    def content_types(self):
        return ['tvshows', 'movies'] if self.content == 'mixed' else [self.content]

    def generate(self):
        with ProgressDialog(i18n('Generating Playlist'), i18n('This may take a while...')) as \
                progress_dialog:

            progress_dialog.update(0, i18n('Retrieving server list...'))
            servers = self._get_servers()
            if progress_dialog.is_canceled():
                return None

            progress_dialog.update(10, i18n('Retrieving server sections...'))
            sections = self._get_sections(servers, progress_dialog)
            if progress_dialog.is_canceled():
                return None

            progress_dialog.update(20, i18n('Retrieving content metadata...'))
            item_collections = self._get_item_collections(sections, progress_dialog)
            if progress_dialog.is_canceled():
                return None

            progress_dialog.update(60, i18n('Retrieving final sample...'))
            items = self._get_sample(item_collections)
            if progress_dialog.is_canceled():
                return None

            progress_dialog.update(70, i18n('Adding items to playlist...'))
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()

            _divisor, _percent_value = self._get_progress_data(items, 29)
            _percent = progress_dialog.percent

            for index, item in enumerate(items):
                if progress_dialog.is_canceled():
                    return None

                if index % _divisor == 0:
                    _percent += _percent_value
                progress_dialog.update(_percent,
                                       i18n('Adding %s to playlist...') % item[1].getLabel())

                playlist.add(*item)

            if progress_dialog.is_canceled():
                return None

            progress_dialog.update(100, i18n('Completed.'))
            xbmc.sleep(500)
            return items[0]

    def _get_progress_data(self, items, percent):
        item_count = len(items)
        _divisor = self._limiter(int(item_count // percent), lower_limit=1)
        _percent_value = self._limiter(int(percent // item_count), lower_limit=1)
        return _divisor, _percent_value

    def _get_servers(self):
        if len(self.servers) == 1 and self.servers[0][1] is None:
            return self.plex_network.get_server_list()

        return [self.plex_network.get_server_from_uuid(uuid)
                for _, uuid in self.servers if uuid is not None]

    def _get_sections(self, servers, dialog):
        server_sections = []
        for server in servers:
            sections = server.get_sections()

            _divisor, _percent_value = self._get_progress_data(sections, 4)
            _percent = dialog.percent

            for index, section in enumerate(sections):
                if dialog.is_canceled():
                    return None

                if index % _divisor == 0:
                    _percent += _percent_value
                dialog.update(_percent, i18n('Checking section %s on %s...') %
                              (section.get_title(), server.get_name()))

                if section.content_type() in self.content_types:
                    server_sections.append((server, section))

        return server_sections

    def _get_item_collection(self, server, tree):
        if PY3:
            branches = tree.iter('Video')
        else:
            branches = tree.getiterator('Video')

        if branches is None:
            return []

        if tree.get('viewGroup') == 'show':
            branches = self._get_distributed_tvshows(branches)

        item_collection = []
        for content in branches:
            item = Item(server, server.get_url_location(), tree, content, up_next=False)
            if content.get('type') == 'episode':
                item_collection.append((server, create_episode_item(self.context, item)))
            elif content.get('type') == 'movie':
                item_collection.append((server, create_movie_item(self.context, item)))

        return item_collection

    def _get_item_collections(self, sections, dialog):
        _trees = self._get_section_trees(sections, dialog)
        if not _trees:
            return []

        server_collections = self._get_distributed_by_server(_trees)

        _divisor, _percent_value = self._get_progress_data(server_collections, 4)
        _percent = dialog.percent

        _index = 0
        item_collections = []
        new_item_collections = []
        for _, trees in server_collections.items():
            if dialog.is_canceled():
                return None

            for _server, tree in trees:
                if dialog.is_canceled():
                    return None

                if _index % _divisor == 0:
                    _percent += _percent_value

                dialog.update(_percent, i18n('Retrieving %s from %s for sample...') %
                              (tree.get('librarySectionTitle'), _server.get_name()))

                new_item_collections.append((_server, tree))

                _index += 1

        if new_item_collections:
            _divisor, _percent_value = self._get_progress_data(new_item_collections, 15)

            for index, (server, tree) in enumerate(new_item_collections):
                if dialog.is_canceled():
                    return None

                if index % _divisor == 0:
                    _percent += _percent_value

                dialog.update(_percent, i18n('Creating samples...'))

                item_collection = self._get_item_collection(server, tree)
                if not item_collection:
                    continue

                item_collections.append(item_collection)

        return item_collections

    def _get_section_trees(self, sections, dialog):
        trees = []

        _divisor, _percent_value = self._get_progress_data(sections, 20)
        _percent = dialog.percent

        for index, (server, section) in enumerate(sections):
            if dialog.is_canceled():
                return None

            if index % _divisor == 0:
                _percent += _percent_value

            tree = None
            if self.source == 'all':
                dialog.update(_percent,
                              i18n('Retrieving section data for %s...') % section.get_title())
                if section.content_type() == 'tvshows':
                    tree = (server, server.get_section_all(int(section.get_key()), item_type=4))
                else:
                    tree = (server, server.get_section_all(int(section.get_key())))
            elif self.source == 'on_deck':
                dialog.update(_percent,
                              i18n('Retrieving section data for %s...') % section.get_title())
                tree = (server, server.get_ondeck(section=int(section.get_key())))
            elif self.source == 'recent_added':
                dialog.update(_percent,
                              i18n('Retrieving section data for %s...') % section.get_title())
                tree = (server, server.get_recently_added(section=int(section.get_key())))
            elif self.source == 'recent_released':
                dialog.update(_percent,
                              i18n('Retrieving section data for %s...') % section.get_title())
                tree = (server, server.get_newest(section=int(section.get_key())))

            if not tree:
                continue

            trees.append(tree)

        return trees

    def _get_sample(self, item_collections):
        if self.shuffle:
            samples = self._get_shuffled_sample(item_collections)
        else:
            samples = self._get_selection_sample(item_collections)

        return [(sample[1][0], sample[1][1]) for sample in samples if sample is not None]

    @staticmethod
    def _get_distributed_by_server(trees):
        server_collections = {}

        _collections = groupby(trees, key=lambda x: x[0].get_uuid())
        for server_uuid, collection in _collections:
            server_collections[server_uuid] = list(collection)

        return server_collections

    def _get_distributed_tvshows(self, branches):
        by_show = {}

        for episode in branches:
            key = episode.get('grandparentRatingKey')
            if key not in by_show:
                by_show[key] = []
            by_show[key].append(episode)

        item_collections = [value for _, value in by_show.items()]
        zipped_collection = self._zipped_collections(item_collections)

        return list(chain.from_iterable(zipped_collection))

    @staticmethod
    def _zipped_collections(item_collections):
        zipped_collection = list(zip_longest(*item_collections))
        collection = []

        for zipped in zipped_collection:
            zipped = [_zip for _zip in zipped if _zip is not None]
            if zipped:
                collection.append(zipped)

        return collection

    def _get_distributed_collections(self, item_collections):
        collection = self._zipped_collections(item_collections)
        return chain.from_iterable(collection)

    def _get_shuffled_sample(self, item_collections):
        distributed_collection = list(self._get_distributed_collections(item_collections))

        # do some pre-shuffling, random.sample pool never felt random enough
        shuffle_times = random.randint(1, 10)
        for _ in range(shuffle_times):
            random.shuffle(distributed_collection)

        sample_size = self._limiter(self.item_count, len(distributed_collection))

        return random.sample(distributed_collection, sample_size)

    def _get_selection_sample(self, item_collections):
        distributed_collection = self._get_distributed_collections(item_collections)

        sample_items = []
        while len(sample_items) < self.item_count:
            item = next(distributed_collection, None)
            if not item:
                break
            sample_items.append(item)

        return sample_items

    @staticmethod
    def _limiter(value, upper_limit=None, lower_limit=None):
        if upper_limit is None:
            upper_limit = float('inf')
        if lower_limit is None:
            lower_limit = 0
        return upper_limit if value > upper_limit else lower_limit if value < lower_limit else value


class RadioButton(pyxbmct.CompareMixin, xbmcgui.ControlRadioButton):

    def __new__(cls, *args, **kwargs):
        kwargs.update({
            'focusOnTexture': os.path.join(pyxbmct.skin.images,
                                           'RadioButton', 'MenuItemFO.png'),
            'noFocusOnTexture': os.path.join(pyxbmct.skin.images,
                                             'RadioButton', 'radiobutton-focus.png'),
            'focusOffTexture': os.path.join(pyxbmct.skin.images,
                                            'RadioButton', 'radiobutton-focus.png'),
            'noFocusOffTexture': os.path.join(pyxbmct.skin.images,
                                              'RadioButton', 'radiobutton-nofocus.png')
        })
        return super(RadioButton, cls).__new__(cls, -10, -10, 1, 1, *args, **kwargs)  # pylint: disable=too-many-function-args


if CONFIG['kodi_version'] >= 19:
    # currently required until pyxbmct is updated to remove deprecated textures
    pyxbmct.RadioButton = RadioButton


def composite_playlist(context):
    play = False
    try:
        with CompositePlaylistWindow(context=context, window=xbmcgui.Window(10000)) as dialog:
            play = dialog.start()
    except AlreadyActiveException:
        pass
    except AttributeError:
        LOG.debug('Failed to load CompositePlaylistWindow ...')

    return play

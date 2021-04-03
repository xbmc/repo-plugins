# -*- coding: utf-8 -*-
""" Menu module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.viervijfzes import STREAM_DICT
from resources.lib.viervijfzes.content import Episode, Program

try:  # Python 3
    from urllib.parse import quote
except ImportError:  # Python 2
    from urllib import quote

_LOGGER = logging.getLogger(__name__)


class Menu:
    """ Menu code """

    def __init__(self):
        """ Initialise object """

    @staticmethod
    def show_mainmenu():
        """ Show the main menu """
        listing = [
            TitleItem(
                title=kodiutils.localize(30001),  # A-Z
                path=kodiutils.url_for('show_catalog'),
                art_dict=dict(
                    icon='DefaultMovieTitle.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30002),
                )
            ),
            TitleItem(
                title=kodiutils.localize(30007),  # TV Channels
                path=kodiutils.url_for('show_channels'),
                art_dict=dict(
                    icon='DefaultAddonPVRClient.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30008),
                )
            ),
            TitleItem(
                title=kodiutils.localize(30003),  # Catalog
                path=kodiutils.url_for('show_categories'),
                art_dict=dict(
                    icon='DefaultGenre.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30004),
                )
            ),
            TitleItem(
                title=kodiutils.localize(30005),  # Recommendations
                path=kodiutils.url_for('show_recommendations'),
                art_dict=dict(
                    icon='DefaultFavourites.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30006),
                )
            ),
            TitleItem(
                title=kodiutils.localize(30011),  # My List
                path=kodiutils.url_for('show_mylist'),
                art_dict=dict(
                    icon='DefaultPlaylist.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30012),
                )
            ),
            TitleItem(
                title=kodiutils.localize(30009),  # Search
                path=kodiutils.url_for('show_search'),
                art_dict=dict(
                    icon='DefaultAddonsSearch.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30010),
                )
            )
        ]

        kodiutils.show_listing(listing, sort=['unsorted'])

    @staticmethod
    def generate_titleitem(item):
        """ Generate a TitleItem based on a Program or Episode.
        :type item: Union[Program, Episode]
        :rtype TitleItem
        """
        info_dict = {
            'title': item.title,
            'plot': item.description,
            'aired': item.aired.strftime('%Y-%m-%d') if item.aired else None,
        }
        prop_dict = {}

        #
        # Program
        #
        if isinstance(item, Program):
            info_dict.update({
                'mediatype': None,
                'season': len(item.seasons) if item.seasons else None,
            })

            art_dict = {
                'poster': item.poster,
                'landscape': item.thumb,
                'thumb': item.thumb,
                'fanart': item.fanart,
            }

            visible = True
            if isinstance(item.episodes, list) and not item.episodes:
                # We know that we don't have episodes
                title = '[COLOR gray]' + item.title + '[/COLOR]'
                visible = kodiutils.get_setting_bool('interface_show_unavailable')

            else:
                # We have episodes, or we don't know it
                title = item.title

            context_menu = []
            if item.uuid:
                if item.my_list:
                    context_menu.append((
                        kodiutils.localize(30101),  # Remove from My List
                        'Container.Update(%s)' %
                        kodiutils.url_for('mylist_del', uuid=item.uuid)
                    ))
                else:
                    context_menu.append((
                        kodiutils.localize(30100),  # Add to My List
                        'Container.Update(%s)' %
                        kodiutils.url_for('mylist_add', uuid=item.uuid)
                    ))

            context_menu.append((
                kodiutils.localize(30102),  # Go to Program
                'Container.Update(%s)' %
                kodiutils.url_for('show_catalog_program', program=item.path)
            ))

            return TitleItem(title=title,
                             path=kodiutils.url_for('show_catalog_program', program=item.path),
                             context_menu=context_menu,
                             art_dict=art_dict,
                             info_dict=info_dict,
                             visible=visible)

        #
        # Episode
        #
        if isinstance(item, Episode):
            info_dict.update({
                'mediatype': 'episode',
                'tvshowtitle': item.program_title,
                'duration': item.duration,
                'season': item.season,
                'episode': item.number,
            })

            art_dict = {
                'landscape': item.thumb,
                'thumb': item.thumb,
                'fanart': item.thumb,
            }

            stream_dict = STREAM_DICT.copy()
            stream_dict.update({
                'duration': item.duration,
            })

            if item.uuid:
                # We have an UUID and can play this item directly
                path = kodiutils.url_for('play_catalog', uuid=item.uuid)
            else:
                # We don't have an UUID, and first need to fetch the video information from the page
                path = kodiutils.url_for('play_from_page', page=quote(item.path, safe=''))

            return TitleItem(title=info_dict['title'],
                             path=path,
                             art_dict=art_dict,
                             info_dict=info_dict,
                             stream_dict=stream_dict,
                             prop_dict=prop_dict,
                             is_playable=True)

        raise Exception('Unknown video_type')

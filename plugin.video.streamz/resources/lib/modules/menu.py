# -*- coding: utf-8 -*-
""" Menu module """

from __future__ import absolute_import, division, unicode_literals

import logging

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.streamz import STOREFRONT_KIDS, STOREFRONT_MAIN, STOREFRONT_MAIN_KIDS, STOREFRONT_MOVIES, STOREFRONT_SERIES, Episode, Movie, Program
from resources.lib.streamz.api import CONTENT_TYPE_MOVIE, CONTENT_TYPE_PROGRAM
from resources.lib.streamz.auth import Auth

_LOGGER = logging.getLogger(__name__)


class Menu:
    """ Menu code """

    def __init__(self):
        """ Initialise object """
        self._auth = Auth(kodiutils.get_setting('username'),
                          kodiutils.get_setting('password'),
                          kodiutils.get_setting('loginprovider'),
                          kodiutils.get_setting('profile'),
                          kodiutils.get_tokens_path())

    def show_mainmenu(self):
        """ Show the main menu. """
        listing = []

        account = self._auth.get_tokens()

        if account.product == 'STREAMZ':
            listing.append(TitleItem(
                title=kodiutils.localize(30015),  # Recommendations
                path=kodiutils.url_for('show_recommendations', storefront=STOREFRONT_MAIN),
                art_dict=dict(
                    icon='DefaultFavourites.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30016),
                ),
            ))

            listing.append(TitleItem(
                title=kodiutils.localize(30003),  # Movies
                path=kodiutils.url_for('show_recommendations', storefront=STOREFRONT_MOVIES),
                art_dict=dict(
                    icon='DefaultMovies.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30004),
                ),
            ))

            listing.append(TitleItem(
                title=kodiutils.localize(30005),  # Series
                path=kodiutils.url_for('show_recommendations', storefront=STOREFRONT_SERIES),
                art_dict=dict(
                    icon='DefaultTVShows.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30006),
                ),
            ))

            listing.append(TitleItem(
                title=kodiutils.localize(30021),  # Kids
                path=kodiutils.url_for('show_recommendations', storefront=STOREFRONT_KIDS),
                art_dict=dict(
                    icon='DefaultFavourites.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30022),
                ),
            ))

        elif account.product == 'STREAMZ_KIDS':
            listing.append(TitleItem(
                title=kodiutils.localize(30015),  # Recommendations
                path=kodiutils.url_for('show_recommendations', storefront=STOREFRONT_MAIN_KIDS),
                art_dict=dict(
                    icon='DefaultFavourites.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30016),
                ),
            ))

        if kodiutils.get_setting_bool('interface_show_az'):
            listing.append(TitleItem(
                title=kodiutils.localize(30001),  # A-Z
                path=kodiutils.url_for('show_catalog_all'),
                art_dict=dict(
                    icon='DefaultMovieTitle.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30002),
                ),
            ))

        if kodiutils.get_setting_bool('interface_show_mylist'):
            listing.append(TitleItem(
                title=kodiutils.localize(30017),  # My List
                path=kodiutils.url_for('show_mylist'),
                art_dict=dict(
                    icon='DefaultPlaylist.png',
                    fanart=kodiutils.get_addon_info('fanart'),
                ),
                info_dict=dict(
                    plot=kodiutils.localize(30018),
                ),
            ))

        # if kodiutils.get_setting_as_bool('interface_show_continuewatching') and kodiutils.has_credentials():
        #     listing.append(TitleItem(
        #         title=kodiutils.localize(30019),  # Continue watching
        #         path=kodiutils.url_for('show_continuewatching'),
        #         art_dict=dict(
        #             icon='DefaultInProgressShows.png',
        #             fanart=kodiutils.get_addon_info('fanart'),
        #         ),
        #         info_dict=dict(
        #             plot=kodiutils.localize(30020),
        #         ),
        #     ))

        listing.append(TitleItem(
            title=kodiutils.localize(30009),  # Search
            path=kodiutils.url_for('show_search'),
            art_dict=dict(
                icon='DefaultAddonsSearch.png',
                fanart=kodiutils.get_addon_info('fanart'),
            ),
            info_dict=dict(
                plot=kodiutils.localize(30010),
            ),
        ))

        kodiutils.show_listing(listing, sort=['unsorted'])

    @staticmethod
    def format_plot(obj):
        """ Format the plot for a item.

        :type obj: object
        :rtype str
        """
        plot = ''

        # Add geo-blocked message
        if hasattr(obj, 'available') and not obj.available:
            plot += kodiutils.localize(30206)  # Available in Streamz+
            plot += '\n'

        # Add remaining
        if hasattr(obj, 'remaining') and obj.remaining is not None:
            if obj.remaining == 0:
                plot += '» ' + kodiutils.localize(30208) + "\n"  # Available until midnight
            elif obj.remaining == 1:
                plot += '» ' + kodiutils.localize(30209) + "\n"  # One more day remaining
            elif obj.remaining / 365 > 5:
                pass  # If it is available for more than 5 years, do not show
            elif obj.remaining / 365 > 2:
                plot += '» ' + kodiutils.localize(30210, years=int(obj.remaining / 365)) + "\n"  # X years remaining
            elif obj.remaining / 30.5 > 3:
                plot += '» ' + kodiutils.localize(30211, months=int(obj.remaining / 30.5)) + "\n"  # X months remaining
            else:
                plot += '» ' + kodiutils.localize(30212, days=obj.remaining) + "\n"  # X days remaining
            plot += '\n'

        # Add geo-blocked message
        if hasattr(obj, 'geoblocked') and obj.geoblocked:
            plot += kodiutils.localize(30207)  # Geo-blocked
            plot += '\n'

        if hasattr(obj, 'description'):
            plot += obj.description
            plot += '\n\n'

        return plot.rstrip()

    @classmethod
    def generate_titleitem(cls, item, progress=False):
        """ Generate a TitleItem based on a Movie, Program or Episode.

        :type item: Union[Movie, Program, Episode]
        :type progress: bool
        :rtype TitleItem
        """
        art_dict = {
            'thumb': item.cover,
            'cover': item.cover,
        }
        info_dict = {
            'title': item.name,
            'plot': cls.format_plot(item),
            # 'studio': CHANNELS.get(item.channel, {}).get('studio_icon'),
            'mpaa': ', '.join(item.legal) if hasattr(item, 'legal') and item.legal else kodiutils.localize(30216),  # All ages
        }
        prop_dict = {}

        #
        # Movie
        #
        if isinstance(item, Movie):
            if item.my_list:
                context_menu = [(
                    kodiutils.localize(30101),  # Remove from My List
                    'Container.Update(%s)' %
                    kodiutils.url_for('mylist_del', video_type=CONTENT_TYPE_MOVIE, content_id=item.movie_id)
                )]
            else:
                context_menu = [(
                    kodiutils.localize(30100),  # Add to My List
                    'Container.Update(%s)' %
                    kodiutils.url_for('mylist_add', video_type=CONTENT_TYPE_MOVIE, content_id=item.movie_id)
                )]

            art_dict.update({
                'fanart': item.image,
            })
            info_dict.update({
                'mediatype': 'movie',
                'duration': item.duration,
                'year': item.year,
                'aired': item.aired,
            })
            stream_dict = {
                'codec': 'h264',
                'duration': item.duration,
                'height': 1080,
                'width': 1920,
            }

            if item.available:
                title = item.name
            else:
                title = item.name + ' [COLOR=red](S+)[/COLOR]'
                info_dict.update({
                    'title': title,
                })

            return TitleItem(
                title=title,
                path=kodiutils.url_for('play', category='movies', item=item.movie_id),
                art_dict=art_dict,
                info_dict=info_dict,
                stream_dict=stream_dict,
                prop_dict=prop_dict,
                context_menu=context_menu,
                is_playable=True,
            )

        #
        # Program
        #
        if isinstance(item, Program):
            if item.my_list:
                context_menu = [(
                    kodiutils.localize(30101),  # Remove from My List
                    'Container.Update(%s)' %
                    kodiutils.url_for('mylist_del', video_type=CONTENT_TYPE_PROGRAM, content_id=item.program_id)
                )]
            else:
                context_menu = [(
                    kodiutils.localize(30100),  # Add to My List
                    'Container.Update(%s)' %
                    kodiutils.url_for('mylist_add', video_type=CONTENT_TYPE_PROGRAM, content_id=item.program_id)
                )]

            art_dict.update({
                'fanart': item.image,
            })
            info_dict.update({
                'mediatype': 'tvshow',
                'season': len(item.seasons),
            })
            prop_dict.update({
                'hash': item.content_hash,
            })

            return TitleItem(
                title=item.name,
                path=kodiutils.url_for('show_catalog_program', program=item.program_id),
                art_dict=art_dict,
                info_dict=info_dict,
                prop_dict=prop_dict,
                context_menu=context_menu,
            )

        #
        # Episode
        #
        if isinstance(item, Episode):
            context_menu = []
            if item.program_id:
                context_menu = [(
                    kodiutils.localize(30102),  # Go to Program
                    'Container.Update(%s)' %
                    kodiutils.url_for('show_catalog_program', program=item.program_id)
                )]

            art_dict.update({
                'fanart': item.cover,
            })
            info_dict.update({
                'mediatype': 'episode',
                'tvshowtitle': item.program_name,
                'duration': item.duration,
                'season': item.season,
                'episode': item.number,
                'set': item.program_name,
                'aired': item.aired,
            })
            if progress and item.watched:
                info_dict.update({
                    'playcount': 1,
                })

            stream_dict = {
                'codec': 'h264',
                'duration': item.duration,
                'height': 1080,
                'width': 1920,
            }

            # Add progress info
            if progress and not item.watched and item.progress:
                prop_dict.update({
                    'ResumeTime': item.progress,
                    'TotalTime': item.progress + 1,
                })

            return TitleItem(
                title=info_dict['title'],
                path=kodiutils.url_for('play', category='episodes', item=item.episode_id),
                art_dict=art_dict,
                info_dict=info_dict,
                stream_dict=stream_dict,
                prop_dict=prop_dict,
                context_menu=context_menu,
                is_playable=True,
            )

        raise Exception('Unknown video_type')

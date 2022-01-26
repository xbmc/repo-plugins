# -*- coding: utf-8 -*-
""" Menu module """

from __future__ import absolute_import, division, unicode_literals

import logging
from datetime import datetime

import dateutil.tz

from resources.lib import kodiutils
from resources.lib.kodiutils import TitleItem
from resources.lib.solocoo import Credit

_LOGGER = logging.getLogger(__name__)


class Menu:
    """ Menu code """

    def __init__(self):
        """ Initialise object. """

    @staticmethod
    def show_mainmenu():
        """ Show the main menu. """
        listing = [
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

    @classmethod
    def generate_titleitem_series(cls, item):
        """ Generate a TitleItem.

        :param resources.lib.solocoo.util.Program item: The Program to convert to a TitleItem.

        :returns:                       A generated TitleItem for a Series.
        :rtype: TitleItem
        """
        return TitleItem(
            title=item.title,
            path=kodiutils.url_for('show_channel_replay_series', series_id=item.series_id),
            art_dict={
                'cover': item.cover,
                'icon': item.preview,
                'thumb': item.preview,
                'fanart': item.preview,
            },
            info_dict={
                'mpaa': item.age,
                'tvshowtitle': item.title,
                'title': item.title,
                'plot': None,
            },
        )

    @classmethod
    def generate_titleitem_program(cls, item, timeline=False):
        """ Generate a TitleItem.

        :param resources.lib.solocoo.util.Program item: The Program to convert to a TitleItem.
        :param boolean timeline:                        Indicates that this TitleItem will be used in a timeline.

        :returns:                       A generated TitleItem for a Program.
        :rtype: TitleItem
        """
        title = item.title

        if item.season and item.episode:
            title += ' (S%02dE%02d)' % (int(item.season), int(item.episode))
        elif item.episode:
            title += ' (E%02d)' % int(item.episode)

        # Prepend a time when used in an EPG view
        if timeline:
            title = '{time} - {title}'.format(
                time=item.start.strftime('%H:%M'),
                title=title,
            )

        # Gray out unavailable programs
        if not item.replay or item.available is False:
            title = '[COLOR gray]' + title + '[/COLOR]'

        return TitleItem(
            title=title,
            path=kodiutils.url_for('play_asset', asset_id=item.uid),
            art_dict={
                'cover': item.cover,
                'icon': item.preview or item.cover,
                'thumb': item.preview or item.cover,
                'fanart': item.preview or item.cover,
            },
            info_dict={
                'tvshowtitle': item.title,
                'title': title,
                'plot': cls._format_program_plot(item),
                'season': item.season,
                'episode': item.episode,
                'mpaa': item.age,
                'mediatype': 'episode',
                'aired': item.start.strftime('%Y-%m-%d'),
                'date': item.start.strftime('%d.%m.%Y'),
                'duration': item.duration,
                'cast':
                    [(credit.person, credit.character) for credit in item.credit if credit.role == Credit.ROLE_ACTOR] +
                    [credit.person for credit in item.credit if credit.role in [Credit.ROLE_PRESENTER, Credit.ROLE_GUEST]],
                'director': [credit.person for credit in item.credit if credit.role in [Credit.ROLE_DIRECTOR, Credit.ROLE_PRODUCER]],
                # 'credits': [credit.person for credit in item.credit if credit.role in [Credit.ROLE_COMPOSER]],
            },
            prop_dict={
                'inputstream.adaptive.play_timeshift_buffer': 'true',  # Play from the beginning
                'inputstream.adaptive.manifest_update_parameter': 'full',
            },
            is_playable=True,
        )

    @classmethod
    def generate_titleitem_channel(cls, item):
        """ Generate a TitleItem for a Channel.

        :param resources.lib.solocoo.util.Channel item: The Channel to convert to a TitleItem.

        :returns:                       A generated TitleItem for a Channel.
        :rtype: TitleItem
        """
        if item.epg_now:
            title = item.title + '[COLOR gray] | {title} ({start} - {end})[/COLOR]'.format(
                title=item.epg_now.title,
                start=item.epg_now.start.strftime('%H:%M'),
                end=item.epg_now.end.strftime('%H:%M'))
        else:
            title = item.title

        return TitleItem(
            title=title,
            path=kodiutils.url_for('play_asset', asset_id=item.uid) + '?.pvr',
            art_dict={
                'cover': item.icon,
                'icon': item.icon,
                'thumb': item.icon,
                # 'fanart': item.preview,  # Preview doesn't seem to work on most channels
            },
            info_dict={
                'title': item.title,
                'plot': cls._format_channel_plot(item),
                'playcount': 0,
                'mediatype': 'video',
            },
            prop_dict={
                'inputstream.adaptive.manifest_update_parameter': 'full',
            },
            is_playable=True,
        )

    @classmethod
    def _format_program_plot(cls, program):
        """ Format a plot for a program.

        :param resources.lib.solocoo.util.Program program: The program we want to have a plot for.

        :returns:                       A formatted plot for this program.
        :rtype: str
        """
        plot = ''

        # Add remaining
        if isinstance(program.available, datetime):
            time_left = (program.available - datetime.now(dateutil.tz.UTC))
            if time_left.days > 1:
                plot += '» ' + kodiutils.localize(30208, days=time_left.days) + "\n"  # [B]{days} days[/B] remaining
            elif time_left.days == 1:
                plot += '» ' + kodiutils.localize(30209) + "\n"  # [B]1 day[/B] remaining
            elif time_left.seconds >= 3600 * 2:
                plot += '» ' + kodiutils.localize(30210, hours=int(time_left.seconds / 3600)) + "\n"  # [B]{hours} hours[/B] remaining
            elif time_left.seconds >= 3600:
                plot += '» ' + kodiutils.localize(30211) + "\n"  # [B]1 hour[/B] remaining
            else:
                plot += '» ' + kodiutils.localize(30212) + "\n"  # [B]less then 1 hour[/B] remaining
            plot += '\n'

        # Add description
        if program.description:
            plot += program.description
            plot += '\n\n'

        return plot

    @classmethod
    def _format_channel_plot(cls, channel):
        """ Format a plot for a channel.

        :param resources.lib.solocoo.util.Channel channel: The channel we want to have a plot for.

        :returns:                       A formatted plot for this channel.
        :rtype: str
        """
        plot = ''

        if channel.epg_now:
            plot += kodiutils.localize(30213,  # Now
                                       start=channel.epg_now.start.strftime('%H:%M'),
                                       end=channel.epg_now.end.strftime('%H:%M'),
                                       title=channel.epg_now.title) + "\n"

        if channel.epg_next:
            plot += kodiutils.localize(30214,  # Next
                                       start=channel.epg_next.start.strftime('%H:%M'),
                                       end=channel.epg_next.end.strftime('%H:%M'),
                                       title=channel.epg_next.title) + "\n"

        return plot

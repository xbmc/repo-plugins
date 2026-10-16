# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations

import re
import json
from urllib.parse import quote

import xbmcplugin
from xbmcgui import ListItem

from resources.lib.route import build_callback
from resources.lib.log import log
from resources.lib.favourites import favourites

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from resources.lib.plugin import Plugin
    from collections.abc import Callable
    from resources.lib.typedef import (
        ListItemTuple,
        ListItemGenerator,
        ContextMenuItem)


BASE_URL = 'https://www.bbc.co.uk/sounds/'
RMS_DOMAIN = 'https://rms.api.bbc.co.uk'
RMS_BASE_URL = 'https://rms.api.bbc.co.uk/v2/'

TXT_ID_LISTEN_FROM_START = 30605
TXT_ID_REMOVE_LISTENING = 30609


def scrape_json_data(html):
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        return None
    data = json.loads(match[1])
    return data


def select_synopsis(item_data) -> tuple[str, str]:
    synopses = item_data.get('synopses')
    if synopses:
        long_synopsis = synopses.get('long')
        if long_synopsis and len(long_synopsis) < 400:
            return long_synopsis, ''
        else:
            plot_outline = (synopses.get('medium')
                            or synopses.get('short')
                            or synopses.get('long')
                            or '')
            return plot_outline, long_synopsis
    else:
        return item_data.get('synopsis', ''), ''


def format_img(img_url: str, img_type: str = 'icon') -> str:
    recipe = {
        'icon': '512x512',
        'fanart': '1280x720',  # Higher resolutions return 403 error.
        'poster': '1000x1500'
    }.get(img_type)
    return img_url.format(recipe=recipe)


def get_rail_url(rail_item: dict) -> str | None:
    """Return the url to the rail's own page, or None if the url is not available."""

    # `uris` is None if no separate page is available.
    uris = rail_item['uris'] or {}
    page_data = uris.get('pagination', '')
    if not page_data:
        return None
    # The page handler will add the required pagination arguments.
    path = page_data['uri'].replace('&offset={offset}', '').replace('&limit={limit}', '')
    if path.endswith('?'):
        path = path[:-1]
    return RMS_DOMAIN + path


def join_ex(sep: str, *args) -> str:
    """Perform a string join on sep, but skip None values and empty strings."""
    return sep.join(filter(None, args))


class Parser:
    def __init__(self,
                 plugin: Plugin,
                 container_type: str | None = None,  # The ID of the container of the items being parsed.
                 parent_url: str | None = '',
                 slug: str = ''):
        self._plugin = plugin
        self._slug = slug
        self.container_type = container_type
        self.parent_url = parent_url
        self.sort_methods = set()
        # Pre-localised strings, as they are used in many items.
        self.TXT_MORE_EPISODES = plugin.translate(30600)
        self.TXT_SUBSCRIBE = plugin.translate(30601)
        self.TXT_UNSUBSCRIBE = plugin.translate(30602)
        self.TXT_BOOKMARK = plugin.translate(30603)
        self.TXT_REMOVE_BOOKMARK = plugin.translate(30604)
        if plugin.settings.getBool('is-signed-in'):
            self.api_domain = RMS_BASE_URL + 'my/'
        else:
            self.api_domain = RMS_BASE_URL

    def urn2url(self, urn: str) -> tuple[str, str]:
        assert urn.startswith('urn:bbc:')
        _, item_type, item_id = urn.rsplit(':', 2)
        if item_id == 'all-podcasts':
            item_id = ''
        url = {
            'brand': self.api_domain + 'programmes/playable?container={}',
            'series': self.api_domain + 'programmes/playable?container={}',
            'collection': RMS_BASE_URL + 'collections/{}/members',
            'category': self.api_domain + 'programmes/tleo/playable?category={}',
            # 'view all' link on most rails:
            'tag': RMS_BASE_URL + 'tagged/{}/playable',
            # 'view all' on podcast rails:
            'podcasts': self.api_domain + 'programmes/tleo/playable?all-categories=podcasts,{}',
            'my': BASE_URL + 'my/{}',
            'curation': self.api_domain + 'curations/{}/members/playable'
        }[item_type].format(item_id)
        return url, item_type

    def parser_from_item_type(self, item_type: str) -> Callable[dict]:
        return {
            'playable_item': self.parse_playable_item,
            'container_item': self.parse_container_item,
            'inline_display_module': self.parse_rail,
        }.get(item_type)

    def parse_items_list(self, items: list[dict]) -> ListItemGenerator:
        for item in items:
            item_type = item['type']
            parser = self.parser_from_item_type(item_type)
            if parser:
                try:
                    yield parser(item)
                except Exception as err:
                    log('Error parsing "%s" item: %r', item_type, err)
            else:
                log('Failed to parse unknown item type "%s".', item_type)

    def parse_rail(self, rail: dict) -> ListItemTuple | None:
        """Parse the rail item itself (not its contents)."""
        if rail['type'] != 'inline_display_module':
            raise ValueError(f'Expected a rail item, got {rail["type"]}')
        if not rail['data']:
            return None
        if rail['id'] == 'single_item_promo':
            return self.parse_promo_item(rail)

        title = rail['title']
        li = ListItem(title, offscreen=True)
        info = li.getVideoInfoTag()
        descr = rail['description']
        if descr:
            info.setPlot(descr)
        li.setIsFolder(True)

        # Prefer to use the rail's own url, but fall back to rail content on the parent page.
        rail_url = get_rail_url(rail)
        if rail_url:
            callback = build_callback('menu/list_rail_by_url',
                                      rail_url=rail_url,
                                      slug=join_ex(' / ', self._slug, title))
        else:
            callback = build_callback('menu/list_rail',
                                      page_url=self.parent_url,
                                      rail_id=rail['id'],
                                      slug=join_ex(' / ', self._slug, title))
        return callback, li, True

    def parse_container_item(self, item: dict) -> ListItemTuple | None:
        if not item:
            return None
        title = item['titles']['primary']
        if item['titles'].get('secondary'):
            title = f'{title}: {item["titles"]["secondary"]}'
        li = ListItem(title, offscreen=True)
        info = li.getVideoInfoTag()
        plot_outline, plot = select_synopsis(item)
        network = item['network'] or {}
        info.setPlotOutline(
            join_ex('\n',
                    network.get('short_title', ''),
                    item['titles'].get('secondary'),
                    item['titles'].get('tertiary'),
                    plot_outline)
        )
        info.setPlot(plot)
        li.setArt({'icon': format_img(item['image_url'])})
        li.setIsFolder(True)

        tlec_urn = item.get('tlec_urn', '')
        if tlec_urn:
            ctx_menu = self.ctx_subscribe(tlec_urn, tlec_urn in favourites.subscriptions)
            if ctx_menu:
                li.addContextMenuItems([ctx_menu])

        callback = build_callback('menu/list_container_content',
                                  urn=item['urn'],
                                  slug=join_ex(' / ', self._slug, item['titles']['primary']))
        return callback, li, True

    def parse_playable_item(self, item: dict) -> ListItemTuple:
        item_urn = item['urn']
        if item_urn.startswith('urn:bbc:radio:network:'):
            return self.parse_live_item(item)

        ctx_menu_items = []
        titles = item['titles']
        item_container = item.get('container')
        plot_outline, plot = select_synopsis(item)
        episode_title = titles.get('entity_title') or titles['tertiary']
        if titles['secondary'] != episode_title:
            episode_title = ': '.join(filter(None, (titles['secondary'], episode_title)))

        if self.container_type in ('brand', 'series'):
            title = episode_title
            description = join_ex('\n\n',
                                  f"{titles['primary']}\n{item['release']['label']}",
                                  plot_outline,
                                  item['availability']['label'])
        else:
            title = titles['primary']
            description = join_ex('\n\n',
                                  f"{episode_title}\n{item['release']['label']}",
                                  plot_outline,
                                  item['availability']['label'])

        li = ListItem(title, offscreen=True)
        li.setArt({'icon': format_img(item['image_url'], 'icon')})
        info = li.getVideoInfoTag()
        info.setPlotOutline(description)
        if plot:
            info.setPlot(plot)

        duration = item.get('duration', {}).get('value')
        if duration:
            info.setDuration(duration)
            self.sort_methods.add(xbmcplugin.SORT_METHOD_DURATION)
        progress = item['progress']
        if progress:
            resume_time = progress['value']
            info.setResumePoint(resume_time, duration)
            # Add a property for the resolver to avoid varying parameter values in the callback url.
            li.setProperty('resume_point', f'{resume_time};{duration}')
            title = f'{title}   [I]{progress["label"]}[/I]'

        info.setTitle(title)

        release_date = item['release'].get('date')
        if release_date:
            info.setYear(int(release_date[:4]))
            li.setDateTime(release_date)
            self.sort_methods.add(xbmcplugin.SORT_METHOD_DATE)

        # Remove from Continue Listening conteXt menu item
        if self.container_type == 'my_sounds_continue_listening':
            ctx_menu_items.append(self.ctx_remove_listening(
                item_urn,
                item['titles']['primary'],
                episode_title))

        # Only add a 'more episodes' context menu item if the item is not listed in the
        # context of its own brand.
        if self.container_type != 'brand' and item_container:
            ctx_menu_items.append(self.ctx_more_episodes(
                item_container['urn'],
                item_container['title'])
            )

        ctx_menu_items.append(self.ctx_bookmark(
            item_urn,
            item_urn in favourites.bookmarks)
        )
        if item_container:  # and item_container['type'] in ('brand', 'series'):
            container_urn = item_container['urn']
            ctx_menu_items.append(self.ctx_subscribe(
                container_urn,
                container_urn in favourites.subscriptions)
            )

        li.addContextMenuItems(ctx_menu_items)
        callback = build_callback('stream/play_od',
                                  service_id=item['id'],
                                  pid=item_urn.split(':')[-1])
        li.setProperty('IsPlayable', 'true')
        li.setPath(callback)
        li.setIsFolder(False)
        return callback, li, False

    def parse_live_item(self, item: dict) -> ListItemTuple:
        titles = item['titles']
        plot_outline, _ = select_synopsis(item)
        title = titles['entity_title'] or titles['tertiary']

        li = ListItem(title, offscreen=True)
        li.setArt({'icon': format_img(item['image_url'], 'icon')})

        start_t, sep, end_t = titles['secondary'].partition(' - ')
        if sep:
            from resources.lib.kodi_utils import local_tz

            local_zone = local_tz()
            start_utc, end_utc = self.utc_programme_time(start_t, end_t, titles['tertiary'])
            start_local = start_utc.astimezone(local_zone)
            end_local = end_utc.astimezone(local_zone)
            description = join_ex('\n\n',
                                  f"[B]Live[/B] {start_local.strftime('%H:%M')} - {end_local.strftime('%H:%M')}",
                                  plot_outline)

            # Context menu item 'Listen from the start'.
            if self._plugin.kodi_version < (21, 90):
                # Not available on Piers, since live dash streams fail to play.
                cmd = (f'PlayMedia(plugin://{self._plugin.addon_id}/stream/play_live?'
                       f'service_id={item["id"]}&start_t={quote(start_utc.isoformat())}, noresume)')
                li.addContextMenuItems([
                    (self._plugin.translate(TXT_ID_LISTEN_FROM_START), cmd)
                ])
        else:
            # Just a failsafe in case the BBC changes the format of the 'secondary' title.
            description = (join_ex('\n\n',
                                   f"[B]Live[/B] {titles['secondary']} - {titles['primary']}",
                                   plot_outline))

        info = li.getVideoInfoTag()
        info.setPlotOutline(description)
        info.setTitle(f"{item['network']['short_title']} - {title}")
        info.setResumePoint(0)
        info.setPlaycount(0)

        callback = build_callback('stream/play_live', service_id=item['id'])
        li.setProperty('IsPlayable', 'true')
        li.setPath(callback)
        li.setIsFolder(False)
        return callback, li, False

    def parse_promo_item(self, item: dict) -> ListItemTuple:
        """Parse the item in a 'single item promo' rail."""
        inner_item = item['data'][0]
        promo_item = inner_item['item']
        titles = inner_item['titles']
        promo_title = f'[B][COLOR orange]{titles["primary"]}: {titles["secondary"]}[/COLOR][/B]'
        parser_func = self.parser_from_item_type(promo_item['type'])
        callback, li, is_folder = parser_func(promo_item)
        info = li.getVideoInfoTag()
        info.setTitle(promo_title)
        info.setPlotOutline('\n'.join((titles['tertiary'], info.getPlotOutline())))
        li.setArt({'icon': format_img(inner_item['image_url'])})
        return callback, li, is_folder

    def parse_controls(self, controls) -> ListItemTuple | None:
        """Parse the navigation control objects in a container.

        Creates items like 'view all', primarily found on rails, e.g. to view the whole collection.

        """
        if not controls:
            return None
        nav_item = controls.get('navigation')
        if not nav_item:
            return None

        nav_id = nav_item['id']
        li = ListItem(nav_item['title'])
        info = li.getVideoInfoTag()
        info.setTitle(f'[B]{nav_item["title"]}[/B]')
        li.setProperty('SpecialSort', 'bottom')
        li.setIsFolder(True)

        urn = nav_item['target']['urn']
        if nav_id == 'see_more':
            callb_url = build_callback('menu/list_container_content', urn=urn, slug=self._slug + ' / all')
        elif nav_id == 'manage_list':
            # Exclusively to navigate from continue-watching on the home page to the equivalent on 'My Sounds'.
            page_url = 'https://www.bbc.co.uk/sounds/my'
            callb_url = build_callback('menu/list_rail',
                                       page_url=page_url,
                                       rail_id='my_sounds_continue_listening',
                                       slug='Continue Listening')
        else:
            log('parse_controls Warning: Unknown item id: "%s"', nav_id)
            return None
        return callb_url, li, True

    def ctx_more_episodes(self, urn, brand_title) -> ContextMenuItem:
        """Context menu to show all episodes of the same programme, or series."""
        url = build_callback('menu/list_container_content', urn=urn, slug=brand_title)
        return self.TXT_MORE_EPISODES, f'Container.Update({url})'

    def ctx_subscribe(self, urn: str, remove: bool) -> ContextMenuItem | None:
        """Context menu item for adding or removing a subscription."""
        if not urn:
            return None
        url = build_callback('contextmnu/handle_subscription', urn=urn, operation='remove' if remove else 'add')
        label = self.TXT_UNSUBSCRIBE if remove else self.TXT_SUBSCRIBE
        return label, f'RunPlugin({url})'

    def ctx_bookmark(self, urn: str, remove: bool) -> ContextMenuItem:
        """Context menu item for adding or removing a bookmark.
        Is ultimately the same action as subscribing, but presented with a different label.
        The BBC handles brands as subscriptions and episodes as bookmarks.

        """
        url = build_callback('contextmnu/handle_subscription', urn=urn, operation='remove' if remove else 'add')
        label = self.TXT_REMOVE_BOOKMARK if remove else self.TXT_BOOKMARK
        return label, f'RunPlugin({url})'

    def ctx_remove_listening(self, urn: str, brand_title: str, episode_title) -> ContextMenuItem:
        """Context menu item to remove an item from 'Continue Listening'."""
        url = build_callback('contextmnu/remove_listening',
                             urn=urn,
                             brand_title=brand_title,
                             episode_title=episode_title)
        return self._plugin.translate(TXT_ID_REMOVE_LISTENING), f'RunPlugin({url})'

    @staticmethod
    def _get_brand_id(item: dict) -> str:
        """Get the top level container id of item."""
        top_level_urn = item.get('tlec_urn', '')
        if top_level_urn:
            return top_level_urn.rsplit(':', 1)[-1]
        else:
            return ''

    @staticmethod
    def utc_programme_time(start_t: str, end_t: str, start_date: str) -> tuple[datetime, datetime]:
        """
        Converts given start and end times on a specific date from UK timezone (Europe/London)
        to datetime objects in UTC.

        :param start_t: The start time of the program in string format 'HH:MM'.
        :param end_t: The end time of the program in string format 'HH:MM'.
        :param start_date: The starting date in string format 'DD/MM/YYYY'.

        """
        from datetime import timedelta, timezone
        from resources.lib.utils import strptime, ZoneInfo

        tz_uk = ZoneInfo('Europe/London')
        start_date = strptime(start_date, '%d/%m/%Y').replace(tzinfo=tz_uk)
        start_time = strptime(start_t, '%H:%M')
        start_utc = start_date.replace(hour=start_time.hour, minute=start_time.minute).astimezone(timezone.utc)
        end_time = strptime(end_t, '%H:%M')
        end_utc = start_date.replace(hour=end_time.hour, minute=end_time.minute).astimezone(timezone.utc)
        if start_utc > end_utc:
            end_utc += timedelta(days=1)
        return start_utc, end_utc

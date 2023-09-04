"""
Various Arte items : basic Arte item, Arte Colleciton, Arte Live Item, etc..
"""

import html
import datetime
# pylint: disable=import-error
import dateutil.parser
# pylint: disable=import-error
from xbmcswift2 import xbmc
# pylint: disable=import-error
from xbmcswift2 import actions


# pylint: disable=too-few-public-methods
class ArteItem:
    """
    Item of Arte TV or HBBTV API. It may be a video, a collection or anything.
    It aims at being mapped into XBMC ListItem.
    """

    PREFERED_KINDS = ['TV_SERIES', 'MAGAZINE']

    def __init__(self, plugin, json_dict):
        self.json_dict = json_dict
        self.plugin = plugin

    def format_title_and_subtitle(self):
        """Build string for menu entry thanks to title and optionally subtitle"""
        title = self.json_dict.get('title')
        subtitle = self.json_dict.get('subtitle')
        label = f"[B]{html.unescape(title)}[/B]"
        # suffixes
        if subtitle:
            label += f" - {html.unescape(subtitle)}"
        return label


class ArteVideoItem(ArteItem):
    """
    Video item of Arte TV or HBBTV API. Extract data to build menu item with video details.
    Use abstract method, when data is available in different ways between HBB TV and Arte TV API.
    It aims at being mapped into XBMC ListItem.
    """

    def build_item(self, path, is_playable):
        """Identify what is the type of current item and build the most detailled item possible"""
        if self.is_hbbtv():
            return ArteHbbTvVideoItem(self.plugin, self.json_dict).build_item(path, is_playable)
        return ArteTvVideoItem(self.plugin, self.json_dict).build_item(path, is_playable)

    def _build_item(self, path, is_playable):
        """
        Build ListItem common to HBB TV and Arte TV API.
        """
        item = self.json_dict
        program_id = item.get('programId')
        label = self.format_title_and_subtitle()
        return {
            'label': label,
            'path': path,
            'thumbnail': self._get_image_url(),
            'is_playable': is_playable,
            'info_type': 'video',
            'info': {
                'title': item.get('title'),
                'duration': self._get_duration(),
                'plot': item.get('shortDescription') or item.get('fullDescription'),
                'plotoutline': item.get('teaserText'),
                'aired': self._get_air_date()
            },
            'properties': {
                'fanart_image': self._get_image_url(),
                'TotalTime': str(self._get_duration()),
            },
            'context_menu': [
                (self.plugin.addon.getLocalizedString(30023),
                    actions.background(self.plugin.url_for(
                        'add_favorite', program_id=program_id, label=label))),
                (self.plugin.addon.getLocalizedString(30024),
                    actions.background(self.plugin.url_for(
                        'remove_favorite', program_id=program_id, label=label))),
                (self.plugin.addon.getLocalizedString(30035),
                    actions.background(self.plugin.url_for(
                        'mark_as_watched', program_id=program_id, label=label))),
            ],
        }

    def _get_duration(self):
        """
        Return video item duration in seconds
        """
        item = self.json_dict
        duration = item.get('durationSeconds')
        if isinstance(duration, int):
            return duration
        duration = item.get('duration', None)
        if isinstance(duration, int):
            return duration
        if isinstance(duration, dict):
            if isinstance(duration.get('seconds', None), int):
                return duration.get('seconds')
        return None

    def _get_air_date(self):
        """
        Abstract method to be implemented in child classes.
        Return date when item was showed to public for the first time.
        """
        return None

    def _get_image_url(self):
        """
        Abstract method to be implemented in child classes.
        Return url to image to display for the current item.
        """

    def is_playlist(self):
        """Return True if program_id is a str starting with PL- or RC-."""
        is_playlist_var = False
        program_id = self.json_dict.get('programId')
        if isinstance(program_id, str):
            is_playlist_var = program_id.startswith('RC-') or program_id.startswith('PL-')
        return is_playlist_var

    def is_hbbtv(self):
        """
        Return True, if current item is coming from HBB TV API,
        False if coming from Arte TV API.
        """
        is_hbbtv_content = True
        item = self.json_dict
        kind = item.get('kind')
        if isinstance(kind, dict) and kind.get('code', False):
            kind = kind.get('code')
            is_hbbtv_content = False
        if isinstance(item.get('lastviewed'), dict):
            is_hbbtv_content = False
        return is_hbbtv_content

    def _get_kind(self):
        """
        Return item kind as a string e.g.
        TV_SERIVES, MAGAZINE... for collections
        SHOW, CLIP... for videos
        EXTERNAL... for links
        """
        return None


class ArteTvVideoItem(ArteVideoItem):
    """
    Data and methods to build a XBMC ListItem to play a video
    from Arte TV API data
    """

    def map_artetv_item(self):
        """
        Return video menu item to show content from Arte TV API.
        Manage specificities of various types : playlist, menu or video items
        """
        item = self.json_dict
        program_id = item.get('programId')
        kind = self._get_kind()
        if kind == 'EXTERNAL':
            return None

        additional_context_menu = []
        if self.is_playlist():
            if kind in self.PREFERED_KINDS:
                # content_type = Content.PLAYLIST
                path = self.plugin.url_for('play_collection', kind=kind, collection_id=program_id)
                is_playable = True
                additional_context_menu = [(
                    self.plugin.addon.getLocalizedString(30011),
                    actions.update_view(
                        self.plugin.url_for(
                            'display_collection', program_id=program_id, kind=kind)))]
            else:
                # content_type = Content.MENU_ITEM
                path = self.plugin.url_for('display_collection', kind=kind, program_id=program_id)
                is_playable = False
        else:
            # content_type = Content.VIDEO
            path = self.plugin.url_for('play', kind=kind, program_id=program_id)
            is_playable = True

        xbmc_item = self.build_item(path, is_playable)
        if xbmc_item is not None:
            xbmc_item['context_menu'].extend(additional_context_menu)
        return xbmc_item

    def build_item(self, path, is_playable):
        """
        Return video menu item to show content from Arte TV API.
        Generic method that take variables mapping in inputs.
        :rtype dict[str, Any] | None: To be used in
        https://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem.setInfo
        """
        basic_item = super()._build_item(path, is_playable)
        if basic_item is None:
            return None
        progress = self.get_progress()
        duration = self._get_duration()
        if self.json_dict.get('lastviewed', False) and duration is not None:
            artetv_item = {
                'info': {
                    'playcount': '1' if progress >= 0.95 else '0',
                },
                'properties': {
                    'fanart_image': self._get_image_url(),
                    # ResumeTime and TotalTime deprecated.
                    # Use InfoTagVideo.setResumePoint() instead.
                    'ResumeTime': str(self._get_time_offset()),
                    'TotalTime': str(self._get_duration()),
                    'StartPercent': str(float(self._get_time_offset()) * 100.0 / float(duration))
                },
            }
            basic_item['info'] = {**basic_item['info'], **artetv_item['info']}
            basic_item['properties'] = {**basic_item['properties'], **artetv_item['properties']}

        return basic_item

    def _get_air_date(self):
        airdate = self.json_dict.get('beginsAt')
        if airdate is not None:
            airdate = str(self._parse_date_artetv(airdate))
        return airdate

    def _parse_date_artetv(self, datestr):
        """Try to parse ``datestr`` into a ``datetime`` object like 2022-07-01T03:00:00Z.
        Return ``None`` if parsing fails.
        Similar to ``parse_date_hbbtv``"""
        date = None
        try:
            date = datetime.datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S%z')
        except TypeError:
            date = None
        return date

    def _get_image_url(self):
        item = self.json_dict
        image_url = None
        if item.get('images') and item.get('images')[0] and item.get('images')[0].get('url'):
            # Remove query param type=TEXT to avoid title embeded in image
            image_url = item.get('images')[0].get('url').replace('?type=TEXT', '')
            # Set same image for fanart and thumbnail to spare network bandwidth
            # and business logic easier to maintain
            # if item.get('images')[0].get('alternateResolutions'):
            #    smallerImage = item.get('images')[0].get('alternateResolutions')[3]
            #    if smallerImage and smallerImage.get('url'):
            #        thumbnailUrl = smallerImage.get('url').replace('?type=TEXT', '')
        if not image_url:
            image_url = item.get('mainImage').get('url').replace('__SIZE__', '1920x1080')
        return image_url

    def _get_kind(self):
        kind = self.json_dict.get('kind')
        if isinstance(kind, dict) and kind.get('code', False):
            kind = kind.get('code')
        return kind

    def get_progress(self):
        """
        Return item progress or 0 as float.
        Never None, even if lastviewed or item is None.
        """
        # pylint raises that it is not snake_case. it's in uppercase, because it's a constant
        # pylint: disable=invalid-name
        DEFAULT_PROGRESS = 0.0
        if not self.json_dict:
            return DEFAULT_PROGRESS
        if not self.json_dict.get('lastviewed'):
            return DEFAULT_PROGRESS
        if not self.json_dict.get('lastviewed').get('progress'):
            return DEFAULT_PROGRESS
        return float(self.json_dict.get('lastviewed').get('progress'))

    def _get_time_offset(self):
        item = self.json_dict
        return item.get('lastviewed') and item.get('lastviewed').get('timecode') or 0


class ArteHbbTvVideoItem(ArteVideoItem):
    """
    Data and methods to build a XBMC ListItem to play a video
    from Arte HBB TV API data
    """

    def build_item(self, path, is_playable):
        basic_item = super()._build_item(path, is_playable)
        if basic_item is None:
            return None
        item = self.json_dict
        hbbtv_item = {
            'info': {
                'genre': item.get('genrePresse'),
                'plot': item.get('shortDescription') or item.get('fullDescription'),
                'plotoutline': item.get('teaserText'),
                # year is not correctly used by kodi :(
                # the aired year will be used by kodi for production year :(
                # 'year': int(config.get('productionYear')),
                'country': [country.get('label') for country in \
                            item.get('productionCountries', [])],
                'director': item.get('director'),
            },
        }
        basic_item['info'] = {**basic_item['info'], **hbbtv_item['info']}
        return basic_item

    def _get_air_date(self):
        airdate = self.json_dict.get('broadcastBegin')
        if airdate is not None:
            airdate = str(self._parse_date_hbbtv(airdate))
        return airdate

    def _parse_date_hbbtv(self, datestr):
        """Try to parse ``datestr`` into a ``datetime`` object. Return ``None`` if parsing fails.
        Similar to parse_date_artetv."""
        date = None
        try:
            date = dateutil.parser.parse(datestr)
        except dateutil.parser.ParserError as error:
            xbmc.log(
                f"[plugin.video.arteplussept] Problem with parsing date: {error}",
                level=xbmc.LOGWARNING)
        return date

    def _get_image_url(self):
        return self.json_dict.get('imageUrl')

    def _get_kind(self):
        return self.json_dict.get('kind')


class ArteCollectionItem(ArteItem):
    """
    A collection item is different from a standard video item,
    because it opens a new menu populated with video or collection items
    instead of playing a video.
    """

    def map_collection_as_menu_item(self):
        """Map JSON item to menu entry to access playlist content"""
        item = self.json_dict
        program_id = item.get('programId')
        kind = item.get('kind')

        return {
            'label': self.format_title_and_subtitle(),
            'path': self.plugin.url_for('display_collection', kind=kind, collection_id=program_id),
            'thumbnail': item.get('imageUrl'),
            'info': {
                'title': item.get('title'),
                'plotoutline': item.get('teaserText')
            }
        }

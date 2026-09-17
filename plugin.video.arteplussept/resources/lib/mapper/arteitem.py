"""
Various Arte items : basic Arte item, Arte Colleciton, Arte Live Item, etc..
"""
import html
import datetime
import xbmc
import xbmcgui
from resources.lib import actions
from resources.lib import utils


# pylint: disable=too-few-public-methods
class ArteItem:
    """
    Item of Arte TV API. It may be a video, a collection or anything.
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
    Video item of Arte TV API. Extract data to build menu item with video details.
    Use abstract method, when data is available in different ways between HBB TV and Arte TV API.
    It aims at being mapped into XBMC ListItem.
    """

    def build_item(self, path, is_playable):
        """Identify what is the type of current item and build the most detailled item possible"""
        return ArteTvVideoItem(self.plugin, self.json_dict).build_item(path, is_playable)

    def _build_item(self, path, is_playable):
        """
        Build a native xbmcgui.ListItem for HBB TV and Arte TV API common data.
        """
        item = self.json_dict
        program_id = item.get('programId')
        label = self.format_title_and_subtitle()
        li = xbmcgui.ListItem(label=label)
        if path:
            li.setPath(str(path))
        if hasattr(li, 'setProperty'):
            li.setProperty('is_playable', str(bool(is_playable)))
        li.setArt({
            'thumb': self._get_image_url('480x270', True),
            'fanart': self._get_image_url('1920x1080', False)
        })

        tag = li.getVideoInfoTag()
        tag.setTitle(self.json_dict.get('title'))
        tag.setPlot(self.json_dict.get('shortDescription') or self.json_dict.get('fullDescription'))
        tag.setPlotOutline(self.json_dict.get('teaserText'))
        tag.setMpaa(self._get_mpaa_age_rating())
        tag.setFirstAired(self._get_air_date())
        duration = self._get_duration()
        if duration is not None:
            tag.setDuration(duration)

        li.addContextMenuItems([
            (self.plugin.addon.getLocalizedString(30023),
                actions.background(self.plugin.url_for(
                    'add_favorite', program_id=program_id, label=label))),
            (self.plugin.addon.getLocalizedString(30024),
                actions.background(self.plugin.url_for(
                    'remove_favorite', program_id=program_id, label=label))),
            (self.plugin.addon.getLocalizedString(30035),
                actions.background(self.plugin.url_for(
                    'mark_as_watched', program_id=program_id, label=label))),
        ], replaceItems=False)
        return li

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

    def _get_mpaa_age_rating(self):
        """
        Return mpaa mapped from age rating

        G – General Audiences
        PG – Parental Guidance Suggested
        PG-13 – Parents Strongly Cautioned
        R – Restricted
        NC-17 – Adults Only
        """
        # 'Unknown' instead of None or '' to avoid TypeError with addon routes
        return 'Unknown'

    def _get_air_date(self):
        """
        Abstract method to be implemented in child classes.
        Return date when item was showed to public for the first time.
        """
        raise NotImplementedError("Subclasses must implement _get_air_date")

    def _get_image_url(self, wished_res, wished_text):
        """
        Abstract method to be implemented in child classes.
        Return url to image to display for the current item.
        """
        raise NotImplementedError("Subclasses must implement _get_image_url")

    def is_playlist(self):
        """Return True if program_id is a str starting with PL- or RC-."""
        is_playlist_var = False
        program_id = self.json_dict.get('programId')
        if isinstance(program_id, str):
            is_playlist_var = program_id.startswith('RC-') or program_id.startswith('PL-')
        return is_playlist_var

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

        path = None
        is_playable = None
        additional_context_menu = []

        if kind == 'EXTERNAL':
            deeplink = item.get('deeplink', '')
            if deeplink is not None and deeplink.strip() != "":
                category = deeplink.rsplit("/", 1)[-1]
                path = self.plugin.url_for('raw_page', category=category)
                li = xbmcgui.ListItem(label=item.get('title'), path=path)
                li.setProperty('is_playable', str(False))
                li.setArt({
                    'thumb': self._get_image_url('480x270', True),
                    'fanart': self._get_image_url('1920x1080', False)
                })
                return li
            # else abort, unable to build an item for an external link
            return None

        if self.is_playlist():
            if kind in self.PREFERED_KINDS:
                # content_type = Content.PLAYLIST
                path = self.plugin.url_for(
                    'play_collection', col_id=program_id,
                    mpaa=self._get_mpaa_age_rating())
                is_playable = True
                additional_context_menu = [(
                    self.plugin.addon.getLocalizedString(30011),
                    actions.update_view(
                        self.plugin.url_for('collection', program_id=program_id))
                )]
            else:
                # content_type = Content.MENU_ITEM
                path = self.plugin.url_for('collection', program_id=program_id)
                is_playable = False
        else:
            # content_type = Content.VIDEO
            path = self.plugin.url_for(
                'play', program_id=program_id,
                mpaa=self._get_mpaa_age_rating())
            is_playable = True

        xbmc_item = self.build_item(path, is_playable)
        if xbmc_item is not None and additional_context_menu:
            xbmc_item.addContextMenuItems(additional_context_menu, replaceItems=False)
        return xbmc_item

    def build_item(self, path, is_playable):
        """
        Return video menu item to show content from Arte TV API.
        Generic method that take variables mapping in inputs.
        """
        li = super()._build_item(path, is_playable)
        if li is None:
            return None
        if is_playable:
            li = self.add_adaptive_hls_attr(li)
        progress = self.get_progress()
        duration = self._get_duration()

        tag = li.getVideoInfoTag()
        if self.json_dict.get('lastviewed', False) and duration is not None:
            resume_offset = self._get_time_offset()
            tag.setResumePoint(resume_offset, duration)
            tag.setPlaycount(1 if progress >= 0.95 else 0)
            li.setProperty('StartPercent', str(float(resume_offset) * 100.0 / float(duration)))
            li.setProperty('StartOffset', str(resume_offset))

        return li

    def add_adaptive_hls_attr(self, li: xbmcgui.ListItem):
        """
        Add attributes for listitem to be played by inputstream adaptive
        """
        kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[0:2])
        li.setMimeType('application/vnd.apple.mpegurl')
        ia_name = 'inputstream.adaptive'
        li.setContentLookup(False)
        li.setProperty('inputstream', ia_name)
        # DEPRECATED ON Kodi v21, because the manifest type is now auto-detected.
        if kodi_version in [19, 20]:
            li.setProperty(f"{ia_name}.manifest_type", 'hls')
        # 'stream_headers' ON KODI v19
        # 'manifest_headers' ON KODI v20 and v21
        # 'common_headers' ON KODI v22 and above
        prop_prefix = 'common'
        if kodi_version == 19:
            prop_prefix = 'stream'
        elif kodi_version in [20, 21]:
            prop_prefix = 'manifest'
        prop = f"{ia_name}.{prop_prefix}_headers"
        # li.setProperty(prop, f"User-Agent=(Windows NT 10.0; Win64; x64; rv:150.0)")
        li.setProperty(prop, f"User-Agent={utils.ADDON_USERAGENT}")
        return li

    def _get_mpaa_age_rating(self):
        return utils.mpaa_from_age(self.json_dict.get('ageRating', None))

    def _get_air_date(self):
        airdate = self.json_dict.get('beginsAt')
        if airdate is not None:
            airdate = str(self._parse_date_artetv(airdate))
        return airdate

    def _parse_date_artetv(self, datestr):
        """
        Try to parse ``datestr`` into a ``datetime`` object like 2022-07-01T03:00:00Z.
        Return ``None`` if parsing fails.
        Return a string in W3C format (YYYY-MM-DD).
        """
        date = None
        try:
            date_obj = datetime.datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S%z')
            date = date_obj.strftime("%Y-%m-%d")
        except (TypeError, ValueError) as e:
            xbmc.log(f"arteitem._parse_date_artetv: failed to parse date '{datestr}': {e}",
                     level=xbmc.LOGERROR)
            date = None
        return date

    def _get_image_url(self, wished_res, wished_text):
        item = self.json_dict
        image_url = None
        # extracting image from arte tv player endpoint
        if item.get('images') and item.get('images')[0] and item.get('images')[0].get('url'):
            image_url = item.get('images')[0].get('url')
        # extracting image from content data from arte tv home page or zone endpoint
        if item.get('mainImage') and item.get('mainImage').get('url'):
            image_url = item.get('mainImage').get('url')

        # post processing
        if isinstance(image_url, str):
            if wished_text is False:
                # Remove query param type=TEXT to avoid title embeded in image
                image_url = image_url.replace('?type=TEXT', '')
            if isinstance(wished_res, str):
                # 940x530 is the most common size from player endpoint
                # __SIZE__ is the size from home page or zone endpoint
                for from_str in ['/940x530', '/__SIZE__']:
                    image_url = image_url.replace(from_str, f"/{wished_res}")

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
        label = self.format_title_and_subtitle()
        li = xbmcgui.ListItem(label=label)
        li.setPath(self.plugin.url_for('collection', program_id=program_id))
        li.setProperty('is_playable', 'False')
        tag = li.getVideoInfoTag()
        tag.setTitle(item.get('title'))
        tag.setPlotOutline(item.get('teaserText'))
        return li

"""
Module for ArteLiveItem depends on ArteTvVideoItem
"""

import html
import xbmcgui
from resources.lib import actions
from resources.lib import utils
from resources.lib.mapper.arteitem import ArteTvVideoItem


class ArteLiveItem(ArteTvVideoItem):
    """
    Arte Live is slightly different from standard item, because it is stream from Arte TV API only.
    It cannot be part of a playlist.
    Its label is prefixed with LIVE.
    """

    def format_title_and_subtitle(self):
        """Orange prefix LIVE for live stream"""
        meta = self.json_dict.get('attributes').get('metadata')
        title = meta.get('title')
        subtitle = meta.get('subtitle')
        label = f"[B][COLOR ffffa500]LIVE[/COLOR] - {html.unescape(title)}[/B]"
        # suffixes
        if subtitle:
            label += f" - {html.unescape(subtitle)}"
        return label

    def build_item_live(self):
        """Return menu entry to watch live content from Arte TV API"""
        item = self.json_dict
        attr = item.get('attributes')
        meta = attr.get('metadata')

        duration = meta.get('duration').get('seconds')

        fanart_url = ""
        thumbnail_url = ""
        if meta.get('images') and meta.get('images')[0] and meta.get('images')[0].get('url'):
            # Remove query param type=TEXT to avoid title embeded in image
            fanart_url = meta.get('images')[0].get('url').replace('?type=TEXT', '')
            thumbnail_url = fanart_url
        mpaa = self._get_mpaa_age_restriction()

        live_item = xbmcgui.ListItem(label=self.format_title_and_subtitle())
        live_item.setArt({'thumb': thumbnail_url, 'fanart': fanart_url})
        tag = live_item.getVideoInfoTag()
        tag.setTitle(meta.get('title'))
        tag.setPlot(self.json_dict.get('shortDescription') or self.json_dict.get('fullDescription'))
        tag.setPlotOutline(self.json_dict.get('teaserText'))
        tag.setCountries([country.get('label') for country in item.get('productionCountries', [])])
        tag.setDirectors([item.get('director')])
        tag.setMpaa(self._get_mpaa_age_rating())
        tag.setFirstAired(self._get_air_date())
        duration = self._get_duration()
        if duration:
            tag.setDuration(duration)
        live_item.setProperty('is_playable', 'True')
        live_item = self.add_adaptive_hls_attr(live_item)

        # playing the stream from program id makes the live starts from the beginning
        # while it starts the video like the live tv, with the above
        prgm_id = meta.get('providerId')
        streams = attr.get('streams', [])
        if len(streams) > 0 and streams[0].get('url'):
            path = streams[0].get('url')
            live_item.setPath(self.plugin.url_for(
                'play_live', stream_url=path, mpaa=mpaa))
            live_item.addContextMenuItems([(
                self.plugin.addon.getLocalizedString(30060),
                actions.background(self.plugin.url_for(
                    'play', program_id=prgm_id, mpaa=mpaa))
            )])
        else:
            live_item.setPath(self.plugin.url_for(
                'play', program_id=prgm_id, mpaa=mpaa)
            )

        return live_item

    def _get_mpaa_age_restriction(self):
        item = self.json_dict
        age_restriction = item.get('attributes').get('restriction').get('ageRestriction', 'Unknown')
        return utils.mpaa_from_age(age_restriction)

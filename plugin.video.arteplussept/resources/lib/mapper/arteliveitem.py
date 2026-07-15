"""
Module for ArteLiveItem depends on ArteTvVideoItem and mapper module
for map_playable and match_hbbtv
"""

import html
# pylint: disable=import-error
from xbmcswift2 import actions
# the goal is to break/limit this dependency as much as possible
from resources.lib.mapper import mapper
from resources.lib.mapper.arteitem import ArteTvVideoItem
from resources.lib import utils
from resources.lib.utils import PlayFrom


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

    def build_item_live(self, quality, audio_slot):
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

        live_item = {
            'label': self.format_title_and_subtitle(),
            'thumbnail': thumbnail_url,
            'is_playable': True,
            'info_type': 'video',
            'info': {
                'title': meta.get('title'),
                'duration': duration,
                'plot': meta.get('description'),
                'playcount': '0',
                'mpaa': self._get_mpaa_age_restriction(),
            },
            'properties': {
                'fanart_image': fanart_url,
            }
        }

        # playing the stream from program id makes the live starts from the beginning
        # while it starts the video like the live tv, with the above
        live_stream_item = mapper.map_playable(
            attr.get('streams'), quality, audio_slot, mapper.match_artetv)
        if live_stream_item:
            live_item['path'] = self.plugin.url_for(
                'play_live', stream_url=live_stream_item.get('path'), mpaa=mpaa)
            live_item['context_menu'] = [(
                self.plugin.addon.getLocalizedString(30060),
                actions.background(self.plugin.url_for(
                    'play_from', kind='SHOW', program_id=meta.get('providerId'), mpaa=mpaa,
                    play_from=PlayFrom.CTX.value))
            )]
        else:
            live_item['path'] = self.plugin.url_for(
                'play_from', kind='SHOW', program_id=meta.get('providerId'), mpaa=mpaa,
                play_from=PlayFrom.ITM.value)

        return live_item

    def _get_mpaa_age_restriction(self):
        item = self.json_dict
        age_restriction = item.get('attributes').get('restriction').get('ageRestriction', None)
        return utils.mpaa_from_age(age_restriction)

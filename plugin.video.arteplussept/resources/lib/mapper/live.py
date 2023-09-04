"""
Module for ArteLiveItem depends on ArteTvVideoItem and mapper module
for map_playable and match_hbbtv
"""

import html
# the goal is to break/limit this dependency as much as possible
from resources.lib.mapper import mapper
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

    def build_item_live(self, quality, audio_slot):
        """Return menu entry to watch live content from Arte TV API"""
        # program_id = item.get('id')
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
            # Set same image for fanart and thumbnail to spare network bandwidth
            # and business logic easier to maintain
            # if item.get('images')[0].get('alternateResolutions'):
            #    smallerImage = item.get('images')[0].get('alternateResolutions')[3]
            #    if smallerImage and smallerImage.get('url'):
            #        thumbnailUrl = smallerImage.get('url').replace('?type=TEXT', '')
        stream_url = mapper.map_playable(
            attr.get('streams'), quality, audio_slot, mapper.match_artetv).get('path')

        return {
            'label': self.format_title_and_subtitle(),
            'path': self.plugin.url_for('play_live', stream_url=stream_url),
            # playing the stream from program id makes the live starts from the beginning
            # while it starts the video like the live tv, with the above
            #  'path': plugin.url_for('play', kind='SHOW', program_id=programId.replace('_fr', '')),
            'thumbnail': thumbnail_url,
            'is_playable': True,  # not show_video_streams
            'info_type': 'video',
            'info': {
                'title': meta.get('title'),
                'duration': duration,
                'plot': meta.get('description'),
                # 'director': item.get('director'),
                # 'aired': airdate
                'playcount': '0',
            },
            'properties': {
                'fanart_image': fanart_url,
            }
        }

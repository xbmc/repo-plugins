# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from resources.lib.vrtplayer import metadatacreator


class MetadataCollector:

    @staticmethod
    def get_az_metadata(tile):
        metadata_creator = metadatacreator.MetadataCreator()
        description = ''
        description_item = tile.find(class_='nui-tile--content')
        if description_item is not None:
            p_item = description_item.find('p')
            if p_item is not None:
                description = p_item.text.strip()
        metadata_creator.plot = description
        return metadata_creator.get_video_dict()

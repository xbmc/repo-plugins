import re
import time
from resources.lib.vrtplayer import metadatacreator
from resources.lib.vrtplayer import statichelper

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
        return metadata_creator.get_video_dictionary()


import re
from resources.lib.vrtplayer import metadatacreator
from resources.lib.vrtplayer import statichelper


class MetadataCollector:

    def __init__(self):
        pass

    def get_single_layout_episode_metadata(self, soup):
        metadata_creator = metadatacreator.MetadataCreator()
        metadata_creator.duration = self.__get_episode_duration(soup)
        metadata_creator.plot = self.get_plot(soup)
        return metadata_creator.get_video_dictionary()

    def get_multiple_layout_episode_metadata(self, soup):
        metadata_creator = metadatacreator.MetadataCreator()
        metadata_creator.duration = self.__get_multiple_layout_episode_duration(soup)
        return metadata_creator.get_video_dictionary()

    @staticmethod
    def __get_episode_duration( soup):
        duration = None
        duration_item = soup.find(class_="content__duration")
        if duration_item is not None:
            minutes = re.findall("\d+", duration_item.text)
            if len(minutes) != 0:
                duration = statichelper.minutes_string_to_seconds_int(minutes[0])
        return duration

    @staticmethod
    def get_az_metadata(tile):
        metadata_creator = metadatacreator.MetadataCreator()
        description = ""
        description_item = tile.find(class_="tile__description")
        if description_item is not None:
            p_item = description_item.find("p")
            if p_item is not None:
                description = p_item.text.strip()
        metadata_creator.plot = description
        return metadata_creator.get_video_dictionary()

    @staticmethod
    def get_plot(soup):
        description = ""
        description_item = soup.find(class_="content__shortdescription")
        if description_item is not None:
            description = description_item.text
        return description

    @staticmethod
    def __get_multiple_layout_episode_duration(soup):
        seconds = None
        minutes_element = soup.find("abbr", {"title": "minuten"})
        if minutes_element is not None and minutes_element.parent is not None:
            minutes = minutes_element.parent.next_element
            seconds = statichelper.minutes_string_to_seconds_int(minutes)
        return seconds

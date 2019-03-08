import requests
from resources.lib.vrtplayer import statichelper, metadatacreator, actions
from resources.lib.helperobjects import helperobjects
from bs4 import BeautifulSoup
import time

class VRTApiHelper:
    
    _API_URL = 'https://search.vrt.be/search?size=150&facets[programUrl]=//www.vrt.be'



    def get_video_items(self, relevant_url, season):
        joined_url = self._API_URL + relevant_url.replace(".relevant" ,"")
        response = (requests.get(joined_url)).json()
        result_list = response['results']
        items = None
        if not season:
            items = VRTApiHelper.__get_seasons_if_multiple_seasons_present(result_list, relevant_url)

        if not items : #if no seasons present get regular video items
           items = VRTApiHelper.__map_to_title_items(result_list, season)
        return items

    @staticmethod
    def __get_seasons_if_multiple_seasons_present( result_list, relevant_url):
        seasons = list(statichelper.distinct(list(map(lambda x: VRTApiHelper.__get_season(x), result_list))))
        items = None
        if len(seasons) > 1:
            items = list(map(lambda x: VRTApiHelper.__map_to_season_title_item(x, relevant_url), seasons))
        return items

    @staticmethod
    def __get_season(result):
        metadata_creator = metadatacreator.MetadataCreator()
        return result['seasonName']

    @staticmethod
    def __map_to_season_title_item(season, url):
        return helperobjects.TitleItem('Seizoen ' +season, {'action': actions.LISTING_VIDEOS, 'season': season,'video': url}, False)
    
    @staticmethod
    def __map_to_title_items(results, season):
        title_items = []
        for result in results:
            season_name = result['seasonName']
            if (season is None) or (season is not None and season_name == season):
                metadata_creator = metadatacreator.MetadataCreator()
                json_broadcast_date = result['broadcastDate']
                title = ''
                if json_broadcast_date != -1 :
                    epoch_in_seconds = result['broadcastDate']/1000
                    metadata_creator.datetime = time.localtime(epoch_in_seconds)
                    title = metadata_creator.datetime_as_short_date + ' '
                description = BeautifulSoup(result['shortDescription'], 'html.parser').text
                metadata_creator.duration = result['duration']
                metadata_creator.plot = BeautifulSoup(result['description'], 'html.parser').text
                metadata_creator.plotoutline = result['shortDescription']
                thumb_url = result['videoThumbnailUrl']
                thumb = statichelper.replace_double_slashes_with_https(thumb_url) if thumb_url.startswith("//") else thumb_url
                
                #sometimes shortdescription is empty if that's the case use title => always prepend date
                title = title +  (description if description != '' else result['title'])
                title_items.append(helperobjects.TitleItem(title, {'action': actions.PLAY, 'video': result['url']}, True, thumb, metadata_creator.get_video_dictionary()))

        return title_items



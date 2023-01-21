# -*- coding: utf-8 -*-
from __future__ import absolute_import,unicode_literals
import json
import re
import requests
from resources.lib.helper import strip_html_tags
from resources.lib import logging
from resources.lib.listing.listitem import VideoItem, ShowItem

class GraphQL:
  """
  The GraphQL module communicates with the Apollo GraphQL server
  used in the SVT backend.

  THe server uses persisted queries which means that instead of a whole
  query only a hash is sent to the server indicating what query to execute.
  The queries may change in the future and the hard coded hashes used here then
  need to be updated.
  More info at https://www.apollographql.com/docs/apollo-server/performance/apq/
  """
    
  def __init__(self):
    pass

  def getPopular(self):
    return self.__get_start_page_selection("popular_start")

  def getLatest(self):
    return self.__get_start_page_selection("latest_start")
  
  def getLastChance(self):
    return self.__get_start_page_selection("lastchance_start")

  def getLive(self):
    return self.__get_start_page_selection("live_start")

  def getAtoO(self):
    return self.__get_all_programs()

  def getProgramsByLetter(self, letter):
    """
    Returns a list of all program starting with the supplied letter.
    """
    logging.log("getProgramsByLetter: {}".format(letter))
    programs = self.__get_all_programs()
    if not programs:
      return None
    items = []
    pattern = "^[{}]".format(letter.upper())
    for item in programs:
      if re.search(pattern, item.title):
        items.append(item)
    return items

  def getGenres(self):
    operation_name = "AllGenres"
    query_hash = "6bef51146d05b427fba78f326453127f7601188e46038c9a5c7b9c2649d4719c"
    json_data = self.__get(operation_name, query_hash)
    if not json_data:
      return None
    genres = []
    for item in json_data["genresSortedByName"]["genres"]:
      genre = {}
      genre["title"] = item["name"]
      genre["genre"] = item["id"]
      genres.append(genre)
    return genres

  def getProgramsForGenre(self, genre):
    operation_name = "GenreProgramsAO"
    query_hash = "189b3613ec93e869feace9a379cca47d8b68b97b3f53c04163769dcffa509318"
    variables = {"genre":[genre]}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    raw_items = []
    for selection in json_data["genres"][0]["selectionsForWeb"]:
      if selection["id"] == "all-{}".format(genre):
        raw_items = selection
        break
    if not raw_items:
      logging.error("Could not find content for genre {}".format(genre))
      return None
    programs = []
    for item in raw_items["items"]:
      item = item["item"]
      title = item["name"]
      item_id = item["urls"]["svtplay"]
      thumbnail = self.get_thumbnail_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
      geo_restricted = item["restrictions"]["onlyAvailableInSweden"]
      info = {
        "plot" : item["longDescription"]
      }
      type_name = item["__typename"]
      play_item = self.__create_item(title, type_name, item_id, geo_restricted, thumbnail, info)
      programs.append(play_item)
    return programs
  
  def getVideoContent(self, slug):
    operation_name = "TitlePage"
    query_hash = "4122efcb63970216e0cfb8abb25b74d1ba2bb7e780f438bbee19d92230d491c5"
    variables = {"titleSlugs":[slug]}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    if not json_data["listablesBySlug"]:
      return None
    video_items = []
    show_data = json_data["listablesBySlug"][0]
    show_image_id = show_data["image"]["id"]
    show_image_changed = show_data["image"]["changed"]
    for content in json_data["listablesBySlug"][0]["associatedContent"]:
      if content["id"] == "upcoming":
        continue
      for item in content["items"]:
        item = item["item"]
        season_title = ""
        if content["type"] == "Season" and content["name"]:
          season_title = content["name"]
        title = item["name"]
        video_id = item["urls"]["svtplay"]
        geo_restricted = item["restrictions"]["onlyAvailableInSweden"]
        thumbnail = self.get_thumbnail_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
        fanart = self.get_fanart_url(show_image_id, show_image_changed)
        info = {
          "plot" : item["longDescription"],
          "duration" : item.get("duration", 0)
        }
        video_item = VideoItem(title, video_id, thumbnail, geo_restricted, info, fanart, season_title)
        video_items.append(video_item)
    return video_items

  def getLatestNews(self):
    return self.__get_latest_for_genre("nyheter")
  
  def __get_latest_for_genre(self, genre):
    operation_name = "GenreLists"
    query_hash = "90dca0b51b57904ccc59a418332e43e17db21c93a2346d1c73e05583a9aa598c"
    variables = {"genre":[genre]}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data or not json_data["genres"]:
      return None
    raw_items = []
    if not json_data["genres"][0]["selectionsForWeb"]:
      return None
    for selection in json_data["genres"][0]["selectionsForWeb"]:
      if selection["id"] != "latest-{}".format(genre):
        continue
      raw_items = selection["items"]
    latest_items = []
    for teaser in raw_items:
      title = "{show} - {episode}".format(show=teaser["heading"], episode=teaser["subHeading"])
      images = teaser.get("images", None)
      item = teaser["item"]
      video_id = item["urls"]["svtplay"]
      thumbnail = self.get_thumbnail_url(images["wide"]["id"], images["wide"]["changed"]) if images else ""
      fanart = self.get_fanart_url(images["wide"]["id"], images["wide"]["changed"]) if images else ""
      geo_restricted = item["restrictions"].get("onlyAvailableInSweden", False)
      info = {
        "duration": item.get("duration", 0)
      }
      video_item = VideoItem(title, video_id, thumbnail, geo_restricted, info, fanart)
      latest_items.append(video_item)
    return latest_items

  def getSearchResults(self, query_string):
    operation_name = "SearchPage"
    query_hash = "ab8c604fc76d14885dcedd0f377b76afae9aabcde73b3324676f60ca86d12606"
    variables = {"querystring":query_string}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None

    if not json_data['searchPage']['flat']:
        return []

    results = []

    for search_hit in json_data["searchPage"]["flat"]["hits"]:
      item = search_hit["teaser"]["item"]
      type_name = item["__typename"]
      if not self.__is_supported_type(type_name):
        logging.log("Unsupported search result type \"{}\"".format(type_name))
        logging.log(item)
        continue
      title = search_hit["teaser"]["heading"]
      geo_restricted = item["restrictions"]["onlyAvailableInSweden"]
      item_id = item["urls"]["svtplay"]
      thumbnail = self.get_thumbnail_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
      info = {
        "plot" : search_hit["teaser"]["description"]
      }
      play_item = self.__create_item(title, type_name, item_id, geo_restricted, thumbnail, info)
      results.append(play_item)
    return results

  def getVideoDataForLegacyId(self, legacy_id):
    """
    legacy_id is the integer part of a video URL.
    24186626 in the case of /video/24186626/filip-och-mona/filip-och-mona-sasong-1-avsnitt-1
    """
    operation_name = "VideoPage"
    query_hash = "ae75c500d4f6f8743f6673f8ade2f8af89fb019d4b23f464ad84658734838c78"
    variables = {"legacyIds":[legacy_id]}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    if not json_data["listablesByEscenicId"]:
      logging.error("Could not find legacy ID {}".format(legacy_id))
      return None
    return {
      "svtId" : json_data["listablesByEscenicId"][0]["svtId"],
      "blockedForChildren" : json_data["listablesByEscenicId"][0]["restrictions"]["blockedForChildren"]
    }

  def getVideoDataForVideoUrl(self, video_url):
    """
    Returns video data for any video url.

    The returned data contains "svtId" and "blockedForChildren"
    """
    operation_name = "DetailsPageQuery"
    query_hash = "5be42eb4028ed8f2680ce2302f6887df3fed2dcb6f61ac091ff5a37a3d0bf477"
    variables = {"path":video_url}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    return {
      "svtId" : json_data["detailsPageByPath"]["video"]["svtId"],
      "blockedForChildren": json_data["detailsPageByPath"]["moreDetails"]["restrictions"]["blockedForChildren"]
    }

  def getChannels(self):
    operation_name = "ChannelsQuery"
    query_hash = "210be4b72f03223b990f031d9a2e3501ff9284f8d2c66b01b255a807775f0b19"
    json_data = self.__get(operation_name, query_hash)
    if not json_data:
      return None
    channels = []
    for channel in json_data["channels"]["channels"]:
      video_id = channel["id"]
      running_show = channel.get("running", None)
      if not running_show:
        continue
      title = channel["name"] + " - " + running_show["name"]
      info = {
        "plot": running_show["description"],
        "title": title
      }
      geo_restricted = True # Channels are always geo restricted
      thumbnail = self.get_thumbnail_url(running_show["image"]["id"], running_show["image"]["changed"])
      video_item = VideoItem(title, video_id, thumbnail, geo_restricted, info)
      channels.append(video_item)
    return channels


  def get_thumbnail_url(self, image_id, image_changed):
    return self.__get_image_url(image_id, image_changed, "thumbnail")

  def get_fanart_url(self, image_id, image_changed):
    return self.__get_image_url(image_id, image_changed, "fanart")
  
  def get_poster_url(self, image_id, image_changed):
    return self.__get_image_url(image_id, image_changed, "poster")

  def __get_start_page_selection(self, selection_id):
    operation_name = "GridPage"
    query_hash = "b30578b1b188242ce190c8a2cefe3d4694efafd17a929d08d273ae224a302b24"
    variables = { "selectionId": selection_id }
    json_data = self.__get(operation_name, query_hash=query_hash, variables=variables)
    if not json_data:
      return None
    selections = json_data["startForSvtPlay"]["selections"]
    if not selections:
      logging.error("No selections returned for start page")
      return None
    selection = {}
    for raw_selection in selections:
      if raw_selection["id"] == selection_id:
        selection = raw_selection
        break
    if not selection:
      logging.error("Selection {selection_id} was not found in selections".format(selection_id=selection_id))
      return None
    video_items = []
    for item in selection["items"]:
      image_id = item["images"]["wide"]["id"]
      image_changed = item["images"]["wide"]["changed"]
      title = "{show} - {episode}".format(show=item["heading"], episode=item["subHeading"])
      item = item["item"]
      video_id = item["urls"]["svtplay"]
      thumbnail = self.get_thumbnail_url(image_id, image_changed)
      geo_restricted = item["restrictions"]["onlyAvailableInSweden"]
      video_info = {
        "plot": item["longDescription"]
      }
      fanart = self.get_fanart_url(image_id, image_changed)
      video_item = VideoItem(title, video_id, thumbnail, geo_restricted, info=video_info, fanart=fanart)
      video_items.append(video_item)
    return video_items

  def __get_all_programs(self):
    operation_name = "ProgramsListing"
    query_hash = "1eeb0fb08078393c17658c1a22e7eea3fbaa34bd2667cec91bbc4db8d778580f"
    json_data = self.__get(operation_name, query_hash)
    if not json_data:
      return None
    items = []
    for raw_item in json_data["programAtillO"]["flat"]:
      if raw_item["oppetArkiv"]:
        continue
      title = raw_item["name"]
      item_id = raw_item["urls"]["svtplay"]
      item_type = raw_item["__typename"]
      geo_restricted = raw_item["restrictions"]["onlyAvailableInSweden"]
      item = self.__create_item(title, item_type, item_id, geo_restricted)
      items.append(item)
    return sorted(items, key=lambda item: item.title)

  def __create_item(self, title, type_name, item_id, geo_restricted, thumbnail="", info={}, fanart=""):
    title = strip_html_tags(title)

    for k in info:
        info[k] = strip_html_tags(info[k])

    if self.__is_video(type_name):
      return VideoItem(title, item_id, thumbnail, geo_restricted, info=info, fanart=fanart)
    elif self.__is_show(type_name):
      slug = item_id.split("/")[-1]
      return ShowItem(title, slug, thumbnail, geo_restricted, info=info, fanart=fanart)
    else:
      raise ValueError("Type {} is not supported!".format(type_name))

  SHOW_TYPES = ["TvShow", "KidsTvShow", "TvSeries"]
  VIDEO_TYPES = ["Episode", "Clip", "Single"]

  def __is_supported_type(self, type_name):
    return type_name in self.SHOW_TYPES + self.VIDEO_TYPES

  def __is_video(self, type_name):
    return type_name in self.VIDEO_TYPES

  def __is_show(self, type_name):
    return type_name in self.SHOW_TYPES    

  def __get_image_url(self, image_id, image_changed, image_type):
    """
    image_id is expected to look like "12345/6789"
    """
    base_url = "https://www.svtstatic.se/image"
    ratio = ""
    size = ""
    if image_type == "thumbnail":
      ratio = "medium"
      size = 800
    elif image_type == "fanart" :
        ratio = "wide"
        size = 1920
    elif image_type == "poster" :
        ratio = "large"
        size = 1080
    else:
      raise ValueError("Image type {} is not supported!".format(image_type))
    return "{base_url}/{ratio}/{size}/{image_id}/{image_changed}"\
      .format(base_url=base_url, ratio=ratio, size=size, image_type=image_type, image_id=image_id, image_changed=image_changed)
    
  def __get(self, operation_name, query_hash="", variables = {}):
    base_url = "https://api.svt.se/contento/graphql"
    param_ua = "svtplaywebb-play-render-prod-client"
    ext = {}
    if query_hash:
        ext["persistedQuery"] = {"version":1,"sha256Hash":query_hash}
    query_params = "operationName={op}&variables={variables}&extensions={ext}&ua={ua}"\
      .format(\
        ua=param_ua, \
        op=operation_name, \
        variables=json.dumps(variables, separators=(',', ':')), \
        ext=json.dumps(ext, separators=(',', ':'))\
      )
    url = "{base}?{query_params}".format(base=base_url, query_params=query_params)
    logging.log("GraphQL request: {}".format(url))
    response = requests.get(url)
    if response.status_code != 200:
      logging.error("Request failed, code: {code}, url: {url}".format(code=response.status_code, url=url))
      return None
    json_data = response.json()
    return json_data["data"]

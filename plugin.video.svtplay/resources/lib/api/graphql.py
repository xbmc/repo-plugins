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
    return self.getGridPageContents("popular_start")

  def getLatest(self):
    return self.getGridPageContents("latest_start")
  
  def getLastChance(self):
    return self.getGridPageContents("lastchance_start")

  def getLive(self):
    return self.getGridPageContents("live_start")

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
    operation_name = "MainGenres"
    query_hash = "65b3d9bccd1adf175d2ad6b1aaa482bb36f382f7bad6c555750f33322bc2b489"
    json_data = self.__get(operation_name, query_hash)
    if not json_data:
      return None
    genres = []
    for item in json_data["genresInMain"]["genres"]:
      genre = {}
      genre["title"] = item["name"]
      genre["genre"] = item["id"]
      genres.append(genre)
    return genres

  def getProgramsForGenre(self, genre):
    operation_name = "CategoryPageQuery"
    query_hash = "00be06320342614f4b186e9c7710c29a7fc235a1936bde08a6ab0f427131bfaf"
    variables = {"id":genre, "tab": "all"}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    selections = []
    for tab in json_data["categoryPage"]["lazyLoadedTabs"]:
      if tab["id"] == "program-ao-{}".format(genre):
        selections = tab["selections"][0]
        break
    if not selections:
      logging.error("Could not find content for genre {}".format(genre))
      return None
    programs = []
    for teaser in selections["items"]:
      item = teaser["item"]
      title = item["name"]
      item_id = item["urls"]["svtplay"]
      thumbnail = self.get_thumbnail_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
      geo_restricted = item["restrictions"]["onlyAvailableInSweden"]
      info = {
        "plot" : teaser["subHeading"]
      }
      type_name = item["__typename"]
      play_item = self.__create_item(title, type_name, item_id, geo_restricted, thumbnail, info)
      programs.append(play_item)
    return programs
  
  def getGridPageContents(self, selectionId):
    operation_name = "GridPage"
    query_hash = "a8248fc130da34208aba94c4d5cc7bd44187b5f36476d8d05e03724321aafb40"
    variables = {"selectionId" : selectionId}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    items = json_data["selectionById"]["items"]
    list_items = []
    for teaser in items:
      item = teaser["item"]
      title = item["name"]
      if self.__is_video(item["__typename"]) and item["__typename"] != "Single":
        title = "{tvshow} - {episode}".format(episode=item["name"], tvshow=item["parent"]["name"])
      item_id = item["urls"]["svtplay"]
      geo_restricted = item["restrictions"]["onlyAvailableInSweden"]
      thumbnail = self.get_thumbnail_url(item["images"]["cleanWide"]["id"], item["images"]["cleanWide"]["changed"]) if "images" in item else ""
      fanart = self.get_fanart_url(teaser["images"]["wide"]["id"], teaser["images"]["wide"]["changed"]) if "images" in teaser else ""
      info = {
        "plot" : teaser["description"],
        "duration" : item.get("duration", 0),
        "episode" : item.get("number", 0),
        "tvshowtitle" : item["parent"]["name"] if "parent" in item else ""
      }
      list_items.append(self.__create_item(title, item["__typename"], item_id, geo_restricted, thumbnail, info, fanart))
    return list_items

  def getVideoContent(self, slug):
    operation_name = "DetailsPageQuery"
    query_hash = "e240d515657bbb54f33cf158cea581f6303b8f01f3022ea3f9419fbe3a5614b0"
    variables = {"path":"/{}".format(slug)}
    json_data = self.__post(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    if not json_data["detailsPageByPath"]:
      return None
    video_items = []
    show_data = json_data["detailsPageByPath"]
    show_image_id = show_data["images"]["wide"]["id"]
    show_image_changed = show_data["images"]["wide"]["changed"]
    for selection in json_data["detailsPageByPath"]["associatedContent"]:
      if selection["id"] == "upcoming":
        continue
      for teaser in selection["items"]:
        item = teaser["item"]
        season_title = selection["name"] if selection["selectionType"] == "season" else ""
        title = item["name"]
        video_id = item["urls"]["svtplay"]
        geo_restricted = item["restrictions"]["onlyAvailableInSweden"]
        thumbnail = self.get_thumbnail_url(item["images"]["cleanWide"]["id"], item["images"]["cleanWide"]["changed"]) if "images" in item else ""
        fanart = self.get_fanart_url(show_image_id, show_image_changed)
        info = {
          "plot" : teaser["description"],
          "duration" : item.get("duration", 0),
          "episode" : item.get("number", 0),
          "tvshowtitle" : item["parent"]["name"] if "parent" in item else ""
        }
        video_item = VideoItem(title, video_id, thumbnail, geo_restricted, info, fanart, season_title)
        video_items.append(video_item)
    return video_items

  def getSearchResults(self, query_string):
    operation_name = "SearchPage"
    query_hash = "f097c31299aa9b4ecdc4aaaf98a14444efda5dfbbc8cdaaeb7c3be37ae2b036a"
    variables = {"query":query_string}
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

  def __get_all_programs(self):
    operation_name = "ProgramsListing"
    query_hash = "17252e11da632f5c0d1b924b32be9191f6854723a0f50fb2adb35f72bb670efa"
    json_data = self.__get(operation_name, query_hash)
    if not json_data:
      return None
    items = []
    for selection in json_data["programAtillO"]["selections"]:
      for teaser in selection["items"]:
        raw_item = teaser["item"]
        title = teaser["heading"]
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
    return self.__fetch(operation_name, query_hash, variables, method="get")

  def __post(self, operation_name, query_hash="", variables = {}):
    return self.__fetch(operation_name, query_hash, variables, method="post")

  def __fetch(self, operation_name, query_hash="", variables = {}, method="get"):
    base_url = "https://api.svt.se/contento/graphql"
    param_ua = "svtplaywebb-play-render-produnction-client"
    ext = {}
    if query_hash:
        ext["persistedQuery"] = {"version":1,"sha256Hash":query_hash}
    response = None
    url = base_url
    if method == "get":
      query_params = "operationName={op}&variables={variables}&extensions={ext}&ua={ua}".format(
        ua=param_ua,
        op=operation_name,
        variables=json.dumps(variables, separators=(',', ':')),
        ext=json.dumps(ext, separators=(',', ':'))
      )
      logging.log("GraphQL GET request: {}".format(url))
      response = requests.get(url, params=query_params)
    elif method == "post":
        payload = {
          "operationName": operation_name,
          "variables": variables,
          "extensions": ext
        }
        logging.log("GraphQL POST request: {}".format(url))
        response = requests.post(url, json=payload)
    if response.status_code != 200:
      logging.error("Request failed, code: {code}, url: {url}".format(code=response.status_code, url=url))
      return None
    json_data = response.json()
    try:
      return json_data["data"]
    except KeyError:
      logging.error("Missing key 'data' in JSON response: {} for operationName={}, variables={}, queryHash={}".format(response.json(), operation_name, variables, query_hash))
      return None

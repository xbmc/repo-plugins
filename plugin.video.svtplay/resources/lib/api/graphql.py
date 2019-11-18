# -*- coding: utf-8 -*-
# system imports
from __future__ import absolute_import,unicode_literals
import json
import re
import requests
from resources.lib import logging

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
      if re.search(pattern, item["title"]):
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
      url = item["urls"]["svtplay"]
      plot = item["longDescription"]
      programs.append({
        "title": title,
        "url": url,
        "thumbnail": self.get_thumbnail_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else "",
        "info": {
          "plot": plot, 
          "fanart": self.get_fanart_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
        },
        "type" : "video" if item["__typename"] == "Single" or item["__typename"] == "Episode" else "program",
        "onlyAvailableInSweden" : item["restrictions"]["onlyAvailableInSweden"],
        "inappropriateForChildren" : False
      })
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
    episodes = []
    inappropriate_for_children = json_data["listablesBySlug"][0]
    for content in json_data["listablesBySlug"][0]["associatedContent"]:
      if content["id"] == "upcoming":
        continue
      for item in content["items"]:
        episode = {}
        item = item["item"]
        episode["title"] = item["name"]
        episode["url"] = item["urls"]["svtplay"]
        episode["onlyAvailableInSweden"] = item["restrictions"]["onlyAvailableInSweden"]
        episode["inappropriateForChildren"] = inappropriate_for_children
        episode["type"] = "video"
        episode["thumbnail"] = self.get_thumbnail_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
        info = {}
        info["plot"] = item["longDescription"]
        info["duration"] = item.get("duration", 0)
        info["fanart"] = self.get_fanart_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
        episode["info"] = info
        episodes.append(episode)
    return episodes

  def getLatestNews(self):
    operation_name = "GenreLists"
    query_hash = "90dca0b51b57904ccc59a418332e43e17db21c93a2346d1c73e05583a9aa598c"
    variables = {"genre":["nyheter"]}
    genre = "nyheter"
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
    latest_news = []
    for item in raw_items:
      title = "{heading} - {subHeading}".format(heading=item["heading"], subHeading=item["subHeading"])
      images = item["images"]
      item = item["item"]
      episode = {}
      episode["title"] = title
      episode["url"] = item["urls"]["svtplay"]
      episode["thumbnail"] = self.get_thumbnail_url(images["wide"]["id"], images["wide"]["changed"]) if images else ""
      episode["inappropriateForChildren"] = False
      episode["onlyAvailableInSweden"] = item["restrictions"].get("onlyAvailableInSweden", False)
      episode["info"] = {
        "duration": item["duration"],
        "fanart": self.get_fanart_url(images["wide"]["id"], images["wide"]["changed"]) if images else ""
      }
      latest_news.append(episode)
    return latest_news

  def getSearchResults(self, query_string):
    operation_name = "SearchPage"
    query_hash = "bed799b6f3105046779adff02a29028c1847782da4b171e9fe1bcc48622a342d"
    variables = {"querystring":query_string}
    json_data = self.__get(operation_name, query_hash, variables=variables)
    if not json_data:
      return None
    results = []
    for search_hit in json_data["search"]:
      item = search_hit["item"]
      content_type = "video"
      if item["__typename"] == "TvShow":
        content_type = "program"
      elif item["__typename"] in ["Episode", "Clip"]:
        content_type = "video"
      else:
        continue
      result = {}
      result["title"] = item["name"]
      if "parent" in item:
        result["title"] = "{parent} - {name}".format(name=item["name"], parent=item["parent"]["name"])
      result["onlyAvailableInSweden"] = item["restrictions"]["onlyAvailableInSweden"]
      result["inappropriateForChildren"] = False
      result["url"] = item["urls"]["svtplay"]
      result["thumbnail"] = self.get_thumbnail_url(item["image"]["id"], item["image"]["changed"]) if "image" in item else ""
      result["type"] = content_type
      info = {}
      info["plot"] = item["longDescription"]
      result["info"] = info
      results.append(result)
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

  def get_thumbnail_url(self, image_id, image_changed):
    return self.__get_image_url(image_id, image_changed, "thumbnail")

  def get_fanart_url(self, image_id, image_changed):
    return self.__get_image_url(image_id, image_changed, "fanart")
  
  def get_poster_url(self, image_id, image_changed):
    return self.__get_image_url(image_id, image_changed, "poster")

  def __get_start_page_selection(self, selection_id):
    operation_name = "StartPage"
    query_hash = "c011159df51539c3604fc09a6ca856af833715d1477d0082afe5a9a871477569"
    json_data = self.__get(operation_name, query_hash=query_hash)
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
      image_id = item["images"]["cleanWide"]["id"]
      image_changed = item["images"]["cleanWide"]["changed"]
      title = "{show} - {episode}".format(show=item["heading"], episode=item["subHeading"])
      item = item["item"]
      video_item = {}
      video_item ["type"] = "video"
      video_item["title"] = title
      video_item["url"] = item["urls"]["svtplay"]
      video_item["parent"] = item["parent"]["id"]
      parent_image_id = item["parent"]["images"]["wide"]["id"]
      parent_image_changed = item["parent"]["images"]["wide"]["changed"]
      video_item["thumbnail"] = self.get_thumbnail_url(image_id, image_changed)
      video_item["onlyAvailableInSweden"] = item["restrictions"]["onlyAvailableInSweden"]
      video_item["inappropriateForChildren"] = False
      video_item["info"] = {
        "plot": item["longDescription"],
        "fanart": self.get_fanart_url(parent_image_id, parent_image_changed)
      }
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
      url = raw_item["urls"]["svtplay"]
      geo_restricted = raw_item["restrictions"]["onlyAvailableInSweden"]
      item = self.__create_item(title, url, geo_restricted)
      items.append(item)
    return sorted(items, key=lambda item: item["title"])

  def __create_item(self, title, url, geo_restricted):
    item = {}
    item["title"] = title
    item["url"] = url
    item["thumbnail"] = ""
    item["type"] = "program"
    item["onlyAvailableInSweden"] = geo_restricted
    if "/video/" in item["url"]:
      item["type"] = "video"
    return item
  
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
    return "{base_url}/{ratio}/{size}/{image_id}/{image_changed}".format(base_url=base_url, ratio=ratio, size=size, image_type=image_type, image_id=image_id, image_changed=image_changed)
    
  def __get(self, operation_name, query_hash="", variables = {}):
    base_url = "https://api.svt.se/contento/graphql"
    param_ua = "svtplaywebb-play-render-prod-client"
    ext = {}
    if query_hash:
        ext["persistedQuery"] = {"version":1,"sha256Hash":query_hash}
    query_params = "ua={ua}&operationName={op}&variables={variables}&extensions={ext}"\
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

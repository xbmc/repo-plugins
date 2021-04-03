# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import json

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib.addon_utils import get_item_media_path
from resources.lib.menu_utils import item_post_treatment


URL_ROOT = 'https://d349g9zuie06uo.cloudfront.net'
# API My5.tv

URL_LIST_CHANNELS = URL_ROOT + '/isl/api/v1/dataservice/SiteMap?device=my5desktop&$format=json'

URL_LIST_ITEMS_OF_CHANNEL = URL_ROOT + "/isl/api/v1/dataservice/Pages('%s')?device=my5desktop&$format=json"
# channelId

URL_PROGRAMS = URL_ROOT + "/isl/api/v1/dataservice/ItemLists('%s')/Items?$expand=Metadata,Images,Ratings,Offers&$select=Slug,CustomId,Id,Title,ShortTitle,ShortDescription,CreatedDate,Images/Id,Images/ImageClass&device=my5desktop&$inlinecount=allpages&$format=json"
# ListItemId

URL_SEASONS = URL_ROOT + "/isl/api/v1/dataservice/Items('%s')/ChildItems?$expand=Metadata,Images,Ratings,Offers&$select=Slug,CustomId,Id,Title,ShortTitle,ShortDescription,ItemType,ParentId,CreatedDate&device=my5desktop&$format=json"
# ProgramId

URL_VIDEOS = URL_ROOT + "/isl/api/v1/dataservice/Items('%s')/ChildItems?$expand=Metadata,Images,Ratings,Offers&$select=Slug,CustomId,Id,Title,ShortDescription,ItemType,ParentId,CreatedDate,Images/Id,Images/ImageClass&device=my5desktop&$format=json"
# SeasonId

URL_VIDEO_DATAS = URL_ROOT + "/isl/api/v1/dataservice/Items('%s')?$expand=Offers,Metadata,Images,Rating,Trailers,Trailers/Images&$select=CustomId,Id,Title&device=my5desktop&$format=json"

URL_IMAGES = URL_ROOT + "/isl/api/v1/dataservice/ResizeImage/$value?ImageId='%s'&EntityId='%s'&EntityType='Item'"
# ImageId, EntityId


@Route.register
def channels(plugin, **kwargs):
    """
    List all france.tv channels
    """
    # (item_id, label, thumb, fanart)
    channels = [
        ('timeline', 'Channel Timeline', 'timeline.png', 'timeline_fanart.jpg'),
        ('plutotvparanormal', 'Pluto TV Paranormal', 'plutotvparanormal.png', 'plutotvparanormal_fanart.jpg'),
        ('plutotvretro', 'Pluto TV Retro', 'plutotvretro.png', 'plutotvretro_fanart.jpg'),
        ('reeltruthcrime', 'Reel Truth Crime', 'reeltruthcrime.png', 'reeltruthcrime_fanart.jpg'),
        ('five', 'Channel 5', 'five.png', 'five_fanart.jpg'),
        ('fiveusa', '5 USA', 'fiveusa.png', 'fiveusa_fanart.jpg'),
        ('fivestar', '5 Star', 'fivestar.png', 'fivestar_fanart.jpg'),
        ('spike', 'Spike', 'spike.png', 'spike_fanart.jpg'),
        ('blaze', 'Blaze', 'blaze.png', 'blaze_fanart.jpg'),
        ('5spike', '5Spike', '5spike.png', '5spike_fanart.jpg'),
        ('5select', '5Select', '5select.png', '5select_fanart.jpg'),
        ('bet', 'Channel BET', 'bet.png', 'bet_fanart.jpg'),
        ('paramount', 'Channel Paramount Network', 'paramount.png', 'paramount_fanart.jpg'),
        ('pbsamerica', 'Channel PBS America', 'pbsamerica.png', 'pbsamerica_fanart.jpg'),
        ('realstories', 'Channel Real Stories', 'realstories.png', 'realstories_fanart.jpg'),
        ('plutotvchristmas', 'Pluto TV Christmas', 'plutotvchristmas.png', 'plutotvchristmas_fanart.jpg'),
        ('togethertv', 'Channel Together TV', 'togethertv.png', 'togethertv_fanart.jpg'),
        ('nextbyhot', 'NEXT by HOT', 'nextbyhot.png', 'nextbyhot_fanart.jpg'),
        ('plutotvdrama', 'PLUTO TV DRAMA', 'plutotvdrama.png', 'plutotvdrama_fanart.jpg'),
        ('plutotvmovies', 'PLUTO TV MOVIES', 'plutotvmovies.png', 'plutotvmovies_fanart.jpg'),
        ('plutotvfood', 'PLUTO TV Food', 'plutotvfood.png', 'plutotvfood_fanart.jpg'),
        ('mastersoffood', 'Masters of Food', 'mastersoffood.png', 'mastersoffood_fanart.jpg'),
        ('wwe', 'WWE', 'wwe.png', 'wwe_fanart.jpg'),
        ('smithsonian', 'Smithsonian', 'smithsonian.png', 'smithsonian_fanart.jpg')
    ]

    for channel_infos in channels:
        item = Listitem()
        item.label = channel_infos[1]
        item.art["thumb"] = get_item_media_path('channels/uk/' + channel_infos[2])
        item.art["fanart"] = get_item_media_path('channels/uk/' + channel_infos[3])
        item.set_callback(list_programs, channel_infos[0])
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    """
    resp = urlquick.get(URL_LIST_CHANNELS)
    json_parser = json.loads(resp.text)

    channel_id = None
    for site_datas in json_parser["value"][0]["ChildPages"]:
        if 'channels' in site_datas["Path"]:
            for channel_datas in site_datas["ChildPages"]:
                if item_id in channel_datas["Path"]:
                    channel_id = channel_datas["Id"]

    if channel_id is not None:
        resp2 = urlquick.get(URL_LIST_ITEMS_OF_CHANNEL % channel_id)
        json_parser2 = json.loads(resp2.text)

        list_items_id = json_parser2["Blocks"][0]["Entries"][0]["ItemListId"]

        resp3 = urlquick.get(URL_PROGRAMS % list_items_id)
        json_parser3 = json.loads(resp3.text)

        for program_datas in json_parser3["value"]:
            program_title = program_datas["Title"]
            program_image = URL_IMAGES % (program_datas["Images"][0]["Id"],
                                          program_datas["Id"])
            program_plot = program_datas["ShortDescription"]
            program_id = program_datas["Id"]

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.info['plot'] = program_plot
            item.set_callback(
                list_seasons, item_id=item_id, program_id=program_id)
            item_post_treatment(item)
            yield item


@Route.register
def list_seasons(plugin, item_id, program_id, **kwargs):

    resp = urlquick.get(URL_SEASONS % program_id)
    json_parser = json.loads(resp.text)

    for season_datas in json_parser["value"]:
        season_title = season_datas["Title"]
        season_plot = season_datas["ShortDescription"]
        season_id = season_datas["Id"]

        item = Listitem()
        item.label = season_title
        item.info['plot'] = season_plot
        item.set_callback(list_videos, item_id=item_id, season_id=season_id)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, season_id, **kwargs):

    resp = urlquick.get(URL_VIDEOS % season_id)
    json_parser = json.loads(resp.text)

    for video_datas in json_parser["value"]:
        video_title = video_datas["Title"]
        video_image = URL_IMAGES % (video_datas["Images"][0]["Id"],
                                    video_datas["Id"])
        video_plot = video_datas["ShortDescription"]
        video_id = video_datas["Id"]

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot
        item.set_callback(
            get_video_url,
            item_id=item_id,
            video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=False)
        yield item


@Resolver.register
def get_video_url(plugin, item_id, video_id, **kwargs):

    # To Uncomment
    # resp = urlquick.get(URL_VIDEO_DATAS % video_id)
    # json_parser = json.loads(resp.text)

    # stream_id = json_parser["CustomId"]
    return False
    # TODO get information of MPD and DRM

    # https://cassie.channel5.com/api/v2/media/my5desktop/C5266140007.json?timestamp=1556276765&auth=T94kIINU2_4yHswfsXfzzyD6IYjCOGr8DvLXQ_q1QkQ
    # StreamId C5266140007
    # Get/Generate timestamp
    # Get/Generate Auth
    # Try to understand the response (maybe cypher) - already test to decode base64

    # Subtitle
    # https://akasubs.akamaized.net/webvtt/C5266140007/C5266140007A.vtt
    # StreamId + StreamId+"A"

    # Stream video
    # https://akadash0.akamaized.net/cenc/C5266140007/C5266140007A/20190423155330/C5266140007A.mpd
    # StreamId + StreamId+"A"
    # Get/Generate the value (20190423155330)

    # DRM Licence
    # https://cassie.channel5.com/api/v2/licences/widevine/75/C5266140007?expiry=1556363165&tag=66616664383363653633396536393661366238333864333036396435306664343639306139303930
    # StreamId
    # Get/Generate Expiry
    # Get/Generate Tag

#!/usr/bin/python
# -*- coding: utf-8 -*-

from resources.lib.Helpers import *
from resources.lib.Directory import Directory
from resources.lib.Episode import Episode

import json
import os

try:
    from urllib.parse import urlencode
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request
    from urllib import urlencode


class RadioThek:
    local_resource_path = "./"
    api_ref = "https://orf.at/app-infos/sound/web/1.0/bundle.json?_o=sound.orf.at"
    api_base = "https://audioapi.orf.at"
    tag_url = "/radiothek/api/tags/%s"
    broadcast_url = "/%s/json/4.0/broadcasts"
    broadcast_detail_url = "/%s/json/4.0/broadcasts/%s"
    search_url = "/radiothek/api/search"
    staple_url = "/radiothek/stapled.json?_o=radiothek.orf.at"
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'
    api_reference = False
    stapled_content = False
    channel_icons = {
        'bgl': 'bgl.png',
        'vbg': 'vbg.png',
        'ooe': 'ooe.png',
        'noe': 'noe.png',
        'ktn': 'ktn.png',
        'sbg': 'sbg.png',
        'stm': 'stm.png',
        'tir': 'tir.png',
        'wie': 'wie.png',
        'fm4': 'fm4.png',
        'oe1': 'oe1.png',
        'oe3': 'oe3.png'
    }
    station_nice = {
        'sbg': 'Radio Salzburg',
        'ooe': 'Radio Oberösterreich',
        'wie': 'Radio Wien',
        'vgrp': 'ORF Volksgruppen',
        'vbg': 'Radio Vorarlberg',
        'oe3': 'Hitradio Ö3',
        'fm4': 'FM4',
        'stm': 'Radio Steiermark',
        'noe': 'Radio Niederösterreich',
        'oe1': 'Ö1',
        'ktn': 'Radio Kärnten',
        'bgl': 'Radio Burgenland',
        'slo': 'Slovenski spored',
        'campus': 'Ö1 Campus',
        'tir': 'Radio Tirol'
    }
    livestream_dd = {
        'oe1': 'https://oe1dd.mdn.ors.at/out/u/oe1dd/manifest.m3u8'
    }
    livestream_qualities_shoutcast = {
        'q1a': 'https://orf-live.ors-shoutcast.at/%s-q1a',
        'q2a': 'https://orf-live.ors-shoutcast.at/%s-q2a',
    }
    livestream_qualities_hls_aac = {
        'q1a': 'https://orf-live-%s.mdn.ors.at/out/u/%s/q1a/manifest.m3u8',
        'q2a': 'https://orf-live-%s.mdn.ors.at/out/u/%s/q2a/manifest.m3u8',
        'q3a': 'https://orf-live-%s.mdn.ors.at/out/u/%s/q3a/manifest.m3u8',
        'q4a': 'https://orf-live-%s.mdn.ors.at/out/u/%s/q4a/manifest.m3u8',
        'qxa': 'https://orf-live-%s.mdn.ors.at/out/u/%s/qxa/manifest.m3u8',
    }

    def __init__(self, local_resource_path, translation, stream_proto, stream_quality):
        self.log("RadioThek API loaded")
        self.local_resource_path = local_resource_path
        self.translation = translation
        # hls or shoutcast
        self.stream_proto = stream_proto
        # shoutcast: q1a, q2a
        # hls: q1a, q2a, q3a, q4a, qxa
        self.stream_quality = stream_quality

        if self.stream_proto == 'shoutcast':
            self.log("Using shoutcast streaming protocol")
            if self.stream_quality not in self.livestream_qualities_shoutcast:
                # Default bad quality settings to highest.
                self.stream_quality = 'q2a'
            self.livestream_recipe = self.livestream_qualities_shoutcast[self.stream_quality]
        else:
            self.log("Using hls streaming protocol")
            if self.stream_quality not in self.livestream_qualities_hls_aac:
                # Default bad quality settings to adaptive.
                self.stream_quality = 'qxa'
            self.livestream_recipe = self.livestream_qualities_hls_aac[self.stream_quality]
        self.log("Using quality setting %s" % self.stream_quality)

    @staticmethod
    def build_stream_url(host_station, loop_stream_id, offset):
        return {'channel': host_station,
                'id': loop_stream_id,
                'shoutcast': 0,
                'player': 'radiothek_v1',
                'referer': 'radiothek.orf.at',
                'offset': offset}

    def get_translation(self, msgid, default=False):
        try:
            if not self.translation(msgid+100) and default:
                return default
            return self.translation(msgid+100)
        except:
            return self.translation(msgid+100).encode('utf-8')

    def get_stream_base(self, station, start, loopStreamIds):
        loopstream_path = ""
        loopstream_offset = 0
        for stream in loopStreamIds:
            if start >= stream['start']:
                loopstream_path = stream['loopStreamId']
                loopstream_offset = start - stream['start']

        api_reference = self.get_api_reference()
        channel_infos = api_reference['stations'][station]
        host = channel_infos['loopstream']['host']
        host_channel = channel_infos['loopstream']['channel']

        return host, host_channel, loopstream_path, loopstream_offset

    def get_stream_url(self, json_item, start=False):
        station = self.get_station_name(json_item, True)
        if start:
            (host, host_channel, loopStreamId, offset) = self.get_stream_base(station, start, json_item['streams'])
        else:
            (host, host_channel, loopStreamId, offset) = self.get_stream_base(station, json_item['start'], json_item['streams'])
        parameters = {'channel': host_channel,
                      'id': loopStreamId,
                      'shoutcast': 0,
                      'player': 'radiothek_v1',
                      'referer': 'radiothek.orf.at',
                      'offset': offset}
        get_params = url_encoder(parameters)
        return "https://%s/?%s" % (host, get_params)

    def format_title(self, json_item, show_station=False, unformatted=False):
        subtitle_max_len = 20
        format_title = ""
        raw_title = ""
        station_name = self.get_station_name(json_item)
        if station_name and show_station:
            format_title += "[%s] " % station_name

        if 'title' in json_item and json_item['title'] is not None:
            raw_title = json_item['title']
            format_title += json_item['title']
        elif 'name' in json_item and json_item['name'] is not None:
            raw_title = json_item['name']
            format_title += json_item['name']
        else:
            format_title = "[ -- %s -- ]" % station_name

        if unformatted:
            return raw_title

        if 'programmTitle' in json_item and json_item['programmTitle'] is not None:
            format_title += " %s" % json_item['programmTitle']
        if 'broadcastDay' in json_item and json_item['broadcastDay'] is not None:
            day = get_date_format(json_item['broadcastDay'])
        else:
            day = ""
        if 'subtitle' in json_item and json_item['subtitle'] is not None:
            subtitle = clean_html(json_item['subtitle'])
        else:
            subtitle = ""

        if subtitle and len(subtitle) < subtitle_max_len:
            format_title += " - %s" % subtitle
        if day:
            format_title += " - %s" % day

        return format_title

    def format_description(self, json_item):
        format_description = ""
        station_name = self.get_station_name(json_item)
        if 'broadcastDay' in json_item and json_item['broadcastDay'] is not None:
            day = get_date_format(json_item['broadcastDay'])
        else:
            if 'published' in json_item and json_item['published'] is not None:
                day = get_time_format(json_item['published'])
            else:
                day = ""
        if 'subtitle' in json_item and json_item['subtitle'] is not None:
            subtitle = clean_html(json_item['subtitle'])
        else:
            subtitle = ""
        if 'description' in json_item and json_item['description'] is not None:
            description = clean_html(json_item['description'], True)
        elif 'text' in json_item and json_item['text'] is not None:
            description = clean_html(json_item['text'], True)
        else:
            description = ""

        broadcasted = ""
        if 'scheduledStart' in json_item and json_item['scheduledStart'] is not None:
            broadcasted = get_time_format(json_item['scheduledStart'], False, True)

        if 'scheduledEnd' in json_item and json_item['scheduledEnd'] is not None:
            broadcasted += " - %s" % get_time_format(json_item['scheduledEnd'], False, True)

        if station_name:
            format_description += "%s: %s\n" % (self.get_translation(30001, 'Broadcasted'), station_name)
        if day or broadcasted:
            format_description += "%s: %s %s\n" % (self.get_translation(30002, 'Broadcasted'), day, broadcasted)
        if subtitle:
            format_description += "%s\n" % subtitle
        if description:
            format_description += "%s\n" % description
        return format_description.strip()

    def get_station_name(self, json_item, raw=False):
        if 'station' in json_item and json_item['station'] is not None:
            if raw:
                return json_item['station']
            if json_item['station'] in self.station_nice:
                try:
                    return self.station_nice[str(json_item['station'])].decode('utf-8')
                except:
                    return self.station_nice[str(json_item['station'])]
            else:
                return json_item['station']
        if 'group' in json_item and json_item['group'] is not None:
            return json_item['group']
        return ""

    def get_directory_image(self, json_item, image_type):
        try:
            station = self.get_station_name(json_item, True)
            if station and station in self.channel_icons:
                if image_type == 'logo':
                    return os.path.join(self.local_resource_path, self.channel_icons[station])

            if 'image' in json_item and json_item["image"] and len(json_item['image']) and 'versions' in json_item['image']:
                image_arr = json_item['image']['versions']
                if image_type == 'thumbnail':
                    return get_images(image_arr, True)
                elif image_type == 'backdrop':
                    images = get_images(image_arr)
                    if images and len(images):
                        return images[0]

            if 'image' in json_item:
                if image_type == 'thumbnail':
                    return json_item['image']

            if 'images' in json_item and json_item["images"] and len(json_item['images']):
                image_arr = json_item['images'][0]['versions']
                if image_type == 'thumbnail':
                    return get_images(image_arr, True)
                elif image_type == 'backdrop':
                    images = get_images(image_arr)
                    if images and len(images):
                        return images[0]
        except:
            self.log("Error loading image %s" % image_type)
        return ""

    @staticmethod
    def get_files(json_item):
        files = []
        if 'enclosures' in json_item:
            for audio_file in json_item['enclosures']:
                files.append(audio_file['url'])
        return files

    @staticmethod
    def get_link(json_item):
        if 'href' in json_item and json_item['href'] is not None:
            return json_item['href']
        elif 'target' in json_item and json_item['target']:
            return json_item['target']

    def get_tag_link(self, json_item):
        rel_link = self.tag_url % json_item['key']
        return "%s%s" % (self.api_base, rel_link)

    def get_day_selection(self, station):
        url = self.broadcast_url % station
        self.log("Loading url %s" % url)
        try:
            days_json = self.request_url(url)
            list_items = []
            for day in days_json:
                if 'broadcasts' in day and day['broadcasts'] and len(day['broadcasts']):
                    station_name = self.get_station_name(day['broadcasts'][0])
                    directory_title = "%s - %s" % (station_name, get_date_format(day['day']))
                    directory_description = ""
                    thumbnail = ""
                    backdrop = ""
                    logo = os.path.join(self.local_resource_path, self.channel_icons[station])
                    link = self.broadcast_detail_url % (station, day['day'])
                    day_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                    list_items.append(day_directory)
            return list_items
        except:
            self.log("This station has no 'missed a show?' feature.")

    def get_day_selection_details(self, url):
        show_json = self.request_url(url)
        list_items = []
        for show in show_json:
            station = self.get_station_name(show)
            title = show['title']
            time_start = "%s | " % get_time_format(show['start'], False, True)
            directory_title = "%s%s" % (time_start, title)
            directory_description = self.format_description(show)
            thumbnail = self.get_directory_image(show, 'thumbnail')
            backdrop = self.get_directory_image(show, 'backdrop')
            logo = self.get_directory_image(show, 'logo')
            link = self.get_link(show)

            broadcast_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
            list_items.append(broadcast_directory)
        return list_items

    def get_tags(self):
        staple = self.get_stapled()
        list_items = []
        if 'tags' in staple:
            for tag_item in staple['tags']:
                station = self.get_station_name(tag_item)
                directory_title = self.format_title(tag_item)
                directory_description = self.format_description(tag_item)
                thumbnail = self.get_directory_image(tag_item, 'thumbnail')
                backdrop = self.get_directory_image(tag_item, 'backdrop')
                logo = self.get_directory_image(tag_item, 'logo')
                link = self.get_tag_link(tag_item)

                tag_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                list_items.append(tag_directory)

        return list_items

    def get_tag_details(self, url):
        items = []
        self.log("Getting Tag Details from %s" % url)
        tag_json = self.request_url(url, True)
        if tag_json['items']:
            for tag_item in tag_json['items']:
                station = self.get_station_name(tag_item)
                directory_title = self.format_title(tag_item)
                directory_description = self.format_description(tag_item)
                thumbnail = self.get_directory_image(tag_item, 'thumbnail')
                backdrop = self.get_directory_image(tag_item, 'backdrop')
                logo = self.get_directory_image(tag_item, 'logo')
                link = self.get_link(tag_item)
                tag_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                items.append(tag_directory)
        return items

    def get_highlights(self):
        staple = self.get_stapled()
        list_items = []
        if 'stations' in staple:
            for station in staple['stations']:
                if 'highlights' in staple['stations'][station]['data']:
                    broadcast_items = staple['stations'][station]['data']['highlights']
                    for broadcast_item in broadcast_items:
                        broadcast_item['station'] = station
                        directory_title = self.format_title(broadcast_item)
                        directory_description = self.format_description(broadcast_item)
                        thumbnail = self.get_directory_image(broadcast_item, 'thumbnail')
                        backdrop = self.get_directory_image(broadcast_item, 'backdrop')
                        logo = self.get_directory_image(broadcast_item, 'logo')
                        link = self.get_link(broadcast_item)
                        broadcast_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                        list_items.append(broadcast_directory)
        return list_items

    def get_archive(self):
        staple = self.get_stapled()
        list_items = []
        if 'archive' in staple:
            for archive_item_container in staple['archive']:
                archive_item = archive_item_container['data']

                station = self.get_station_name(archive_item)
                directory_title = self.format_title(archive_item)
                directory_description = self.format_description(archive_item)
                thumbnail = self.get_directory_image(archive_item, 'thumbnail')
                backdrop = self.get_directory_image(archive_item, 'backdrop')
                logo = self.get_directory_image(archive_item, 'logo')
                link = self.get_link(archive_item_container)

                archive_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                list_items.append(archive_directory)
        return list_items

    def get_podcasts(self):
        staple = self.get_stapled()
        list_items = []
        if 'podcasts' in staple:
            for station in staple['podcasts']:
                for podcast_item_container in staple['podcasts'][station]:
                    podcast_item = podcast_item_container['data']
                    podcast_item['station'] = station

                    station = self.get_station_name(podcast_item)
                    directory_title = self.format_title(podcast_item)
                    directory_description = self.format_description(podcast_item)
                    thumbnail = self.get_directory_image(podcast_item, 'thumbnail')
                    backdrop = self.get_directory_image(podcast_item, 'backdrop')
                    logo = self.get_directory_image(podcast_item, 'logo')
                    link = self.get_link(podcast_item_container)

                    podcast_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                    list_items.append(podcast_directory)
        return list_items

    def get_podcast_details(self, url):
        episodes = []
        self.log("Getting Podcast Details from %s" % url)
        detail_json = self.request_url(url, True)
        item_type = 'Podcast'
        if 'data' in detail_json and 'episodes' in detail_json['data']:
            data_json = detail_json['data']
            show_title = self.format_title(data_json, True, True)
            for episode_json in data_json['episodes']:
                cms_id = detail_json['slug']
                station = self.get_station_name(detail_json)
                raw_episode_title = self.format_title(episode_json, True, True)
                episode_title = self.format_title(episode_json)
                if raw_episode_title != show_title:
                    episode_title = "%s - %s" % (show_title, episode_title)
                episode_description = self.format_description(episode_json)
                thumbnail = self.get_directory_image(data_json, 'thumbnail')
                backdrop = self.get_directory_image(data_json, 'backdrop')
                logo = self.get_directory_image(detail_json, 'logo')
                files = self.get_files(episode_json)
                meta = self.get_broadcast_meta(episode_json)
                episode = Episode(cms_id, episode_title, episode_description, files, item_type, thumbnail, backdrop, station, logo, 0, meta)
                episodes.append(episode)
        return episodes

    def get_broadcast_details(self, url):
        list_items = []
        broadcast_details = self.request_url(url, True)
        if broadcast_details and 'entity' in broadcast_details and broadcast_details['entity'] == 'Broadcast':
            cms_id = broadcast_details['id']
            item_type = broadcast_details['entity']
            station = self.get_station_name(broadcast_details)
            directory_title = self.format_title(broadcast_details, True, True)
            directory_description = self.format_description(broadcast_details)
            thumbnail = self.get_directory_image(broadcast_details, 'thumbnail')
            backdrop = self.get_directory_image(broadcast_details, 'backdrop')
            logo = self.get_directory_image(broadcast_details, 'logo')
            stream_url = self.get_stream_url(broadcast_details)
            meta = self.get_broadcast_meta(broadcast_details)
            broadcast_episode = Episode(cms_id, directory_title, directory_description, [stream_url], item_type, thumbnail, backdrop, station, logo, 0, meta)
            list_items.append(broadcast_episode)
            if 'items' in broadcast_details:
                for broadcast_detail_item in broadcast_details['items']:
                    broadcast_episode = self.get_broadcast_items(broadcast_detail_item, broadcast_details)
                    list_items.append(broadcast_episode)
        return list_items

    def get_broadcast_items(self, broadcast_json, parent_broadcast_json):
        if broadcast_json and 'entity' in broadcast_json and broadcast_json['entity'] == 'BroadcastItem':
            hidden = 0
            cms_id = broadcast_json['id']
            item_type = broadcast_json['entity']
            station = self.get_station_name(parent_broadcast_json)
            parent_directory_title = self.format_title(parent_broadcast_json, True, True)
            directory_title = "%s - %s" % (parent_directory_title, self.format_title(broadcast_json, True, True))
            directory_description = self.format_description(broadcast_json)
            thumbnail = self.get_directory_image(broadcast_json, 'thumbnail')
            if not thumbnail:
                thumbnail = self.get_directory_image(parent_broadcast_json, 'thumbnail')
            backdrop = self.get_directory_image(broadcast_json, 'backdrop')
            if not backdrop:
                backdrop = self.get_directory_image(parent_broadcast_json, 'backdrop')
            logo = self.get_directory_image(parent_broadcast_json, 'logo')
            if not logo:
                logo = self.get_directory_image(parent_broadcast_json, 'logo')

            stream_url = self.get_stream_url(parent_broadcast_json, broadcast_json['start'])
            meta = self.get_broadcast_meta(broadcast_json)
            if not self.format_title(broadcast_json, True, True):
                hidden = 1
            return Episode(cms_id, directory_title, directory_description, [stream_url], item_type, thumbnail, backdrop, station, logo, hidden, meta)

    @staticmethod
    def get_broadcast_meta(broadcast_json):
        meta = {}
        if 'interpreter' in broadcast_json:
            meta['artist'] = broadcast_json['interpreter']
            meta['trackname'] = broadcast_json['title']
        if 'duration' in broadcast_json:
            meta['duration'] = broadcast_json['duration']
        elif 'start' in broadcast_json and 'end' in broadcast_json:
            meta['duration'] = broadcast_json['end'] - broadcast_json['start']
        if 'start' in broadcast_json:
            meta['start'] = get_time_format(broadcast_json['start'], False, True)
        if 'end' in broadcast_json:
            meta['end'] = get_time_format(broadcast_json['end'], False, True)
        return meta

    def get_broadcast(self):
        staple = self.get_stapled()
        list_items = []
        if 'stations' in staple:
            for station in staple['stations']:
                if 'broadcast' in staple['stations'][station]['data']:
                    broadcast_item = staple['stations'][station]['data']['broadcast']

                    station = self.get_station_name(broadcast_item)
                    directory_title = self.format_title(broadcast_item)
                    directory_description = self.format_description(broadcast_item)
                    thumbnail = self.get_directory_image(broadcast_item, 'thumbnail')
                    backdrop = self.get_directory_image(broadcast_item, 'backdrop')
                    logo = self.get_directory_image(broadcast_item, 'logo')
                    link = self.get_link(broadcast_item)

                    broadcast_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                    list_items.append(broadcast_directory)
        return list_items

    def get_livestream(self):
        self.get_api_reference()
        list_items = []

        for station in self.api_reference['stations']:
            item = self.api_reference['stations'][station]
            title = item['title']
            description = "%s Livestream" % title

            if station in self.livestream_dd:
                link = self.livestream_dd[station]
                thumbnail = ""
                backdrop = ""
                logo = self.get_directory_image({'station': station}, 'logo')
                if link:
                    episode = Episode(station, "%s (5.1 DD)" % title, description, [link], 'Livestream', thumbnail, backdrop, station,
                                      logo)
                    list_items.append(episode)

            if 'livestream' in item:
                link = self.build_livestream_url(station)
                thumbnail = ""
                backdrop = ""
                logo = self.get_directory_image({'station': station}, 'logo')
                if link:
                    episode = Episode(station, title, description, [link], 'Livestream', thumbnail, backdrop, station, logo)
                    list_items.append(episode)
        return list_items

    def build_livestream_url(self, channel):
        if self.stream_proto == 'hls':
            return self.livestream_recipe % (channel, channel)
        else:
            return self.livestream_recipe % channel

    def get_search(self, query):
        list_items = []
        parameters = {
            'q': query,
            'offset': 0,
            'limit': 20,
            '_o': 'radiothek.orf.at'
        }
        get_parameters = url_encoder(parameters)
        url = "%s?%s" % (self.search_url, get_parameters)
        search_json = self.request_url(url, False)
        if search_json['length'] > 0 and search_json['total'] > 0:
            for search_item_container in search_json['hits']:
                search_item = search_item_container['data']
                station = self.get_station_name(search_item)
                directory_title = self.format_title(search_item)
                directory_description = self.format_description(search_item)
                thumbnail = self.get_directory_image(search_item, 'thumbnail')
                backdrop = self.get_directory_image(search_item, 'backdrop')
                logo = self.get_directory_image(search_item, 'logo')
                link = self.get_link(search_item)
                search_directory = Directory(directory_title, directory_description, link, thumbnail, backdrop, station, logo)
                list_items.append(search_directory)
        return list_items

    def get_api_reference(self):
        if not self.api_reference:
            content = self.request_url(self.api_ref, True, False)
            self.api_reference = json.loads(content)
        return self.api_reference

    def get_stapled(self):
        if not self.stapled_content:
            self.stapled_content = self.request_url(self.staple_url)
        return self.stapled_content

    def request_url(self, url, absolute_url=False, parse_json=True):
        if not absolute_url:
            request_url = "%s%s" % (self.api_base, url)
        else:
            request_url = url
        self.log("Loading from %s" % request_url)
        request = urlopen(Request(request_url, headers={'User-Agent': self.user_agent}))
        request_data = request.read()
        if parse_json:
            return json.loads(request_data)
        else:
            return request_data

    @staticmethod
    def log(msg):
        try:
            radiothek_log(msg)
        except Exception as e:
            radiothek_log(msg.encode('utf-8'))

#!/usr/bin/env python3
# coding: utf-8

__author__ = 'stsmith'

# sd_json.py: Python wrapper and xmltv generator for Schedules Direct JSON API

# Copyright © 2019 Steven T. Smith <steve dot t dot smith at gmail dot com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Schedules Direct API documentation:
# https://github.com/SchedulesDirect/JSON-Service/wiki/API-20141201

# XMLTV documentation:
# https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd

__version__ = '1.0'

__all__ = ['SD_JSON']

import datetime as dt
import hashlib as hl
import json
import math
import re
import string
import warnings as warn
import xml.etree.ElementTree as et
from xml.dom import minidom

import requests
from codequick import Script
from resources.lib.py_utils import datetime_strptime


class SD_JSON:
    """
    Schedules Direct JASON API for http://schedulesdirect.org.

    Reference: https://github.com/SchedulesDirect/JSON-Service/wiki/API-20141201
    """

    def __init__(self,
                 username,
                 password,
                 xmltv_filepath,
                 lineup,
                 date,
                 xmltv_ids,
                 verboseMap=True):
        self.sd_url = "https://json.schedulesdirect.org/20141201"
        self.username = username
        self.password_sha1 = hl.sha1(password.encode()).hexdigest()
        self.lineup = lineup
        self.date = date
        self.xmltv_ids = xmltv_ids
        self.headers = {"Content-type": "application/json", "Accept": "text/plain,deflate,gzip"}
        self.verboseMap = verboseMap
        self.xmltv_filepath = xmltv_filepath

    # def parseArgs(self,parseArgs_flag):
    #     parser = ap.ArgumentParser()
    #     parser.add_argument('-U', '--sd-url', help="Schedules Direct URL (no trailing '/')", type=str, default=None)
    #     parser.add_argument('-u', '--username', help="Schedules Direct username", type=str, default=None)
    #     parser.add_argument('-p', '--password-sha1', help="Schedules Direct SHA1-hashed password", type=str, default=None)
    #     parser.add_argument('-c', '--country', help="3-character country code", type=str, default=None)
    #     parser.add_argument('-z', '--postalcode', help="Postal Code", type=str, default=None)
    #     parser.add_argument('-l', '--lineup', help="Lineup Code", type=str, default=None)
    #     parser.add_argument('-H', '--headers', help="HTTP Headers", type=str, default=None)
    #     parser.add_argument('-M', '--verboseMap', help="verboseMap off", action='store_false')
    #     parser.add_argument('-T', '--timedelta-days', help="Number of days retrieved", type=int, default=self.timedelta_days)
    #     parser.add_argument('-q', '--quiet', help="Quiet on", action='store_true')
    #     parser.add_argument('-v', '--verbose', help="Verbose on", action='store_true')
    #     parser.add_argument('-g', '--debug', help="Debug on", action='store_true')
    #     parser.add_argument('-A', '--api-call', help="Schedules Direct API Call", type=str, default=None)
    #     parser.add_argument('-S', '--service', help="Schedules Direct Service name", type=str, default=None)
    #     parser.add_argument('-X', '--xmltv-file', help="XMLtv file name", type=str, default=None)
    #     args = []
    #     if parseArgs_flag:
    #         args = parser.parse_args()
    #         for k in args.__dict__:
    #             if getattr(args, k) is not None: setattr(self, k, getattr(args, k))
    #         if "headers" in args.__dict__:  # load the headers string as json
    #             if getattr(args, "headers") is not None: setattr(self, "headers", json.loads(getattr(args, "headers")))
    #     return args

    def api_token(self):
        sd_token_request = {"username": self.username, "password": self.password_sha1}
        resp = requests.post("{}/token".format(self.sd_url), data=json.dumps(sd_token_request))
        resp_json = None
        try:
            resp.raise_for_status()
            # assert resp.status_code < 400, f'API token response status code {resp.status_code}.'
            resp_json = resp.json()
        except Exception as e:
            raise Exception("Failed to get user token: {}".format(e))
        if "token" not in resp_json:
            raise Exception("Token not found in {}".format(resp_json))
        self.token = resp_json['token']
        self.api_token_data = sd_token_request
        self.api_token_json = resp_json
        return

    def api_channel_mapping(self):
        """StationID / channel mapping for a lineup."""
        @self.sd_verbose_map
        @self.sd_api_token_required
        def sd_api_channel_mapping():
            return requests.get('{}/lineups/{}'.format(self.sd_url, self.lineup), headers=self.headers)
        Script.log('[sd_json] Get stationID/channel mapping with lineup {}'.format(self.lineup), lvl=Script.DEBUG)
        full_api_channel_mapping_json = sd_api_channel_mapping()
        channels_map = []
        for channel_map in full_api_channel_mapping_json['map']:
            channel = 'I{}.json.schedulesdirect.org'.format(channel_map["stationID"])
            if channel in self.xmltv_ids:
                channels_map.append(channel_map)
        stations = []
        for station in full_api_channel_mapping_json['stations']:
            channel = 'I{}.json.schedulesdirect.org'.format(station["stationID"])
            if channel in self.xmltv_ids:
                stations.append(station)
        self.api_channel_mapping_json = {"map": channels_map, "stations": stations}
        return

    def api_schedules(self, max_stationIDs=5000):
        """Schedules API takes a POST of:
            [ {"stationID": "20454", "date": [ "2015-03-13", "2015-03-17" ]}, …]

        The schedules for the current date to `timedelta_days` is retrieved.
        date in %Y-%m-%d format
        """
        @self.sd_api_token_required
        def sd_api_schedules():
            return requests.post('{}/schedules'.format(self.sd_url), data=json.dumps(sd_schedule_query), headers=self.headers)
        dates = {"date": [self.date]}
        self.api_channel_mapping()
        idx = 0  # block indexing through stationID's
        sd_schedule_data = [dict(stationID=sid["stationID"], **dates) for sid in self.api_channel_mapping_json["map"]]
        resp_json = []
        while True:
            sd_schedule_query = sd_schedule_data[idx:idx + max_stationIDs]
            if len(sd_schedule_query) == 0:
                break  # no more stations
            resp_json += sd_api_schedules()  # API returns a list of dicts
            idx += max_stationIDs
        Script.log('[sd_json] Schedules retrieved: {}'.format(len(resp_json)), lvl=Script.DEBUG)
        self.api_schedules_data = sd_schedule_data
        self.api_schedules_json = resp_json
        return

    def api_programs(self, max_programIDs=500):
        """Programs API takes a POST of: ["EP000000060003", "EP000000510142"]"""
        @self.sd_api_token_required
        def sd_api_programs():
            return requests.post('{}/programs'.format((self.sd_url)), data=json.dumps(sd_pgm_query), headers=self.headers)
        self.api_schedules()
        sd_programs_data = list(set([p["programID"] for s in self.api_schedules_json if "programs" in s for p in s["programs"] if p["md5"] not in {}]))

        Script.log('[sd_json] Programs requested: {}'.format(len(sd_programs_data)), lvl=Script.DEBUG)
        idx = 0  # block indexing through programID's
        resp_json = []
        while True:
            sd_pgm_query = sd_programs_data[idx:idx + max_programIDs]
            if len(sd_pgm_query) == 0:
                break  # no more programs
            resp_json += sd_api_programs()  # API returns a list of dicts
            idx += max_programIDs
        Script.log('[sd_json] Programs retrieved: {}'.format(len(resp_json)), lvl=Script.DEBUG)
        self.api_programs_data = sd_programs_data
        self.api_programs_json = resp_json
        return

    def get_xmltv(self):
        """
        Write the xmltv.xml EPG file.

        References:
            https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd
            https://github.com/kgroeneveld/tv_grab_sd_json/blob/master/tv_grab_sd_json
        """
        root = et.Element(
            "tv",
            attrib={
                "source-info-name": "Schedules Direct",
                "generator-info-name": "sd_json.py",
                "generator-info-url": "https://github.com/essandess/sd-py"}
        )

        # get channel mapping, schedule, and programs
        self.api_programs()

        # channels
        stationID_map_dict = {
            sid["stationID"]: {"id": 'I{}.json.schedulesdirect.org'.format(sid["stationID"]),
                               "channel": str(int(sid["channel"]))} for k, sid in enumerate(self.api_channel_mapping_json["map"])}
        for k, stn in enumerate(self.api_channel_mapping_json["stations"]):
            channel = et.SubElement(root, "channel", attrib={"id": stationID_map_dict[stn["stationID"]]["id"]})
            # "mythtv seems to assume that the first three display-name elements are
            # name, callsign and channel number. We follow that scheme here."
            et.SubElement(channel, "display-name").text = '{} {}'.format((stationID_map_dict[stn["stationID"]]["channel"]), (stn["name"]))
            et.SubElement(channel, "display-name").text = stn["callsign"]
            et.SubElement(channel, "display-name").text = stationID_map_dict[stn["stationID"]]["channel"]
            # if "logo" in stn:
            #     icon = et.SubElement(
            #         channel,
            #         "icon",
            #         attrib={"src": stn["logo"]["URL"], "width": str(stn["logo"]["width"]), "height": str(stn["logo"]["height"])}
            #     )

        # programs
        stationID_stn_dict = {
            stn["stationID"]: stn for k, stn in enumerate(self.api_channel_mapping_json["stations"])}
        programID_dict = {pid["programID"]: k for k, pid in enumerate(self.api_programs_json)}
        pgmid_counts = {k: 0 for k in programID_dict}
        pgm_prec = math.ceil(math.log10(max(1, len(self.api_programs_json))))
        for sid in (sidp for sidp in self.api_schedules_json if "programs" in sidp):
            for sid_pgm in sid["programs"]:
                if sid_pgm["programID"] not in programID_dict:
                    warn.warn("No program data for hash '{}' or program id '{}'.".format(sid_pgm["md5"], sid_pgm["programID"]))
                    continue
                attrib_lang = {"lang": stationID_stn_dict[sid["stationID"]]["broadcastLanguage"][0]} \
                    if "broadcastLanguage" in stationID_stn_dict[sid["stationID"]] \
                    else None
                # programme

                # Get the naive datetime object in UTC
                start = datetime_strptime(sid_pgm["airDateTime"], "%Y-%m-%dT%H:%M:%S%z")
                stop = start + dt.timedelta(seconds=sid_pgm["duration"])
                programme_attrib = dict(
                    start=start.strftime("%Y%m%d%H%M%S"),
                    stop=stop.strftime("%Y%m%d%H%M%S"),
                    channel=stationID_map_dict[sid["stationID"]]["id"])
                pgm = self.api_programs_json[programID_dict[sid_pgm["programID"]]]
                programme = et.SubElement(root, "programme", attrib=programme_attrib)
                # title
                if "titles" in pgm:
                    for ttl in pgm["titles"]:
                        if "title120" in ttl:
                            et.SubElement(programme, "title", attrib=attrib_lang).text = ttl["title120"]
                # sub-title
                if "episodeTitle150" in pgm:
                    et.SubElement(programme, "sub-title", attrib=attrib_lang).text = pgm["episodeTitle150"]
                # desc
                if "descriptions" in pgm:
                    attrib_desc_lang = attrib_lang
                    if "description1000" in pgm["descriptions"]:
                        if "descriptionLanguage" in pgm["descriptions"]["description1000"][0]:
                            attrib_desc_lang = {"lang": pgm["descriptions"]["description1000"][0]["descriptionLanguage"]}
                        et.SubElement(programme, "desc", attrib=attrib_desc_lang).text = pgm["descriptions"]["description1000"][0]["description"]
                    elif "description100" in pgm["descriptions"]:
                        if "descriptionLanguage" in pgm["descriptions"]["description100"][0]:
                            attrib_desc_lang = {"lang": pgm["descriptions"]["description100"][0]["descriptionLanguage"]}
                        et.SubElement(programme, "desc", attrib=attrib_desc_lang).text = pgm["descriptions"]["description100"][0]["description"]
                # date
                if "movie" in pgm and "year" in pgm["movie"]:
                    et.SubElement(programme, "date").text = pgm["movie"]["year"]
                elif "originalAirDate" in pgm:
                    et.SubElement(programme, "date").text = datetime_strptime(pgm["originalAirDate"], "%Y-%m-%d").strftime("%Y%m%d")
                # length
                if "duration" in pgm:
                    et.SubElement(programme, "length", attrib={"units": "seconds"}).text = str(pgm["duration"])
                elif "movie" in pgm and "duration" in pgm["movie"]:
                    et.SubElement(programme, "length", attrib={"units": "seconds"}).text = str(pgm["movie"]["duration"])
                # category
                if "genres" in pgm:
                    for gnr in pgm["genres"]:
                        et.SubElement(programme, "category", attrib=attrib_lang).text = gnr
                # episode-num
                if "metadata" in pgm and "Gracenote" in pgm["metadata"][0]:
                    et.SubElement(programme, "episode-num", attrib={"system": "xmltv_ns"}).text = self.create_episode_num(pgm["metadata"][0]["Gracenote"])
                et.SubElement(programme, "episode-num", attrib={"system": "dd_progid"}).text = '{}.{:0{}d}'.format(pgm["programID"], pgmid_counts[pgm["programID"]], pgm_prec)
                pgmid_counts[pgm["programID"]] += 1
                # previously-shown
                if "originalAirDate" in pgm:
                    et.SubElement(programme, "previously-shown", attrib={"start": datetime_strptime(pgm["originalAirDate"], "%Y-%m-%d").strftime("%Y%m%d%H%M%S")})
                # rating
                if "contentRating" in pgm:
                    for rtn in pgm["contentRating"]:
                        rating = et.SubElement(programme, "rating", attrib={"system": rtn["body"]})
                        et.SubElement(rating, "value").text = rtn["code"]
                # credits
                xmltv_roles = ["director", "actor", "writer", "adapter", "producer", "composer", "editor", "presenter", "commentator", "guest"]

                def role_to_xml(role):
                    role_normalized = re.sub(r" ", "-", role.lower().translate(str.maketrans('', '', string.punctuation)))
                    role_xml = None
                    for x in xmltv_roles:
                        if bool(re.match(x, role_normalized, re.IGNORECASE)):
                            role_xml = x
                            break
                    return role_xml
                credits = None
                if "cast" in pgm:
                    if credits is None:
                        credits = et.SubElement(programme, "credits")
                    for cst in pgm["cast"]:
                        role_xml = role_to_xml(cst["role"])
                        if role_xml is not None:
                            attrib_role = {}
                            if role_xml == "actor" and "characterName" in cst:
                                attrib_role = {"role": cst["characterName"]}
                            et.SubElement(credits, role_xml, attrib=attrib_role).text = cst["name"]
                if "crew" in pgm:
                    if credits is None:
                        credits = et.SubElement(programme, "credits")
                    for crw in pgm["crew"]:
                        role_xml = role_to_xml(crw["role"])
                        if role_xml is not None:
                            et.SubElement(credits, role_xml).text = crw["name"]

                # video
                def re_any(pattern, list_of_str, *args, **kwargs):
                    return any([bool(re.match(pattern, x, *args, **kwargs)) for x in list_of_str])
                if "videoProperties" in pgm and re_any("HDTV", pgm["videoProperties"], re.IGNORECASE):
                    video = et.SubElement(programme, "video")
                    et.SubElement(video, "quality").text = "HDTV"
                # audio
                if "audioProperties" in pgm:
                    if re_any("mono", pgm["audioProperties"], re.IGNORECASE):
                        audio = et.SubElement(programme, "audio")
                        et.SubElement(audio, "stereo").text = "mono"
                    elif re_any("stereo", pgm["audioProperties"], re.IGNORECASE):
                        audio = et.SubElement(programme, "audio")
                        et.SubElement(audio, "stereo").text = "stereo"
                    elif re_any("DD", pgm["audioProperties"], re.IGNORECASE):
                        audio = et.SubElement(programme, "audio")
                        et.SubElement(audio, "stereo").text = "dolby digital"
                # subtitles
                if "audioProperties" in pgm and re_any("cc", pgm["audioProperties"], re.IGNORECASE):
                    et.SubElement(programme, "subtitles", attrib={"type": "teletext"})
                # url
                if "officialURL" in pgm:
                    et.SubElement(programme, "url").text = pgm["officialURL"]
                # premiere
                if "isPremiereOrFinale" in pgm and bool(re.match("premiere", pgm["isPremiereOrFinale"], re.IGNORECASE)):
                    et.SubElement(programme, "premiere").text = pgm["isPremiereOrFinale"]
                # new
                if "new" in pgm:
                    et.SubElement(programme, "new")
                # star-rating
                if "movie" in pgm and "qualityRating" in pgm["movie"]:
                    for qrt in pgm["movie"]["qualityRating"]:
                        star_rating = et.SubElement(programme, "star-rating")
                        et.SubElement(star_rating, "value").text = '{}/{}'.format(qrt["rating"], qrt["maxRating"])

        # (re-)write the XML file
        rough_string = et.tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        with open(self.xmltv_filepath, 'wb') as f:
            f.write(reparsed.toprettyxml(indent="  ").encode('utf-8'))

        # print(et.tostring(root, pretty_print=True, xml_declaration=True, encoding="ISO-8859-1", doctype='<!DOCTYPE tv SYSTEM "xmltv.dtd">').decode())

    def create_episode_num(self, gracenote):
        """Reference: https://github.com/XMLTV/xmltv/blob/master/xmltv.dtd"""
        episode_num = ""
        if "season" in gracenote:
            episode_num += str(gracenote["season"] - 1)
        if "totalSeasons" in gracenote:
            episode_num += "/" + str(gracenote["totalSeasons"])
        episode_num += "."
        if "episode" in gracenote:
            episode_num += str(gracenote["episode"] - 1)
        if "totalEpisodes" in gracenote:
            episode_num += "/" + str(gracenote["totalEpisodes"])
        episode_num += "."
        if "part" in gracenote:
            episode_num += str(gracenote["part"] - 1)
        if "totalParts" in gracenote:
            episode_num += "/" + str(gracenote["totalParts"])
        return episode_num

    # handle Schedules Direct API calls and HTTP-Headers with decorators
    # Example syntax:
    # @sd_api_token_required
    # def sd_api_block():
    #     return requests.get(<The API call>, headers=headers)
    # sd_api_block()

    def sd_api_no_token(self, func):
        """API call with error handling. Note that the JSON is returned, not the response."""
        def call_func(*args, **kwargs):
            resp = func(*args, **kwargs)
            resp.raise_for_status()
            # assert resp.status_code < 400, f'API response status code {resp.status_code}.'
            return resp.json()
        return call_func

    def sd_api_token_required(self, func):
        """Set the HTTP Header "token" to the API token, call the API, then remove the header."""
        def call_func(*args, **kwargs):
            if not hasattr(self, "token"):
                self.api_token()
            self.headers["token"] = self.token

            @self.sd_api_no_token
            def sd_api_call():
                return func(*args, **kwargs)
            resp_json = sd_api_call()
            del self.headers["token"]
            return resp_json
        return call_func

    def sd_verbose_map(self, func):
        """Set the HTTP Header "verboseMap" to "true", per API documentation."""
        def call_func(*args, **kwargs):
            if self.verboseMap:
                self.headers["verboseMap"] = "true"
            resp_json = func(*args, **kwargs)
            self.headers.pop("verboseMap", None)  # silently delete "verboseMap"
            return resp_json
        return call_func

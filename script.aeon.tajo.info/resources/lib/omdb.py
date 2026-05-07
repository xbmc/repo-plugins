#!/usr/bin/python
# coding: utf-8

########################

import json
import sys
import requests
import xml.etree.ElementTree as ET

from resources.lib.helper import *

########################

OMDB_API_KEY = ADDON.getSettingString('omdb_api_key')

########################

def omdb_api(imdbnumber=None,title=None,year=None,content_type=None):
    if imdbnumber:
        url = 'http://www.omdbapi.com/?apikey=%s&i=%s&plot=short&r=xml&tomatoes=true' % (OMDB_API_KEY, imdbnumber)

    elif title and year and content_type:
        # urllib has issues with some asian letters
        try:
            title = urllib.quote(title)
        except KeyError:
            return

        url = 'http://www.omdbapi.com/?apikey=%s&t=%s&year=%s&plot=short&r=xml&tomatoes=true' % (OMDB_API_KEY, title, year)

    else:
        return

    omdb = get_cache(url)
    if omdb:
        return omdb

    elif OMDB_API_KEY:
        omdb = {}

        for i in range(1,4): # loop if heavy server load
            try:
                request = requests.get(url, timeout=5)

                if not request.ok:
                    raise Exception(str(request.status_code))

                result = request.text

                tree = ET.ElementTree(ET.fromstring(result))
                root = tree.getroot()

                for child in root:
                    # imdb ratings
                    omdb['imdbRating'] = child.get('imdbRating', '').replace('N/A', '')
                    omdb['imdbVotes'] = child.get('imdbVotes', '0').replace('N/A', '0').replace(',', '')

                    # regular rotten rating
                    omdb['tomatometerallcritics'] = child.get('tomatoMeter', '').replace('N/A', '')
                    omdb['tomatometerallcritics_avg'] = child.get('tomatoRating', '').replace('N/A', '')
                    omdb['tomatometerallcritics_votes'] = child.get('tomatoReviews', '0').replace('N/A', '0').replace(',', '')

                    # user rotten rating
                    omdb['tomatometerallaudience'] = child.get('tomatoUserMeter', '').replace('N/A', '')
                    omdb['tomatometerallaudience_avg'] = child.get('tomatoUserRating', '').replace('N/A', '')
                    omdb['tomatometerallaudience_votes'] = child.get('tomatoUserReviews', '0').replace('N/A', '0').replace(',', '')

                    # metacritic
                    omdb['metacritic'] = child.get('metascore', '').replace('N/A', '')

                    # other
                    omdb['awards'] = child.get('awards', '').replace('N/A', '')
                    omdb['DVD'] = date_format(child.get('DVD', '').replace('N/A', ''), scheme='%d %b %Y')

            except Exception as error:
                log('OMDB Error: %s' % error)
                pass

            else:
                write_cache(url,omdb)
                break

        return omdb
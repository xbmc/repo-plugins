#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2016 Asier Iturralde Sarasola
#
#    This file is part of plugin.audio.euskarazko-irratiak.
#
#    plugin.audio.euskarazko-irratiak is free software: you can redistribute it
#    and/or modify it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the License,
#    or (at your option) any later version.
#
#    plugin.audio.euskarazko-irratiak is distributed in the hope that it will
#    be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with plugin.audio.euskarazko-irratiak.
#    If not, see <http://www.gnu.org/licenses/>.
#

# http://docs.python-requests.org/en/latest/
import requests
from datetime import datetime
import time
import HTMLParser
from bs4 import BeautifulSoup, BeautifulStoneSoup

# WP-JSON API for the podcast Gramofonoa from Etzi.pm.
ETZI_PM_GRAMOFONOA_API_URL = 'http://etzi.pm/wp-json/wp/v2/posts?categories=794'
ETZI_PM_PLACEHOLDER_IMAGE_URL = 'http://etzi.pm/wp-content/themes/newsmag-etzi/assets/images/picture_placeholder.jpg'

radios = [{
    'name': 'Etzi Portu Maritimoa',
    'url': ''
}]

def get_radios():
    return radios

def is_in_list_of_radios(name):
    for radio in radios:
        if radio['name'] == name:
            return True

    return False

def get_programs():
    program_list = []

    program_list.append({'name': 'Gramofonoa', 'url': ETZI_PM_GRAMOFONOA_API_URL, 'radio': 'Etzi Portu Maritimoa'})

    return program_list

def get_audios(url):
    audios = []

    data = requests.get(url)
    audios_json = data.json()

    for audio in audios_json:
        title = HTMLParser.HTMLParser().unescape(audio['title']['rendered'])

        # Change the format of the date
        # TypeError: attribute of type 'NoneType' is not callable
        # http://forum.kodi.tv/showthread.php?tid=112916
        try:
            dateobj = datetime.strptime(audio['date'], "%Y-%m-%dT%H:%M:%S")
        except TypeError:
            dateobj = datetime(*(time.strptime(audio['date'], "%Y-%m-%dT%H:%M:%S")[0:6]))

        date = dateobj.strftime("%Y/%m/%d")

        # Parse the content
        content = BeautifulSoup(audio['content']['rendered'], 'html.parser')

        # Scrape the url of the audio from the content
        audio_url = content.select('audio a')[0]['href']

        # If an image is available use it
        if 'wp:featuredmedia' in audio['_links']:
            image_url = requests.get(audio['_links']['wp:featuredmedia'][0]['href']).json()['source_url']
        else:
            # Else use a placeholder image
            image_url = ETZI_PM_PLACEHOLDER_IMAGE_URL

        audios.append({'title': title, 'date': date, 'image': image_url, 'url': audio_url})
    return audios

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
from bs4 import BeautifulSoup

ARROSA_PODCASTS_URL = 'http://www.arrosasarea.eus/category/irratien-programak/'

def format_date(date):
    months = ["urtarrila", "otsaila", "martxoa", "apirila", "maiatza", "ekaina", "uztaila", "abuztua", "iraila", "urria", "azaroa", "abendua"]

    date_parts = date.split(" ")

    year = date_parts[2]
    month = "%02d" % (months.index(date_parts[0]) + 1)
    day = date_parts[1][:-1].rjust(2, '0')

    return "{0}/{1}/{2}".format(year, month, day)

def get_page(url):
    # download the source HTML for the page using requests
    # and parse the page using BeautifulSoup
    r = requests.get(url)

    if r.status_code == 404:
        return False

    return BeautifulSoup(r.text, 'html.parser')

def get_radios():
    radios = []

    # parse the website of arrosa irrati sarea
    page = get_page(ARROSA_PODCASTS_URL)

    radios_li = page.select('.dcw > li')

    for radio in radios_li:
        radio_a = radio.find('a', recursive=False)
        name = format_radio_name(radio_a.string)
        url = radio_a['href']
        radios.append({'name': name, 'url': url})

    return radios

def format_radio_name(name):
    # The names of the radios scraped from the website of Arrosa irrati sarea are uppercase.
    # They should be lowercase with every word capitalized except 'irratia' for the sake of consistency.
    return ' '.join(word[0].upper() + word[1:] if word != 'irratia' else word[0] + word[1:] for word in name.lower().split())

def get_programs(url, radio):
    programs = []

    # parse the website of the podcast of the selected radio
    page = get_page(url)

    programs_li = page.select('.dcw > li')

    for program in programs_li:
        program_a = program.find('a', recursive=False)

        if program_a is not None:
            name = program_a.string
            url = program_a['href']
            programs.append({'name': name, 'url': url, 'radio': radio})

    return programs

def get_audios_from_page(page):
    audios = []

    audios_div = page.select('.post')

    for audio in audios_div:
        title = audio.select('.big-title h3 a')[0].text
        date = format_date(audio.select('.magz-meta')[0].text.split('|')[0].strip())

        image = ''
        if len(audio.select('.magz-image img')) > 0:
            image = audio.select('.magz-image img')[0]['src']

        url = ''
        if len(audio.select('.powerpress_link_d')) > 0:
            url = audio.select('.powerpress_link_d')[0]['href']

        audios.append({'title': title, 'date': date, 'image': image, 'url': url})

    return audios

def get_audios(base_url):
    index = 1
    audios = []

    while True:
        podcast_page = get_page(base_url + 'page/' + str(index))

        if podcast_page:
            audios = audios + get_audios_from_page(podcast_page)
            index = index + 1
        else:
            break

    return audios

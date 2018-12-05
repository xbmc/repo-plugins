# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

    This file is part of Catch-up TV & More.

    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

# Source: https://github.com/melmorabity/tv_grab_fr_telerama

import datetime
import hashlib
import hmac
import re
import urllib

import html2text
import pytz
import pytz.reference
import requests
import time


'''
'13eme RUE': '2',
'2M Monde': '340',
'3SAT': '3',
'6ter': '1403',
'8 Mont-Blanc': '421',
'A+ International France': '2049',
'AB 1': '5',
'AB 3': '254',
'AB Moteurs': '15',
'ABXPLORE': '303',
'Action': '10',
'Al Jazeera English': '525',
'Alsace 20': '524',
'Altice Studio': '2320',
'Animaux': '12',
'ARD': '13',
'Arte': '111',
'Arte Belgique': '516',
'ATV Martinique': '295',
'Baby TV': '483',
'BBC 1': '16',
'BBC 2': '17',
'BBC Entertainment': '18',
'BBC World News': '19',
'BE 1': '29',
'Be Ciné': '417',
'Be Séries': '418',
'beIN SPORTS 1': '1290',
'beIN SPORTS 2': '1304',
'beIN SPORTS 3': '1335',
'beIN SPORTS MAX 10': '1342',
'beIN SPORTS MAX 4': '1336',
'beIN SPORTS MAX 5': '1337',
'beIN SPORTS MAX 6': '1338',
'beIN SPORTS MAX 7': '1339',
'beIN SPORTS MAX 8': '1340',
'beIN SPORTS MAX 9': '1341',
'BET': '1960',
'BFM Business': '1073',
'BFM TV': '481',
'Bloomberg UK-Europe': '410',
'Boing': '924',
'Boomerang': '321',
'Brazzers TV': '475',
'C8': '445',
'Canal+': '34',
'Canal 32': '534',
'Canal+ Afrique Ouest': '227',
'Canal+ Cinéma': '33',
'Canal+ Cinéma DROM': '1105',
'Canal+ Décalé': '30',
'Canal+ Family': '657',
'Canal J': '32',
'Canal partagé TNT Ile-de-France': '703',
'Canal+ Polynésie': '461',
'Canal+ Séries': '1563',
'Canal+ Sport': '35',
'Canvas': '24',
'Cartoon Network': '36',
'CBS Reality EMAE1': '514',
'CGTN': '318',
'Chasse et pêche': '38',
'Chérie 25': '1399',
'Ciné+ (A la carte)': '523',
'Ciné+ Classic': '287',
'Ciné+ Classic Belgique': '437',
'Ciné+ Club': '285',
'Ciné+ Emotion': '283',
'Ciné+ Famiz': '401',
'Ciné+ Frisson': '284',
'Ciné+ Frisson Afrique': '280',
'Ciné FX': '288',
'Ciné+ Premier': '282',
'Ciné+ Premier Belgique': '294',
'Ciné+ Star Afrique': '279',
'Classica English': '1353',
'Club RTL': '50',
'CNBC Europe': '51',
'CNBC Europe + Nat Geo': '52',
'CNEWS': '226',
'CNN': '53',
'Comédie+': '54',
'Crime District': '2037',
'CSTAR': '458',
'Demain TV': '57',
'Discovery Channel': '400',
'Discovery Science': '1374',
'Disney Channel': '58',
'Disney Channel +1': '299',
'Disney Cinema': '652',
'Disney Junior': '300',
'Disney XD': '79',
'Dorcel TV': '560',
'DW (English)': '61',
'E !': '405',
'één': '23',
'ElleGirl': '403',
'Equidia': '64',
'Equidia Life': '1146',
'ETB 1': '71',
'ETB 2': '72',
'Eurochannel': '1190',
'Euronews': '140',
'Eurosport 1': '76',
'Eurosport 2': '439',
'Extreme Sports Channel': '253',
'Fashion TV': '1996',
'Foot+ 24/24': '100',
'france2': '4',
'France 24': '529',
'France 3': '80',
'France 3 Alpes': '1921',
'France 3 Alsace': '1922',
'France 3 Aquitaine': '1923',
'France 3 Auvergne': '1924',
'France 3 Basse-Normandie': '1925',
'France 3 Bourgogne': '1926',
'France 3 Bretagne': '1927',
'France 3 Centre-Val de Loire': '1928',
'France 3 Champagne-Ardennes': '1929',
'France 3 Corse Via Stella': '308',
'France 3 Côte d\'Azur': '1931',
'France 3 Franche-Comté': '1932',
'France 3 Haute-Normandie': '1933',
'France 3 Languedoc-Roussillon': '1934',
'France 3 Limousin': '1935',
'France 3 Lorraine': '1936',
'France 3 Midi-Pyrénées': '1937',
'France 3 Nord Pas-de-Calais': '1938',
'France 3 Paris Ile-de-France': '1939',
'France 3 Pays de la Loire': '1940',
'France 3 Picardie': '1941',
'France 3 Poitou-Charentes': '1942',
'France 3 Provence-Alpes': '1943',
'France 3 Rhône-Alpes': '1944',
'France 4': '78',
'France 5': '47',
'France Ô': '160',
'Franceinfo': '2111',
'Game One': '87',
'Ginx': '563',
'Golf+': '1295',
'Golf Channel': '1166',
'Gong Max': '621',
'Guadeloupe la 1ère': '329',
'Gulli': '482',
'Guyane la 1ère': '260',
'Histoire': '88',
'Hustler TV': '416',
'I24news': '781',
'IDF1': '701',
'Infosport+': '94',
'J-One': '1585',
'Ketnet': '1280',
'KTO': '110',
'KZTV': '929',
'L\'Equipe': '1401',
'La Chaîne Météo': '124',
'La Chaîne parlementaire': '234',
'La Deux': '187',
'La Trois': '892',
'La Une': '164',
'LCI': '112',
'LM TV Sarthe': '535',
'm6': '118',
'M6 Boutique': '184',
'M6 Music': '453',
'Man-X': '683',
'Mangas': '6',
'Martinique la 1ère': '328',
'MCE (Ma Chaîne Etudiante)': '987',
'MCM': '121',
'MCM Top': '343',
'MCS Bien-être': '1136',
'MCS Maison': '2021',
'Melody': '265',
'Mezzo': '125',
'Mezzo Live HD': '907',
'Mirabelle TV': '1045',
'Motorsport TV': '237',
'MTV': '128',
'MTV Base': '263',
'MTV Dance': '2014',
'MTV Hits': '262',
'MTV Hits (France)': '2006',
'MTV Rocks': '264',
'Multisports': '98',
'Multisports 1': '101',
'Multisports 2': '102',
'Multisports 3': '103',
'Multisports 4': '104',
'Multisports 5': '105',
'Multisports 6': '106',
'Museum': '1072',
'Nat Geo Wild': '719',
'National Geographic': '243',
'Nautical Channel': '415',
'Nickelodéon': '473',
'Nickelodeon Junior': '888',
'Nickelodéon Teen': '1746',
'Nolife': '787',
'Nollywood TV': '1461',
'Nouvelle-Calédonie la 1ère': '240',
'NPO1': '910',
'NPO2': '911',
'NPO3': '912',
'NRJ 12': '444',
'NRJ Hits': '605',
'Numéro 23': '1402',
'OCS Choc': '732',
'OCS City': '733',
'OCS Géants': '734',
'OCS Max': '730',
'OLTV': '463',
'OMTV': '334',
'Onzéo': '517',
'Paramount Channel': '1562',
'Paris Première': '145',
'Pink TV': '406',
'Piwi+': '344',
'Planète+': '147',
'Planète+ Aventure Expérience': '402',
'Planète+ Crime Investigation': '662',
'Plug RTL': '377',
'Polar+': '2326',
'Polar': '289',
'Polynésie la 1ère': '459',
'Private TV': '558',
'Proximus 11': '1075',
'Q2': '108',
'Rai Due': '154',
'Rai Tre': '155',
'Rai Uno': '156',
'Real Madrid TV': '478',
'Réunion la 1ère': '245',
'RFM TV': '241',
'RMC': '546',
'RMC Découverte': '1400',
'RMC Sport 4': '1382',
'RMC Sport Access 1': '2095',
'RMC Sport Access 2': '675',
'RMC Sport UHD': '2029',
'RSI LA 1': '200',
'RSI LA 2': '201',
'RTL 9': '115',
'RTL Télévision': '166',
'RTL TVI': '168',
'RTPI': '169',
'RTS Deux': '183',
'RTS Un': '202',
'Sat 1': '172',
'Science & Vie TV': '63',
'Seasons': '173',
'serieclub': '49',
'SFR Sport 4': '1153',
'SRF 1': '59',
'SRF 2': '174',
'Stingray Brava': '835',
'Stingray Djazz': '1357',
'Stingray i-Concerts': '604',
'Sundance TV': '833',
'Supersport 3': '420',
'SWR': '182',
'Syfy': '479',
'TCM Cinéma': '185',
'Télénantes': '491',
'Télésud': '449',
'TéléToon+': '197',
'TéléToon+1': '293',
'Téva': '191',
'TF1': '192',
'TF1 Séries Films': '1404',
'TFX': '446',
'TIJI': '229',
'TLM (Télé Lyon Métropole)': '116',
'TMC': '195',
'Toonami': '2040',
'Toute l\'histoire': '7',
'Trace Africa': '1179',
'TRACE Sport Stars': '1168',
'Trace Toca': '1948',
'Trace Tropical': '753',
'Trace Urban': '325',
'Trek': '1776',
'TV Tours': '540',
'TV5MONDE': '205',
'TV5MONDE Afrique': '233',
'TV5MONDE Europe': '232',
'TV7 Bordeaux': '273',
'TvBreizh': '225',
'TVE': '208',
'TVE 1': '206',
'TVE 2': '207',
'TVR Rennes 35 Bretagne': '539',
'TVSUD Marseille': '492',
'Txingudi': '507',
'Ushuaïa TV': '451',
'VH1': '210',
'VH1 Classic': '690',
'Vier': '214',
'Vijf': '691',
'Vivolta': '659',
'VOOsport World 1': '413',
'VOOsport World 2': '414',
'Voyage': '212',
'VTM': '215',
'W9': '119',
'Warner TV': '2334',
'WDR': '217',
'XXL': '218',
'ZDF': '219',
'Zee Cinéma': '527',
'Zee TV': '526.tv.telerama.fr'
'''


CHANNELS_ID = {
    'tf1': '192',
    'tf1-series-films': '1404',
    'tfx': '446',
    'tmc': '195',
    'lci': '112',
    'gulli': '482',
    'canalplus': '34',
    'c8': '445',
    'cstar': '458',
    'france-2': '4',
    'france-3': '80',
    'france-4': '78',
    'france-5': '47',
    'france-o': '160',
    'lequipe': '1401',
    'cnews': '226',
    'rmcdecouverte': '1400',
    'rmcstory': '1402',
    'cherie25': '1399',
    'nrj12': '444',
    'bfmbusiness': '1073',
    'bfmtv': '481',
    'kto': '110',
    'lcp': '234',
    'franceinfo': '2111'
}

ID_CHANNELS = {
    192: 'tf1',
    1404: 'tf1-series-films',
    446: 'tfx',
    195: 'tmc',
    112: 'lci',
    482: 'gulli',
    34: 'canalplus',
    445: 'c8',
    458: 'cstar',
    4: 'france-2',
    80: 'france-3',
    78: 'france-4',
    47: 'france-5',
    160: 'france-o',
    1401: 'lequipe',
    226: 'cnews',
    1400: 'rmcdecouverte',
    1402: 'rmcstory',
    1399: 'cherie25',
    444: 'nrj12',
    481: 'bfmtv',
    1073: 'bfmbusiness',
    110: 'kto',
    234: 'lcp',
    2111: 'franceinfo'
}


class TeleramaXMLTVGrabber:
    """Implements grabbing and processing functionalities required to generate XMLTV data from
    Télérama mobile API.
    """

    _API_URL = 'https://api.telerama.fr'
    _API_USER_AGENT = 'okhttp/3.2.0'
    _API_KEY = 'apitel-5304b49c90511'
    _API_SECRET = 'Eufea9cuweuHeif'
    _API_DEVICE = 'android_tablette'
    _API_ENCODING = 'UTF-8'
    _TELERAMA_PROGRAM_URL = 'http://www.telerama.fr'
    _RATING_ICON_URL_TEMPLATE = 'http://television.telerama.fr/sites/tr_master/themes/tr/html/' \
                                'images/tv/-{}.png'

    _TELERAMA_TIMEZONE = pytz.timezone('Europe/Paris')
    _TELERAMA_START_TIME = datetime.time(6, 0)
    _TELERAMA_DATE_FORMAT = '%Y-%m-%d'
    _TELERAMA_TIME_FORMAT = '{} %H:%M:%S'.format(_TELERAMA_DATE_FORMAT)
    _XMLTV_DATETIME_FORMAT = '%Y%m%d%H%M%S %z'
    _XMLTV_DATETIME_FORMAT_PP = '%d/%m/%Y %H:%M:%S'

    _MAX_PROGRAMS_PER_PAGE = 100
    _MAX_DAYS = 13

    _XMLTV_CREDIT_ROLES = {
        'Acteur': 'actor',
        'Auteur': 'writer',
        'Autre Invité': 'guest',
        'Autre présentateur': 'presenter',
        'Compositeur': 'composer',
        'Créateur': 'writer',
        'Dialogue': 'writer',
        'Guest star': 'guest',
        'Interprète': 'actor',
        'Invité vedette': 'guest',
        'Invité': 'guest',
        'Metteur en scène': 'director',
        'Musique': 'composer',
        'Origine Scénario': 'presenter',
        'Présentateur vedette': 'presenter',
        'Présentateur': 'presenter',
        'Réalisateur': 'director',
        'Scénario': 'writer',
        'Scénariste': 'writer',
        'Voix Off VF': 'actor',
        'Voix Off VO': 'actor'
    }

    _ETSI_PROGRAM_CATEGORIES = {
        'Divertissement': 'Variety show',
        'Documentaire': 'Documentary',
        'Film': 'Movie / Drama',
        'Jeunesse': "Children's / Youth programmes",
        'Magazine': 'Magazines / Reports / Documentary',
        'Musique': 'Music / Ballet / Dance',
        'Sport': 'Sports',
        'Série': 'Movie / Drama',
        'Téléfilm': 'Movie / Drama'
    }

    # http://www.microsoft.com/typography/unicode/1252.htm
    _WINDOWS_1252_UTF_8 = {
        u"\x80": u"\u20AC",  # EURO SIGN
        u"\x82": u"\u201A",  # SINGLE LOW-9 QUOTATION MARK
        u"\x83": u"\u0192",  # LATIN SMALL LETTER F WITH HOOK
        u"\x84": u"\u201E",  # DOUBLE LOW-9 QUOTATION MARK
        u"\x85": u"\u2026",  # HORIZONTAL ELLIPSIS
        u"\x86": u"\u2020",  # DAGGER
        u"\x87": u"\u2021",  # DOUBLE DAGGER
        u"\x88": u"\u02C6",  # MODIFIER LETTER CIRCUMFLEX ACCENT
        u"\x89": u"\u2030",  # PER MILLE SIGN
        u"\x8A": u"\u0160",  # LATIN CAPITAL LETTER S WITH CARON
        u"\x8B": u"\u2039",  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
        u"\x8C": u"\u0152",  # LATIN CAPITAL LIGATURE OE
        u"\x8E": u"\u017D",  # LATIN CAPITAL LETTER Z WITH CARON
        u"\x91": u"\u2018",  # LEFT SINGLE QUOTATION MARK
        u"\x92": u"\u2019",  # RIGHT SINGLE QUOTATION MARK
        u"\x93": u"\u201C",  # LEFT DOUBLE QUOTATION MARK
        u"\x94": u"\u201D",  # RIGHT DOUBLE QUOTATION MARK
        u"\x95": u"\u2022",  # BULLET
        u"\x96": u"\u2013",  # EN DASH
        u"\x97": u"\u2014",  # EM DASH
        u"\x98": u"\u02DC",  # SMALL TILDE
        u"\x99": u"\u2122",  # TRADE MARK SIGN
        u"\x9A": u"\u0161",  # LATIN SMALL LETTER S WITH CARON
        u"\x9B": u"\u203A",  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
        u"\x9C": u"\u0153",  # LATIN SMALL LIGATURE OE
        u"\x9E": u"\u017E",  # LATIN SMALL LETTER Z WITH CARON
        u"\x9F": u"\u0178",  # LATIN CAPITAL LETTER Y WITH DIAERESIS
    }

    def __init__(self):
        initialization_data = self._get_initialization_data()
        self._channels = {self._telerama_to_xmltv_id(c['id']): {'display_name': c['nom'],
                                                                'url': c['link'],
                                                                'icon': c['logo'],
                                                                'telerama_id': c['id']}
                          for c in initialization_data['donnees']['chaines']}
        self._categories = {c['id']: c['libelle'] for c in initialization_data['donnees']['genres']}

    def _query_telerama_api(self, procedure, **query):
        """Query the Télérama API."""

        # Authentication method taken from https://github.com/zubrick/tv_grab_fr_telerama
        updated_query = dict(query)
        updated_query['appareil'] = self._API_DEVICE
        signing_string = procedure + ''.join(sorted([k + str(v) for k, v in updated_query.items()]))
        signature = hmac.new(self._API_SECRET.encode(), signing_string.encode(),
                             hashlib.sha1).hexdigest()
        updated_query['api_signature'] = signature
        updated_query['api_cle'] = self._API_KEY

        url = '{}{}?{}'.format(self._API_URL, procedure, urllib.urlencode(updated_query))

        # print('Retrieving URL %s', url)

        with requests.Session() as session:
            response = session.get(url, headers={'User-agent': self._API_USER_AGENT})
            return response

    @staticmethod
    def _telerama_to_xmltv_id(telerama_id):
        """Convert a Télérama channel ID to a valid XMLTV channel ID."""

        return '{}.tv.telerama.fr'.format(telerama_id)

    def _get_initialization_data(self):
        """Retrieve Télérama initalization data, such as predefined program categories and available
        channels.
        """

        # print('Getting available channels')
        response = self._query_telerama_api('/v1/application/initialisation')
        if response.status_code != 200:
            # print('Unable to retrieve initialisation data')
            response.raise_for_status()
        return response.json()

    def _get_programs(self, channels, date):
        """Get Télérama programs for a given channel and a given day."""

        # print('Getting Télérama programs on %s', date)

        telerama_ids = []
        for channel in channels:
            if channel in CHANNELS_ID:
                telerama_ids.append(CHANNELS_ID[channel])
        page = 1
        programs = []
        while True:
            response = self._query_telerama_api(
                '/v1/programmes/telechargement',
                dates=datetime.datetime.strftime(date, self._TELERAMA_DATE_FORMAT),
                id_chaines=','.join(str(i) for i in telerama_ids), page=page,
                nb_par_page=self._MAX_PROGRAMS_PER_PAGE
            )
            try:
                data = response.json()
                if response.status_code == 200:
                    programs += data.get('donnees', [])
                    page += 1
                    continue
                else:
                    data = response.json()
                    if response.status_code == 404 and data.get('error') and \
                       data.get('msg') == "Il n'y a pas de programmes.":
                        # No more program page available
                        break
            except ValueError:
                pass

            # print('Unable to retrieve program data for date %s', str(date))
            response.raise_for_status()

        return programs

    def _etsi_category(self, category):
        """Translate Télérama program category to ETSI EN 300 468 category."""

        etsi_category = self._ETSI_PROGRAM_CATEGORIES.get(category)
        if etsi_category is None:
            # print('Télérama category "%s" has no defined ETSI equivalent', category)
            pass
        return etsi_category

    def _fix_xml_unicode_string(self, text):
        """Replace in a string all Windows-1252 specific chars to UTF-8 and delete non
        XML-compatible characters.
        """

        fixed_text = ''.join([self._WINDOWS_1252_UTF_8.get(c, c) for c in text])
        fixed_text = re.sub(r'[\x00-\x08\x0b\x0E-\x1F\x7F]', '', fixed_text)

        return fixed_text

    @staticmethod
    def _html_to_text(text):
        html_format = html2text.HTML2Text()
        html_format.ignore_emphasis = True
        html_format.body_width = False
        html_format.ignore_links = True
        return html_format.handle(text)

    def _parse_program_dict(self, program):
        program_dict = {}

        # Channel ID
        program_dict['id_chaine'] = program['id_chaine']

        # Showview
        if program['showview']:
            program_dict['showview'] = program['showview']

        # # Start and stop time, for the current timezone
        # start = self._TELERAMA_TIMEZONE.localize(
        #     datetime.datetime.strptime(program['horaire']['debut'], self._TELERAMA_TIME_FORMAT)
        # )
        # stop = self._TELERAMA_TIMEZONE.localize(
        #     datetime.datetime.strptime(program['horaire']['fin'], self._TELERAMA_TIME_FORMAT)
        # )

        try:
            start = datetime.datetime.strptime(program['horaire']['debut'], self._TELERAMA_TIME_FORMAT)
        except TypeError:
            start = datetime.datetime(*(time.strptime(program['horaire']['debut'], self._TELERAMA_TIME_FORMAT)[0:6]))

        try:
            stop = datetime.datetime.strptime(program['horaire']['fin'], self._TELERAMA_TIME_FORMAT)
        except TypeError:
            stop = datetime.datetime(*(time.strptime(program['horaire']['fin'], self._TELERAMA_TIME_FORMAT)[0:6]))

        program_dict['start'] = datetime.datetime.strftime(start, self._XMLTV_DATETIME_FORMAT)
        program_dict['stop'] = datetime.datetime.strftime(stop, self._XMLTV_DATETIME_FORMAT)

        # Title
        program_dict['title'] = program['titre']

        if program['titre_original']:
            program_dict['originaltitle'] = program['titre_original']

        # Sub-title
        if program['soustitre']:
            program_dict['soustitre'] = program['soustitre']

        # Desc
        if program['resume']:
            program_dict['plot'] = self._html_to_text(self._fix_xml_unicode_string(program['resume']))

        # Credits
        if 'intervenants' in program:

            directors = set()
            actors = set()
            writers = set()
            composers = set()
            presenters = set()
            guests = set()

            for credit in program['intervenants']:
                role = self._XMLTV_CREDIT_ROLES.get(credit['libelle'])
                if role is None:
                    if credit['libelle']:
                        pass
                        # print('Télérama role "' + credit['libelle'] + '" has no XMLTV equivalent')
                    continue
                name = credit['nom']
                if credit['prenom']:
                    name = '{} {}'.format(credit['prenom'], name)

                if role == 'director':
                    directors.add(name)
                elif role == 'actor':
                    actors.add(name)
                elif role == 'writer':
                    writers.add(name)
                elif role == 'composer':
                    composers.add(name)
                elif role == 'presenter':
                    presenters.add(name)
                elif role == 'guests':
                    guests.add(name)

            program_dict['directors'] = list(directors)
            program_dict['actors'] = list(actors)
            program_dict['writers'] = list(writers)
            program_dict['composers'] = list(composers)
            program_dict['presenters'] = list(presenters)
            program_dict['guests'] = list(guests)

        # Year
        if program['annee_realisation']:
            program_dict['year'] = program['annee_realisation']

        # Categories
        category = self._categories.get(program['id_genre'])
        if program['id_genre'] is not None:
            '''
            etsi_category = self._etsi_category(category)
            if etsi_category is not None:
                category_xml = SubElement(program_xml, 'category')
                category_xml.text = etsi_category
            '''
            # Keep original category in French
            program_dict['genre'] = []
            program_dict['genre'].append(category)

            # Add specific category
            if program['genre_specifique'] and category != program['genre_specifique']:
                program_dict['genre'].append(program['genre_specifique'])

        # Icon
        if 'vignettes' in program:
            program_dict['image'] = program['vignettes']['grande']

        # URL
        if program['url']:
            program_dict['url'] = '{}/{}'.format(self._TELERAMA_PROGRAM_URL, program['url'])

        # Episode/season
        if program['serie'] and program['serie']['numero_episode']:
            program_dict['season'] = (program['serie'].get('saison', 1) or 1) - 1
            program_dict['episode'] = program['serie']['numero_episode'] - 1
            '''
            episode_num_xml = SubElement(program_xml, 'episode-num', system='xmltv_ns')
            episode_num_xml.text = '{}.{}'.format(season, episode)
            if program['serie'].get('nombre_episode'):
                episode_num_xml.text += '/{}'.format(program['serie']['nombre_episode'])
            episode_num_xml.text += '.0/1'
            '''

        # Video format
        aspect = None
        if program['flags']['est_ar16x9']:
            aspect = '16:9'
        elif program['flags']['est_ar4x3']:
            aspect = '4:3'
        if aspect is not None:
            program_dict['aspect'] = aspect
        if program['flags']['est_hd']:
            program_dict['quality'] = 'HDTV'
        '''
        if list(video_xml):
            program_xml.append(video_xml)
        '''

        # Audio format
        stereo = None
        if program['flags']['est_dolby']:
            stereo = 'dolby'
        elif program['flags']['est_stereoar16x9'] or program['flags']['est_stereo']:
            stereo = 'stereo'
        elif program['flags']['est_vm']:
            stereo = 'bilingual'
        if stereo is not None:
            program_dict['audio'] = stereo

        # Check whether the program was previously shown
        if program['flags']['est_premdif'] or program['flags']['est_inedit']:
            # program_xml.append(Element('premiere'))
            program_dict['diffusion'] = 'Inédit'
        elif program['flags']['est_redif']:
            # program_xml.append(Element('previously-shown'))
            program_dict['diffusion'] = 'Redifusion'
        elif program['flags']['est_derdif']:
            # program_xml.append(Element('last-chance'))
            program_dict['diffusion'] = 'Dernière chance'

        # Subtitles
        if program['flags']['est_stm']:
            # program_xml.append(Element('subtitles', type='deaf-signed'))
            program_dict['subtitles'] = 'deaf-signed'
        elif program['flags']['est_vost']:
            # program_xml.append(Element('subtitles', type='onscreen'))
            program_dict['subtitles'] = 'onscreen'

        '''
        # Rating
        if program['csa_full']:
            rating_xml = SubElement(program_xml, 'rating', system='CSA')
            rating_value_xml = SubElement(rating_xml, 'value')
            rating_value_xml.text = program['csa_full'][0]['nom_long']
            if program['csa_full'][0]['nom_court'] != 'TP':
                rating_icon = self._RATING_ICON_URL_TEMPLATE.format(
                    program['csa_full'][0]['nom_court']
                )
                rating_xml.append(Element('icon', src=rating_icon))
        '''

        # Star rating
        if program['note_telerama'] > 0:
            #program_dict['note_telerama'] = '{}/5'.format(program['note_telerama'])
            program_dict['rating'] = float(program['note_telerama'] * 2)  # Pour avoir sur 10 pour Kodi
        # Review
        review = ''
        if program['critique']:
            review = self._html_to_text(program['critique'])
        if program['notule']:
            notule = self._html_to_text(self._fix_xml_unicode_string(program['notule']))
            if review:
                review = '{}\n\n{}'.format(notule, review)
            else:
                review = notule
        if review:
            program_dict['review'] = review.strip()

        return program_dict

    def _get_programs_data(self, channels):

        today = datetime.date.today()
        today = datetime.datetime.combine(today, datetime.time(0))
        today = today.replace(tzinfo=pytz.reference.LocalTimezone())

        # Pyhton 3
        # today = datetime.datetime.combine(
        #     datetime.date.today(),
        #     datetime.time(0),
        #     tzinfo=pytz.reference.LocalTimezone()
        # )

        # print('TODAY: ' + str(today))

        current_time = datetime.datetime.now().replace(
            tzinfo=pytz.reference.LocalTimezone())
        # print('CURRENT_TIME: ' + str(current_time))
        days = 1
        # Dates to fetch from the Télérama API
        telerama_fetch_dates = [today.date() + datetime.timedelta(days=d) for d in range(days)]
        # Télérama data for a given day contain programs starting between 6:00 AM and 6:00 AM the
        # next day (Paris time)
        if current_time < self._TELERAMA_TIMEZONE.localize(
                datetime.datetime.combine(current_time, self._TELERAMA_START_TIME)
        ):
            telerama_fetch_dates.insert(0, current_time.date() - datetime.timedelta(days=1))

        programs = {}
        for date in telerama_fetch_dates:
            for program in self._get_programs(channels, date):

                try:
                    program_start_0 = datetime.datetime.strptime(program['horaire']['debut'], self._TELERAMA_TIME_FORMAT)
                except TypeError:
                    program_start_0 = datetime.datetime(*(time.strptime(program['horaire']['debut'], self._TELERAMA_TIME_FORMAT)[0:6]))

                program_start = self._TELERAMA_TIMEZONE.localize(program_start_0)

                try:
                    program_stop_0 = datetime.datetime.strptime(program['horaire']['fin'], self._TELERAMA_TIME_FORMAT)
                except TypeError:
                    program_stop_0 = datetime.datetime(*(time.strptime(program['horaire']['fin'], self._TELERAMA_TIME_FORMAT)[0:6]))

                program_stop = self._TELERAMA_TIMEZONE.localize(program_stop_0)

                # Keep only current program
                if program_start <= current_time and program_stop >= current_time:
                    program_dict = self._parse_program_dict(program)
                    programs[ID_CHANNELS[program_dict['id_chaine']]] = program_dict

        return programs


def grab_tv_guide(channels):
    telerama = TeleramaXMLTVGrabber()
    programs = telerama._get_programs_data(channels)
    return programs


# Only for testing purpose
if __name__ == '__main__':
    channels = ['france2', 'm6', 'w9', 'test_channel_no_present']

    programs = grab_tv_guide(channels)

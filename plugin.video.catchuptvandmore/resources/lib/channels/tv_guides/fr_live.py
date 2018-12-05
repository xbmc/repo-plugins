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

from codequick import utils
import urlquick
import pytz
import hashlib
import hmac
import re
import urllib
import datetime
import time
from resources.lib.tzlocal import get_localzone


class TeleramaXMLTVGrabber:
    """Implements grabbing and processing functionalities required to generate XMLTV data from
    Télérama mobile API.
    """

    CHANNELS_ID = {}  # Built on the fly

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
    _TELERAMA_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'

    _XMLTV_DATETIME_FORMAT = '%Y%m%d%H%M%S %z'
    _XMLTV_DATETIME_FORMAT_PP = '%d/%m/%Y %H:%M:%S'

    _MAX_PROGRAMS_PER_PAGE = 100

    _TELERAMA_CATEGORIES = {
        1: "Divertissement",
        2: "Documentaire",
        3: "Film",
        4: "Jeunesse",
        5: "Magazine",
        6: "Musique",
        7: "Série",
        8: "Sport",
        9: "Téléfilm"
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
        self.CHANNELS_ID = {v: k for k, v in self.ID_CHANNELS.iteritems()}

    def _fix_xml_unicode_string(self, text):
        """Replace in a string all Windows-1252 specific chars to UTF-8 and delete non
        XML-compatible characters.
        """
        fixed_text = ''.join(
            [self._WINDOWS_1252_UTF_8.get(c, c) for c in text])
        fixed_text = re.sub(r'[\x00-\x08\x0b\x0E-\x1F\x7F]', '', fixed_text)

        return fixed_text

    def _parse_program_dict(self, program):
        program_dict = {}

        # Channel ID
        program_dict['id_chaine'] = program['id_chaine']

        # Horaire
        try:
            local_tz = get_localzone()
        except:
            # Hotfix issue #102
            local_tz = pytz.timezone('Europe/Paris')

        start_s = program['horaire']['debut']
        try:
            start = datetime.datetime.strptime(
                start_s,
                self._TELERAMA_TIME_FORMAT)
        except TypeError:
            start = datetime.datetime(*(time.strptime(
                start_s, self._TELERAMA_TIME_FORMAT)[0:6]))

        start = self._TELERAMA_TIMEZONE.localize(start)
        start = start.astimezone(local_tz)
        final_start_s = start.strftime("%Hh%M")
        program_dict['start_time'] = final_start_s


        stop_s = program['horaire']['fin']
        try:
            stop = datetime.datetime.strptime(
                stop_s,
                self._TELERAMA_TIME_FORMAT)
        except TypeError:
            stop = datetime.datetime(*(time.strptime(
                stop_s, self._TELERAMA_TIME_FORMAT)[0:6]))

        stop = self._TELERAMA_TIMEZONE.localize(stop)
        stop = stop.astimezone(local_tz)
        final_stop_s = stop.strftime("%Hh%M")
        program_dict['stop_time'] = final_stop_s

        # Title
        program_dict['title'] = program['titre']

        if program['titre_original']:
            program_dict['originaltitle'] = program['titre_original']

        # Sub-title
        if program['soustitre']:
            program_dict['subtitle'] = program['soustitre']

        # Desc
        if program['resume']:
            program_dict['plot'] = utils.strip_tags(
                self._fix_xml_unicode_string(program['resume']))

        # Categories
        if program['id_genre']:
            program_dict['genre'] = self._TELERAMA_CATEGORIES.get(
                program['id_genre'], 'Inconnue')

        # Add specific category
        if program['genre_specifique']:
            program_dict['specific_genre'] = program['genre_specifique']

        # Icon
        if 'vignettes' in program:
            program_dict['thumb'] = program['vignettes']['grande']
            program_dict['fanart'] = program['vignettes']['grande169']

        # Episode/season
        if program['serie'] and program['serie']['numero_episode']:
            program_dict['season'] = (program['serie'].get('saison', 1) or 1) - 1
            program_dict['episode'] = program['serie']['numero_episode'] - 1

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

        # Star rating
        if program['note_telerama'] > 0:
            program_dict['rating'] = float(program['note_telerama'] * 2)  # Pour avoir sur 10 pour Kodi

        return program_dict

    def _query_telerama_api(self, procedure, **query):
        """Query the Télérama API."""

        # Authentication method taken from https://github.com/zubrick/tv_grab_fr_telerama
        updated_query = dict(query)
        updated_query['appareil'] = self._API_DEVICE
        signing_string = procedure + ''.join(
            sorted([k + str(v) for k, v in updated_query.items()]))
        signature = hmac.new(
            self._API_SECRET.encode(),
            signing_string.encode(),
            hashlib.sha1).hexdigest()
        updated_query['api_signature'] = signature
        updated_query['api_cle'] = self._API_KEY

        url = '{}{}?{}'.format(
            self._API_URL, procedure, urllib.urlencode(updated_query))

        # print('Retrieving URL %s', url)
        return urlquick.get(
            url,
            headers={'User-agent': self._API_USER_AGENT},
            max_age=-1)


    def _get_current_programs(self, channels):
        """Get Télérama current programs for a given channel and a given day."""

        # print('Getting Télérama programs on %s', date)

        telerama_ids = []
        for channel in channels:
            if channel in self.CHANNELS_ID:
                telerama_ids.append(self.CHANNELS_ID[channel])
        page = 1
        programs = []
        while True:
            response = self._query_telerama_api(
                '/v1/programmes/maintenant',
                id_chaines=','.join(str(i) for i in telerama_ids),
                page=page,
                nb_par_page=self._MAX_PROGRAMS_PER_PAGE
            )
            try:
                data = response.json()
                if response.status_code == 200:
                    programs += data.get('donnees', [])
                    page += 1
                    # continue
                    break  # 100 programmes c'est déjà bien, il ne devrait pas y avoir d'autres pages
                else:
                    data = response.json()
                    if response.status_code == 404 and data.get('error') and \
                       data.get('msg') == "Il n'y a pas de programmes.":
                        # No more program page available
                        break
            except ValueError:
                pass

            # print('Unable to retrieve program data for date %s', str(date))
            # response.raise_for_status()

        return programs

    def _get_programs_data(self, channels):

        programs = {}
        for program in self._get_current_programs(channels):
            program_dict = self._parse_program_dict(program)
            programs[self.ID_CHANNELS[program_dict['id_chaine']]] = program_dict

        return programs


def grab_tv_guide(channels):
    telerama = TeleramaXMLTVGrabber()
    programs = telerama._get_programs_data(channels)
    return programs


# Only for testing purpose
if __name__ == '__main__':
    channels = ['france2', 'm6', 'w9', 'test_channel_no_present']

    programs = grab_tv_guide(channels)


'''
Telerama ID

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
'Zee TV': '526'
'''

# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Benjamin Bertrand
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.
# http://www.gnu.org/copyleft/gpl.html

import sys
from xbmcswift import xbmcgui
from collections import deque
from SimpleDownloader import SimpleDownloader
import resources.lib.scraper as scraper
from config import plugin

URLEMISSION = 'http://www.arretsurimages.net/toutes-les-emissions.php?id=%d&'
URL = {'toutesLesEmissions': 'http://www.arretsurimages.net/emissions.php?',
       'arretSurImages': URLEMISSION % 1,
       'ligneJaune': URLEMISSION % 2,
       'dansLeTexte': URLEMISSION % 3,
       'auxSources': URLEMISSION % 4,
       'auProchainEpisode': URLEMISSION % 5}
SORTMETHOD = ['date_publication', 'nb_vues', 'nb_comments']
BESTOF_SORTMETHOD = ['recent', 'visited', 'commented', 'rated']
STREAMS = ['stream_h264_hq_url', 'stream_h264_url']


def login():
    """Login or exit if it fails"""
    # Only available with a subscription
    # Check if username and password have been set
    username = plugin.get_setting('username')
    password = plugin.get_setting('password')
    if not username or not password:
        xbmcgui.Dialog().ok(plugin.get_string(30050), plugin.get_string(30051), plugin.get_string(30052))
        sys.exit(0)
    # Try to login only if username isn't already logged in
    # (we don't have to login everytime as we use a cookie)
    if not scraper.is_logged_in(username) and not scraper.login(username, password):
        xbmcgui.Dialog().ok(plugin.get_string(30050), plugin.get_string(30053))
        sys.exit(0)


@plugin.route('/')
def index():
    """Default view"""
    quick_access = plugin.get_setting('quickAccess')
    if quick_access == 'true':
        # Jump directly to 'toutesLesEmissions'
        login()
        return show_programs('toutesLesEmissions', '1')
    items = [
        {'label': plugin.get_string(30010), 'url': plugin.url_for('emissions')},
        {'label': plugin.get_string(30011), 'url': plugin.url_for('bestof', page='1')},
        {'label': plugin.get_string(30012), 'url': plugin.url_for('settings')},
    ]
    return plugin.add_items(items)


@plugin.route('/emissions/')
def emissions():
    """Display the available programs categories"""
    login()
    items = [
        {'label': 'Toutes les émissions',
         'url': plugin.url_for('show_programs', label='toutesLesEmissions', page='1'),
         'is_folder': True},
        {'label': '@rrêt sur images',
         'url': plugin.url_for('show_programs', label='arretSurImages', page='1'),
         'info': {'Plot':plugin.get_string(30031)},
         'is_folder': True},
        {'label': 'D@ns le texte',
         'url': plugin.url_for('show_programs', label='dansLeTexte', page='1'),
         'info': {'Plot': plugin.get_string(30033)},
         'is_folder': True},
        {'label': '@ux sources',
         'url': plugin.url_for('show_programs', label='auxSources', page='1'),
         'info': {'Plot': plugin.get_string(30034)},
         'is_folder': True},
        {'label': '@u Prochain Episode',
         'url': plugin.url_for('show_programs', label='auProchainEpisode', page='1'),
         'info': {'Plot': plugin.get_string(30035)},
         'is_folder': True},
        {'label': 'Ligne j@une',
         'url': plugin.url_for('show_programs', label='ligneJaune', page='1'),
         'info': {'Plot': plugin.get_string(30032)},
         'is_folder': True}
    ]
    return plugin.add_items(items)


@plugin.route('/bestof/<page>')
def bestof(page):
    """Display ASI BestOf videos"""
    # No subscription required
    sort_method = BESTOF_SORTMETHOD[int(plugin.get_setting('bestOfSortMethod'))]
    result = scraper.get_bestof_videos(page, sort_method)
    items = [{'label': video['title'],
              'url': plugin.url_for('play_video_id', video_id=video['id']),
              'thumbnail': video['thumbnail_url'],
              'is_folder': False,
              'is_playable': True,
             } for video in result['list']]
    # Add navigation items (Previous / Next) if needed
    page = int(page)
    if result['has_more']:
        next_page = str(page + 1)
        items.insert(0, {'label': plugin.get_string(30020),
                         'url': plugin.url_for('bestof',
                                               page=next_page)})
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {'label': plugin.get_string(30021),
                         'url': plugin.url_for('bestof',
                                               page=previous_page)})
    return plugin.add_items(items, update_listing=(page != 1))


@plugin.route('/settings/')
def settings():
    """Open the addon settings"""
    plugin.open_settings()


@plugin.route('/labels/<label>/<page>/')
def show_programs(label, page):
    """Display the list of programs"""
    sortMethod = SORTMETHOD[int(plugin.get_setting('sortMethod'))]
    programs = scraper.Programs('%sp=%s&orderby=%s' % (URL[label], page, sortMethod))
    entries = programs.get_programs()
    if plugin.get_setting('displayParts') == 'true':
        # Displayed programs are not playable
        # We will display all the parts
        items = [{'label': program['title'],
                  'url': plugin.url_for('get_program_parts',
                                        url=program['url'],
                                        name=program['title'],
                                        icon=program['thumb']),
                  'thumbnail': program['thumb'],
                  'is_folder': True,
                 } for program in entries]
    else:
        # Displayed programs are playable
        # We will try to play the main (xvid) video
        items = [{'label': program['title'],
                  'url': plugin.url_for('play_program', url=program['url']),
                  'thumbnail': program['thumb'],
                  'is_folder': False,
                  'is_playable': True,
                  'context_menu': [(plugin.get_string(30180),
                                    'XBMC.RunPlugin(%s)' %
                                        plugin.url_for('download_program',
                                                        url=program['url']))],
                 } for program in entries]
    # Add navigation items (Previous / Next) if needed
    nav_items = programs.get_nav_items()
    page = int(page)
    if nav_items['next']:
        next_page = str(page + 1)
        items.insert(0, {'label': plugin.get_string(30020),
                         'url': plugin.url_for('show_programs',
                                               label=label,
                                               page=next_page)})
    if nav_items['previous']:
        previous_page = str(page - 1)
        items.insert(0, {'label': plugin.get_string(30021),
                         'url': plugin.url_for('show_programs',
                                               label=label,
                                               page=previous_page)})
    return plugin.add_items(items, update_listing=(page != 1))


@plugin.route('/program/<url>', mode='play', name='play_program')
@plugin.route('/download_program/<url>', mode='download', name='download_program')
def get_program(url, mode):
    """Play or download the selected program"""
    video = scraper.get_main_video(url)
    if video['url'] is None:
        # No main video was found
        # Ask user to enable the DisplayParts setting
        xbmcgui.Dialog().ok(plugin.get_string(30054),
                            plugin.get_string(30055),
                            plugin.get_string(30052))
        sys.exit(0)
    if mode == 'play':
        return play_video(video['url'])
    elif mode == 'download':
        download_video(video['url'], video['title'])


@plugin.route('/play/<url>')
def play_video(url):
    """Play the video"""
    return plugin.set_resolved_url(url)


@plugin.route('/download/<url>/<title>')
def download_video(url, title):
    """Download the video"""
    downloader = SimpleDownloader()
    if plugin.get_setting('downloadMode') == 'true':
        # Ask for the path
        download_path = xbmcgui.Dialog().browse(3, plugin.get_string(30090), 'video')
    else:
        download_path = plugin.get_setting('downloadPath')
    if download_path:
        params = {'url': url, 'download_path': download_path}
        downloader.download(title, params)


@plugin.route('/parts/<url>/<name>/<icon>')
def get_program_parts(url, name, icon):
    """Display all parts of the program"""
    parts = scraper.get_program_parts(url, name, icon)
    part = parts[0]
    if 'url' in part:
        # Display the main video if available
        main_item = [{'label': part['title'],
                  'url': plugin.url_for('play_video', url=part['url']),
                  'thumbnail': part['thumb'],
                  'is_folder': False,
                  'is_playable': True,
                  'context_menu': [(plugin.get_string(30180),
                                    'XBMC.RunPlugin(%s)' %
                                        plugin.url_for('download_video',
                                                        url=part['url'],
                                                        title=part['title']))],
                 }]
        parts = parts[1:]
    else:
        main_item = []
    # Display the remaining videos
    items = [{'label': part['title'],
              'url': plugin.url_for('play_video_id', video_id=part['video_id']),
              'thumbnail': part['thumb'],
              'is_folder': False,
              'is_playable': True,
              'context_menu': [(plugin.get_string(30180),
                                'XBMC.RunPlugin(%s)' %
                                    plugin.url_for('download_video_id',
                                                    video_id=part['video_id']))],
             } for part in parts]
    return plugin.add_items(main_item + items)


@plugin.route('/play_video_id/<video_id>', mode='play', name='play_video_id')
@plugin.route('/download_video_id/<video_id>', mode='download', name='download_video_id')
def get_video_by_id(video_id, mode):
    """Play or download the dailymotion video"""
    streams = deque(STREAMS)
    # Order the streams depending on the quality chosen
    streams.rotate(int(plugin.get_setting('quality')) * -1)
    video = scraper.get_video_by_id(video_id, streams)
    if mode == 'play':
        return plugin.set_resolved_url(video['url'])
    elif mode == 'download':
        download_video(video['url'], video['title'])


if __name__ == '__main__':
    plugin.run()

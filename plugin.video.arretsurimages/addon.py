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
from xbmcswift2 import xbmcgui
from collections import deque
from SimpleDownloader import SimpleDownloader
import resources.lib.scraper as scraper
from config import plugin

URLEMISSION = 'http://www.arretsurimages.net/toutes-les-emissions.php?id=%d&'
URL = {'fiveLast': 'http://www.arretsurimages.net/emissions.php?',
       'arretSurImages': URLEMISSION % 1,
       'ligneJaune': URLEMISSION % 2,
       'dansLeTexte': URLEMISSION % 3,
       'auxSources': URLEMISSION % 4,
       'auProchainEpisode': URLEMISSION % 5,
       '14h42': URLEMISSION % 6,
       'CPQJ': URLEMISSION % 7,
      }
SORTMETHOD = ['date_publication', 'nb_vues', 'nb_comments']
BESTOF_SORTMETHOD = ['recent', 'visited', 'commented', 'rated']
STREAMS = ['stream_h264_hq_url', 'stream_h264_url']


def login():
    """Login or exit if it fails"""
    # Only available with a subscription
    # Check if username and password have been set
    username = plugin.get_setting('username', unicode)
    password = plugin.get_setting('password', unicode)
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
    quick_access = plugin.get_setting('quickAccess', bool)
    if quick_access:
        # Jump directly to 'fiveLast'
        login()
        return show_programs('fiveLast', '1')
    items = [
        {'label': plugin.get_string(30010), 'path': plugin.url_for('emissions')},
        {'label': plugin.get_string(30011), 'path': plugin.url_for('bestof', page='1')},
        {'label': plugin.get_string(30012), 'path': plugin.url_for('settings')},
    ]
    return plugin.finish(items)


@plugin.route('/emissions/')
def emissions():
    """Display the available programs categories"""
    login()
    items = [
        {'label': plugin.get_string(30013),
         'path': plugin.url_for('show_programs', label='fiveLast', page='1'),
        },
        {'label': '@rrêt sur images',
         'path': plugin.url_for('show_programs', label='arretSurImages', page='1'),
         'info': {'Plot':plugin.get_string(30031)},
        },
        {'label': 'D@ns le texte',
         'path': plugin.url_for('show_programs', label='dansLeTexte', page='1'),
         'info': {'Plot': plugin.get_string(30033)},
        },
        {'label': '14:42',
         'path': plugin.url_for('show_programs', label='14h42', page='1'),
         'info': {'Plot': plugin.get_string(30036)},
        },
        {'label': "C'est p@s qu'un jeu",
         'path': plugin.url_for('show_programs', label='CPQJ', page='1'),
         'info': {'Plot': plugin.get_string(30037)},
        },
        {'label': '@ux sources',
         'path': plugin.url_for('show_programs', label='auxSources', page='1'),
         'info': {'Plot': plugin.get_string(30034)},
        },
        {'label': '@u Prochain Episode',
         'path': plugin.url_for('show_programs', label='auProchainEpisode', page='1'),
         'info': {'Plot': plugin.get_string(30035)},
        },
        {'label': 'Ligne j@une',
         'path': plugin.url_for('show_programs', label='ligneJaune', page='1'),
         'info': {'Plot': plugin.get_string(30032)},
        }
    ]
    return plugin.finish(items)


@plugin.route('/bestof/<page>')
def bestof(page):
    """Display ASI BestOf videos"""
    # No subscription required
    sort_method = BESTOF_SORTMETHOD[plugin.get_setting('bestOfSortMethod', int)]
    result = scraper.get_bestof_videos(page, sort_method)
    items = [{'label': video['title'],
              'path': plugin.url_for('play_video_id', video_id=video['id']),
              'thumbnail': video['thumbnail_url'],
              'is_playable': True,
             } for video in result['list']]
    # Add navigation items (Previous / Next) if needed
    page = int(page)
    if result['has_more']:
        next_page = str(page + 1)
        items.insert(0, {'label': plugin.get_string(30020),
                         'path': plugin.url_for('bestof',
                                               page=next_page)})
    if page > 1:
        previous_page = str(page - 1)
        items.insert(0, {'label': plugin.get_string(30021),
                         'path': plugin.url_for('bestof',
                                               page=previous_page)})
    return plugin.finish(items, update_listing=(page != 1))


@plugin.route('/settings/')
def settings():
    """Open the addon settings"""
    plugin.open_settings()


@plugin.route('/labels/<label>/<page>/')
def show_programs(label, page):
    """Display the list of programs"""
    sortMethod = SORTMETHOD[plugin.get_setting('sortMethod', int)]
    programs = scraper.Programs('%sp=%s&orderby=%s' % (URL[label], page, sortMethod))
    entries = programs.get_programs()
    if plugin.get_setting('displayParts', bool):
        # Displayed programs are not playable
        # We will display all the parts
        items = [{'label': program['title'],
                  'path': plugin.url_for('get_program_parts',
                                        url=program['url'],
                                        name=program['title'],
                                        icon=program['thumb']),
                  'thumbnail': program['thumb'],
                 } for program in entries]
    else:
        # Displayed programs are playable
        # We will try to play the main (xvid) video
        items = [{'label': program['title'],
                  'path': plugin.url_for('play_program', url=program['url']),
                  'thumbnail': program['thumb'],
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
                         'path': plugin.url_for('show_programs',
                                               label=label,
                                               page=next_page)})
    if nav_items['previous']:
        previous_page = str(page - 1)
        items.insert(0, {'label': plugin.get_string(30021),
                         'path': plugin.url_for('show_programs',
                                               label=label,
                                               page=previous_page)})
    return plugin.finish(items, update_listing=(page != 1))


@plugin.route('/program/<url>', name='play_program', options={'mode': 'play'})
@plugin.route('/download_program/<url>', name='download_program', options={'mode': 'download'})
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
    if plugin.get_setting('downloadMode', bool):
        # Ask for the path
        download_path = xbmcgui.Dialog().browse(3, plugin.get_string(30090), 'video')
    else:
        download_path = plugin.get_setting('downloadPath', unicode)
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
                  'path': plugin.url_for('play_video', url=part['url']),
                  'thumbnail': part['thumb'],
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
              'path': plugin.url_for('play_video_id', video_id=part['video_id']),
              'thumbnail': part['thumb'],
              'is_playable': True,
              'context_menu': [(plugin.get_string(30180),
                                'XBMC.RunPlugin(%s)' %
                                    plugin.url_for('download_video_id',
                                                    video_id=part['video_id']))],
             } for part in parts]
    return plugin.finish(main_item + items)


@plugin.route('/play_video_id/<video_id>', name='play_video_id', options={'mode': 'play'})
@plugin.route('/download_video_id/<video_id>', name='download_video_id', options={'mode': 'download'})
def get_video_by_id(video_id, mode):
    """Play or download the dailymotion video"""
    streams = deque(STREAMS)
    # Order the streams depending on the quality chosen
    streams.rotate(plugin.get_setting('quality', int) * -1)
    video = scraper.get_video_by_id(video_id, streams)
    if mode == 'play':
        return plugin.set_resolved_url(video['url'])
    elif mode == 'download':
        download_video(video['url'], video['title'])


if __name__ == '__main__':
    plugin.run()

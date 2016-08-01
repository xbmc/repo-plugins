import re
import urllib
from config import config
import requests
from bs4 import BeautifulSoup
from xbmcswift2 import actions


class API(object):
    def __init__(self, plugin):
        self.plugin = plugin

    def get_modes(self):
        """
        Get modes
        :return: ListItem objects array
        """
        return self.plugin.finish([
            {
                'label': self.plugin.get_string(30013),
                'icon': 'DefaultPlaylist.png',
                'path': self.plugin.url_for('show_favorites'),
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                    'artist_description': ''
                }
            },
            {
                'label': self.plugin.get_string(30010),
                'icon': 'DefaultMusicGenres.png',
                'path': self.plugin.url_for('show_categories', mode='by_type'),
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                    'artist_description': ''
                }
            },
            {
                'label': self.plugin.get_string(30011),
                'icon': 'DefaultAddonLanguage.png',
                'path': self.plugin.url_for('show_categories', mode='by_location'),
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                    'artist_description': ''
                }
            },
            {
                'label': self.plugin.get_string(30012),
                'icon': 'DefaultAddonSubtitles.png',
                'path': self.plugin.url_for('show_subcategories', mode='by_language', category='All Languages'),
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                    'artist_description': ''
                }
            },
            # {
            #     'label': self.plugin.get_string(30014),
            #     'icon': 'DefaultMusicTop100.png',
            #     'path': self.plugin.url_for('show_editors_choice'),
            #     'properties': {
            #         'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
            #         'artist_description': ''
            #     }
            # },
            {
                'label': self.plugin.get_string(30015),
                'icon': 'DefaultMusicSongs.png',
                'path': self.plugin.url_for('show_search'),
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                    'artist_description': ''
                }
            }
        ])

    def get_categories(self, mode):
        """
        Get mode's categories
        :param mode:
        :return:
        """
        switcher = {
            'by_type': [
                {
                    'label': self.plugin.get_string(30020),
                    'icon': 'DefaultMusicGenres.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_type', category='Music'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30021),
                    'icon': 'DefaultMusicGenres.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_type', category='Talk'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                # {
                #     'label': self.plugin.get_string(30022),
                #     'icon': 'DefaultMusicGenres.png',
                #     'path': self.plugin.url_for('show_subcategories', mode='by_type', category='Television'),
                #     'properties': {
                #         'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                #         'artist_description': ''
                #     }
                # },
                # {
                #     'label': self.plugin.get_string(30023),
                #     'icon': 'DefaultMusicGenres.png',
                #     'path': self.plugin.url_for('show_subcategories', mode='by_type', category='Webcam'),
                #     'properties': {
                #         'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                #         'artist_description': ''
                #     }
                # }
            ],
            'by_language': [],
            'by_location': [
                {
                    'label': self.plugin.get_string(30030),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Africa'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30031),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Asia'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30032),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Caribbean'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30033),
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Central America'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30034),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Europe'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30035),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Internet Only'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30036),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Middle East'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30037),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='North America'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30038),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='United States'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30039),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='Oceania'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                },
                {
                    'label': self.plugin.get_string(30040),
                    'icon': 'DefaultAddonLanguage.png',
                    'path': self.plugin.url_for('show_subcategories', mode='by_location', category='South America'),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': ''
                    }
                }
            ]
        }
        return switcher.get(mode, [])

    def get_subcategories(self, mode, category):
        """
        Get category's items
        :param mode:
        :param category:
        :return:
        """
        r = requests.get(config['endpoints'][mode])
        items = []

        if r.status_code == 200:
            soup = BeautifulSoup(r.content, 'html5lib')
            links = soup.find('img', src='../../images/{0}.gif'.format(category)).parent.parent.find_next(
                'tr').find_all('a')
            for item in links:
                matches = re.search('^([\w\-&()., ]+) \((\d+)\)$', item.get_text())
                items.append({
                    'label': matches.group(1),
                    'icon': config['icons'][mode],
                    'path': self.plugin.url_for('show_items', mode=mode, category=category, index='1',
                                                link=item.get('href')),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart'),
                        'artist_description': u'[B]{0}[/B][CR]{1} {2}'.format(matches.group(1), matches.group(2),
                                                                              self.plugin.get_string(30100))
                    }
                })

        return sorted(items, key=lambda item: item['label'])

    def get_editors_choice(self):
        return [
            {
                'label': '1.fm Blues',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u22140.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            },
            {
                'label': '181.fm - True Blues',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u30939.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            },
            {
                'label': 'Eco 99 FM',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u78391.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            },
            {
                'label': '1.fm Absolute TOP 40',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u22148.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            },
            {
                'label': 'Antenne Bayern - Oldies but Goldies',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u25747.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            },
            {
                'label': 'Dinner Jazz Excursion Radio',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u26889.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            },
            {
                'label': 'The Voice of Peace',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u31145.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            },
            {
                'label': 'BBC Radio 6 Music',
                'icon': config['icons']['by_editor'],
                'path': 'http://www.vtuner.com/vtunerweb/mms/m3u26128.m3u',
                'is_playable': True,
                'properties': {
                    'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                }
            }
        ]

    def get_items(self, mode, category, link, index):
        """
        Get sub-category's items
        :param mode:
        :param category:
        :param link:
        :param index:
        :return:
        """
        items = []
        if 'Startpage.asp' in link:
            full_link = '{0}/BrowsePremiumStations.asp?{1}&sWhatList=ALL&sSortby=AA&iCurrPage=' \
                .format(config['endpoints']['base_url'],
                        urllib.unquote(link.replace('../BrowseStations/Startpage.asp?', '')).decode('utf8'))
        else:
            full_link = '{0}/BrowsePremiumStations.asp?{1}&sWhatList=ALL&sSortby=AA&iCurrPage=' \
                .format(config['endpoints']['base_url'],
                        urllib.unquote(link.replace('../BrowseStations/BrowsePremiumStations.asp?', '')).decode('utf8'))
        r = requests.get(full_link + index)
        if r.status_code == 200:
            # Add link to previous page:
            if int(index) > 2:
                items.append({
                    'label': self.plugin.get_string(30101),
                    'icon': 'DefaultFolder.png',
                    'path': self.plugin.url_for('show_items', mode=mode, category=category, index='1', link=link),
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                    }
                })
            # Add stations links:
            soup = BeautifulSoup(r.content, 'html.parser')
            links = soup.select('td > a[href*="dynampls.asp"]')
            for item in links:
                if 'Calm Radio' not in item.get_text():
                    station_id = re.search('id=(\d+)$', item.get('href')).group(1)
                    items.append({
                        'label': item.get_text(),
                        'icon': config['icons'][mode],
                        'path': 'http://www.vtuner.com/vtunerweb/mms/m3u{0}.m3u'.format(station_id),
                        'is_playable': True,
                        'context_menu': [
                            self.make_favorite_ctx(item.get_text().encode('utf-8'), station_id),
                        ],
                        'properties': {
                            'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                        },
                        'info': {
                            'Title': item.get_text(),
                            'Artist': [self.plugin.get_string(30000)]
                        }
                    })
            # Add link to next page:
            if len(links) > 0:
                if soup.find('img', src='../../images/next.jpg'):
                    items.append({
                        'label': self.plugin.get_string(30102),
                        'icon': 'DefaultFolder.png',
                        'path': self.plugin.url_for('show_items', mode=mode, category=category,
                                                    index=str(int(index) + 1), link=link),
                        'properties': {
                            'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                        }
                    })
        return items

    def search_items(self, query, index='1'):
        """
        Get sub-category's items
        :param query:
        :param index:
        :return:
        """
        items = []
        full_link = '{0}{1}'.format(config['endpoints']['base_url'],
                                    config['endpoints']['search_items'].format(query))

        r = requests.get(full_link + index)
        if r.status_code == 200:
            # Add link to previous page:
            if int(index) > 2:
                items.append({
                    'label': self.plugin.get_string(30101),
                    'path': self.plugin.url_for('show_search_results', query=query, index='1')
                })
            # Add stations links:
            soup = BeautifulSoup(r.content, 'html.parser')
            links = soup.select('td > a[href*="dynampls.asp"]')
            for item in links:
                if 'Calm Radio' not in item.get_text():
                    station_id = re.search('id=(\d+)$', item.get('href')).group(1)
                    items.append({
                        'label': item.get_text(),
                        'icon': config['icons']['by_search'],
                        'path': 'http://www.vtuner.com/vtunerweb/mms/m3u{0}.m3u'.format(station_id),
                        'is_playable': True,
                        'context_menu': [
                            self.make_favorite_ctx(item.get_text().encode('utf-8'), station_id),
                        ],
                        'properties': {
                            'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                        },
                        'info': {
                            'Title': item.get_text(),
                            'Artist': [self.plugin.get_string(30000)]
                        }
                    })
            # Add link to next page:
            if len(links) > 0:
                if soup.find('img', src='../../images/next.jpg'):
                    items.append({
                        'label': self.plugin.get_string(30102),
                        'path': self.plugin.url_for('show_search_results', query=query, index=str(int(index) + 1))
                    })
        return items

    def get_favorites(self):
        """
        Get user;s favorites stations
        :return: ListItem objects array
        """
        favorites = self.plugin.get_storage('favorites')
        return [{
                    'label': item[1]['title'],
                    'icon': config['icons']['by_favorites'],
                    'path': 'http://www.vtuner.com/vtunerweb/mms/m3u{0}.m3u'.format(str(item[1]['station_id'])),
                    'is_playable': True,
                    'context_menu': [
                        self.make_unfavorite_ctx(item[1]['station_id']),
                    ],
                    'properties': {
                        'fanart_image': self.plugin.addon.getAddonInfo('fanart')
                    },
                    'info': {
                        'Title': item[1]['title'],
                        'Artist': [self.plugin.get_string(30000)]
                    }
                } for item in favorites.items()]

    def add_favorite(self, title, station_id):
        """
        Adds a stations to user's stations list
        :param title:
        :param station_id:
        :return:
        """
        favorites = self.plugin.get_storage('favorites')
        if not favorites.get(station_id):
            favorites[station_id] = {
                'title': title,
                'station_id': station_id
            }
            return True
        return False

    def remove_favorite(self, station_id):
        """
        Removes a stations from user's stations list
        :param station_id:
        :return:
        """
        favorites = self.plugin.get_storage('favorites')
        if favorites.get(station_id):
            favorites.pop(station_id)
            return True
        return False

    def make_favorite_ctx(self, title, station_id):
        """
        Returns action url to Add to Favorites
        :param title:
        :param station_id:
        :return:
        """
        label = self.plugin.get_string(30120)
        new_url = self.plugin.url_for('add_to_favorites', title=title, station_id=station_id)
        return label, actions.background(new_url)

    def make_unfavorite_ctx(self, station_id):
        """
        Returns action url to Remove from Favorites
        :param station_id:
        :return:
        """
        label = self.plugin.get_string(30121)
        new_url = self.plugin.url_for('remove_from_favorites', station_id=station_id)
        return (label, actions.update_view(new_url))

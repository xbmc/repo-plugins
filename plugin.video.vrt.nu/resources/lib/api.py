# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements VRT MAX GraphQL API functionality"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.parse import quote_plus
except ImportError:  # Python 2
    from urllib import quote_plus

from helperobjects import TitleItem
from kodiutils import (colour, get_cache, get_setting_bool, get_setting_int, get_url_json, has_credentials,
                       localize, localize_from_data, log, update_cache, url_for)
from utils import find_entry, from_unicode, reformat_image_url, shorten_link, to_unicode, url_to_program
from graphql_data import EPISODE_TILE

GRAPHQL_URL = 'https://www.vrt.be/vrtnu-api/graphql/v1'
RESUMEPOINTS_URL = 'https://ddt.profiel.vrt.be/resumePoints'
RESUMEPOINTS_MARGIN = 30  # The margin at start/end to consider a video as watched


def get_sort(program_type):
    """Get sorting method"""
    sort = 'unsorted'
    ascending = True
    if program_type in ('mixed_episodes', 'daily'):
        sort = 'dateadded'
        ascending = False
    elif program_type == 'oneoff':
        sort = 'label'
    elif program_type in 'reeksoplopend':
        sort = 'episode'
    elif program_type == 'reeksaflopend':
        sort = 'episode'
        ascending = False
    return sort, ascending


def get_context_menu(program_name, program_id, program_title, program_type, is_favorite, is_continue=False, episode_id=None):
    """Get context menu for listitem"""
    from addon import plugin
    plugin_path = plugin.path
    context_menu = []

    # Follow/unfollow
    follow_suffix = localize(30410) if program_type != 'oneoff' else ''  # program
    encoded_program_title = to_unicode(quote_plus(from_unicode(program_title)))  # We need to ensure forward slashes are quoted
    if is_favorite:
        extras = {}
        # If we are in a favorites menu, move cursor down before removing a favorite
        if plugin_path.startswith('/favorites'):
            extras = {'move_down': True}
        context_menu.append((
            localize(30412, title=follow_suffix),  # Unfollow
            'RunPlugin(%s)' % url_for('unfollow', program_name=program_name, title=encoded_program_title, program_id=program_id, **extras)
        ))
    else:
        context_menu.append((
            localize(30411, title=follow_suffix),  # Follow
            'RunPlugin(%s)' % url_for('follow', program_name=program_name, title=encoded_program_title, program_id=program_id)
        ))

    # Go to program
    if program_type != 'oneoff':
        if plugin_path.startswith(('/favorites/offline', '/favorites/recent', '/offline', '/recent',
                                   '/resumepoints/continue', '/tvguide')):
            context_menu.append((
                localize(30417),  # Go to program
                'Container.Update(%s)' % url_for('programs', program_name=program_name)
            ))

    # Delete continue
    if is_continue:
        context_menu.append((
            localize(30455),  # Delete from this list
            'RunPlugin(%s)' % url_for('resumepoints_continue_delete', episode_id=episode_id)
        ))
    return context_menu


def format_label(program_title, episode_title, program_type, ontime=None, is_favorite=False, item_type='episode'):
    """Format label"""
    if item_type == 'program' or program_type == 'oneoff':
        label = program_title
    elif program_type == 'mixed_episodes':
        label = '[B]{}[/B] - {}'.format(program_title, episode_title)
    elif program_type == 'daily':
        label = '{} - {}'.format(ontime.strftime('%d/%m'), episode_title)
    else:
        label = episode_title

    # Favorite marker
    if is_favorite:
        label += colour('[COLOR={highlighted}]ᵛ[/COLOR]')

    return label


def format_plot(plot, region, product_placement, mpaa, offtime, permalink):
    """Format plot"""
    from datetime import datetime
    import dateutil.tz

    # Add additional metadata to plot
    plot_meta = ''
    # Only display when a video disappears if it is within the next 3 months
    # Show the remaining days/hours the episode is still available
    if offtime:
        now = datetime.now(dateutil.tz.tzlocal())
        remaining = offtime - now
        if remaining.days / 365 > 5:
            pass  # If it is available for more than 5 years, do not show
        elif remaining.days / 365 > 2:
            plot_meta += localize(30202, years=int(remaining.days / 365))  # X years remaining
        elif remaining.days / 30.5 > 3:
            plot_meta += localize(30203, months=int(remaining.days / 30.5))  # X months remaining
        elif remaining.days > 1:
            plot_meta += localize(30204, days=remaining.days)  # X days to go
        elif remaining.days == 1:
            plot_meta += localize(30205)  # 1 day to go
        elif remaining.seconds // 3600 > 1:
            plot_meta += localize(30206, hours=remaining.seconds // 3600)  # X hours to go
        elif remaining.seconds // 3600 == 1:
            plot_meta += localize(30207)  # 1 hour to go
        else:
            plot_meta += localize(30208, minutes=remaining.seconds // 60)  # X minutes to go

    if region == 'BE':
        if plot_meta:
            plot_meta += '  '
        plot_meta += localize(30201)  # Geo-blocked

    # Add product placement
    if product_placement is True:
        if plot_meta:
            plot_meta += '  '
        plot_meta += '[B]PP[/B]'

    # Add film rating
    if mpaa:
        if plot_meta:
            plot_meta += '  '
        plot_meta += '[B]{}[/B]'.format(mpaa)

    if plot_meta:
        plot = '{}\n\n{}'.format(plot_meta, plot)

    permalink = shorten_link(permalink)
    if permalink and get_setting_bool('showpermalink', default=False):
        plot = '{}\n\n[COLOR={{highlighted}}]{}[/COLOR]'.format(plot, permalink)
    return colour(plot)


def resumepoints_is_activated():
    """Is resumepoints activated in the menu and do we have credentials ?"""
    return get_setting_bool('usefavorites', default=True) and get_setting_bool('useresumepoints', default=True) and has_credentials()


def get_resumepoint_data(episode_id):
    """Get resumepoint data from GraphQL API"""
    data_json = get_single_episode_data(episode_id)
    video_id = data_json.get('data').get('catalogMember').get('watchAction').get('videoId')
    resumepoint_title = data_json.get('data').get('catalogMember').get('watchAction').get('resumePointTitle')
    return video_id, resumepoint_title


def get_next_info(episode_id):
    """ Get up next data"""
    import dateutil.parser
    next_info = {}
    data_json = get_single_episode_data(episode_id)
    current_ep = data_json.get('data').get('catalogMember')
    # Only get add data when there is a next episode
    if current_ep.get('nextUp').get('title') == 'Volgende aflevering':
        next_ep = current_ep.get('nextUp').get('tile').get('episode')

        current_episode = {
            'episodeid': current_ep.get('id'),
            'tvshowid': current_ep.get('program').get('id'),
            'title': current_ep.get('title'),
            'art': {
                'tvshow.poster': reformat_image_url(current_ep.get('program').get('posterImage').get('templateUrl')),
                'thumb': reformat_image_url(current_ep.get('image').get('templateUrl')),
                'tvshow.fanart': reformat_image_url(current_ep.get('program').get('image').get('templateUrl')),
                'tvshow.landscape': reformat_image_url(current_ep.get('image').get('templateUrl')),
                'tvshow.clearart': None,
                'tvshow.clearlogo': None,
            },
            'plot': current_ep.get('description'),
            'showtitle': current_ep.get('program').get('title'),
            'playcount': None,
            'season': int(''.join(i for i in current_ep.get('season').get('titleRaw') if i.isdigit()) or 0),
            'episode': int(current_ep.get('episodeNumberRaw') or 0),
            'rating': None,
            'firstaired': dateutil.parser.parse(current_ep.get('analytics').get('airDate')).strftime('%Y-%m-%d'),
            'runtime': int(current_ep.get('durationSeconds')),
        }

        next_episode = {
            'episodeid': next_ep.get('id'),
            'tvshowid': next_ep.get('program').get('id'),
            'title': next_ep.get('title'),
            'art': {
                'tvshow.poster': reformat_image_url(next_ep.get('program').get('posterImage').get('templateUrl')),
                'thumb': reformat_image_url(next_ep.get('image').get('templateUrl')),
                'tvshow.fanart': reformat_image_url(next_ep.get('program').get('image').get('templateUrl')),
                'tvshow.landscape': reformat_image_url(next_ep.get('image').get('templateUrl')),
                'tvshow.clearart': None,
                'tvshow.clearlogo': None,
            },
            'plot': next_ep.get('description'),
            'showtitle': next_ep.get('program').get('title'),
            'playcount': None,
            'season': int(''.join(i for i in next_ep.get('season').get('titleRaw') if i.isdigit()) or 0),
            'episode': int(next_ep.get('episodeNumberRaw') or 0),
            'rating': None,
            'firstaired': dateutil.parser.parse(next_ep.get('analytics').get('airDate')).strftime('%Y-%m-%d'),
            'runtime': int(next_ep.get('durationSeconds')),
        }
        next_info = {
            'current_episode': current_episode,
            'next_episode': next_episode,
            'play_info': {
                'episode_id': next_ep.get('id'),
            }
        }
    return next_info


def get_stream_id_data(vrtmax_url):
    """Get stream_id from from GraphQL API"""
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
        }
        page_id = vrtmax_url.split('www.vrt.be')[1].replace('/vrtmax/', '/vrtnu/').rstrip('/') + '.model.json'
        graphql_query = """
             query StreamId($pageId: ID!) {
              page(id: $pageId) {
                ... on IPage {
                  ... on LivestreamPage {
                    player {
                      watchAction {
                        ... on LiveWatchAction {
                          streamId
                        }
                      }
                    }
                  }
                }
                ... on EpisodePage {
                  episode {
                    watchAction {
                      streamId
                    }
                  }
                }
              }
            }
        """
        payload = {
            'operationName': 'StreamId',
            'variables': {
                'pageId': page_id
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def get_single_episode_data(episode_id):
    """Get single episode data from GraphQL API"""
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
        }
        graphql_query = """
            query PlayerData($id: ID!) {
              catalogMember(id: $id) {
                __typename
              ...episode
              }
            }
            fragment episode on Episode {
              __typename
              id
              title
              description
              episodeNumberRaw
              durationSeconds
              offTimeRaw
              onTimeRaw
              image {
                alt
                templateUrl
              }
              analytics {
                airDate
                categories
              }
              program {
                id
                title
                link
                programType
                image {
                  alt
                  templateUrl
                }
                posterImage {
                  alt
                  templateUrl
                }
              }
              season {
                titleRaw
              }
              watchAction {
                avodUrl
                completed
                resumePoint
                resumePointTotal
                resumePointProgress
                resumePointTitle
                episodeId
                videoId
                publicationId
                streamId
              }
              favoriteAction {
                favorite
                id
                title
              }
              nextUp {
                title
                autoPlay
                countdown
                tile {
                  __typename
                  ...episodeTile
                }
              }
            }
            %s
        """ % EPISODE_TILE
        payload = {
            'operationName': 'PlayerData',
            'variables': {
                'id': episode_id,
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def get_latest_episode_data(program_name):
    """Get latest episode data from GraphQL API"""
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
        }
        graphql_query = """
            query VideoProgramPage($pageId: ID!, $lazyItemCount: Int = 500, $after: ID) {
              page(id: $pageId) {
                ... on ProgramPage {
                  components {
                    __typename
                    ... on PageHeader {
                      mostRelevantEpisodeTile {
                        __typename
                        title
                        tile {
                          ...episodeTile
                          __typename
                        }
                        __typename
                      }
                      __typename
                    }
                    ... on ContainerNavigation {
                      items {
                        title
                        components {
                          __typename
                          ... on PaginatedTileList {
                            __typename
                            paginatedItems(first: $lazyItemCount, after: $after) {
                              __typename
                              edges {
                                __typename
                                cursor
                                node {
                                  __typename
                                  ... on EpisodeTile {
                                    id
                                    description
                                    ...episodeTile
                                  }
                                }
                              }
                            }
                          }
                          ... on ContainerNavigation {
                            items {
                              title
                              components {
                                __typename
                                ... on PaginatedTileList {
                                  __typename
                                  paginatedItems(first: $lazyItemCount, after: $after) {
                                    __typename
                                    edges {
                                      __typename
                                      cursor
                                      node {
                                        __typename
                                        ... on EpisodeTile {
                                          id
                                          description
                                          ...episodeTile
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                            __typename
                          }
                        }
                        __typename
                      }
                      __typename
                    }
                  }
                  __typename
                }
                __typename
              }
            }
            %s
        """ % EPISODE_TILE
        payload = {
            'operationName': 'VideoProgramPage',
            'variables': {
                'pageId': '/vrtnu/a-z/{}.model.json'.format(program_name),
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def get_seasons_data(program_name):
    """Get seasons data from GraphQL API"""
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
        }
        graphql_query = """
            query VideoProgramPage(
              $pageId: ID!) {
              page(id: $pageId) {
                ... on ProgramPage {
                  id
                  permalink
                  components {
                    __typename
                    ... on PageHeader {
                      mostRelevantEpisodeTile {
                        __typename
                        title
                        tile {
                          ...episodeTile
                          __typename
                        }
                        __typename
                      }
                      __typename
                    }
                    ... on PaginatedTileList {
                      __typename
                      id: objectId
                      objectId
                      listId
                      title
                      tileContentType
                    }
                    ... on ContainerNavigation {
                      id: objectId
                      navigationType
                      items {
                        id: objectId
                        title
                        active
                        components {
                          __typename
                          ... on PaginatedTileList {
                            __typename
                            id: objectId
                            objectId
                            listId
                            title
                            tileContentType
                          }
                          ... on StaticTileList {
                            __typename
                            id: objectId
                            objectId
                            listId
                            title
                            tileContentType
                          }
                          ... on LazyTileList {
                            __typename
                            id: objectId
                            objectId
                            listId
                            title
                            tileContentType
                          }
                          ... on IComponent {
                            ... on ContainerNavigation {
                              id: objectId
                              navigationType
                              items {
                                id: objectId
                                title
                                components {
                                  __typename
                                  ... on Component {
                                    ... on PaginatedTileList {
                                      __typename
                                      id: objectId
                                      objectId
                                      listId
                                      title
                                      tileContentType
                                    }
                                    ... on StaticTileList {
                                      __typename
                                      id: objectId
                                      objectId
                                      listId
                                      title
                                      tileContentType
                                    }
                                    ... on LazyTileList {
                                      __typename
                                      id: objectId
                                      objectId
                                      listId
                                      title
                                      tileContentType
                                    }
                                    __typename
                                  }
                                }
                                __typename
                              }
                              __typename
                            }
                            __typename
                          }
                        }
                        __typename
                      }
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }
            }
            %s
        """ % EPISODE_TILE
        payload = {
            'operationName': 'VideoProgramPage',
            'variables': {
                'pageId': '/vrtnu/a-z/{}.model.json'.format(program_name),
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def set_resumepoint(video_id, title, position, total):
    """Set resumepoint"""
    # Respect resumepoint margins
    if position and total:
        if position < RESUMEPOINTS_MARGIN:
            position = 0
        if position > total - RESUMEPOINTS_MARGIN:
            position = total

    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    if access_token:
        gdpr = '{} gekeken tot {} seconden.'.format(title, position)
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
        }
        payload = {
            'at': position,
            'total': total,
            'gdpr': gdpr,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url='{}/{}'.format(RESUMEPOINTS_URL, video_id), cache=None, headers=headers, data=data, raise_errors='all')
        log(3, '[Resumepoints] Updated resumepoint {data}', data=data_json)


def get_paginated_episodes(list_id, page_size, end_cursor=''):
    """Get paginated list of episodes from GraphQL API"""
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
        }
        graphql_query = """
            query ListedEpisodes(
              $listId: ID!
              $endCursor: ID!
              $pageSize: Int!
            ) {
              list(listId: $listId) {
                __typename
                ... on PaginatedTileList {
                  paginated: paginatedItems(first: $pageSize, after: $endCursor) {
                    edges {
                      node {
                        __typename
                        ...episodeTile
                      }
                    }
                    pageInfo {
                      startCursor
                      endCursor
                      hasNextPage
                      hasPreviousPage
                      __typename
                    }
                  }
                }
              }
            }
            %s
        """ % EPISODE_TILE
        # FIXME: Find a better way to change GraphQL typename
        if list_id.startswith('static:/'):
            graphql_query = graphql_query.replace('on PaginatedTileList', 'on StaticTileList')

        payload = {
            'operationName': 'ListedEpisodes',
            'variables': {
                'listId': list_id,
                'endCursor': end_cursor,
                'pageSize': page_size,
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def get_paginated_programs(list_id, page_size, end_cursor=''):
    """Get paginated list of episodes from GraphQL API"""
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
            'x-vrt-client-name': 'MobileAndroid',
        }
        graphql_query = """
            query PaginatedPrograms(
              $listId: ID!
              $endCursor: ID!
              $pageSize: Int!
            ) {
              list(listId: $listId) {
                __typename
                ... on PaginatedTileList {
                  paginated: paginatedItems(first: $pageSize, after: $endCursor) {
                    edges {
                      node {
                        __typename
                        ...ep
                      }
                    }
                    pageInfo {
                      startCursor
                      endCursor
                      hasNextPage
                      hasPreviousPage
                      __typename
                    }
                  }
                }
              }
            }
            fragment ep on ProgramTile {
              __typename
              objectId
              id
              link
              tileType
              image {
                alt
                templateUrl
              }
              title
              program {
                title
                id
                link
                programType
                description
                shortDescription
                subtitle
                announcementType
                announcementValue
                whatsonId
                image {
                  alt
                  templateUrl
                }
                posterImage {
                  alt
                  templateUrl
                }
                favoriteAction {
                  favorite
                  id
                  title
                }
              }
            }
        """
        # FIXME: Find a better way to change GraphQL typename
        if list_id.startswith('static:/'):
            graphql_query = graphql_query.replace('on PaginatedTileList', 'on StaticTileList')

        payload = {
            'operationName': 'PaginatedPrograms',
            'variables': {
                'listId': list_id,
                'endCursor': end_cursor,
                'pageSize': page_size,
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def convert_programs(api_data, destination, use_favorites=False, **kwargs):
    """Convert paginated list of programs to Kodi list items"""

    programs = []

    item_list = api_data.get('data').get('list')
    if item_list:
        for item in item_list.get('paginated').get('edges'):
            program = item.get('node')

            program_name = url_to_program(program.get('link'))
            program_id = program.get('id')
            program_type = program.get('programType')
            program_title = program.get('title')
            episode_title = None
            ontime = None
            path = url_for('programs', program_name=program_name)
            plot = program.get('program').get('shortDescription') or program.get('program').get('description')
            plotoutline = program.get('subtitle')

            # Art
            fanart = ''
            poster_img = program.get('program').get('posterImage')
            if poster_img:
                fanart = reformat_image_url(poster_img.get('templateUrl'))
            poster = fanart
            thumb = ''
            thumb_img = program.get('image')
            if thumb_img:
                thumb = reformat_image_url(thumb_img.get('templateUrl'))

            # Check favorite
            is_favorite = program.get('program').get('favoriteAction').get('favorite')

            # Filter favorites for favorites menu
            if use_favorites and is_favorite is False:
                continue

            # Context menu
            context_menu = get_context_menu(program_name, program_id, program_title, program_type, is_favorite)

            # Label
            label = format_label(program_title, episode_title, program_type, ontime, is_favorite, item_type='program')

            programs.append(
                TitleItem(
                    label=label,
                    path=path,
                    art_dict={
                        'thumb': thumb,
                        'poster': poster,
                        'banner': fanart,
                        'fanart': fanart,
                    },
                    info_dict={
                        'title': label,
                        'tvshowtitle': program_title,
                        'plot': plot,
                        'plotoutline': plotoutline,
                        'mediatype': 'tvshow',
                    },
                    context_menu=context_menu,
                    is_playable=False,
                )
            )

        # Paging
        # Remove kwargs with None value
        kwargs = {k: v for k, v in list(kwargs.items()) if v is not None}
        page_info = api_data.get('data').get('list').get('paginated').get('pageInfo')

        # FIXME: find a better way to disable more when favorites are filtered
        page_size = get_setting_int('itemsperpage', default=50)
        if len(programs) == page_size and page_info.get('hasNextPage'):
            end_cursor = page_info.get('endCursor')
            # Add 'More...' entry at the end
            programs.append(
                TitleItem(
                    label=colour(localize(30300)),
                    path=url_for(destination, end_cursor=end_cursor, **kwargs),
                    art_dict={'thumb': 'DefaultInProgressShows.png'},
                    info_dict={},
                )
            )
    return programs


def convert_episode(item, destination=None):
    """Convert paginated episode item to TitleItem"""
    import dateutil.parser
    data = item.get('node') or item.get('data') or item.get('tile')
    episode = data.get('episode') or data.get('catalogMember')
    # FIXME: find a better way to abort when we have no valid api data
    if not episode:
        return None, None, None, None
    episode_id = episode.get('id')
    video_id = episode.get('watchAction').get('videoId')
    publication_id = episode.get('watchAction').get('publicationId')
    path = url_for('play_id', video_id=video_id, publication_id=publication_id, episode_id=episode_id)
    program_name = url_to_program(episode.get('program').get('link'))
    program_id = episode.get('program').get('id')
    program_title = episode.get('program').get('title')
    program_type = episode.get('program').get('programType')

    # FIXME: Find a better way to determine mixed episodes
    if destination in ('recent', 'favorites_recent', 'resumepoints_continue', 'featured'):
        program_type = 'mixed_episodes'

    episode_title = episode.get('title')
    offtime = dateutil.parser.parse(episode.get('offTimeRaw'))
    ontime = dateutil.parser.parse(episode.get('onTimeRaw'))
    mpaa = episode.get('ageRaw') or ''
    product_placement = episode.get('productPlacementShortValue') == 'pp'
    region = episode.get('regionRaw')
    permalink = episode.get('permalink')
    plot = episode.get('description')
    plot = format_plot(plot, region, product_placement, mpaa, offtime, permalink)
    plotoutline = episode.get('program').get('subtitle')
    duration = int(episode.get('durationSeconds'))
    episode_no = int(episode.get('episodeNumberRaw') or 0)
    season_no = int(''.join(i for i in episode.get('season').get('titleRaw') if i.isdigit()) or 0)
    studio = episode.get('brand').title() if episode.get('brand') else 'VRT'
    aired = dateutil.parser.parse(episode.get('analytics').get('airDate')).strftime('%Y-%m-%d')
    dateadded = ontime.strftime('%Y-%m-%d %H:%M:%S')
    year = int(dateutil.parser.parse(episode.get('onTimeRaw')).strftime('%Y'))
    tag = [tag.title() for tag in episode.get('analytics').get('categories').split(',') if tag]

    # Art
    fanart = ''
    fanart_img = episode.get('program').get('image')
    if fanart_img:
        fanart = reformat_image_url(fanart_img.get('templateUrl'))
    poster = ''
    poster_img = episode.get('program').get('posterImage')
    if poster_img:
        poster = reformat_image_url(poster_img.get('templateUrl'))
    thumb = ''
    thumb_img = episode.get('image')
    if thumb_img:
        thumb = reformat_image_url(thumb_img.get('templateUrl'))

    # Check favorite
    is_favorite = episode.get('favoriteAction').get('favorite')

    # Check continue
    is_continue = False
    if destination == 'resumepoints_continue':
        is_continue = True

    # Context menu
    context_menu = get_context_menu(program_name, program_id, program_title, program_type,
                                    is_favorite, is_continue, episode_id)

    # Label
    label = format_label(program_title, episode_title, program_type, ontime, is_favorite)

    # Sorting
    sort, ascending = get_sort(program_type)

    # Resumepoint
    position = episode.get('watchAction').get('resumePoint')
    total = episode.get('watchAction').get('resumePointTotal')
    prop_dict = {}
    playcount = -1

    if resumepoints_is_activated():
        # Override Kodi watch status
        if position and total:
            if RESUMEPOINTS_MARGIN < position < total - RESUMEPOINTS_MARGIN:
                prop_dict['resumetime'] = position
                prop_dict['totaltime'] = total
            if position > total - RESUMEPOINTS_MARGIN:
                playcount = 1

    return sort, ascending, is_favorite, TitleItem(
        label=label,
        path=path,
        art_dict={
            'thumb': thumb,
            'poster': poster,
            'banner': fanart,
            'fanart': fanart,
        },
        info_dict={
            'title': label,
            'tvshowtitle': program_title,
            'aired': aired,
            'dateadded': dateadded,
            'episode': episode_no,
            'season': season_no,
            'playcount': playcount,
            'plot': plot,
            'plotoutline': plotoutline,
            'mpaa': mpaa,
            'tagline': plotoutline,
            'duration': duration,
            'studio': studio,
            'year': year,
            'tag': tag,
            'mediatype': 'episode',
        },
        context_menu=context_menu,
        is_playable=True,
        prop_dict=prop_dict,
    )


def convert_episodes(api_data, destination, use_favorites=False, **kwargs):
    """Convert paginated episode list to TitleItems"""
    episodes = []
    sort = 'unsorted'
    ascending = True

    item_list = api_data.get('data').get('list')
    if item_list:
        for item in item_list.get('paginated').get('edges'):

            sort, ascending, is_favorite, title_item = convert_episode(item, destination)

            # Filter favorites for favorites menu
            if use_favorites and is_favorite is False:
                continue

            episodes.append(title_item)

        # Paging
        # Remove kwargs with None value
        kwargs = {k: v for k, v in list(kwargs.items()) if v is not None}
        page_info = api_data.get('data').get('list').get('paginated').get('pageInfo')

        # FIXME: find a better way to disable more when favorites are filtered
        page_size = get_setting_int('itemsperpage', default=50)
        if len(episodes) == page_size and page_info.get('hasNextPage'):
            end_cursor = page_info.get('endCursor')
            # Add 'More...' entry at the end
            episodes.append(
                TitleItem(
                    label=colour(localize(30300)),
                    path=url_for(destination, end_cursor=end_cursor, **kwargs),
                    art_dict={'thumb': 'DefaultInProgressShows.png'},
                    info_dict={},
                )
            )
    return episodes, sort, ascending


def get_single_episode(episode_id):
    """Get single episode"""
    api_data = get_single_episode_data(episode_id)
    _, _, _, title_item = convert_episode(api_data)
    return title_item


def get_latest_episode(program_name):
    """Get the latest episode of a program"""
    latest_episode = {}
    video = None
    api_data = get_latest_episode_data(program_name=program_name)
    page = api_data.get('data').get('page')
    if page:
        most_relevant_ep = page.get('components')[0].get('mostRelevantEpisodeTile')
        if most_relevant_ep.get('title') == 'Meest recente aflevering':
            latest_episode = most_relevant_ep
        else:
            items = page.get('components')[1].get('items')[0].get('components')[0]
            if not items.get('paginatedItems'):
                items = items.get('items')[0].get('components')[0]
            edges = items.get('paginatedItems').get('edges')
            highest_ep_no = 0
            highest_ep = {}
            for edge in edges:
                ep_no = int(edge.get('node').get('episode').get('episodeNumberRaw'))
                if ep_no > highest_ep_no:
                    highest_ep_no = ep_no
                    highest_ep = edge
            latest_episode = highest_ep

        _, _, _, title_item = convert_episode(latest_episode)
        video = {
            'listitem': title_item,
            'video_id': title_item.path.split('/')[5],
            'publication_id': title_item.path.split('/')[6],
        }
    return video


def get_favorite_programs(end_cursor=''):
    """Get favorite programs"""
    page_size = get_setting_int('itemsperpage', default=50)
    list_id = 'dynamic:/vrtnu.model.json@favorites-list-video'
    api_data = get_paginated_programs(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
    programs = convert_programs(api_data, destination='favorites_programs')
    return programs


def get_programs(category=None, channel=None, keywords=None, end_cursor=''):
    """Get programs"""
    import base64
    from json import dumps
    page_size = get_setting_int('itemsperpage', default=50)
    query_string = None
    if category:
        destination = 'categories'
        facets = [{
            'name': 'programCategories',
            'values': [category]
        }]
    elif channel:
        destination = 'channels'
        facets = [{
            'name': 'programBrands',
            'values': [channel]
        }]
    elif keywords:
        destination = 'search_query'
        facets = None
        query_string = keywords

    search_dict = {
        'queryString': query_string,
        'facets': facets,
        'resultType': 'watch',
    }
    encoded_search = base64.b64encode(dumps(search_dict).encode('utf-8'))
    list_id = 'uisearch:searchdata@{}'.format(encoded_search.decode('utf-8'))

    api_data = get_paginated_programs(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
    programs = convert_programs(api_data, destination=destination, category=category, channel=channel, keywords=keywords)
    return programs


def get_continue_episodes(end_cursor=''):
    """Get continue episodes"""
    page_size = get_setting_int('itemsperpage', default=50)
    list_id = 'dynamic:/vrtnu.model.json@resume-list-video'
    api_data = get_paginated_episodes(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
    episodes, sort, ascending = convert_episodes(api_data, destination='resumepoints_continue')
    return episodes, sort, ascending, 'episodes'


def get_recent_episodes(end_cursor='', use_favorites=False):
    """Get recent episodes"""
    page_size = get_setting_int('itemsperpage', default=50)
    list_id = 'static:/vrtnu/kijk.model.json@par_list_copy_copy_copy'
    api_data = get_paginated_episodes(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
    destination = 'favorites_recent' if use_favorites else 'recent'
    episodes, sort, ascending = convert_episodes(api_data, destination=destination, use_favorites=use_favorites)
    return episodes, sort, ascending, 'episodes'


def get_offline_programs(end_cursor='', use_favorites=False):
    """Get laatste kans/soon offline programs"""
    page_size = get_setting_int('itemsperpage', default=50)
    list_id = 'dynamic:/vrtnu.model.json@par_list_1624607593_copy_1408213323'
    api_data = get_paginated_programs(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
    destination = 'favorites_offline' if use_favorites else 'offline'
    programs = convert_programs(api_data, destination=destination, use_favorites=use_favorites)
    return programs


def get_episodes(program_name, season_name=None, end_cursor=''):
    """Get episodes"""
    sort = 'unsorted'
    ascending = True
    content = 'files'
    page_size = get_setting_int('itemsperpage', default=50)
    if season_name is None:
        # Check for multiple seasons
        api_data = get_seasons(program_name)
        number_of_seasons = len(api_data)
        if number_of_seasons == 1:
            season_name = api_data[0].get('name')
        elif number_of_seasons > 1:
            seasons = convert_seasons(api_data, program_name)
            return seasons, sort, ascending, content

    if program_name and season_name:
        if season_name.startswith('parsys'):
            list_id = 'static:/vrtnu/a-z/{}.model.json@{}'.format(program_name, season_name)
        else:
            list_id = 'static:/vrtnu/a-z/{}/{}.episodes-list.json'.format(program_name, season_name)
        api_data = get_paginated_episodes(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
        episodes, sort, ascending = convert_episodes(api_data, destination='programs', program_name=program_name, season_name=season_name)
        return episodes, sort, ascending, 'episodes'
    return None


def convert_seasons(api_data, program_name):
    """Convert seasons"""
    seasons = []
    for season in api_data:
        if season.get('name') == 'mostRelevantEpisode':
            _, _, _, title_item = convert_episode(season.get('episode'))
            title_item.label = '[B]{}:[/B] {}'.format(season.get('title'), title_item.label)
            title_item.info_dict['title'] = '[B]{}:[/B] {}'.format(season.get('title'), title_item.info_dict.get('title'))
            seasons.append(title_item)
        else:
            season_title = season.get('title')
            season_name = season.get('name')
            path = url_for('programs', program_name=program_name, season_name=season_name)
            seasons.append(
                TitleItem(
                    label=season_title,
                    path=path,
                    info_dict={
                        'title': season_title,
                        'mediatype': 'season',
                    },
                    is_playable=False,
                )
            )
    return seasons


def create_season_dict(data_json):
    """Create season dictionary"""
    season_dict = {}
    # title
    season_dict['title'] = data_json.get('title') or data_json.get('mostRelevantEpisodeTile').get('title')

    # list_id
    if data_json.get('components'):
        list_id = data_json.get('components')[0].get('listId')
    elif data_json.get('mostRelevantEpisodeTile'):
        list_id = 'mostRelevantEpisode'
        season_dict['episode'] = data_json.get('mostRelevantEpisodeTile')
    else:
        list_id = data_json.get('listId')

    # season name
    if '.episodes-list.json' in list_id:
        season_dict['name'] = list_id.split('.episodes-list.json')[0].split('/')[-1]
    else:
        season_dict['name'] = list_id.split('@')[-1]
    return season_dict


def get_seasons(program_name):
    """Get seasons"""
    seasons = []
    components = get_seasons_data(program_name).get('data').get('page').get('components')
    # Extract season data from components
    for component in components:
        # Check component type
        if component.get('navigationType') == 'bar':
            # Get items
            for item in component.get('items'):
                # Get components
                for nested_component in item.get('components'):
                    # Append component
                    components.append(nested_component)
        elif component.get('navigationType') == 'select':
            # Get items
            for item in component.get('items'):
                # Store season
                if item.get('title'):
                    seasons.append(create_season_dict(item))
        elif component.get('__typename') == 'PaginatedTileList' and component.get('tileContentType') == 'episode':
            # Store season
            if component.get('title'):
                seasons.append(create_season_dict(component))
        elif component.get('__typename') == 'PageHeader' and component.get('mostRelevantEpisodeTile'):
            seasons.append(create_season_dict(component))
    return seasons


def get_featured_data():
    """Get featured data"""
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
            'x-vrt-client-name': 'MobileAndroid',
        }
        graphql_query = """
            query Page(
              $pageId: ID!
              $lazyItemCount: Int = 10
              $after: ID
              $before: ID
              $componentCount: Int = 5
              $componentAfter: ID
            ) {
              page(id: $pageId) {
                ... on IPage {
                  title
                  permalink
                  paginatedComponents(first: $componentCount, after: $componentAfter) {
                    __typename
                    edges {
                      __typename
                      node {
                        ... on PaginatedTileList {
                          __typename
                          listId
                          componentType
                          paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
                            __typename
                            edges {
                              __typename
                              node {
                                __typename
                              }
                            }
                          }
                          tileContentType
                          title
                          __typename
                        }
                        ... on StaticTileList {
                          __typename
                          listId
                          title
                          header {
                            brand
                            ctaText
                            description
                          }
                          componentType
                          tileContentType
                        }
                        __typename
                      }
                    }
                  }
                }
              }
            }
        """
        payload = {
            'operationName': 'Page',
            'variables': {
                'pageId': '/vrtmax/',
                'pageContext': {
                    'mediaType': 'watch'
                },
                'componentAfter': '',
                'componentCount': 50,
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def get_featured(feature=None, end_cursor=''):
    """Get featured menu items"""
    content = 'files'
    sort = 'unsorted'
    ascending = True
    if feature:
        page_size = get_setting_int('itemsperpage', default=50)
        if feature.startswith('program_'):
            list_id = feature.replace('_proto_', ':/').split('program_')[1]
            api_data = get_paginated_programs(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
            programs = convert_programs(api_data, destination='featured', feature=feature)
            return programs, sort, ascending, 'tvshows'

        if feature.startswith('episode_'):
            list_id = feature.replace('_proto_', ':/').split('episode_')[1]
            api_data = get_paginated_episodes(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
            episodes, sort, ascending = convert_episodes(api_data, destination='featured', feature=feature)
            return episodes, sort, ascending, 'episodes'
    else:
        featured = []
        featured_json = get_featured_data()
        for edge in featured_json.get('data').get('page').get('paginatedComponents').get('edges'):
            node = edge.get('node')
            content_type = node.get('tileContentType')
            if content_type in ('program', 'episode'):
                title = node.get('title').strip() or node.get('header').get('description')
                feature_id = node.get('listId').replace(':/', '_proto_')
                featured.append(
                    TitleItem(
                        label=title,
                        path=url_for('featured', feature='{}_{}'.format(content_type, feature_id)),
                        art_dict={'thumb': 'DefaultCountry.png'},
                        info_dict={
                            'title': title,
                            'plot': '[B]%s[/B]' % title,
                            'studio': 'VRT',
                            'mediatype': 'season',
                        },
                        is_playable=False,
                    )
                )
    return featured, sort, ascending, content


def get_categories_data():
    """Return a list of categories"""
    cache_file = 'categories.json'

    # Try the cache if it is fresh
    categories = get_cache(cache_file, ttl=7 * 24 * 60 * 60)
    if valid_categories(categories):
        return categories

    # Try online categories json
    categories = get_online_categories()
    if valid_categories(categories):
        from json import dumps
        update_cache(cache_file, dumps(categories))
        return categories

    # Fall back to internal hard-coded categories
    from data import CATEGORIES
    log(2, 'Fall back to internal hard-coded categories')
    return CATEGORIES


def get_categories():
    """Get categories"""
    categories_data = get_categories_data()
    categories = []
    from data import CATEGORIES
    for category in localize_categories(categories_data, CATEGORIES):
        if get_setting_bool('showfanart', default=True):
            thumbnail = category.get('thumbnail', 'DefaultGenre.png')
        else:
            thumbnail = 'DefaultGenre.png'
        categories.append(TitleItem(
            label=category.get('name'),
            path=url_for('categories', category=category.get('id')),
            art_dict={'thumb': thumbnail, 'icon': 'DefaultGenre.png'},
            info_dict={'plot': '[B]%s[/B]' % category.get('name'), 'studio': 'VRT'},
        ))
    return categories


def get_online_categories():
    """Return a list of categories from the VRT MAX website"""
    categories = []
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    categories_json = {}
    if access_token:
        headers = {
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
            'x-vrt-client-name': 'MobileAndroid',
        }
        graphql_query = """
            query Search(
              $q: String
              $mediaType: MediaType
              $facets: [SearchFacetInput]
            ) {
              uiSearch(input: { q: $q, mediaType: $mediaType, facets: $facets }) {
                __typename
                ... on IIdentifiable {
                  objectId
                  __typename
                }
                ... on IComponent {
                  componentType
                  __typename
                }
                ...staticTileListFragment
              }
            }
            fragment staticTileListFragment on StaticTileList {
              __typename
              id: objectId
              objectId
              listId
              title
              componentType
              tileContentType
              tileOrientation
              displayType
              expires
              tileVariant
              sort {
                icon
                order
                title
                __typename
              }
              actionItems {
                ...actionItem
                __typename
              }
              header {
                action {
                  ...action
                  __typename
                }
                brand
                brandLogos {
                  height
                  mono
                  primary
                  type
                  width
                  __typename
                }
                ctaText
                description
                image {
                  ...imageFragment
                  __typename
                }
                type
                compactLayout
                backgroundColor
                textTheme
                __typename
              }
              bannerSize
              items {
                ...tileFragment
                __typename
              }
              ... on IComponent {
                __typename
              }
            }
            fragment tileFragment on Tile {
              ... on IIdentifiable {
                __typename
                objectId
              }
              ... on IComponent {
                title
                componentType
                __typename
              }
              ... on ITile {
                title
                action {
                  ...action
                  __typename
                }
                image {
                  ...imageFragment
                  __typename
                }
                __typename
              }
              ... on BannerTile {
                id
                backgroundColor
                textTheme
                active
                description
                __typename
              }
            }
            fragment actionItem on ActionItem {
              __typename
              id: objectId
              accessibilityLabel
              action {
                ...action
                __typename
              }
              active
              analytics {
                __typename
                eventId
                interaction
                interactionDetail
                pageProgrambrand
              }
              icon
              iconPosition
              mode
              objectId
              title
            }
            fragment action on Action {
              __typename
              ... on SearchAction {
                facets {
                  name
                  values
                  __typename
                }
                mediaType
                navigationType
                q
                __typename
              }
            }
            fragment imageFragment on Image {
              id: objectId
              alt
              title
              focalPoint
              objectId
              templateUrl
            }
        """
        payload = {
            'operationName': 'Search',
            'variables': {
                'facets': [],
                'mediaType': 'watch',
                'q': '',
            },
            'query': graphql_query,
        }
        from json import dumps
        data = dumps(payload).encode('utf-8')
        categories_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
        if categories_json is not None:
            content_types = find_entry(categories_json.get('data').get('uiSearch'), 'listId', 'initialsearchcontenttypes').get('items')
            genres = find_entry(categories_json.get('data').get('uiSearch'), 'listId', 'initialsearchgenres').get('items')
            category_items = content_types + genres
            for category in category_items:
                # Don't add audio-only categories
                if category.get('title') in ('Podcasts', 'Radio'):
                    continue
                thumb = category.get('image')
                if thumb:
                    thumb = thumb.get('templateUrl')
                categories.append({
                    'id': category.get('action').get('facets')[0].get('values')[0],
                    'thumbnail': thumb,
                    'name': category.get('title'),
                })
            categories.sort(key=lambda x: x.get('name'))
    return categories


def valid_categories(categories):
    """Check if categories contain all necessary keys and values"""
    return bool(categories) and all(item.get('id') and item.get('name') for item in categories)


def localize_categories(categories, categories2):
    """Return a localized and sorted listing"""
    for category in categories:
        for key, val in list(category.items()):
            if key == 'name':
                category[key] = localize_from_data(val, categories2)
    return sorted(categories, key=lambda x: x.get('name'))

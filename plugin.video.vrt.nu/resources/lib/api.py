# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements VRT MAX GraphQL API functionality"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.parse import quote_plus
except ImportError:  # Python 2
    from urllib import quote_plus

from helperobjects import TitleItem
from kodiutils import colour, get_setting_bool, get_setting_int, get_url_json, localize, ttl, url_for
from utils import from_unicode, shorten_link, to_unicode, url_to_program

GRAPHQL_URL = 'https://www.vrt.be/vrtnu-api/graphql/v1'


def get_sort(program_type):
    """Get sorting method"""
    sort = 'unsorted'
    ascending = True
    if program_type == 'mixed_episodes':
        sort = 'dateadded'
        ascending = False
    elif program_type == 'daily':
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


def get_context_menu(program_name, program_id, program_title, program_type, plugin_path, is_favorite):
    """Get context menu for listitem"""
    context_menu = []

    # Follow/unfollow
    follow_suffix = localize(30410) if program_type != 'oneoff' else ''  # program
    encoded_program_title = to_unicode(quote_plus(from_unicode(program_title)))  # We need to ensure forward slashes are quoted
    if is_favorite:
        extras = {}
        # If we are in a favorites menu, move cursor down before removing a favorite
        if plugin_path.startswith('/favorites'):
            extras = dict(move_down=True)
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

    return context_menu


def format_label(program_title, episode_title, program_type, ontime, is_favorite):
    """Format label"""
    if program_type == 'mixed_episodes':
        label = '[B]{}[/B] - {}'.format(program_title, episode_title)
    elif program_type == 'daily':
        label = '{} - {}'.format(ontime.strftime('%d/%m'), episode_title)
    elif program_type == 'oneoff':
        label = program_title
    else:
        label = episode_title

    # Favorite marker
    if is_favorite:
        label += colour('[COLOR={highlighted}]ᵛ[/COLOR]')

    return label


def format_plot(plot, region, product_placement, mpaa, offtime, permalink):
    """Format plot"""
    from datetime import datetime
    import dateutil.parser
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
            fragment ep on EpisodeTile {
              __typename
              id
              title
              episode {
                __typename
                id
                name
                available
                whatsonId
                title
                description
                subtitle
                permalink
                logo
                brand
                brandLogos {
                  type
                  mono
                  primary
                }
                image {
                  alt
                  templateUrl
                }

                ageRaw
                ageValue

                durationRaw
                durationValue
                durationSeconds

                episodeNumberRaw
                episodeNumberValue
                episodeNumberShortValue

                onTimeRaw
                onTimeValue
                onTimeShortValue

                offTimeRaw
                offTimeValue
                offTimeShortValue

                productPlacementValue
                productPlacementShortValue

                regionRaw
                regionValue
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
                }
                season {
                  id
                  titleRaw
                  titleValue
                  titleShortValue
                }
                analytics {
                  airDate
                  categories
                  contentBrand
                  episode
                  mediaSubtype
                  mediaType
                  name
                  pageName
                  season
                  show
                  }
                primaryMeta {
                  longValue
                  shortValue
                  type
                  value
                  __typename
                }
                secondaryMeta {
                  longValue
                  shortValue
                  type
                  value
                  __typename
                }
                watchAction {
                  avodUrl
                  completed
                  resumePoint
                  resumePointProgress
                  resumePointTitle
                  episodeId
                  videoId
                  publicationId
                  streamId
                }
              }
            }
        """
        # FIXME: Find a better way to change GraphQL typename
        if list_id.startswith('static:/'):
            graphql_query = graphql_query.replace('on PaginatedTileList', 'on StaticTileList')

        payload = dict(
            operationName='ListedEpisodes',
            variables=dict(
                listId=list_id,
                endCursor=end_cursor,
                pageSize=page_size,
            ),
            query=graphql_query,
        )
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
              }
            }
        """
        # FIXME: Find a better way to change GraphQL typename
        if list_id.startswith('static:/'):
            graphql_query = graphql_query.replace('on PaginatedTileList', 'on StaticTileList')

        payload = dict(
            operationName='PaginatedPrograms',
            variables=dict(
                listId=list_id,
                endCursor=end_cursor,
                pageSize=page_size,
            ),
            query=graphql_query,
        )
        from json import dumps
        data = dumps(payload).encode('utf-8')
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data, raise_errors='all')
    return data_json


def convert_programs(api_data, destination, use_favorites=False, **kwargs):
    """Convert paginated list of programs to Kodi list items"""
    from addon import plugin
    from favorites import Favorites

    programs = []

    # Favorites for context menu
    favorites = Favorites()
    favorites.refresh(ttl=ttl('indirect'))
    plugin_path = plugin.path

    program_list = api_data.get('data').get('list')
    if program_list:
        for item in program_list.get('paginated').get('edges'):
            program = item.get('node')

            program_name = url_to_program(program.get('link'))
            program_id = program.get('id')
            program_type = program.get('programType')
            program_title = program.get('title')
            path = url_for('programs', program_name=program_name)
            plot = program.get('program').get('shortDescription') or program.get('program').get('description')
            plotoutline = program.get('subtitle')

            # Art
            fanart = ''
            poster_img = program.get('program').get('posterImage')
            if poster_img:
                fanart = poster_img.get('templateUrl')
            poster = fanart
            thumb = ''
            thumb_img = program.get('image')
            if thumb_img:
                thumb = thumb_img.get('templateUrl')

            # Check favorite
            is_favorite = favorites.is_favorite(program_name)

            # Filter favorites for favorites menu
            if use_favorites and is_favorite is False:
                continue

            # Context menu
            context_menu = get_context_menu(program_name, program_id, program_title, program_type, plugin_path, is_favorite)

            # Label
            if is_favorite:
                label = program_title + colour('[COLOR={highlighted}]ᵛ[/COLOR]')
            else:
                label = program_title

            programs.append(
                TitleItem(
                    label=label,
                    path=path,
                    art_dict=dict(
                        thumb=thumb,
                        poster=poster,
                        banner=fanart,
                        fanart=fanart,
                    ),
                    info_dict=dict(
                        title=label,
                        tvshowtitle=program_title,
                        plot=plot,
                        plotoutline=plotoutline,
                        mediatype='tvshow',
                    ),
                    context_menu=context_menu,
                    is_playable=False,
                )
            )

        # Paging
        # Remove kwargs with None value
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        page_info = api_data.get('data').get('list').get('paginated').get('pageInfo')

        # FIXME: find a better way to disable more when favorites are filtered
        page_size = get_setting_int('itemsperpage', default=50)
        if len(programs) == page_size:
            if page_info.get('hasNextPage'):
                end_cursor = page_info.get('endCursor')
                # Add 'More...' entry at the end
                programs.append(
                    TitleItem(
                        label=colour(localize(30300)),
                        path=url_for(destination, end_cursor=end_cursor, **kwargs),
                        art_dict=dict(thumb='DefaultInProgressShows.png'),
                        info_dict={},
                    )
                )
    return programs


def convert_episodes(api_data, destination, use_favorites=False, **kwargs):
    """Convert paginated list of episodes to Kodi list items"""
    import dateutil.parser
    from addon import plugin
    from favorites import Favorites

    episodes = []
    sort = 'unsorted'
    ascending = True

    # Favorites for context menu
    favorites = Favorites()
    favorites.refresh(ttl=ttl('indirect'))
    plugin_path = plugin.path

    episode_list = api_data.get('data').get('list')
    if episode_list:
        for item in episode_list.get('paginated').get('edges'):
            episode = item.get('node').get('episode')
            video_id = episode.get('watchAction').get('videoId')
            publication_id = episode.get('watchAction').get('publicationId')
            path = url_for('play_id', video_id=video_id, publication_id=publication_id)
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
            product_placement = True if episode.get('productPlacementShortValue') == 'pp' else False
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
            fanart = episode.get('program').get('image').get('templateUrl')
            poster = episode.get('program').get('posterImage').get('templateUrl')
            thumb = episode.get('image').get('templateUrl')

            # Check favorite
            is_favorite = favorites.is_favorite(program_name)

            # Filter favorites for favorites menu
            if use_favorites and is_favorite is False:
                continue

            # Context menu
            context_menu = get_context_menu(program_name, program_id, program_title, program_type, plugin_path, is_favorite)

            # Label
            label = format_label(program_title, episode_title, program_type, ontime, is_favorite)

            # Sorting
            sort, ascending = get_sort(program_type)

            episodes.append(
                TitleItem(
                    label=label,
                    path=path,
                    art_dict=dict(
                        thumb=thumb,
                        poster=poster,
                        banner=fanart,
                        fanart=fanart,
                    ),
                    info_dict=dict(
                        title=label,
                        tvshowtitle=program_title,
                        aired=aired,
                        dateadded=dateadded,
                        episode=episode_no,
                        season=season_no,
                        plot=plot,
                        plotoutline=plotoutline,
                        mpaa=mpaa,
                        tagline=plotoutline,
                        duration=duration,
                        studio=studio,
                        year=year,
                        tag=tag,
                        mediatype='episode',
                    ),
                    context_menu=context_menu,
                    is_playable=True,
                )
            )
        # Paging
        # Remove kwargs with None value
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        page_info = api_data.get('data').get('list').get('paginated').get('pageInfo')

        # FIXME: find a better way to disable more when favorites are filtered
        page_size = get_setting_int('itemsperpage', default=50)
        if len(episodes) == page_size:
            if page_info.get('hasNextPage'):
                end_cursor = page_info.get('endCursor')
                # Add 'More...' entry at the end
                episodes.append(
                    TitleItem(
                        label=colour(localize(30300)),
                        path=url_for(destination, end_cursor=end_cursor, **kwargs),
                        art_dict=dict(thumb='DefaultInProgressShows.png'),
                        info_dict={},
                    )
                )
    return episodes, sort, ascending


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
        facets = [dict(
            name='categories',
            values=[category]
        )]
    elif channel:
        destination = 'channels'
        facets = [dict(
            name='brands',
            values=[channel]
        )]
    elif keywords:
        destination = 'search_query'
        facets = None
        query_string = keywords

    search_dict = dict(
        queryString=query_string,
        facets=facets,
        resultType='watch',
    )
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
    content = 'files'
    sort = 'unsorted'
    ascending = True
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
        list_id = 'static:/vrtnu/a-z/{}/{}.episodes-list.json'.format(program_name, season_name)
        api_data = get_paginated_episodes(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
        episodes, sort, ascending = convert_episodes(api_data, destination='noop')
        return episodes, sort, ascending, 'episodes'
    return None


def convert_seasons(api_data, program_name):
    """Convert seasons"""
    seasons = []
    for season in api_data:
        season_title = season.get('title').get('raw')
        season_name = season.get('name')
        label = '{} {}'.format(localize(30131), season_title)  # Season X
        path = url_for('programs', program_name=program_name, season_name=season_name)
        seasons.append(
            TitleItem(
                label=label,
                path=path,
                info_dict=dict(
                    title=label,
                    mediatype='season',
                ),
                is_playable=False,
            )
        )
    return seasons


def get_seasons(program_name):
    """Get seasons"""
    season_json = get_url_json('https://www.vrt.be/vrtmax/a-z/{}.model.json'.format(program_name))
    seasons = season_json.get('details').get('data').get('program').get('seasons')
    return seasons


def get_featured(feature=None, end_cursor=''):
    """Get featured menu items"""
    content = 'files'
    sort = 'unsorted'
    ascending = True
    if feature:
        page_size = get_setting_int('itemsperpage', default=50)
        if feature.startswith('program_'):
            list_id = 'static:/vrtnu/kijk.model.json@{}'.format(feature.split('program_')[1])
            api_data = get_paginated_programs(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
            programs = convert_programs(api_data, destination='featured', feature=feature)
            return programs, sort, ascending, 'tvshows'

        elif feature.startswith('episode_'):
            feature_id = feature.split('episode_')[1]
            list_id = 'static:/vrtnu/kijk.model.json@{}'.format(feature.split('episode_')[1])
            api_data = get_paginated_episodes(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
            episodes, sort, ascending = convert_episodes(api_data, destination='featured', feature=feature)
            return episodes, sort, ascending, 'episodes'
    else:
        featured = []
        featured_json = get_url_json('https://www.vrt.be/vrtmax/kijk.model.json')
        items = featured_json.get(':items').get('par').get(':items')
        for item in items:
            content_type = items.get(item).get('tileContentType')
            if content_type in ('program', 'episode'):
                title = items.get(item).get('title')
                feature_id = items.get(item).get('id')
                path = url_for('featured', feature='{}_{}'.format(content_type, feature_id))
                label = title
                featured.append(
                    TitleItem(
                        label=label,
                        path=path,
                        info_dict=dict(
                            title=label,
                            mediatype='season',
                        ),
                        is_playable=False,
                    )
                )
    return featured, sort, ascending, content

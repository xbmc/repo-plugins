# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements VRT MAX GraphQL API functionality"""

import random

from urllib.parse import quote, quote_plus, unquote

from data import CHANNELS
from helperobjects import TitleItem
from kodiutils import (colour, delete_cached_thumbnail, get_cache, get_setting_bool, get_setting_int, get_url_json, has_addon, has_credentials,
                       localize, localize_datelong, localize_from_data, log, update_cache, url_for)
from utils import find_entry, parse_duration, reformat_image_url, shorten_link, url_to_program, youtube_to_plugin_url
from graphql_data import EPISODE, EPISODE_TILE, PROGRAM_TILE


SCREENSHOT_URL = 'https://www.vrt.be/vrtnu-static/screenshots'
GRAPHQL_URL = 'https://www.vrt.be/vrtnu-api/graphql/v1'
RESUMEPOINTS_URL = 'https://ddt.profiel.vrt.be/resumePoints'
RESUMEPOINTS_MARGIN = 30  # The margin at start/end to consider a video as watched
LIVESTREAM_CACHE_HOURS = 24


def get_sort(program_type):
    """Get sorting method"""
    sort = 'unsorted'
    ascending = True
    if program_type in ('mixed_episodes', 'daily'):
        sort = 'dateadded'
        ascending = False
    elif program_type == 'oneoff':
        sort = 'label'
    elif program_type in ('series', 'reeksoplopend'):
        sort = 'episode'
    elif program_type == 'reeksaflopend':
        sort = 'episode'
        ascending = False
    return sort, ascending


def get_context_menu(program_name, program_id, program_title, program_type, favorited, is_continue=False, episode_id=None):
    """Get context menu for listitem"""
    from addon import plugin
    plugin_path = plugin.path
    context_menu = []

    # Follow/unfollow
    follow_suffix = localize(30410) if program_type != 'oneoff' else ''  # program
    encoded_program_title = quote_plus(program_title)  # We need to ensure forward slashes are quoted
    if favorited:
        context_menu.append((
            localize(30412, title=follow_suffix),  # Unfollow
            'RunPlugin(%s)' % url_for('unfollow', program_id=program_id, program_title=encoded_program_title)
        ))
    else:
        context_menu.append((
            localize(30411, title=follow_suffix),  # Follow
            'RunPlugin(%s)' % url_for('follow', program_id=program_id, program_title=encoded_program_title)
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
        context_menu.append((
            localize(30456),  # Mark as watched (VRT MAX)
            'RunPlugin(%s)' % url_for('resumepoints_continue_finish', episode_id=episode_id)
        ))
    return context_menu


def format_label(program_title, episode_title, program_type, start_dt=None, favorited=False, item_type='episode', is_playable=True, is_live=False):
    """Format label"""
    import dateutil.tz
    if item_type == 'program' or program_type == 'oneoff':
        label = program_title
    elif program_type == 'mixed_episodes':
        label = '[B]{}[/B] - {}'.format(program_title, episode_title)
    elif program_type == 'daily':
        label = '{} - {}'.format(start_dt.astimezone(dateutil.tz.gettz('Europe/Brussels')).strftime('%d/%m'), episode_title)
    elif program_type == 'epg':
        parts = [
            start_dt.astimezone(dateutil.tz.gettz('Europe/Brussels')).strftime("%H:%M"),
            '[B]{}[/B]'.format(program_title) if program_title else None,
            episode_title
        ]
        label = ' - '.join(p for p in parts if p)
    else:
        label = episode_title or ''

    # Favorite marker
    if favorited:
        label += '[COLOR={highlighted}]ᵛ[/COLOR]'

    # Non-actionable item
    if item_type == 'episode' and not is_playable:
        label = '[COLOR={{greyedout}}]{}[/COLOR]'.format(label)

    # Now playing
    if is_live:
        if item_type == 'episode' and is_playable:
            label = '[COLOR={{highlighted}}]{}[/COLOR] {}'.format(label, localize(30301))
        else:
            label += localize(30301)

    return colour(label)


def format_plot(plot, region, product_placement, mpaa, program_type=None, start_dt=None, stop_dt=None, offtime=None, permalink=None):
    """Format plot"""
    from datetime import datetime
    import dateutil.tz

    # Add additional metadata to plot
    plot_meta = ''
    plot_date = ''

    if program_type == 'epg' and start_dt and stop_dt:
        start_str = start_dt.astimezone(dateutil.tz.gettz('Europe/Brussels')).strftime("%H:%M")
        stop_str = stop_dt.astimezone(dateutil.tz.gettz('Europe/Brussels')).strftime("%H:%M")
        local_start = start_dt.astimezone(dateutil.tz.gettz('Europe/Brussels'))
        plot_date += f'[B]{localize_datelong(local_start)}[/B]\n{start_str} - {stop_str}'

    # Only display when a video disappears if it is within the next 3 months
    # Show the remaining days/hours the episode is still available
    if offtime:
        now = datetime.now(dateutil.tz.tzlocal())
        remaining = offtime - now
        total_seconds = remaining.total_seconds()

        if total_seconds <= 0:
            plot_meta += localize(30209)  # Already expired or 0 time left
        else:
            total_days = total_seconds / 86400
            if total_days > 5 * 365:
                pass  # more than 5 years, do not show
            elif total_days > 2 * 365:
                plot_meta += localize(30202, years=int(total_days // 365))
            elif total_days > 3 * 30.5:
                plot_meta += localize(30203, months=int(total_days // 30.5))
            elif total_days > 1:
                plot_meta += localize(30204, days=int(total_days))
            elif int(total_days) == 1:
                plot_meta += localize(30205)  # 1 day to go
            else:
                total_hours = total_seconds / 3600
                if total_hours > 1:
                    plot_meta += localize(30206, hours=int(total_hours))
                elif int(total_hours) == 1:
                    plot_meta += localize(30207)  # 1 hour to go
                else:
                    plot_meta += localize(30208, minutes=int(total_seconds // 60))

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
        plot_meta += f'[B]{mpaa}[/B]'

    if plot_date:
        plot = f'{plot_date}\n\n{plot}'

    if plot_meta:
        plot = f'{plot}\n\n{plot_meta}'

    permalink = shorten_link(permalink)
    if permalink and get_setting_bool('showpermalink', default=False):
        plot = '{}\n\n[COLOR={{highlighted}}]{}[/COLOR]'.format(plot, permalink)
    return colour(plot)


def resumepoints_is_activated():
    """Is resumepoints activated in the menu and do we have credentials ?"""
    return get_setting_bool('usefavorites', default=True) and get_setting_bool('useresumepoints', default=True) and has_credentials()


def get_resumepoint_data(episode_id):
    """Get resumepoint data from GraphQL API"""
    data_json = get_stream_data(episode_id)
    return next(
        (mode.get('resumePointTemplate', {})
         for mode in data_json.get('data', {}).get('page', {}).get('player', {}).get('modes', [])
         if mode.get('__typename') == 'VideoPlayerMode'),
        None
    )


def get_next_info(episode_id):
    """ Get up next data"""
    import dateutil.parser
    next_info = {}
    data_json = get_single_episode_data(episode_id)
    current_ep = data_json.get('data').get('page').get('episode')
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
                'episode_id': next_ep.get('shareAction').get('url'),
            }
        }
    return next_info


def get_stream_data(vrtmax_url):
    """Get stream data from from GraphQL API"""
    page_id = vrtmax_url.split('www.vrt.be')[1]
    graphql_query = """
         query StreamId($pageId: ID!) {
          page(id: $pageId) {
            ... on IPage {
              ... on LivestreamPage {
                player {
                  modes {
                    ... on VideoPlayerMode {
                      streamId
                    }
                    __typename
                  }
                }
              }
            }
            ... on EpisodePage {
              player {
                modes {
                  ... on VideoPlayerMode {
                    streamId
                    resumePointTemplate {
                      mediaId
                      mediaName
                    }
                  }
                  __typename
                }
              }
            }
          }
          __typename
        }
    """
    operation_name = 'StreamId'
    variables = {
        'pageId': page_id
    }
    return api_req(graphql_query, operation_name, variables)


def get_single_episode_data(episode_id):
    """Get single episode data from GraphQL API"""
    graphql_query = """
        query OnePlayerData($id: ID!) {
          page(id: $id) {
            __typename
            ... on EpisodePage {
              episode {
                ...ep
              }
            }
          }
        }
        fragment ep on Episode {
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
            contentBrand
            episode
            mediaSubtype
            mediaType
            name
            pageName
            season
            show
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
          shareAction {
            url
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
              ...episodeTileFragment
            }
          }
        }
        %s
    """ % EPISODE_TILE
    operation_name = 'OnePlayerData'
    variables = {
        'id': episode_id,
    }
    return api_req(graphql_query, operation_name, variables)


def get_latest_episode_data(program_name):
    """Get latest episode data from GraphQL API"""
    latest_episode = None
    graphql_query = """
        query VideoProgramPage(
          $pageId: ID!,
          $lazyItemCount: Int = 500,
          $after: ID
          ) {
          page(id: $pageId) {
            ... on ProgramPage {
              header {
                title
                actionItems {
                  accessibilityLabel
                  active
                  mode
                  title
                  action {
                    ... on LinkAction {
                      internalTarget
                      link
                    }
                  }
                }
              }
              components {
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
                                ...episodeTileFragment
                                __typename
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
                                      ...episodeTileFragment
                                      __typename
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        %s
    """ % EPISODE_TILE
    operation_name = 'VideoProgramPage'
    variables = {
        'pageId': '/vrtmax/a-z/{}/'.format(program_name),
    }
    data = api_req(graphql_query, operation_name, variables)
    if data.get('data').get('page'):
        for action in data.get('data').get('page').get('header').get('actionItems'):
            if action.get('title') == 'Bekijk de recentste aflevering':
                latest_episode = get_single_episode_data(action.get('action').get('link')).get('data').get('page')
            else:
                items = data.get('data').get('page').get('components')[0].get('items')[0].get('components')[0]
                if not items.get('paginatedItems'):
                    items = items.get('items')[0].get('components')[0]
                edges = items.get('paginatedItems').get('edges')
                highest_ep_no = 0
                highest_ep = {}
                for edge in edges:
                    ep_no = int(edge.get('node').get('episode').get('episodeNumberRaw') or 0)
                    if ep_no > highest_ep_no:
                        highest_ep_no = ep_no
                        highest_ep = edge.get('node')
                latest_episode = highest_ep
    return latest_episode


def get_seasons_data(program_name):
    """Get seasons data from GraphQL API"""
    graphql_query = """
        query program(
          $pageId: ID!,
          $lazyItemCount: Int = 500,
          $before: ID
          $after: ID
          ) {
          page(id: $pageId) {
            ... on EpisodePage {
              episode {
                ...episode
              }
            }
            ... on ProgramPage {
              brand
              program {
                brand
                brandLogos {
                  type
                  mono
                  primary
                }
                catalogMemberType
                title
                description
                shortDescription
                subtitle
                id
                link
                permalink
                objectId
                programType
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
                richDescription {
                  html
                  text
                }
                richShortDescription {
                  html
                  text
                }
                mostRelevantEpisodeTile {
                  __typename
                  title
                  id
                  tile {
                    __typename
                    ...on EpisodeTile {
                      ...episodeTileFragment
                    }
                  }
                }
                navigation {
                  __typename
                  items {
                    __typename
                    title
                    icon
                    action {
                      __typename
                      ... on EpisodeWatchAction {
                        avodUrl
                        completed
                        episodeId
                        playlistUrl
                        publicationId
                        resumePoint
                        resumePointProgress
                        resumePointTitle
                        resumePointTotal
                        resumePointUpdated
                        streamId
                        videoId
                        videoType
                        videoUrl
                        __typename
                      }
                      ... on ShowComponentAction {
                        component {
                          __typename
                          ...on StaticTileList {
                            ...staticTileListFragment
                          }
                          ...on LazyTileList {
                            ...lazyTileListFragment
                          }
                        }
                      }
                      ... on SubNavigationAction {
                        items {
                          __typename
                          title
                          action {
                            __typename
                            ... on ShowComponentAction {
                              component {
                                __typename
                                ...on StaticTileList {
                                  ...staticTileListFragment
                                }
                                ...on LazyTileList {
                                  ...lazyTileListFragment
                                }
                              }
                            }
                          }
                        }
                      }
                      ... on LinkAction {
                        displayLink
                        externalTarget
                        internalTarget
                        link
                        linkTokens {
                          __typename
                          placeholder
                          value
                        }
                        page {
                          ...on EpisodePage {
                            episode {
                              ...episode
                            }
                          }
                          __typename
                        }
                        passUserIdentity
                        zone {
                          preferredZone
                          isExclusive
                          __typename
                        }
                        __typename
                      }
                    }
                  }
                }
                seasons {
                  catalogMemberType
                  id
                  navigationTitle
                  numEpisodesRaw
                  numEpisodesShortValue
                  numEpisodesValue
                  objectId
                  programId
                  programName
                  programTitle
                  programType
                  titleRaw
                  titleShortValue
                  titleValue


                }
              }
            }
          }
        }
        fragment staticTileListFragment on StaticTileList {
          __typename
          componentType
          objectId
          listId
          tileContentType
          tileVariant
          items {
            ...on EpisodeTile {
              ...episodeTileFragment
            }
          }
        }
        fragment lazyTileListFragment on LazyTileList {
          __typename
          componentType
          title
          listId
          tileContentType
          tileVariant
          action {
            __typename
          }
          actionItems {
            ...actionItemFragment
            __typename
          }
          items {
            __typename
            ...on EpisodeTile {
              ...episodeTileFragment
            }
          }
          paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
            __typename
            edges {
              __typename
              cursor
              node {
                __typename
                ...on EpisodeTile {
                  ...episodeTileFragment
                }
              }
            }
          }
        }
        fragment actionItemFragment on ActionItem {
          __typename
          objectId
          accessibilityLabel
          active
          mode
          title
          themeOverride
          action {
            __typename
          }
          icons {
            __typename
          }
        }
        %s
    """ % EPISODE_TILE
    operation_name = 'program'
    variables = {
        'pageId': '/vrtmax/a-z/{}/'.format(program_name),
    }
    return api_req(graphql_query, operation_name, variables)


def set_favorite(program_id, program_title, favorited=True):
    """Set favorite(add/remove to/from my list)"""
    graphql_query = """
        mutation setFavoriteActionItem($input: FavoriteActionInput!) {
          setFavoriteActionItem(input: $input) {
            __typename
            objectId
            accessibilityLabel
            action {
              ... on FavoriteAction {
                __typename
                id
                favorite
              }
              __typename
            }
            active
            mode
            title
          }
        }
    """
    operation_name = 'setFavoriteActionItem'
    variables = {
        'input': {
            'favorite': favorited,
            'id': program_id,
            'title': program_title,
        },
    }
    return api_req(graphql_query, operation_name, variables)


def is_favorite(program_name):
    """Wether a program a favorited"""
    favorite = get_latest_episode_data(program_name).get('episode').get('favoriteAction').get('favorite')
    return favorite


def get_program_id(program_name):
    """Get the id of a program"""
    program_id = get_latest_episode_data(program_name).get('episode').get('program').get('id')
    return program_id


def set_resumepoint(video_id, title, position, total):
    """Set resumepoint"""
    data_json = {}
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
    return data_json


def delete_continue(episode_id):
    """Delete continue episode using GraphQL API"""
    import base64
    from json import dumps
    graphql_query = """
        mutation listDelete($input: ListDeleteActionInput!) {
          setListDeleteActionItem(input: $input) {
            title
            active
            action {
              __typename
              ... on NoAction {
                __typename
                reason
              }
              ... on ListTileDeletedAction {
                __typename
                listId
                listName
                id
              }
            }
            __typename
          }
        }
    """
    list_name = {
        'listId': 'dynamic:/vrtnu.model.json@resume-list-video',
        'listType': 'verderkijken',
    }
    encoded_list_name = base64.b64encode(dumps(list_name).encode('utf-8'))
    operation_name = 'listDelete'
    variables = {
        'input': {
            'id': episode_id,
            'listName': encoded_list_name.decode('utf-8'),
        },
    }
    return api_req(graphql_query, operation_name, variables)


def finish_continue(episode_id):
    """Finish continue episode using GraphQL API"""
    graphql_query = """
        mutation finishItem($input: FinishActionInput!) {
          setFinishActionItem(input: $input) {
            __typename
            objectId
            title
            accessibilityLabel
            action {
              ... on FinishAction {
                id
                __typename
              }
              __typename
            }
          }
        }
    """
    operation_name = 'finishItem'
    variables = {
        'input': {
            'id': episode_id,
        },
    }
    return api_req(graphql_query, operation_name, variables)


def get_entities(list_id, page_size='', end_cursor=''):
    """Get a list of episodes or programs using GraphQL API"""
    graphql_query = """
         query TileList(
          $listId: ID!
          $lazyItemCount: Int = 20
          $after: ID
          $before: ID
        ) {
          list(listId: $listId) {
            __typename
            ... on PaginatedTileList {
              ...paginatedTileListFragment
              __typename
            }
            ... on StaticTileList {
              ...staticTileListFragment
              __typename
            }
          }
        }
        fragment paginatedTileListFragment on PaginatedTileList {
          __typename
          objectId
          listId
          tileVariant
          tileContentType
          title
          description
          paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
            __typename
            edges {
              __typename
              cursor
              node {
                __typename
                ...tileFragment
              }
            }
            pageInfo {
              __typename
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
          }
        }
        fragment staticTileListFragment on StaticTileList {
          __typename
          objectId
          listId
          tileVariant
          tileContentType
          title
          description
          paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
            __typename
            edges {
              __typename
              cursor
              node {
                __typename
                ...tileFragment
              }
            }
            pageInfo {
              __typename
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
          }
        }
        fragment tileFragment on Tile {
          ... on IIdentifiable {
            __typename
            objectId
          }
          ... on ITile {
            title
            active
            accessibilityTitle
            action {
              __typename
              ... on LinkAction {
                internalTarget
                link
                internalTarget
                externalTarget
                __typename
              }
            }
            actionItems {
              ...actionItemFragment
              __typename
            }
            image {
              ...imageFragment
              __typename
            }
            primaryMeta {
              ...metaFragment
              __typename
            }
            secondaryMeta {
              ...metaFragment
              __typename
            }
            tertiaryMeta {
              ...metaFragment
              __typename
            }
            indexMeta {
              ...metaFragment
              __typename
            }
            statusMeta {
              ...metaFragment
              __typename
            }
            labelMeta {
              ...metaFragment
              __typename
            }
            componentId
            __typename
          }
          ... on EpisodeTile {
            ...episodeTileFragment
            __typename
          }
          ... on ProgramTile {
            ...programTileFragment
          }
          __typename
        }
        fragment actionItemFragment on ActionItem {
          __typename
          objectId
          accessibilityLabel
          active
          mode
          title
          themeOverride
          action {
            ...actionFragment
            __typename
          }
          icons {
            ...iconFragment
            __typename
          }
        }
        fragment actionFragment on Action {
          __typename
          ... on FavoriteAction {
            id
            favorite
            title
            __typename
          }
          ... on ListDeleteAction {
            listName
            id
            listId
            title
            __typename
          }
          ... on ListTileDeletedAction {
            listName
            id
            listId
            __typename
          }
          ... on LinkAction {
            internalTarget
            link
            internalTarget
            externalTarget
            passUserIdentity
            zone {
              preferredZone
              isExclusive
              __typename
            }
            linkTokens {
              __typename
              placeholder
              value
            }
            __typename
          }
          ... on ClientDrivenAction {
            __typename
            clientDrivenActionType
          }
          ... on ShareAction {
            title
            url
            __typename
          }
          ... on SwitchTabAction {
            referencedTabId
            link
            __typename
          }
          ... on FinishAction {
            id
            __typename
          }
        }
        fragment iconFragment on Icon {
          __typename
          accessibilityLabel
          position
          type
          ... on DesignSystemIcon {
            value {
              __typename
              color
              name
            }
            activeValue {
              __typename
              color
              name
            }
            __typename
          }
          ... on ImageIcon {
            value {
              __typename
              srcSet {
                src
                format
                __typename
              }
            }
            activeValue {
              __typename
              srcSet {
                src
                format
                __typename
              }
            }
            __typename
          }
        }
        fragment imageFragment on Image {
          __typename
          objectId
          alt
          focusPoint {
            x
            y
            __typename
          }
          templateUrl
        }
        fragment metaFragment on MetaDataItem {
          __typename
          type
          value
          shortValue
          longValue
        }
        %s
        %s
    """ % (PROGRAM_TILE, EPISODE_TILE)
    operation_name = 'TileList'
    variables = {
        'listId': list_id,
        'after': end_cursor,
        'lazyItemCount': page_size,
    }
    return api_req(graphql_query, operation_name, variables)


def get_epg_page(page_id, page_size='', end_cursor=''):
    """Get a program guide page using GraphQL API"""
    graphql_query = """
        query Page(
          $pageId: ID!
          $lazyItemCount: Int = 100
          $after: ID
          $before: ID
        ) {
          page(id: $pageId) {
            ... on IIdentifiable {
              __typename
              objectId
            }
            ... on ElectronicProgramGuidePage {
              brand
              brandLogos {
                ...brandLogosFragment
                __typename
              }
              current {
                __typename
                objectId
                title
                ... on StandaloneTile {
                  __typename
                  objectId
                  tile {
                    ...tileFragment
                    __typename
                  }
                }
              }
              linkTemplate
              previous {
                __typename
                ...paginatedTileListFragment
              }
              next {
                __typename
                ...paginatedTileListFragment
              }
              __typename
            }
            ... on IPage {
              title
              permalink
              __typename
            }
            __typename
          }
        }
        fragment tileFragment on Tile {
          ... on IIdentifiable {
            __typename
            objectId
          }
          ... on IComponent {
            ...componentTrackingDataFragment
            __typename
          }
          ... on ITile {
            title
            active
            accessibilityTitle
            tileType
            action {
              __typename
              ... on LinkAction {
                internalTarget
                link
                internalTarget
                externalTarget
                __typename
              }
            }
            actionItems {
              ...actionItemFragment
              __typename
            }
            image {
              ...imageFragment
              __typename
            }
            primaryMeta {
              ...metaFragment
              __typename
            }
            secondaryMeta {
              ...metaFragment
              __typename
            }
            indexMeta {
              __typename
              type
              value
            }
            statusMeta {
              ...metaFragment
              __typename
            }
            status {
              accessibilityLabel
              icon {
                ...iconFragment
                __typename
              }
              text {
                small
                default
                __typename
              }
              __typename
            }
            labelMeta {
              __typename
              type
              value
            }
            componentId
            __typename
          }
          ... on EpisodeTile {
            tileType
            title
            componentType
            description
            available
            chapterStart
            formattedDuration
            progress {
              completed
              progressInSeconds
              durationInSeconds
              __typename
            }
            whatsonId
            episode {
              ...episode
            }
            __typename
          }
          ... on LivestreamTile {
            description
            brand
            livestream {
              title
              subtitle
              startDateTime
              episode {
                ...episode
              }
              __typename
            }
            progress {
              durationInSeconds
              progressInSeconds
              __typename
            }
            componentId
            __typename
          }
          __typename
        }
        fragment actionItemFragment on ActionItem {
          __typename
          objectId
          accessibilityLabel
          active
          mode
          title
          themeOverride
          action {
            ...actionFragment
            __typename
          }
          icons {
            ...iconFragment
            __typename
          }
        }
        fragment actionFragment on Action {
          __typename
          ... on FavoriteAction {
            id
            favorite
            title
            __typename
          }
          ... on LinkAction {
            internalTarget
            link
            internalTarget
            externalTarget
            passUserIdentity
            zone {
              preferredZone
              isExclusive
              __typename
            }
            linkTokens {
              __typename
              placeholder
              value
            }
            __typename
          }
          ... on ClientDrivenAction {
            __typename
            clientDrivenActionType
          }
          ... on ShareAction {
            title
            url
            __typename
          }
          ... on FinishAction {
            id
            __typename
          }
        }
        fragment iconFragment on Icon {
          __typename
          accessibilityLabel
          position
          type
          ... on DesignSystemIcon {
            value {
              __typename
              color
              name
            }
            activeValue {
              __typename
              color
              name
            }
            __typename
          }
          ... on ImageIcon {
            value {
              __typename
              srcSet {
                src
                format
                __typename
              }
            }
            activeValue {
              __typename
              srcSet {
                src
                format
                __typename
              }
            }
            __typename
          }
        }
        fragment brandLogosFragment on Logo {
          colorOnColor
          height
          mono
          primary
          type
          width
          __typename
        }
        fragment componentTrackingDataFragment on IComponent {
          trackingData {
            data
            perTrigger {
              trigger
              data
              template {
                id
                __typename
              }
              __typename
            }
            __typename
          }
          __typename
        }
        fragment imageFragment on Image {
          __typename
          objectId
          alt
          focusPoint {
            x
            y
            __typename
          }
          templateUrl
        }
        fragment metaFragment on MetaDataItem {
          __typename
          type
          value
          shortValue
          longValue
        }
        fragment paginatedTileListFragment on PaginatedTileList {
          __typename
          objectId
          listId
          action {
            ... on LinkAction {
              __typename
              externalTarget
              link
            }
            __typename
          }
          banner {
            actionItems {
              ...actionItemFragment
              __typename
            }
            backgroundColor
            compactLayout
            description
            image {
              ...imageFragment
              __typename
            }
            titleArt {
              ...imageFragment
              __typename
            }
            textTheme
            title
            __typename
          }
          bannerSize
          displayType
          maxAge
          tileVariant
          paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
            __typename
            edges {
              __typename
              cursor
              node {
                __typename
                ...tileFragment
              }
            }
            pageInfo {
              __typename
              endCursor
              hasNextPage
              hasPreviousPage
              startCursor
            }
          }
          tileContentType
          title
          description
          ... on IComponent {
            ...componentTrackingDataFragment
            __typename
          }
        }
        %s
    """ % EPISODE
    operation_name = 'Page'
    variables = {
        'pageId': page_id,
        'after': end_cursor,
        'lazyItemCount': page_size,
    }
    return api_req(graphql_query, operation_name, variables)


def get_epg_list(channel, date, page=None):
    """Generate EPG list from the EPG page. If page is None, return full list."""

    page_size = get_setting_int('itemsperpage', default=50)
    api_page_size = 50

    # Base page (center block)
    page_id = f'/vrtmax/tv-gids/{channel}/{date}/'
    base = get_epg_page(page_id, page_size=api_page_size, end_cursor='')

    api_page = base.get('data', {}).get('page', {}) or {}
    prev_page = api_page.get('previous', {}) or {}
    next_page = api_page.get('next', {}) or {}
    current = api_page.get('current') or {}
    current_item = current.get('tile')

    # Initial blocks available
    prev_items = prev_page.get('paginatedItems', {}).get('edges') or []
    next_items = next_page.get('paginatedItems', {}).get('edges') or []

    prev_info = prev_page.get('paginatedItems', {}).get('pageInfo', {}) or {}
    next_info = next_page.get('paginatedItems', {}).get('pageInfo', {}) or {}

    prev_list_id = prev_page.get('listId')
    next_list_id = next_page.get('listId')

    # Count known items
    def known_total():
        return len(prev_items) + (1 if current_item else 0) + len(next_items)

    # Load a 50-item API block
    def load_more(list_id, page_info, collector):
        has_more = page_info.get('hasNextPage', False)
        cursor = page_info.get('endCursor')
        if not list_id or not has_more:
            return False, page_info

        data = get_entities(list_id=list_id, page_size=api_page_size, end_cursor=cursor)
        p = data.get('data', {}).get('list', {}).get('paginatedItems', {}) or {}
        edges = p.get('edges') or []
        collector.extend(edges)
        info = p.get('pageInfo', {}) or {}
        return info.get('hasNextPage', False), info

    prev_has_more = prev_info.get('hasNextPage', False)
    next_has_more = next_info.get('hasNextPage', False)

    # full list mode
    if page is None:
        # load everything until both sides exhausted
        while prev_has_more or next_has_more:
            if prev_has_more:
                prev_has_more, prev_info = load_more(prev_list_id, prev_info, prev_items)
            if next_has_more:
                next_has_more, next_info = load_more(next_list_id, next_info, next_items)

        # merge everything
        full = prev_items + ([current_item] if current_item else []) + next_items
        return full, ''  # no next page

    # paged mode
    page = int(page)
    offset = (page - 1) * page_size
    end_index = offset + page_size

    # fetch only what we need
    while known_total() < end_index and (prev_has_more or next_has_more):
        index_of_current = len(prev_items)
        current_count = 1 if current_item else 0

        if offset >= index_of_current + current_count:
            # page lies after the current item
            if next_has_more:
                next_has_more, next_info = load_more(next_list_id, next_info, next_items)
            elif prev_has_more:
                prev_has_more, prev_info = load_more(prev_list_id, prev_info, prev_items)
            else:
                break
        else:
            # page lies before the current item
            if prev_has_more:
                prev_has_more, prev_info = load_more(prev_list_id, prev_info, prev_items)
            elif next_has_more:
                next_has_more, next_info = load_more(next_list_id, next_info, next_items)
            else:
                break

    # merge
    full = prev_items + ([current_item] if current_item else []) + next_items

    # slice
    page_slice = full[offset:end_index]

    # determine next page
    if len(full) > end_index:
        next_page = str(page + 1)
    else:
        next_page = str(page + 1) if (next_has_more or prev_has_more) and page_slice else ''

    return page_slice, next_page


def get_epg_episodes(channel, date, page):
    """Return Title items from epg data"""
    tile_list, next_page = get_epg_list(channel, date, page=page)
    episodes, _, _ = convert_episodes(tile_list, destination='tvguide', end_cursor=next_page, date=date, channel=channel)
    return episodes


def convert_programs(item_list, destination, end_cursor='', use_favorites=False, **kwargs):
    """Convert paginated list of programs to Kodi list items"""

    programs = []

    for item in item_list:
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
        favorited = program.get('program').get('favoriteAction').get('favorite')

        # Filter favorites for favorites menu
        if use_favorites and favorited is False:
            continue

        # Context menu
        context_menu = get_context_menu(program_name, program_id, program_title, program_type, favorited)

        # Label
        label = format_label(program_title, episode_title, program_type, ontime, favorited, item_type='program')

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

    if end_cursor:
        # Add 'More...' entry at the end
        programs.append(
            TitleItem(
                label=colour(localize(30300)),
                path=url_for(destination, end_cursor=end_cursor, **kwargs),
                art_dict={'thumb': 'DefaultInProgressShows.png'},
                info_dict={},
                prop_dict={'SpecialSort': 'bottom'},
            )
        )
    return programs


def convert_episode(episode_tile, destination=None):
    """Convert paginated episode item to TitleItem"""
    import dateutil.parser
    from datetime import datetime, timedelta
    from base64 import b64decode
    import dateutil.tz

    title_item = TitleItem(label=None, art_dict={}, info_dict={})
    now = datetime.now(dateutil.tz.tzlocal())

    # Defaults
    path = None
    duration = timedelta(seconds=0)
    start_dt = stop_dt = None
    program_type = None
    favorited = False
    plot = ''
    region = None
    product_placement = None
    mpaa = None
    offtime = None
    permalink = None

    # Basic tile properties
    is_playable = episode_tile.get('available', True)
    is_live = episode_tile.get('active', False)
    program_title = episode_tile.get('title')
    episode_title = episode_tile.get('subtitle')

    if episode_tile.get('livestream'):
        episode = episode_tile.get('livestream').get('episode')
    else:
        episode = episode_tile.get('episode')
    if episode:
        analytics = episode.get('analytics', {})
        program = episode.get('program', {})
        share_action = episode.get('shareAction', {})

        # IDs and paths
        episode_id = episode.get('id')
        video_url = share_action.get('url') if share_action else ''

        path = url_for('play_url', video_url=video_url)
        program_name = url_to_program(program.get('link'))
        program_id = program.get('id')
        program_title = program.get('title')
        program_type = program.get('programType')
        episode_title = episode.get('title')

        # Timing and duration
        ontime = dateutil.parser.parse(episode.get('onTimeRaw') or '1970-01-01T00:00:00.000+00:00')
        offtime = dateutil.parser.parse(episode.get('offTimeRaw') or '1970-01-01T00:00:00.000+00:00')
        start_dt = ontime

        if episode.get('durationRaw'):
            duration = parse_duration(episode['durationRaw'])
        else:
            duration = timedelta(seconds=episode.get('durationSeconds', 0))
        stop_dt = start_dt + duration

        # Metadata
        mpaa = episode.get('ageRaw') or ''
        product_placement = episode.get('productPlacementShortValue') == 'pp'
        region = episode.get('regionRaw')
        permalink = episode.get('permalink')
        plot = episode.get('description') or ''
        plotoutline = program.get('subtitle')
        studio = episode.get('brand').title() if episode.get('brand') else 'VRT'
        aired = dateutil.parser.parse(analytics.get('airDate', now.isoformat())).strftime('%Y-%m-%d')
        dateadded = ontime.strftime('%Y-%m-%d %H:%M:%S')
        year = int(ontime.strftime('%Y'))
        tag = [t.strip().title() for t in analytics.get('categories', '').split(',') if t.strip()]

        episode_no = int(episode.get('episodeNumberRaw') or 0)
        season_no = int(''.join(ch for ch in episode.get('season', {}).get('titleRaw', '') if ch.isdigit()) or 0)

        # Art
        fanart = ''
        poster = ''
        thumb = ''

        fanart_img = program.get('image')
        if fanart_img:
            fanart = reformat_image_url(fanart_img.get('templateUrl'))

        poster_img = program.get('posterImage')
        if poster_img:
            poster = reformat_image_url(poster_img.get('templateUrl'))

        thumb_img = episode.get('image')
        if thumb_img:
            thumb = reformat_image_url(thumb_img.get('templateUrl'))

        title_item.art_dict = {
            'thumb': thumb,
            'poster': poster,
            'banner': fanart,
            'fanart': fanart,
        }

        # Favorite / Continue
        favorited = (episode.get('favoriteAction') or {}).get('favorite')
        is_continue = destination == 'resumepoints_continue'

        # Mark mixed episode categories
        if destination in ('recent', 'favorites_recent', 'resumepoints_continue', 'featured', 'search_query'):
            program_type = 'mixed_episodes'

        # Context menu
        context_menu = get_context_menu(
            program_name, program_id, program_title, program_type, favorited, is_continue, episode_id
        )

        # FIXME: Resume point logic is broken
        # position = watch_action.get('resumePoint')
        # total = watch_action.get('resumePointTotal')
        position = 0
        total = 0
        prop_dict = {}
        playcount = -1

        if resumepoints_is_activated() and position and total:
            if RESUMEPOINTS_MARGIN < position < total - RESUMEPOINTS_MARGIN:
                prop_dict.update({'resumetime': position, 'totaltime': total})
            if position > total - RESUMEPOINTS_MARGIN:
                playcount = 1

        # Info dict
        title_item.info_dict = {
            'aired': aired,
            'dateadded': dateadded,
            'episode': episode_no,
            'season': season_no,
            'playcount': playcount,
            'plotoutline': plotoutline,
            'mpaa': mpaa,
            'tagline': plotoutline,
            'studio': studio,
            'year': year,
            'tag': tag,
        }
        title_item.context_menu = context_menu
        title_item.prop_dict = prop_dict

    else:
        # Fallback when no 'episode' key
        if episode_tile.get('image'):
            img = episode_tile['image'].get('templateUrl')
            title_item.art_dict['thumb'] = img
            title_item.art_dict['fanart'] = img

    # EPG entries
    if episode_tile.get('indexMeta'):
        program_type = 'epg'
        if episode_tile.get('tileType') == 'livestream':
            is_live = True
            is_playable = True
            channel = episode_tile.get('brand')
            start_str = episode_tile.get('livestream').get('startDateTime')
        else:
            comp_id = episode_tile.get('componentId', '').lstrip('#')
            decoded = b64decode(comp_id.encode('utf-8')).decode('utf-8')
            epg_parts = decoded.split('#1')
            channel_id, start_str = epg_parts[1], epg_parts[2].split('|')[0]
            channel = find_entry(CHANNELS, 'id', channel_id).get('name')

        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))

        if not duration:
            if episode_tile.get('progress'):
                duration = timedelta(seconds=episode_tile.get('progress').get('durationInSeconds'))
            else:
                duration = timedelta(minutes=int(episode_tile['statusMeta'][0]['value'].split()[0]))
        stop_dt = start_dt + duration

        # Fix unplayable episodes
        if not is_playable:
            # Play episode from past 24h livestream cache
            if now - timedelta(hours=LIVESTREAM_CACHE_HOURS) <= start_dt <= now:
                is_playable = True
                start_iso = start_dt.astimezone(dateutil.tz.gettz('Europe/Brussels')).isoformat()[:19]
                stop_iso = stop_dt.astimezone(dateutil.tz.gettz('Europe/Brussels')).isoformat()[:19]
                path = url_for('play_air_date', channel, start_iso, stop_iso)
            else:
                path = url_for('noop')
        # Play livestream
        elif is_live:
            path = url_for('play_url', 'https://www.vrt.be' + episode_tile['action']['link'])

    # Final formatting
    plot = format_plot(plot, region, product_placement, mpaa, program_type, start_dt, stop_dt, offtime, permalink)
    title_item.info_dict['plot'] = plot
    title_item.path = path

    # Label
    label = format_label(program_title, episode_title, program_type, start_dt, favorited,
                         is_playable=is_playable, is_live=is_live)

    title_item.label = label
    title_item.info_dict['title'] = label
    title_item.info_dict['tvshowtitle'] = program_title
    title_item.info_dict['mediatype'] = 'episode'
    title_item.info_dict['duration'] = duration.total_seconds()
    title_item.is_playable = is_playable

    # Sorting
    sort, ascending = get_sort(program_type)
    return sort, ascending, favorited, title_item


def convert_episodes(item_list, destination, end_cursor='', use_favorites=False, **kwargs):
    """Convert paginated episode list to TitleItems"""
    episodes = []
    sort = 'unsorted'
    ascending = True

    if item_list:

        for item in item_list:
            episode = item.get('node') or item

            sort, ascending, favorited, title_item = convert_episode(episode, destination)

            # Filter favorites for favorites menu
            if use_favorites and favorited is False:
                continue

            episodes.append(title_item)

        # Paging
        # Remove kwargs with None value
        kwargs = {k: v for k, v in list(kwargs.items()) if v is not None}

        if end_cursor:
            # Add 'More...' entry at the end
            episodes.append(
                TitleItem(
                    label=colour(localize(30300)),
                    path=url_for(destination, end_cursor=quote(end_cursor, safe=''), **kwargs),
                    art_dict={'thumb': 'DefaultInProgressShows.png'},
                    info_dict={},
                    prop_dict={'SpecialSort': 'bottom'},
                )
            )

    return episodes, sort, ascending


def get_single_episode(episode_id):
    """Get single episode"""
    title_item = None
    episode = get_single_episode_data(episode_id).get('data').get('page')
    if episode is not None:
        _, _, _, title_item = convert_episode(episode)
    return title_item


def get_latest_episode(program_name):
    """Get the latest episode of a program"""
    latest_episode = {}
    video = None
    latest_episode = get_latest_episode_data(program_name=program_name)
    if latest_episode:
        _, _, _, title_item = convert_episode(latest_episode)
        video = {
            'listitem': title_item,
            'video_id': title_item.path.split('/')[5],
            'publication_id': title_item.path.split('/')[6],
        }
    return video


def get_offline_programs(end_cursor='', use_favorites=False):
    """Get laatste kans/soon offline programs"""
    list_id = 'dynamic:/vrtnu.model.json@par_list_1624607593_copy_1408213323'
    destination = 'favorites_offline' if use_favorites else 'offline'
    programs = get_programs(list_id=list_id, destination=destination, end_cursor=end_cursor, use_favorites=use_favorites)
    return programs


def get_favorite_programs(end_cursor=''):
    """Get favorite programs"""
    import base64
    list_id = 'o%25|o%9|video-program%|video-program|b%0%'
    list_id = '${}'.format(base64.b64encode(list_id.encode('utf-8')).decode('utf-8'))
    programs = get_programs(list_id=list_id, destination='favorites_programs', end_cursor=end_cursor)
    return programs


def get_featured(feature=None, end_cursor=''):
    """Get featured menu items"""
    content = 'files'
    sort = 'unsorted'
    ascending = True
    if feature:
        if feature.startswith('program_'):
            list_id = feature.replace('_proto_', ':/').split('program_')[1]
            programs = get_programs(list_id=list_id, destination='featured', end_cursor=end_cursor, feature=feature)
            return programs, sort, ascending, 'tvshows'

        if feature.startswith('episode_'):
            list_id = feature.replace('_proto_', ':/').split('episode_')[1]
            episodes, sort, ascending, content = get_episodes(list_id=list_id, destination='featured', end_cursor=end_cursor, feature=feature)
            return episodes, sort, ascending, content
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


def get_search(keywords, end_cursor=''):
    """Get search items"""
    import base64
    from json import dumps
    query_string = None
    destination = None

    entity_types = ['video-program', 'video-episode']
    programs = []
    episodes = []
    items = []

    for entity_type in entity_types:
        facets = []
        if keywords:
            destination = 'search_query'
            query_string = keywords
        facets.append({
            'name': 'entitytype',
            'values': [entity_type],
        })
        if entity_type == 'video-program':
            result_type = 'watch'
        else:
            result_type = entity_type
        search_dict = {
            'facets': facets,
            'resultType': result_type,
        }
        if query_string:
            search_dict['q'] = query_string

        list_id = 'o%14|{}|{}%'.format(dumps(search_dict), result_type)
        list_id = '${}'.format(base64.b64encode(list_id.encode('utf-8')).decode('utf-8'))

        if entity_type == 'video-program' and not end_cursor:
            programs = get_programs(keywords=keywords, end_cursor=end_cursor)
            items.extend(programs)
        elif entity_type == 'video-episode':
            episodes, _, _, _, = get_episodes(list_id=list_id, destination=destination, end_cursor=end_cursor, keywords=keywords)
            items.extend(episodes)
    return items


def get_programs(list_id=None, destination=None, end_cursor='', category=None, channel=None, keywords=None, feature=None, use_favorites=False):
    """Get programs"""

    if not list_id:
        import base64
        from json import dumps
        query_string = None
        facets = []
        if category:
            facet_name = 'genre'
            # VRT MAX uses 'contenttype' facet name instead of 'genre' for some categories
            if category in ('docu', 'films', 'series', 'talkshows'):
                facet_name = 'contenttype'
            destination = 'categories'
            facets.append({
                'name': facet_name,
                'values': [category],
            })
        elif channel:
            destination = 'channels'
            facets.append({
                'name': 'brand',
                'values': [channel]
            })
        elif keywords:
            destination = 'search_query'
            query_string = keywords
        facets.append({
            'name': 'entitytype',
            'values': ['video-program'],
        })
        search_dict = {
            'facets': facets,
            'resultType': 'watch',
        }
        if query_string:
            search_dict['q'] = query_string

        list_id = 'o%14|{}|{}%'.format(dumps(search_dict), 'watch')
        list_id = '${}'.format(base64.b64encode(list_id.encode('utf-8')).decode('utf-8'))

    # kodi paging
    kodi_page_size = get_setting_int('itemsperpage', default=50)
    fetched = 0
    item_list = []
    while fetched < kodi_page_size:
        page_size = kodi_page_size - fetched
        api_data = get_entities(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
        paginated = api_data.get('data', {}).get('list', {}).get('paginatedItems', {})
        edges = paginated.get('edges', [])
        page_info = paginated.get('pageInfo', {})
        item_list.extend(edges)
        fetched += len(edges)
        if not page_info.get('hasNextPage'):
            end_cursor = ''
            break
        end_cursor = page_info.get('endCursor')

    programs = convert_programs(item_list, destination=destination, end_cursor=end_cursor, category=category,
                                channel=channel, feature=feature, keywords=keywords, use_favorites=use_favorites)
    return programs


def get_continue_episodes(end_cursor=''):
    """Get continue episodes"""
    list_id = 'dynamic:/vrtnu.model.json@resume-list-video'
    destination = 'resumepoints_continue'
    episodes, sort, ascending, content = get_episodes(list_id=list_id, destination=destination, end_cursor=end_cursor)
    return episodes, sort, ascending, content


def get_recent_episodes(end_cursor='', use_favorites=False):
    """Get recent episodes"""
    list_id = 'static:/vrtnu/kijk.model.json@par_list_copy_copy_copy'
    destination = 'favorites_recent' if use_favorites else 'recent'
    episodes, sort, ascending, content = get_episodes(list_id=list_id, destination=destination, end_cursor=end_cursor)
    return episodes, sort, ascending, content


def get_episodes(list_id=None, destination=None, end_cursor='', program_name=None, season_name=None, use_favorites=False,
                 feature=None, keywords=None, date=None, channel=None):
    """Get episodes"""
    sort = 'unsorted'
    ascending = True
    content = 'files'

    if not list_id:
        if season_name is None:
            # Check for multiple seasons
            api_data = get_seasons(program_name)
            number_of_seasons = len(api_data)
            if number_of_seasons == 1 and api_data[0].get('list_id'):
                destination = 'programs'
                list_id = api_data[0].get('list_id')
                season_name = list_id.split('@')[-1]
            else:
                seasons = convert_seasons(api_data, program_name)
                return seasons, sort, ascending, content

        # reconstruct list_id from program_name and season_name
        if program_name and season_name:
            destination = 'programs'
            if season_name.startswith('parsys'):
                list_id = 'static:/vrtnu/a-z/{}.model.json@{}'.format(program_name, season_name)
            elif season_name.startswith('dynamic_'):
                list_id = 'dynamic:/vrtnu/a-z/{}.model.json@{}'.format(program_name, season_name.split('dynamic_')[1])
            else:
                list_id = 'static:/vrtnu/a-z/{}/{}.episodes-list.json'.format(program_name, season_name)

    # kodi paging
    kodi_page_size = get_setting_int('itemsperpage', default=50)
    fetched = 0
    item_list = []
    while fetched < kodi_page_size:
        page_size = kodi_page_size - fetched
        api_data = get_entities(list_id=list_id, page_size=page_size, end_cursor=end_cursor)
        paginated = api_data.get('data', {}).get('list', {}).get('paginatedItems', {})
        edges = paginated.get('edges', [])
        page_info = paginated.get('pageInfo', {})
        item_list.extend(edges)
        fetched += len(edges)
        if not page_info.get('hasNextPage'):
            end_cursor = ''
            break
        end_cursor = page_info.get('endCursor')

    episodes, sort, ascending = convert_episodes(item_list, destination=destination, end_cursor=end_cursor, use_favorites=use_favorites,
                                                 program_name=program_name, season_name=season_name, feature=feature, keywords=keywords,
                                                 date=date, channel=channel)
    return episodes, sort, ascending, 'episodes'


def convert_seasons(api_data, program_name):
    """Convert seasons"""
    seasons = []
    for season in api_data:
        if season.get('path'):
            episode_tile = season.get('episode_tile')
            if not episode_tile:
                episode_tile = get_single_episode_data(season.get('path')).get('data').get('page')

            _, _, _, title_item = convert_episode(episode_tile)
            if len(api_data) > 1:
                season_title = '[B]{}:[/B] {}'.format(season.get('title'), title_item.label)
            elif title_item.info_dict['tvshowtitle'] != title_item.label:
                season_title = '[B]{}:[/B] {}'.format(title_item.info_dict['tvshowtitle'], title_item.label)
            else:
                season_title = title_item.label

            title_item.label = season_title
            title_item.info_dict['title'] = season_title
            seasons.append(title_item)

        elif season.get('list_id'):
            season_title = season.get('title')

            # season name
            list_id = season.get('list_id')
            if '.episodes-list.json' in list_id:
                season_name = list_id.split('.episodes-list.json')[0].split('/')[-1]
            elif list_id.startswith('dynamic:/'):
                season_name = 'dynamic_' + list_id.split('@')[-1]
            else:
                season_name = list_id.split('@')[-1]

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


def get_seasons(program_name):
    """Fetch seasons for a program, return list of dicts with title, episode, and either path or list_id."""
    data = get_seasons_data(program_name)
    program = (data.get('data') or {}).get('page', {}).get('program', {})
    seasons = []

    def get_episode_from_component(component):
        if not component or component.get('tileContentType') != 'episode':
            return {}
        items = component.get('items')
        if items:
            return random.choice(items).get('episode', {})
        list_id = component.get('listId')
        if not list_id:
            return {}
        for se in program.get('seasons', []):
            if component.get('title', '').startswith(se.get('titleRaw', '')):
                items = (se.get('episodeList') or {}).get('items') or []
                if items:
                    return random.choice(items).get('episode', {})
        return {}

    def add_entry(title, episode=None, list_id=None, path=None):
        entry = {'title': title, 'episode': episode or {}}
        if list_id:
            entry['list_id'] = list_id
        elif path:
            entry['path'] = path
        seasons.append(entry)

    def handle_component(title, component):
        if component and component.get('tileContentType') == 'episode':
            episode = get_episode_from_component(component)
            add_entry(title, episode, list_id=component.get('listId'))

    def find_episode_by_id(target_id):
        for se in program.get('seasons', []):
            for ep in se.get('episodeList', {}).get('items', []):
                episode = ep.get('episode') or {}
                if target_id == episode.get('id'):
                    return episode
        return {}

    # Process all navigation-based entries
    navigation_items = (program.get('navigation') or {}).get('items', []) or []

    for item in navigation_items:
        action = item.get('action', {})

        if action.get('component'):
            handle_component(item.get('title'), action['component'])
            continue

        if action.get('items'):
            for subitem in action['items']:
                comp = (subitem.get('action') or {}).get('component')
                handle_component(subitem.get('title') or item.get('title'), comp)
            continue

        if action.get('videoUrl'):
            episode = find_episode_by_id(action.get('episodeId'))
            add_entry(item.get('title'), episode=episode, path=action['videoUrl'])
        elif action.get('page'):
            if action.get('page').get('episode'):
                add_entry(item.get('title'), episode=action.get('page').get('episode'), path=action['link'])

    # Prepend most relevant episode if no entries or more than one entry
    if not seasons or len(seasons) > 1:
        tile = program.get('mostRelevantEpisodeTile')
        if tile:
            episode = (tile.get('tile', {}).get('episode', {}))
            path = episode.get('shareAction', {}).get('url')

            # Build entry
            entry = {
                'title': tile.get('title'),
                'episode': episode,
                'path': path,
            }

            # Only insert if path is not already present
            if not any(s.get('path') == path for s in seasons):
                seasons.insert(0, entry)

    return seasons


def api_req(graphql_query, operation_name, variables, client='WEB'):
    """GraphQL API Request"""
    from json import dumps
    from tokenresolver import TokenResolver
    access_token = TokenResolver().get_token('vrtnu-site_profile_at')
    data_json = {}
    if access_token:
        payload = {
            'operationName': operation_name,
            'query': graphql_query,
            'variables': variables,
        }
        data = dumps(payload).encode('utf-8')
        headers = {
            'Accept': 'application/json',
            'Authorization': 'Bearer ' + access_token,
            'Content-Type': 'application/json',
            'x-vrt-client-name': client,
            'x-vrt-client-version': '1.5.12',
        }
        data_json = get_url_json(url=GRAPHQL_URL, cache=None, headers=headers, data=data)
    return data_json


def get_featured_data():
    """Get featured data"""
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
    operation_name = 'Page'
    variables = {
        'pageId': '/vrtmax/',
        'pageContext': {
            'mediaType': 'watch'
        },
        'componentAfter': '',
        'componentCount': 50,
    }
    return api_req(graphql_query, operation_name, variables)


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
            ... on IIdentifiable {
              __typename
              objectId
            }
            ... on IPage {
              paginatedComponents(first: $componentCount, after: $componentAfter) {
                __typename
                edges {
                  __typename
                  node {
                    ... on PaginatedTileList {
                      __typename
                      objectId
                      listId
                      displayType
                      paginatedItems(first: $lazyItemCount, after: $after, before: $before) {
                        __typename
                        edges {
                          __typename
                          cursor
                          node {
                            __typename
                          }
                        }
                        pageInfo {
                          __typename
                          endCursor
                          hasNextPage
                          hasPreviousPage
                          startCursor
                        }
                      }
                      tileContentType
                      title
                      description
                      __typename
                    }
                    ... on StaticTileList {
                      __typename
                      objectId
                      listId
                      title
                      tileContentType
                      displayType
                      items {
                        ... on ButtonTile {
                          mode
                          title
                          id
                          objectId
                          action {
                            ... on LinkAction {
                              link
                              internalTarget
                              externalTarget
                              __typename
                            }
                          }
                          tileType
                          image {
                            templateUrl
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
                __typename
              }
              __typename
            }
            __typename
          }
        }
    """
    operation_name = 'Page'
    variables = {
        'pageId': '/vrtmax/zoeken/',
    }
    categories_json = api_req(graphql_query, operation_name, variables)
    if categories_json is not None:
        from json import loads
        edges = categories_json.get('data', {}).get('page', {}).get('paginatedComponents', {}).get('edges', [])
        content_types = next(
            (
                item.get('node')
                for item in edges
                if item.get('node', {}).get('listId') == 'initialsearchcontenttypes'
            ),
            {}
        ).get('items', [])
        genres = next(
            (
                item.get('node')
                for item in edges
                if item.get('node', {}).get('listId') == 'initialsearchgenres'
            ),
            {}
        ).get('items', [])
        category_items = content_types + genres
        for category in category_items:
            # Don't add audio-only categories
            if category.get('title') in ('Podcasts', 'Radio'):
                continue
            category_id = loads(unquote(category.get('action').get('link')).split('?facets=')[1])[0].get('values')[0]
            categories.append({
                'id': category_id,
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


def get_episode_by_air_date(channel_name, start_date, end_date=None):
    """Get an episode of a program given the channel and the air date in iso format (2024-10-04T19:35:00)"""
    channel = find_entry(CHANNELS, 'name', channel_name)
    if not channel:
        return None

    from datetime import datetime, timedelta
    import dateutil.parser
    import dateutil.tz
    offairdate = None
    try:
        onairdate = dateutil.parser.parse(start_date, default=datetime.now(dateutil.tz.gettz('Europe/Brussels')))
    except ValueError:
        return None

    if end_date:
        try:
            offairdate = dateutil.parser.parse(end_date, default=datetime.now(dateutil.tz.gettz('Europe/Brussels')))
        except ValueError:
            return None
    video = None
    now = datetime.now(dateutil.tz.gettz('Europe/Brussels'))
    if onairdate.hour < 6:
        schedule_date = onairdate - timedelta(days=1)
    else:
        schedule_date = onairdate
    schedule_datestr = schedule_date.isoformat().split('T')[0]
    url = 'https://www.vrt.be/bin/epg/schedule.{date}.json'.format(date=schedule_datestr)
    schedule_json = get_url_json(url, fail={})
    episodes = schedule_json.get(channel.get('id'), [])
    if not episodes:
        return None

    # Guess the episode
    episode_guess = None
    if not offairdate:
        mindate = min(abs(onairdate - dateutil.parser.parse(episode.get('startTime'))) for episode in episodes)
        episode_guess = next((episode for episode in episodes if abs(onairdate - dateutil.parser.parse(episode.get('startTime'))) == mindate), None)
    else:
        duration = offairdate - onairdate
        midairdate = onairdate + timedelta(seconds=duration.total_seconds() / 2)
        mindate = min(abs(midairdate
                          - (dateutil.parser.parse(episode.get('startTime'))
                             + timedelta(seconds=(dateutil.parser.parse(episode.get('endTime'))
                                                  - dateutil.parser.parse(episode.get('startTime'))).total_seconds() / 2))) for episode in episodes)
        episode_guess = next((episode for episode in episodes
                              if abs(midairdate
                                     - (dateutil.parser.parse(episode.get('startTime'))
                                        + timedelta(seconds=(dateutil.parser.parse(episode.get('endTime'))
                                                             - dateutil.parser.parse(episode.get('startTime'))).total_seconds() / 2))) == mindate), None)
    if episode_guess:
        if episode_guess.get('episodeId'):
            episode = get_single_episode_data(episode_guess.get('url')).get('data').get('page')
            if episode.get('available'):
                log(2, 'Guessed available episode {item}', item=episode_guess.get('url'))
                _, _, _, video_item = convert_episode(episode)
                video = {
                    'listitem': video_item,
                    'video_url': episode.get('episode').get('shareAction').get('url'),
                }
                if video:
                    return video

        # Airdate live2vod feature: use livestream cache of last 24 hours if no video was found
        offairdate_guess = dateutil.parser.parse(episode_guess.get('endTime'))
        if now - timedelta(hours=LIVESTREAM_CACHE_HOURS) <= dateutil.parser.parse(episode_guess.get('endTime')) <= now:
            start_date = onairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19]
            end_date = offairdate_guess.astimezone(dateutil.tz.UTC).isoformat()[0:19]

        # Offairdate defined
        if offairdate and now - timedelta(hours=LIVESTREAM_CACHE_HOURS) <= offairdate <= now:
            start_date = onairdate.astimezone(dateutil.tz.UTC).isoformat()[:19]
            end_date = offairdate.astimezone(dateutil.tz.UTC).isoformat()[:19]

        if start_date and end_date:
            live2vod_title = '{} ({})'.format(episode_guess.get('title'), localize(30454))  # from livestream cache
            log(2, live2vod_title)
            video_item = TitleItem(
                label=live2vod_title,
                info_dict={
                    'tvshowtitle': live2vod_title,
                    'aired': start_date[:10],
                    'year': int(start_date[:4]),
                    'mediatype': 'episode',
                },
                art_dict={
                    'thumb': episode_guess.get('image'),
                    'poster': episode_guess.get('image'),
                    'banner': episode_guess.get('image'),
                    'fanart': episode_guess.get('image'),
                },
            )
            video = {
                'listitem': video_item,
                'video_id': channel.get('live_stream_id'),
                'start_date': start_date,
                'end_date': end_date,
            }
            return video

        video = {
            'errorlabel': episode_guess.get('title')
        }
    return video


def get_channels(channels=None, live=True):
    """Construct a list of channel ListItems, either for Live TV or the TV Guide listing"""
    from tvguide import TVGuide
    _tvguide = TVGuide()

    channel_items = []
    for channel in CHANNELS:
        if channels and channel.get('name') not in channels:
            continue

        context_menu = []
        art_dict = {}
        path = None

        # Try to use the white icons for thumbnails (used for icons as well)
        if has_addon('resource.images.studios.white'):
            art_dict['thumb'] = 'resource://resource.images.studios.white/{studio}.png'.format(**channel)
        else:
            art_dict['thumb'] = 'DefaultTags.png'

        if not live:
            path = url_for('channels', channel=channel.get('name'))
            label = channel.get('label')
            plot = '[B]%s[/B]' % channel.get('label')
            is_playable = False
            info_dict = {'title': label, 'plot': plot, 'studio': channel.get('studio'), 'mediatype': 'video'}
            stream_dict = []
            prop_dict = {}
        elif channel.get('live_stream') or channel.get('live_stream_id'):
            if channel.get('live_stream_id'):
                path = url_for('play_id', video_id=channel.get('live_stream_id'))
            elif channel.get('live_stream'):
                path = url_for('play_url', video_url=channel.get('live_stream'))
            label = localize(30141, **channel)  # Channel live
            playing_now = _tvguide.playing_now(channel.get('name'))
            if playing_now:
                label += ' [COLOR=yellow]| %s[/COLOR]' % playing_now
            # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
            if channels and len(channels) == 1:
                label = '[B]%s[/B]' % label
            is_playable = True
            if channel.get('name') in ['een', 'canvas', 'ketnet']:
                if get_setting_bool('showfanart', default=True):
                    art_dict['fanart'] = get_live_screenshot(channel.get('name', art_dict.get('fanart')))
                plot = '%s\n\n%s' % (localize(30142, **channel), _tvguide.live_description(channel.get('name')))
            else:
                plot = localize(30142, **channel)  # Watch live
            # NOTE: Playcount and resumetime are required to not have live streams as "Watched" and resumed
            info_dict = {'title': label, 'plot': plot, 'studio': channel.get('studio'), 'mediatype': 'video', 'playcount': 0, 'duration': 0}
            prop_dict = {'resumetime': 0}
            stream_dict = {'duration': 0}
            context_menu.append((
                localize(30413),  # Refresh menu
                'RunPlugin(%s)' % url_for('delete_cache', cache_file='channel.{channel}.json'.format(channel=channel)),
            ))
        else:
            # Not a playable channel
            continue

        channel_items.append(TitleItem(
            label=label,
            path=path,
            art_dict=art_dict,
            info_dict=info_dict,
            prop_dict=prop_dict,
            stream_dict=stream_dict,
            context_menu=context_menu,
            is_playable=is_playable,
        ))

    return channel_items


def get_youtube(channels=None):
    """Construct a list of youtube ListItems, either for Live TV or the TV Guide listing"""

    youtube_items = []

    if not has_addon('plugin.video.youtube') or not get_setting_bool('showyoutube', default=True):
        return youtube_items

    for channel in CHANNELS:
        if channels and channel.get('name') not in channels:
            continue

        art_dict = {}

        # Try to use the white icons for thumbnails (used for icons as well)
        if has_addon('resource.images.studios.white'):
            art_dict['thumb'] = 'resource://resource.images.studios.white/{studio}.png'.format(**channel)
        else:
            art_dict['thumb'] = 'DefaultTags.png'

        for youtube in channel.get('youtube', []):
            path = youtube_to_plugin_url(youtube['url'])
            label = localize(30143, **youtube)  # Channel on YouTube
            # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
            if channels and len(channels) == 1:
                label = '[B]%s[/B]' % label
            plot = localize(30144, **youtube)  # Watch on YouTube
            # NOTE: Playcount is required to not have live streams as "Watched"
            info_dict = {'title': label, 'plot': plot, 'studio': channel.get('studio'), 'mediatype': 'video', 'playcount': 0}

            context_menu = [(
                localize(30413),  # Refresh menu
                'RunPlugin(%s)' % url_for('delete_cache', cache_file='channel.{channel}.json'.format(channel=channel)),
            )]

            youtube_items.append(TitleItem(
                label=label,
                path=path,
                art_dict=art_dict,
                info_dict=info_dict,
                context_menu=context_menu,
                is_playable=False,
            ))

    return youtube_items


def get_live_screenshot(channel):
    """Get a live screenshot for a given channel, only supports VRT 1, Canvas and Ketnet"""
    url = '%s/%s.jpg' % (SCREENSHOT_URL, channel)
    delete_cached_thumbnail(url)
    return url

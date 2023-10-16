
# ----------------------------------------------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.viwx.
#  SPDX-License-Identifier: GPL-2.0-or-later
#  See LICENSE.txt
# ----------------------------------------------------------------------------------------------------------------------

import json
import logging
import pytz

from codequick.support import logger_id

from . import utils
from .errors import ParseError


logger = logging.getLogger(logger_id + '.parse')

# NOTE: The resolutions below are those specified by Kodi for their respective usage. There is no guarantee that
#       the image returned by itvX is of that exact resolution.
IMG_PROPS_THUMB = {'treatment': 'title', 'aspect_ratio': '16x9', 'class': '04_DesktopCTV_RailTileLandscape',
                   'distributionPartner': '', 'fallback': 'standard', 'width': '960', 'height': '540',
                   'quality': '80', 'blur': 0, 'bg': 'false', 'image_format': 'jpg'}
IMG_PROPS_POSTER = {'treatment': 'title', 'aspect_ratio': '2x3', 'class': '07_RailTilePortrait',
                    'distributionPartner': '', 'fallback': 'standard', 'width': '1000', 'height': '1500',
                    'quality': '80', 'blur': 0, 'bg': 'false', 'image_format': 'jpg'}
IMG_PROPS_FANART = {'treatment': '', 'aspect_ratio': '16x9', 'class': '01_Hero_DesktopCTV',
                    'distributionPartner': '', 'fallback': 'standard', 'width': '1920', 'height': '1080',
                    'quality': '80', 'blur': 0, 'bg': 'false', 'image_format': 'jpg'}


url_trans_table = str.maketrans(' ', '-', '#/?:\'')


def build_url(programme, programme_id, episode_id=None):
    progr_slug = (programme.lower()
                           .replace('&', 'and')
                           .replace(' - ', '-')
                           .translate(url_trans_table))
    base_url = ('https://www.itv.com/watch/' + progr_slug)
    if episode_id:
        return '/'.join((base_url, programme_id, episode_id))
    else:
        return '/'.join((base_url, programme_id))


def premium_plot(plot: str):
    """Add a notice of paid or premium content tot the plot."""
    return '\n'.join(('[COLOR yellow]itvX premium[/COLOR]', plot))


def sort_title(title: str):
    """Return a string te be used as sort title of `title`

    The returned sort title is lowercase and stripped of a possible leading 'The'
    """
    l_title = title.lower()
    return l_title[4:] if l_title.startswith('the ') else l_title


def scrape_json(html_page):
    # noinspection GrazieInspection
    """Return the json data embedded in a script tag on an html page"""
    import re
    result = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html_page, flags=re.DOTALL)
    if result:
        json_str = result[1]
        try:
            data = json.loads(json_str)
            return data['props']['pageProps']
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning("__NEXT_DATA__ in HTML page has unexpected format: %r", e)
            raise ParseError('Invalid data received')
    raise ParseError('No data available')


# noinspection PyTypedDict
def parse_hero_content(hero_data):
    # noinspection PyBroadException
    try:
        item_type = hero_data['contentType']
        title = hero_data['title']
        item = {
            'label': title,
            'art': {'thumb': hero_data['imageTemplate'].format(**IMG_PROPS_THUMB),
                    'fanart': hero_data['imageTemplate'].format(**IMG_PROPS_FANART)},
            'info': {'title': ''.join(('[B][COLOR orange]', title, '[/COLOR][/B]'))}
        }

        brand_img = hero_data.get('brandImageTemplate')
        if brand_img:
            item['art']['fanart'] = brand_img.format(**IMG_PROPS_FANART)

        if item_type in ('simulcastspot', 'fastchannelspot'):
            item['params'] = {'channel': hero_data['channel'], 'url': None}
            item['info'].update(plot='[B]Watch Live[/B]\n' + hero_data.get('description', ''))

        elif item_type in ('series', 'brand'):
            item['info'].update(plot=''.join((hero_data.get('ariaLabel', ''), '\n\n', hero_data.get('description'))))
            item['params'] = {'url': build_url(title, hero_data['encodedProgrammeId']['letterA']),
                              'series_idx': hero_data.get('series')}

        elif item_type in ('special', 'film'):
            item['info'].update(plot=''.join(('[B]Watch ',
                                              'FILM' if item_type == 'film' else 'NOW',
                                              '[/B]\n',
                                              hero_data.get('description'))),
                                duration=utils.duration_2_seconds(hero_data.get('duration')))
            item['params'] = {'url': build_url(title, hero_data['encodedProgrammeId']['letterA']),
                              'name': title}

        elif item_type == 'collection':
            item = parse_item_type_collection(hero_data)
            info = item['show']['info']
            info['title'] = ''.join(('[COLOR orange]', info['title'], '[/COLOR]'))
            return item
        else:
            logger.warning("Hero item %s is of unknown type: %s", hero_data['title'], item_type)
            return None
        return {'type': item_type, 'show': item}
    except:
        logger.warning("Failed to parse hero item '%s':\n", hero_data.get('title', 'unknown title'), exc_info=True)


def parse_short_form_slider(slider_data, url=None):
    """Parse a shortFormSlider from the main page or a collection page.

    Returns the link to the collection page associated with the shortFormSlider.

    """
    # noinspection PyBroadException
    try:
        header = slider_data['header']
        link = header.get('linkHref')
        title = header.get('title') or header.get('iconTitle', '')
        if url:
            # A shortFormSlider from a collection page.
            params = {'url': url, 'slider': 'shortFormSlider'}
        elif link:
            # A shortFormSlider from the main page
            params = {'url': 'https://www.itv.com' + link}
        else:
            return

        return {'type': 'collection',
                'show': {'label': title,
                         'params': params,
                         'info': {'sorttitle': sort_title(title)}
                         }
                }
    except:
        logger.error("Unexpected error parsing shorFormSlider.", exc_info=True)
        return None


def parse_slider(slider_name, slider_data):
    """Parse editorialSliders from the main page or from a collection."""
    # noinspection PyBroadException
    try:
        coll_data = slider_data['collection']
        page_link = coll_data.get('headingLink')
        base_url = 'https://www.itv.com/watch'
        if page_link:
            # Link to the collection's page if available
            params = {'url': base_url + page_link['href']}
        else:
            # Provide the slider name when the collection content is to be obtained from the main page.
            params = {'slider': slider_name}

        return {'type': 'collection',
                'show': {'label': coll_data['headingTitle'],
                         'params': params,
                         'info': {'sorttitle': sort_title(coll_data['headingTitle'])}}}
    except:
        logger.error("Unexpected error parsing editorialSlider %s", slider_name, exc_info=True)
        return None


def parse_collection_item(show_data, hide_paid=False):
    """Parse a show item from a collection page

    Very much like category content, but not just quite.

    """
    # noinspection PyBroadException
    try:
        content_type = show_data.get('contentType') or show_data['type']
        is_playable = content_type in ('episode', 'film', 'special', 'title', 'fastchannelspot', 'simulcastspot')
        title = show_data['title']
        content_info = show_data.get('contentInfo', '')

        if content_type == 'collection':
            return parse_item_type_collection(show_data)

        if show_data.get('isPaid'):
            if hide_paid:
                return None
            plot = premium_plot(show_data['description'])
        else:
            plot = show_data['description']

        programme_item = {
            'label': title,
            'art': {'thumb': show_data['imageTemplate'].format(**IMG_PROPS_THUMB),
                    'fanart': show_data['imageTemplate'].format(**IMG_PROPS_FANART)},
            'info': {'title': title if is_playable else '[B]{}[/B] {}'.format(title, content_info),
                     'plot': plot,
                     'sorttitle': sort_title(title)},
        }

        if content_type in ('fastchannelspot', 'simulcastspot'):
            programme_item['params'] = {'channel': show_data['channel'], 'url': None}
            # TODO: Enable watch from the start on simulcastspots
        else:
            programme_item['params'] = {'url': build_url(show_data['titleSlug'],
                                        show_data['encodedProgrammeId']['letterA'],
                                        show_data.get('encodedEpisodeId', {}).get('letterA'))}

        if 'FILMS' in show_data.get('categories', ''):
            programme_item['art']['poster'] = show_data['imageTemplate'].format(**IMG_PROPS_POSTER)

        if is_playable:
            programme_item['info']['duration'] = utils.duration_2_seconds(content_info)
        return {'type': content_type,
                'show': programme_item}
    except Exception as err:
        logger.warning("Failed to parse collection_item: %r\n%s", err, json.dumps(show_data, indent=4))
        return None


# noinspection GrazieInspection
def parse_shortform_item(item_data, time_zone, time_fmt, hide_paid=False):
    """Parse an item from a shortFormSlider.

    ShortFormSliders are found on the main page, some collection pages.
    Items from heroAndLatest and curatedRails in category news also have a shortForm-like content.

    """
    """Parse data found in news collection and in short news clips from news sub-categories

    """
    try:
        if 'encodedProgrammeId' in item_data.keys():
            # The news item is a 'normal' catchup title. Is usually just the latest ITV news.
            # Do not use field 'href' as it is known to have non-a-encoded program and episode Id's which doesn't work.
            url = '/'.join(('https://www.itv.com/watch',
                            item_data['titleSlug'],
                            item_data['encodedProgrammeId']['letterA'],
                            item_data.get('encodedEpisodeId', {}).get('letterA', ''))).rstrip('/')
        else:
            # This item is a 'short item', aka 'news clip'.
            href = item_data.get('href', '/watch/news/undefined')
            url = ''.join(('https://www.itv.com', href, '/', item_data['episodeId']))

        # dateTime field occasionally has milliseconds. Strip these when present.
        item_time = pytz.UTC.localize(utils.strptime(item_data['dateTime'][:19], '%Y-%m-%dT%H:%M:%S'))
        loc_time = item_time.astimezone(time_zone)
        title = item_data.get('episodeTitle')
        plot = '\n'.join((loc_time.strftime(time_fmt), item_data.get('synopsis', title)))

        # Does paid news exists?
        if item_data.get('isPaid'):
            if hide_paid:
                return None
            plot = premium_plot(plot)

        # TODO: consider adding poster image, but it is not always present.
        #       Add date.
        return {
            'type': 'title',
            'show': {
                'label': title,
                'art': {'thumb': item_data['imageUrl'].format(**IMG_PROPS_THUMB)},
                'info': {'plot': plot, 'sorttitle': sort_title(title), 'duration': item_data.get('duration')},
                'params': {'url': url}
            }
        }
    except Exception as err:
        logger.error("Unexpected error parsing a shortForm item: %r\n%s", err, json.dumps(item_data, indent=4))
        return None


def parse_trending_collection_item(trending_item, hide_paid=False):
    """Parse an item in the collection 'Trending'
    The only real difference with the regular parse_collection_item() is
    adding field `contentInfo` to plot and the fact that all items are being
    treated as playable.

    """
    try:
        # No idea if premium content can be trending, but just to be sure.
        plot = '\n'.join((trending_item['description'], trending_item['contentInfo']))
        if trending_item.get('isPaid'):
            if hide_paid:
                return None
            plot = premium_plot(plot)

        # NOTE:
        # Especially titles of type 'special' may lack a field encodedEpisodeID. For those titles it
        # should not be necessary, but for episodes they are a requirement otherwise the page
        # will always return the first episode.

        return {
            'type': 'title',
            'show': {
                'label': trending_item['title'],
                'art': {'thumb': trending_item['imageUrl'].format(**IMG_PROPS_THUMB)},
                'info': {'plot': plot, 'sorttitle': sort_title(trending_item['title'])},
                'params': {'url': build_url(trending_item['titleSlug'],
                                            trending_item['encodedProgrammeId']['letterA'],
                                            trending_item.get('encodedEpisodeId', {}).get('letterA'))}
            }
        }
    except Exception:
        logger.warning("Failed to parse trending_collection_item:\n%s", json.dumps(trending_item, indent=4))
        return None


def parse_category_item(prog, category):
    # At least all items without an encodedEpisodeId are playable.
    # Unfortunately there are items that do have an episodeId, but are in fact single
    # episodes, and thus playable, but there is no reliable way of detecting these,
    # since category items lack a field like `contentType`.
    # The previous method of detecting the presence of 'series' in contentInfo proved
    # to be very unreliable.
    #
    # All items with episodeId are returned as series folder, with the odd change some
    # contain only one item.

    is_playable = prog['encodedEpisodeId']['letterA'] == ''
    playtime = utils.duration_2_seconds(prog['contentInfo'])
    title = prog['title']

    if 'FREE' in prog['tier']:
        plot = prog['description']
    else:
        plot = premium_plot(prog['description'])

    programme_item = {
        'label': title,
        'art': {'thumb': prog['imageTemplate'].format(**IMG_PROPS_THUMB),
                'fanart': prog['imageTemplate'].format(**IMG_PROPS_FANART)},
        'info': {'title': title if is_playable
                          else '[B]{}[/B] {}'.format(title, prog['contentInfo'] if not playtime else ''),
                 'plot': plot,
                 'sorttitle': sort_title(title)},
    }

    if category == 'films':
        programme_item['art']['poster'] = prog['imageTemplate'].format(**IMG_PROPS_POSTER)

    if is_playable:
        programme_item['info']['duration'] = playtime
        programme_item['params'] = {'url': build_url(title, prog['encodedProgrammeId']['letterA'])}
    else:
        programme_item['params'] = {'url': build_url(title,
                                                     prog['encodedProgrammeId']['letterA'],
                                                     prog['encodedEpisodeId']['letterA'])}
    return {'type': 'title' if is_playable else 'series',
            'show': programme_item}


def parse_item_type_collection(item_data):
    """Parse an item of type 'collection' found in heroContent or a collection.
    The collection items refer to another collection.

    .. note::
        Only items from heroContent seem to have a field `ctaLabel`.

    """
    title = item_data['title']
    item = {
        'label': title,
        'art': {'thumb': item_data['imageTemplate'].format(**IMG_PROPS_THUMB),
                'fanart': item_data['imageTemplate'].format(**IMG_PROPS_FANART)},
        'info': {'title': '[B]{}[/B]'.format(title),
                 'plot': item_data.get('ctaLabel', 'Collection'),
                 'sorttitle': sort_title(title)},
        'params': {'url': '/'.join(('https://www.itv.com/watch/collections',
                                    item_data.get('titleSlug', ''),
                                    item_data.get('collectionId')))}
    }
    return {'type': 'collection', 'show': item}


def parse_episode_title(title_data, brand_fanart=None):
    """Parse a title from episodes listing"""
    # Note: episodeTitle may be None
    title = title_data['episodeTitle'] or title_data['heroCtaLabel']
    img_url = title_data['image']
    plot = '\n\n'.join((title_data['longDescription'], title_data['guidance'] or ''))
    if title_data['premium']:
        plot = premium_plot(plot)

    episode_nr = title_data.get('episode')
    if episode_nr and title_data['episodeTitle'] is not None:
        info_title = '{}. {}'.format(episode_nr, title_data['episodeTitle'])
    else:
        info_title = title_data['heroCtaLabel']

    title_obj = {
        'label': title,
        'art': {'thumb': img_url.format(**IMG_PROPS_THUMB),
                'fanart': brand_fanart,
                # 'poster': img_url.format(**IMG_PROPS_POSTER)
                },
        'info': {'title': info_title,
                 'plot': plot,
                 'duration': int(utils.iso_duration_2_seconds(title_data['notFormattedDuration'])),
                 'date': title_data['dateTime'],
                 'episode': episode_nr,
                 'season': title_data.get('series'),
                 'year': title_data.get('productionYear')},
        'params': {'url': title_data['playlistUrl'], 'name': title}
    }

    return title_obj


def parse_legacy_episode_title(title_data, brand_fanart=None):
    """Parse a title from episodes listing in old format"""
    # Note: episodeTitle may be None
    title = title_data['episodeTitle'] or title_data['numberedEpisodeTitle']
    img_url = title_data['imageUrl']
    plot = '\n\n'.join((title_data['synopsis'], title_data['guidance'] or ''))
    if 'PAID' in title_data.get('tier', []):
        plot = premium_plot(plot)

    title_obj = {
        'label': title,
        'art': {'thumb': img_url.format(**IMG_PROPS_THUMB),
                'fanart': brand_fanart,
                # 'poster': img_url.format(**IMG_PROPS_POSTER)
                },
        'info': {'title': title_data['numberedEpisodeTitle'],
                 'plot': plot,
                 'duration': utils.duration_2_seconds(title_data['duration']),
                 'date': title_data['broadcastDateTime']},
        'params': {'url': title_data['playlistUrl'], 'name': title}
    }
    if title_data['titleType'] == 'EPISODE':
        try:
            episode_nr = int(title_data['episodeNumber'])
        except ValueError:
            episode_nr = None
        try:
            series_nr = int(title_data['seriesNumber'])
        except ValueError:
            series_nr = None
        title_obj['info'].update(episode=episode_nr, season=series_nr)
    return title_obj


def parse_search_result(search_data):
    entity_type = search_data['entityType']
    result_data = search_data['data']
    api_episode_id = ''
    if 'FREE' in result_data['tier']:
        plot = result_data['synopsis']
    else:
        plot = premium_plot(result_data['synopsis'])

    if entity_type == 'programme':
        prog_name = result_data['programmeTitle']
        title = '[B]{}[/B] - {} episodes'.format(prog_name, result_data.get('totalAvailableEpisodes', ''))
        img_url = result_data['latestAvailableEpisode']['imageHref']
        api_prod_id = result_data['legacyId']['officialFormat']

    elif entity_type == 'special':
        # A single programme without episodes
        title = result_data['specialTitle']
        img_url = result_data['imageHref']

        programme = result_data.get('specialProgramme')
        if programme:
            prog_name = result_data['specialProgramme']['programmeTitle']
            api_prod_id = result_data['specialProgramme']['legacyId']['officialFormat']
            api_episode_id = result_data['legacyId']['officialFormat']
        else:
            prog_name = title
            api_prod_id = result_data['legacyId']['officialFormat']

    elif entity_type == 'film':
        prog_name = result_data['filmTitle']
        title = '[B]Film[/B] - ' + result_data['filmTitle']
        img_url = result_data['imageHref']
        api_prod_id = result_data['legacyId']['officialFormat']

    else:
        logger.warning("Unknown search result item entityType %s", entity_type)
        return None

    return {
        'type': entity_type,
        'show': {
            'label': prog_name,
            'art': {'thumb': img_url.format(**IMG_PROPS_THUMB)},
            'info': {'plot': plot,
                     'title': title},
            'params': {'url': build_url(prog_name, api_prod_id.replace('/', 'a'), api_episode_id.replace('/', 'a'))}
        }
    }

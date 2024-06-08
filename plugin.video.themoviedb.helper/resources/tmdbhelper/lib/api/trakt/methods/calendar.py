from tmdbhelper.lib.api.trakt.decorators import is_authorized
from tmdbhelper.lib.files.bcache import use_simple_cache


@is_authorized
def get_calendar(self, trakt_type, user=True, start_date=None, days=None, endpoint=None, **kwargs):
    user = 'my' if user else 'all'
    return self.get_response_json('calendars', user, trakt_type, endpoint, start_date, days, extended='full')


@use_simple_cache(cache_days=0.25)
def get_calendar_episodes(self, startdate=0, days=1, user=True, endpoint=None):
    # Broaden date range in case utc conversion bumps into different day
    from jurialmunkey.parser import try_int
    from tmdbhelper.lib.addon.tmdate import get_datetime_today, get_timedelta
    mod_date = try_int(startdate) - 1
    mod_days = try_int(days) + 2
    date = get_datetime_today() + get_timedelta(days=mod_date)
    return get_calendar(self, 'shows', user, start_date=date.strftime('%Y-%m-%d'), days=mod_days, endpoint=endpoint)


def get_calendar_episode_item(i):
    from jurialmunkey.parser import try_int
    from tmdbhelper.lib.addon.tmdate import convert_timestamp, get_region_date, get_datetime_today
    from tmdbhelper.lib.api.mapping import get_empty_item

    air_date = convert_timestamp(i.get('first_aired'), utc_convert=True)
    epsd = i.get('episode', {})
    show = i.get('show', {})
    sids = show.get('ids', {})
    item = get_empty_item()
    item['label'] = epsd.get('title')
    item['infolabels'] = {
        'mediatype': 'episode',
        'premiered': air_date.strftime('%Y-%m-%d'),
        'year': air_date.strftime('%Y'),
        'title': item['label'],
        'episode': epsd.get('number'),
        'season': epsd.get('season'),
        'tvshowtitle': show.get('title'),
        'duration': try_int(epsd.get('runtime', 0)) * 60,
        'plot': epsd.get('overview'),
        'mpaa': show.get('certification')}
    item['infoproperties'] = {
        'air_date': get_region_date(air_date, 'datelong'),
        'air_time': get_region_date(air_date, 'time'),
        'air_day': air_date.strftime('%A'),
        'air_day_short': air_date.strftime('%a'),
        'air_date_short': air_date.strftime('%d %b')}
    days_to_air = (air_date.date() - get_datetime_today().date()).days
    dtaproperty = 'days_from_aired' if days_to_air < 0 else 'days_until_aired'
    item['infoproperties'][dtaproperty] = str(abs(days_to_air))
    item['infoproperties']['episode_type'] = epsd.get('episode_type')
    item['unique_ids'] = {f'tvshow.{k}': v for k, v in sids.items()}
    item['params'] = {
        'info': 'details',
        'tmdb_type': 'tv',
        'tmdb_id': sids.get('tmdb'),
        'episode': epsd.get('number'),
        'season': epsd.get('season')}
    return item


def get_calendar_episode_item_bool(i, kodi_db, user, startdate, days):
    from tmdbhelper.lib.addon.tmdate import date_in_range
    if kodi_db and not user:
        try:
            sids = i['show']['ids']
        except KeyError:
            return False
        if not kodi_db.get_info(info='dbid', tmdb_id=sids.get('tmdb'), tvdb_id=sids.get('tvdb'), imdb_id=sids.get('imdb')):
            return False
    # Do some timezone conversion so we check that we're in the date range for our timezone
    if not date_in_range(i.get('first_aired'), utc_convert=True, start_date=startdate, days=days):
        return False
    return True


def get_stacked_item(next_item, last_item, stack_info='episodes'):
    # If the next item is the same show then we stack the details onto the last item and add it next iteration
    from jurialmunkey.parser import try_int
    from tmdbhelper.lib.addon.plugin import get_localized
    ip = last_item['infoproperties']

    # First time setup
    if not ip.get('stacked_count'):
        ip['stacked_count'] = 1
        ti = last_item['infolabels']['title']
        se = f'{try_int(last_item["infolabels"]["season"])}x{try_int(last_item["infolabels"]["episode"]):0>2}'
        ep = f'{se}. {ti}'
        ip['stacked_labels'] = ep
        ip['stacked_titles'] = ti
        ip['stacked_episodes'] = se
        ip['stacked_first'] = f'{try_int(last_item["infolabels"].get("season"))}x{try_int(last_item["infolabels"].get("episode")):0>2}'
        ip['stacked_first_episode'] = last_item['infolabels']['episode']
        ip['stacked_first_season'] = last_item['infolabels']['season']
        ip['no_label_formatting'] = True
        last_item['params'].pop('episode', None)
        last_item['params']['info'] = stack_info
        last_item['is_folder'] = True

    # Stacked Setup
    ti = next_item['infolabels']['title']
    se = f'{try_int(next_item["infolabels"]["season"])}x{try_int(next_item["infolabels"]["episode"]):0>2}'
    ep = f'{se}. {ti}'
    ip['stacked_count'] = ip.get('stacked_count', 1) + 1
    ip['stacked_labels'] = f'{ip["stacked_labels"]}, {ep}'
    ip['stacked_titles'] = f'{ip["stacked_titles"]}, {ti}'
    ip['stacked_episodes'] = f'{ip["stacked_episodes"]}, {se}'
    ip['stacked_last'] = se
    ip['stacked_last_episode'] = next_item['infolabels']['episode']
    ip['stacked_last_season'] = next_item['infolabels']['season']
    last_item['label'] = f'{ip["stacked_first"]}-{ip["stacked_last"]}. {ip["stacked_count"]} {get_localized(20360)}'
    return last_item


def stack_calendar_episodes(episode_list, flipped=False, stack_info='episodes'):
    items = []
    last_item = None
    for i in reversed(episode_list) if flipped else episode_list:
        if not last_item:
            last_item = i
            continue

        # If the next item is a different show or day then we stop stacking and add the item
        if (
                last_item['infolabels']['tvshowtitle'] != i['infolabels']['tvshowtitle']
                or last_item['infolabels']['premiered'] != i['infolabels']['premiered']
        ):
            items.append(last_item)
            last_item = i
            continue

        last_item = get_stacked_item(i, last_item, stack_info=stack_info)

    else:  # The last item in the list won't be added in the for loop so do an extra action at the end to add it
        if last_item:
            items.append(last_item)
    return items[::-1] if flipped else items


def stack_calendar_tvshows(self, tvshow_list, flipped=False):
    items, titles = [], []
    for i in reversed(tvshow_list) if flipped else tvshow_list:
        t = i['infolabels']['title']
        if t not in titles:
            items.append(i)
            titles.append(t)
            continue
        x = titles.index(t)
        i = items[x]
        i['infoproperties']['stacked_count'] = i['infoproperties'].get('stacked_count', 0) + 1
    return items[::-1] if flipped else items


@use_simple_cache(cache_days=0.25)
def get_calendar_episodes_listitems(self, startdate=0, days=1, user=True, kodi_db=None, stack=True, endpoint=None, stack_info='episodes'):
    # Get response
    response = get_calendar_episodes(self, startdate=startdate, days=days, user=user, endpoint=endpoint)
    if not response:
        return
    # Reverse items for date ranges in past
    traktitems = reversed(response) if startdate < -1 else response
    items = [get_calendar_episode_item(i) for i in traktitems if get_calendar_episode_item_bool(i, kodi_db, user, startdate, days)]
    if not stack:
        return items
    return stack_calendar_episodes(items, flipped=startdate < -1, stack_info=stack_info)


def get_calendar_episodes_list(self, startdate=0, days=1, user=True, kodi_db=None, page=1, limit=None, endpoint=None):
    from tmdbhelper.lib.addon.plugin import get_setting
    from tmdbhelper.lib.items.pages import PaginatedItems
    limit = limit or self.sync_item_limit
    stack = get_setting('calendar_flatten')
    stack_info = 'details' if kodi_db and get_setting('nextaired_linklibrary') else 'episodes'  # Fix for stacked episodes linking to library
    response_items = get_calendar_episodes_listitems(self, startdate, days, user, kodi_db, stack=stack, endpoint=endpoint, stack_info=stack_info)
    response = PaginatedItems(response_items, page=page, limit=limit)
    if response and response.items:
        return response.items + response.next_page

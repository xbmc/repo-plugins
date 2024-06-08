from tmdbhelper.lib.addon.consts import CACHE_LONG


def get_details(self, trakt_type, trakt_id, season=None, episode=None, extended='full'):
    if not season or not episode:
        return self.get_request_lc(trakt_type + 's', trakt_id, extended=extended)
    return self.get_request_lc(trakt_type + 's', trakt_id, 'seasons', season, 'episodes', episode, extended=extended)


def get_id(self, unique_id, id_type, trakt_type, output_type=None, output_trakt_type=None, season_episode_check=None):
    """
    id_type: imdb, tmdb, trakt, tvdb
    trakt_type: movie, show, episode, person, list
    output_type: trakt, slug, imdb, tmdb, tvdb
    output_trakt_type: optionally change trakt_type for output

    Example usage: self.get_id(1234, 'tmdb', 'episode', 'slug', 'show')
        -- gets trakt slug of the parent show for the episode with tmdb id 1234
    """
    cache_name = f'trakt_get_id.{id_type}.{unique_id}.{trakt_type}.{output_type}'

    # Some plugins incorrectly put TMDb ID for the **tvshow** in the episode instead of the **episode** ID
    # season_episode_check tuple of season/episode numbers is used to bandaid against incorrect metadata
    if trakt_type == 'episode' and season_episode_check is not None:
        cache_name = f'{cache_name}.{season_episode_check[0]}.{season_episode_check[1]}'

    # Avoid unnecessary extra API calls by only adding output type to cache name if it differs from input type
    if output_trakt_type and output_trakt_type != trakt_type:
        cache_name = f'{cache_name}.{output_trakt_type}'

    return self._cache.use_cache(
        self.get_id_search, unique_id, id_type, trakt_type=trakt_type, output_type=output_type, output_trakt_type=output_trakt_type,
        season_episode_check=season_episode_check,
        cache_name=cache_name,
        cache_days=CACHE_LONG)


def get_id_search(self, unique_id, id_type, trakt_type, output_type=None, output_trakt_type=None, season_episode_check=None):
    response = self.get_request_lc('search', id_type, unique_id, type=trakt_type)

    for i in response:
        try:
            if i['type'] != trakt_type:
                continue
            if f'{i[trakt_type]["ids"][id_type]}' != f'{unique_id}':
                continue
            if trakt_type == 'episode' and season_episode_check is not None:
                if f'{i["episode"]["season"]}' != f'{season_episode_check[0]}':
                    continue
                if f'{i["episode"]["number"]}' != f'{season_episode_check[1]}':
                    continue

            if not output_type:
                return i[output_trakt_type or trakt_type]['ids']
            return i[output_trakt_type or trakt_type]['ids'][output_type]

        except (TypeError, KeyError):
            continue


def get_showitem_details(self, i):
    try:
        show, slug = None, None
        show = i['show']
        slug = show['ids']['slug']
    except KeyError:
        pass
    try:
        i_ep, snum, enum = None, None, None
        i_ep = i['episode']
        snum = i_ep['season']
        enum = i_ep['number']
    except KeyError:
        pass
    return {'show': show, 'episode': self.get_details('show', slug, season=snum, episode=enum) or i_ep}


def get_episode_type(self, trakt_id=None, season=None, episode=None):
    if not trakt_id or not episode or not season:
        return
    from contextlib import suppress
    with suppress(KeyError, TypeError):
        return self.get_details('show', trakt_id, season=season, episode=episode)['episode_type']


def get_ratings(self, trakt_type, trakt_id, season=None, episode=None):
    from contextlib import suppress

    def _get_url():
        if episode and season:
            return f'shows/{trakt_id}/seasons/{season}/episodes/{episode}/ratings'
        if season:
            return f'shows/{trakt_id}/seasons/{season}/ratings'
        return f'{trakt_type}s/{trakt_id}/ratings'

    response = self.get_request_sc(_get_url())

    trakt_rating, trakt_votes = None, None
    with suppress(KeyError, TypeError):
        trakt_rating = f'{response["rating"] or 0.0:0.1f}'
        trakt_votes = f'{response["votes"] or 0.0:0,.0f}'

    return (trakt_rating, trakt_votes)

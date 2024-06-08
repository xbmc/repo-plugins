from tmdbhelper.lib.api.tvdb.api import TVDb
from tmdbhelper.lib.api.tmdb.api import TMDb
from tmdbhelper.lib.addon.dialog import ProgressDialog
from tmdbhelper.lib.files.futils import dumps_to_file
from threading import Thread


class AwardsBuilder():
    def __init__(self):
        self.tvdb_api = TVDb()
        self.tmdb_api = TMDb()
        self.listings_tvdb = {'movie': {}, 'series': {}}
        self.listings_tmdb = {'movie': {}, 'tv': {}}
        self._pd = None

    def get_award_nominees(self):

        def _get_category(tvdb_id):
            self._pd.update(f'Getting Categories {tvdb_id}')
            awards_categories = self.tvdb_api.get_request_lc('awards', tvdb_id, 'extended')
            try:
                return awards_categories['categories']
            except (KeyError, AttributeError, TypeError):
                return []

        def _get_nominees(tvdb_id):
            self._pd.update(f'Getting Nominees {tvdb_id}')
            return self.tvdb_api.get_request_lc('awards', 'categories', tvdb_id, 'extended')

        awards = self.tvdb_api.get_request_lc('awards')
        self._pd.update('Getting Categories', total=len(awards))
        awards = [j for i in awards for j in _get_category(i['id']) if i.get('id') if j]
        self._pd.update('Getting Nominees', total=len(awards))
        return [_get_nominees(i['id']) for i in awards if i.get('id')]

    def sort_nominees(self, nominees_list):
        for award_category in nominees_list:
            self._pd.update(f'Sorting {award_category.get("name")}')
            try:
                ac_name = award_category['name']
                ac_type = award_category['award']['name']
                ac_nominees = award_category['nominees']
            except(KeyError, TypeError, AttributeError):
                continue

            for nominee in ac_nominees:
                if nominee.get('movie'):
                    it_type = 'movie'
                elif nominee.get('series'):
                    it_type = 'series'
                else:
                    continue
                nom_it_id = nominee[it_type]['id']
                nom_year = nominee.get('year')
                nom_winner = nominee.get('isWinner')

                nom_dict = self.listings_tvdb[it_type].setdefault(nom_it_id, {})
                nom_dict['name'] = nominee[it_type]['name']
                nom_dict['year'] = nominee[it_type].get('year')

                nom_awards = nom_dict.setdefault('awards_won' if nom_winner else 'awards_nominated', {})
                nom_awards_cat = nom_awards.setdefault(ac_type, [])
                nom_awards_cat.append(f'{ac_name} ({nom_year})')

    def get_tmdb_ids(self):

        def _get_tmdb_id(tvdb_id, v):
            tmdb_id = None
            if tmdb_type == 'tv':
                tmdb_id = self.tmdb_api.get_tmdb_id(tmdb_type, tvdb_id=tvdb_id, query=v.get('name'), year=v.get('year'))
            else:
                tmdb_id = self.tmdb_api.get_tmdb_id(tmdb_type, query=v.get('name'), year=v.get('year'))
            if not tmdb_id:
                self._pd.update(f'Failed to get TMDb ID for {v.get("name")}')
                return
            self.listings_tmdb[tmdb_type][tmdb_id] = v
            self.listings_tmdb[tmdb_type][tmdb_id]['tvdb_id'] = tvdb_id
            self._pd.update(f'Got TMDb ID for {tmdb_type} {v.get("name")}')

        _pool = []
        _threads = 20
        for i_type in self.listings_tvdb:
            tmdb_type = {'movie': 'movie', 'series': 'tv'}[i_type]
            self._pd.update('Getting TMDb IDs', total=len(self.listings_tvdb[i_type]))
            for tvdb_id, v in self.listings_tvdb[i_type].items():
                t = Thread(target=_get_tmdb_id, args=[tvdb_id, v])
                t.start()
                _pool.append(t)
                if len(_pool) >= _threads:
                    for _ in range(_threads // 3):
                        _pool.pop(0).join()
        for t in _pool:
            t.join()

    def run(self):
        with ProgressDialog('Building Awards', total=1) as self._pd:
            award_nominees = self.get_award_nominees()
            self._pd.update('Sorting Nominees', total=len(award_nominees))
            self.sort_nominees(award_nominees)
            self.get_tmdb_ids()
        return self.listings_tmdb


def build_awards(**kwargs):
    data = AwardsBuilder().run()
    path = 'special://home/addons/plugin.video.themoviedb.helper/resources/jsondata/'
    file = 'awards.json'
    dumps_to_file(data, path, file, join_addon_data=False)

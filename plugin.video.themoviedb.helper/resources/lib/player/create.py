from xbmcgui import Dialog
from resources.lib.addon.plugin import get_localized
from resources.lib.addon.consts import PLAYERS_BASEDIR_SAVE, PLAYERS_BASEDIR_TEMPLATES
from resources.lib.files.futils import get_files_in_folder, read_file, write_to_file
from resources.lib.api.kodi.rpc import get_directory
from resources.lib.items.listitem import ListItem
from resources.lib.addon.dialog import BusyDialog


class CreatePlayer():
    def __init__(self):
        self.plugin_name = ''  # Name of player file $STR_PLUGINNAME
        self.plugin_id = ''  # plugin.video.xyz #STR_PLUGINID
        self.search_url_movie = ''  # plugin://plugin.video.xyz?info=search $STR_PLUGINMOVIESEARCHURL
        self.search_url_tv = ''  # plugin://plugin.video.xyz?info=search $STR_PLUGINTVSEARCHURL
        self.search_url_movie_query = '{title_url}'
        self.search_url_tv_query = '{showname_url}'
        self.template = {}  # The template to use for building our plugin
        self.template_filename = ''
        self.filename = ''  # The filename to save the player as

    def reconfigure_urls(self):
        def _reconfigure_url(url_name, url):
            new_url = Dialog().input(f'{url_name} URL\n{get_localized(32435)}', defaultt=url)
            if 'QUERYKEY' not in new_url:
                Dialog().ok(get_localized(32433), f'{new_url}\n\n{get_localized(32433)}. {get_localized(32434)}.')
                return _reconfigure_url(url_name, url)
            new_url = new_url.replace('QUERYKEY', f'STR_PLUGIN{url_name}QUERYKEY')
            return new_url

        for url_name, key in [('MOVIE', 'search_url_movie'), ('TV', 'search_url_tv')]:
            self.__dict__[key] = _reconfigure_url(url_name, self.__dict__[key])

    def get_template(self):
        template_files = get_files_in_folder(PLAYERS_BASEDIR_TEMPLATES, r'.*\.json')
        x = Dialog().select(get_localized(32432), [i for i in template_files])
        if x == -1:
            return
        self.template_filename = template_files[x]
        return read_file(PLAYERS_BASEDIR_TEMPLATES + self.template_filename)

    def make_template(self):
        template = self.template
        if not template:
            return
        template = template.replace('STR_PLUGINNAME', self.plugin_name)
        template = template.replace('STR_PLUGINID', self.plugin_id)
        template = template.replace('STR_PLUGINMOVIESEARCHURL', self.search_url_movie)
        template = template.replace('STR_PLUGINTVSEARCHURL', self.search_url_tv)
        template = template.replace('STR_PLUGINMOVIEQUERYKEY', self.search_url_movie_query)
        template = template.replace('STR_PLUGINTVQUERYKEY', self.search_url_tv_query)
        return template

    def _select_from_dir(self, url, header='', use_current='', parent_url=''):
        with BusyDialog():
            plugins_dir = []
            if parent_url and url != f'plugin://{self.plugin_id}':
                plugins_dir.append({'label': get_localized(32426), 'file': parent_url})
            if use_current:
                plugins_dir.append({'label': use_current, 'file': url})
            plugins_dir += get_directory(url)
            plugins_gui = [
                ListItem(
                    label=i.get('label'), label2=i.get('file', ''),
                    art={'thumb': i.get('thumbnail', '')}).get_listitem()
                for i in plugins_dir]
        x = Dialog().select(header, plugins_gui, useDetails=True)
        if x == -1:
            return
        return plugins_dir[x]

    def get_plugin_id(self):
        try:
            plugin = self._select_from_dir('addons://sources/video', 'Select plugin')
            return plugin['file'].replace('plugin://', '')
        except (KeyError, AttributeError, TypeError):
            return

    def save_player(self):
        filename = f'autogen.{self.plugin_id}.json'
        write_to_file(self.template, PLAYERS_BASEDIR_SAVE, filename, join_addon_data=False)
        return filename

    def get_search_urls(self):
        def _get_search_url(url, header='', parent_urls=None):
            parent_urls = parent_urls or {}
            try:
                new_item = self._select_from_dir(
                    url, header, use_current=get_localized(32427),
                    parent_url=parent_urls.get(url))
                new_url = new_item['file']
                if new_item['label'] == get_localized(32427):
                    return new_url
            except (KeyError, AttributeError, TypeError):
                return
            if new_url not in parent_urls:
                parent_urls[new_url] = url
            return _get_search_url(new_url, header, parent_urls=parent_urls)

        self.search_url_movie = _get_search_url(f'plugin://{self.plugin_id}', get_localized(32428))

        if self.search_url_movie and Dialog().yesno(get_localized(32429), get_localized(32431)):
            self.search_url_tv = self.search_url_movie
            return

        self.search_url_tv = _get_search_url(f'plugin://{self.plugin_id}', get_localized(32429))

    def create_player(self):
        self.plugin_id = self.get_plugin_id()
        if not self.plugin_id:
            return

        self.template = self.get_template()
        if not self.template:
            return

        if 'plugins_' not in self.template_filename:
            self.get_search_urls()
            if not self.search_url_movie and not self.search_url_tv:
                return
        if 'urlquery_' in self.template_filename:
            self.reconfigure_urls()

        self.plugin_name = Dialog().input(get_localized(32430))
        if not self.plugin_name:
            return

        self.template = self.make_template()
        if not self.template:
            return

        self.filename = self.save_player()
        return self.filename
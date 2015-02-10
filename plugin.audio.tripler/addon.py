from xbmcswift2 import Plugin, xbmcgui
from resources.lib import tripler


plugin = Plugin()


@plugin.route('/')
def main_menu():
    items = [
        {'label': plugin.get_string(30000),'path': "http://media.on.net/radio/114.m3u",'is_playable': True},
        {'label': plugin.get_string(30001), 'path': plugin.url_for(program_menu)},
        {'label': plugin.get_string(30002), 'path': plugin.url_for(audio_archives)},
        ]

    return items


@plugin.route('/program_menu/')
def program_menu():
    programs = tripler.get_programs("/programs/podcasts")
    items = []

    for program in programs:
        items.append({'label': program['title'], 'path': program['url'], 'is_playable': True})

    return items


@plugin.route('/audio_archives/')
def audio_archives():
	archives = tripler.get_audio()

	items = []
	for archive in archives:
		items.append({'label': archive['title'], 'path': archive['url'], 'is_playable': True})

	return items


if __name__ == '__main__':
    plugin.run()
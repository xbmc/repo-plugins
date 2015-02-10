from xbmcswift2 import Plugin, xbmcgui
from resources.lib import abcradionational

plugin = Plugin()

@plugin.route('/')
def main_menu():
    items = [
        {'label': plugin.get_string(30000), 'path': "http://www.abc.net.au/res/streaming/audio/aac/news_radio.pls",
         'is_playable': True},
        {'label': plugin.get_string(30001), 'path': plugin.url_for('just_in')},
        {'label': plugin.get_string(30002), 'path': plugin.url_for('subject_list')},
        {'label': plugin.get_string(30003), 'path': plugin.url_for('program_menu')},
    ]

    return items


@plugin.route('/just_in/')
def just_in():
    subjects = abcradionational.get_podcasts("/podcasts")

    items = [{
        'label': subject['title'],
        'path': subject['url'],
        'is_playable': True,
    } for subject in subjects]

    return items


@plugin.route('/subject_list/')
def subject_list():
    subjects = abcradionational.get_subjects("/podcasts/subjects")

    items = [{
        'label': subject['title'],
        'path': plugin.url_for('subject_item', url=subject['url']),
    } for subject in subjects]

    sorted_items = sorted(items, key=lambda item: item['label'])

    return sorted_items


@plugin.route('/subject_item/<url>/')
def subject_item(url):
    subjects = abcradionational.podcasts_get(url)

    items = [{
        'label': subject['title'],
        'path': subject['url'],
        'is_playable': True,
    } for subject in subjects]

    return items

             
@plugin.route('/program_menu/')
def program_menu():
    subjects = abcradionational.get_programs("/podcasts/program")

    items = [{
        'label': subject['title'],
        'path': plugin.url_for('program_item',url=subject['url']),
    } for subject in subjects]

    #sorted_items = sorted(items, key=lambda item: item['label'])

    return items


@plugin.route('/program_item/<url>/')
def program_item(url):
    programs = abcradionational.podcasts_get(url)

    items = [{
        'label': program['title'],
        'path': program['url'],
        'is_playable': True,
    } for program in programs]
    return items


if __name__ == '__main__':
    plugin.run()

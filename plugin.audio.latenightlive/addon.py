from xbmcswift2 import Plugin, xbmcgui
from resources.lib import latenightlive

plugin = Plugin()

URL = "http://abc.net.au/radionational/programs/latenightlive"


@plugin.route('/')
def main_menu():
    
    items = [
        {
            'label': plugin.get_string(30000),
            'path': plugin.url_for('latest_podcasts', page_no=1),
            'thumbnail': "http://a2.mzstatic.com/us/r30/Music4/v4/45/ff/6e/45ff6eb2-18c8-5aa4-e365-bf429a117f4a/cover170x170.jpeg"}, 
        {
            'label': plugin.get_string(30001), 
            'path': plugin.url_for('browse_subjects'),
            'thumbnail': "http://www.abc.net.au/radionational/image/5698480-3x2-700x467.jpg"},
    ]

    return items


@plugin.route('/latest_podcasts/<page_no>')
def latest_podcasts(page_no):
    url = 'http://www.abc.net.au/radionational/programs/latenightlive/past-programs/?page={0}'.format(page_no)
    next_page = int(page_no) + 1

    items = latenightlive.get_audio(url)
    
    # append next page to list of podcasts
    items.append(
            {'label': 'NEXT PAGE',
             'path': plugin.url_for('latest_podcasts', page_no=next_page)})

    return items


@plugin.route('/browse_subjects/')
def browse_subjects():
    
    url = "http://www.abc.net.au/radionational/programs/latenightlive/past-programs/subjects/"

    items = []

    subjects = latenightlive.get_subjects(url)
    
    for subject in subjects:
        items.append({
            'label': subject['title'],
            'path': plugin.url_for('subject_contents', url=subject['url']),
        })

    return items


@plugin.route('/browse_subjects/<url>/')
def subject_contents(url):
    
    items = []

    subjects = latenightlive.get_subjects_contents(url)
    
    for subject in subjects: 
        items.append({
            'label': subject['title'],
            'thumbnail': subject['img'],
            'path': plugin.url_for('play_subjects', url=subject['url']),
    })

    return items


@plugin.route('/browse_subjects/subject/<url>/')
def play_subjects(url):

    items = latenightlive.get_playable_subjects(url)
        
    return items


if __name__ == '__main__':
    plugin.run()

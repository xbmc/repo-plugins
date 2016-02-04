from xbmcswift2 import Plugin, xbmcgui
from resources.lib import skepticsscraper
import pyxbmct.addonwindow as pyxbmct

plugin = Plugin()

PODCAST_URL = 'http://www.theskepticsguide.org/podcast/sgu'


@plugin.route('/')
def main_menu():
    
    items = [
        {
            'label': plugin.get_string(30000),
            'path': plugin.url_for('latest_podcast'),
            'thumbnail': 'http://www.podcastone.com/imagesproc/L2ltYWdlcy9wcm9ncmFtcy9TR1UxNV9sb2dvXzE0MDB4MTQwMC5qcGc=_H_SW250_MH250.jpg'
        },
        {
            'label': plugin.get_string(30001),
            'path': plugin.url_for('archive_podcast'),
            'thumbnail': 'http://www.podcastone.com/imagesproc/L2ltYWdlcy9wcm9ncmFtcy9TR1UxNV9sb2dvXzE0MDB4MTQwMC5qcGc=_H_SW250_MH250.jpg'
        },
        {
            'label': plugin.get_string(30002),
            'path': plugin.url_for('podcast_5x5'),
            'thumbnail': 'http://www.podcastone.com/imagesproc/L2ltYWdlcy9wcm9ncmFtcy9TR1UxNV9sb2dvXzE0MDB4MTQwMC5qcGc=_H_SW250_MH250.jpg',
        }
    ]

    return items


@plugin.route('/latest_podcast/')
def latest_podcast():

    content = skepticsscraper.get_latest_podcast(PODCAST_URL)
    
    items = []
    for i in content:
        items.append({
            'label': i['label'],
            'path': plugin.url_for('play_podcast', url=i['path']),
            'thumbnail': i['thumbnail'],
        })

    return items

@plugin.route('/latest_podcast/<url>')
def play_podcast(url):
    WINDOW_NAME = 'Skeptics Guide to the Universe'
    WORD = """What's the Word:  """
    NEWS_ITEMS_NAME = "News Items: "
    QUOTE_LABEL = "Skeptical Quote of the Week:"

    item = skepticsscraper.get_podcast_content(url)
    for i in item:
        sub_title = i['title']
        what_is_word = i['word']
        img = i['img']
        quote = i['quote']
        path = i['path']
        
    news_items = []
    news = skepticsscraper.get_news_items(url)
    for i in news:
        news_items.append({
            'news_label': i['news_label'],
            'news_link': i['news_link'],
        })

    window = PodcastWindow(WINDOW_NAME)
    window.set_sub_title(sub_title)
    window.set_podcast_content(WORD, what_is_word)
    window.set_news_items(NEWS_ITEMS_NAME, news_items)
    window.set_quote(QUOTE_LABEL, quote)
    window.set_image(img)
    window.play_podcast(path)
    window.doModal()
    del window

@plugin.route('/archive_podcast/')
def archive_podcast():
    items = []
    content = skepticsscraper.get_podcast_archive(PODCAST_URL)
    
    for i in content:
        items.append({
            'label': i['label'],
            'path': i['path'],
            'is_playable': True,
        })
    
    return items

@plugin.route('/podcast_5x5/')
def podcast_5x5():
    items = []
    content = skepticsscraper.get_podcast_archive('http://www.theskepticsguide.org/podcast/5x5')

    for i in content:
        items.append({
            'label': i['label'],
            'path': i['path'],
            'is_playable': True,
    })

    return items


class PodcastWindow(pyxbmct.AddonDialogWindow):
    
    def __init__(self, title=''):
        super(PodcastWindow, self).__init__(title)
        self.setGeometry(900,650, 3, 3)
        # connect a key action (Backspace) to close window
        self.connect(pyxbmct.ACTION_NAV_BACK, self.close)

    def set_sub_title(self, sub_title):
        label = pyxbmct.Label(sub_title, alignment=pyxbmct.ALIGN_JUSTIFY)
        self.placeControl(label, 0, 0, columnspan = 3)

    def set_podcast_content(self, WORD, what_is_word):
        # Label
        self.label = pyxbmct.Label(WORD)
        self.placeControl(self.label, 0.4, 1.2)
        # Label Value
        self.label = pyxbmct.Label(what_is_word, textColor='0xFF808080')
        self.placeControl(self.label, 0.4, 1.8)

    def set_news_items(self, NEWS_ITEMS_NAME, news_items):
        list_label = pyxbmct.Label(NEWS_ITEMS_NAME)
        self.placeControl(list_label, .65, 1.2)
        # List
        self.list = pyxbmct.List(textColor='0xFF808080')
        self.placeControl(self.list, .8, 1.2, 1, 4)
        # Add items to the list
        for i in news_items:
            items = [ i['news_label'] ]
            self.list.addItems(items)
    
    def set_quote(self, QUOTE_LABEL, quote): 
        # Set textbox label
        self.label = pyxbmct.Label(QUOTE_LABEL)
        self.placeControl(self.label, 1.8, 0)
        # Set TextBox
        self.textbox = pyxbmct.TextBox(textColor='0xFF808080')
        self.placeControl(self.textbox, 2, 0, 3, 2.5)
        self.textbox.setText(quote)
 
    def set_image(self, img):
        self.img = img
        self.image = pyxbmct.Image(self.img)
        self.placeControl(self.image, .3, 0, 1.5, 1.1)

    def play_podcast(self, path):
        link = path
        xbmc.Player().play(item=link)

if __name__ == '__main__':
    plugin.run()

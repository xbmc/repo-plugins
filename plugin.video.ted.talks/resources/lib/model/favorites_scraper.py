from url_constants import URLTED, URLFAVORITES
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup
import re

class Favorites:

    def __init__(self, logger, get_HTML):
        self.logger = logger
        self.get_HTML = get_HTML

    def getFavoriteTalks(self, userID):
        if userID:
            html = self.get_HTML(URLFAVORITES % (userID))
            print html
            talkContainer = SoupStrainer(attrs={'class':re.compile('col clearfix')})
            for talk in BeautifulSoup(html, parseOnlyThese=talkContainer):
                title = talk.a['title']
                link = URLTED + talk.a['href']
                img = talk.a.img['src']
                yield title, link, img
        else:
            self.logger('invalid user object')



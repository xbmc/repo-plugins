from url_constants import URLTED, URLFAVORITES, URLADDFAV, URLREMFAV
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup
from util import resizeImage
import re

class Favorites:

    def __init__(self, logger, get_HTML):
        self.logger = logger
        self.get_HTML = get_HTML

    def getFavoriteTalks(self, userID, url = URLFAVORITES):
        if userID:
            html = self.get_HTML(url + userID)
            talkContainer = SoupStrainer(attrs = {'class':re.compile('box clearfix')})
            for talk in BeautifulSoup(html, parseOnlyThese = talkContainer):
                title = talk.ul.a.string
                link = URLTED+talk.dt.a['href']
                pic = resizeImage(talk.find('img', attrs = {'src':re.compile('.+?\.jpg')})['src'])
                yield {'url':link, 'Title':title, 'Thumb':pic}
        else:
            self.logger('invalid user object')

    def addToFavorites(self, talkID):
        response = self.get_HTML(URLADDFAV % (talkID))
        if not response:
            self.logger('failed to add favorite with id: %s' % (talkID))
        return response != None

    def removeFromFavorites(self, talkID):
        response = self.get_HTML(URLREMFAV % (id))
        if not response:
            self.logger('failed to remove favorite with id: %s' % (talkID))
        return response != None
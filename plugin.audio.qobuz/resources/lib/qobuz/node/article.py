'''
    qobuz.node.article
    ~~~~~~~~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
import xbmcgui  # @UnresolvedImport
from inode import INode
from gui.contextmenu import contextMenu
from node import Flag
from api import api
import qobuz  # @UnresolvedImport


class WidgetArticle(xbmcgui.WindowDialog):
    def __init__(self, *a, **ka):
        super(WidgetArticle, self).__init__()

    def onInit(self):
        self.image = xbmcgui.ControlImage(100, 250, 125, 75, aspectRatio=2)

    def onClick(self, action):
        super(WidgetArticle, self).onClick(action)

    def onAction(self, action):
        super(WidgetArticle, self).onAction(action)

    def onFocus(self, action):
        super(WidgetArticle, self).onFocus(action)


class Node_article(INode):
    """@class Node_articles
    """
    def __init__(self, parent=None, parameters=None):
        super(Node_article, self).__init__(parent, parameters)
        self.nt = Flag.ARTICLE
        self.is_folder = True
        self.hasWidget = False

    def get_label(self):
        author = self.get_property('author')
        if author:
            author += '%s / ' % (author)
        return '%s%s' % (author,
                             self.get_property('title'))

    def makeListItem(self, **ka):

        item = xbmcgui.ListItem(
            self.get_label(),
            self.get_property('source'),
            self.get_image(),
            self.get_image(),
            'url=:p'
        )
        ctxMenu = contextMenu()
        self.attach_context_menu(item, ctxMenu)
        item.addContextMenuItems(ctxMenu.getTuples(), ka['replaceItems'])
        return item

    def hook_post_data(self):
        self.label = self.get_property('title')
        self.image = self.get_property('image')

    def get_image(self):
        image = self.get_property('image')
        if image:
            image = image.replace('http://player.', 'http://www.')
        return image

    def fetch(self, Dir, lvl, whiteFlag, blackFlag):
        data = api.get('/article/get', article_id=self.nid)
        if not data:
            return False
        self.data = data['data']
        return True

    def populate(self, Dir, lvl, whiteFlag, blackFlag):
        pass

    def displayWidget(self):
        w = xbmcgui.WindowXMLDialog('plugin.audio.qobuz-article.xml',
                                    qobuz.path.base)
        w.show()
        w.doModal()
        w.close()
        del w
        return True

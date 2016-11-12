from de.generia.kodi.plugin.frontend.base.Pagelet import Item        
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class ItemPage(Pagelet):


    def _createItem(self, teaser, apiToken):
        item = None
        genre = ''
        sep = ''
        if teaser.genre:
            genre += sep + teaser.genre
            sep = ' | '
        if teaser.category:
            genre += sep + teaser.category
        title = teaser.title

        #self.log.info("settings.mergeCategoryAndTitle: {} - cat: {}, title: {}, starts: {}.", self.settings.mergeCategoryAndTitle, teaser.category, title, title.startswith(teaser.category))
        if self.settings.mergeCategoryAndTitle:        
            if teaser.category is not None and title.startswith(teaser.category):
                title = title[len(teaser.category):].strip()
        #self.log.info("settings.mergeCategoryAndTitle: {} - cat: {}, title: {}, starts: {}.", self.settings.mergeCategoryAndTitle, teaser.category, title, title.startswith(teaser.category))

        if teaser.label is not None and teaser.label != "":
            label = teaser.label
            if teaser.type is not None:
                label = teaser.type.capitalize() + ": " + label
            title = '[' + label + '] ' + title
        title.strip()
        
        if teaser.playable:
            title = '(>) ' + title
        if genre is not None and genre != "":
            title = '[' + genre + '] ' + title
        title = title.strip()

        if teaser.date is not None:
            title = teaser.date + " " + title
           
        isFolder = False
        if teaser.contentName is not None and teaser.playable:
            action = Action(pagelet='PlayVideo', params={'apiToken': apiToken, 'contentName': teaser.contentName})
            isFolder = False
        else:   
            action = Action(pagelet='RubricPage', params={'apiToken': apiToken, 'rubricUrl': teaser.url})
            self.info("redirecting to rubric-url  '{}' and teaser-title '{}' ...", teaser.url, title)
            isFolder = True
            #return None
        item = Item(title, action, teaser.image, teaser.text, genre, teaser.date, isFolder, teaser.playable)
        return item

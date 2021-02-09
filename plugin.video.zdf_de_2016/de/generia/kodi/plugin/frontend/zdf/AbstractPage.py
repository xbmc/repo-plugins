from de.generia.kodi.plugin.frontend.base.Pagelet import Item        
from de.generia.kodi.plugin.frontend.base.Pagelet import Action        
from de.generia.kodi.plugin.frontend.base.Pagelet import Pagelet        

from de.generia.kodi.plugin.frontend.zdf.Constants import Constants


class AbstractPage(Pagelet):


    def _createItem(self, teaser):
        settings = self.settings
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
        if settings.mergeCategoryAndTitle and settings.showGenreInTitle:        
            if teaser.category is not None and title.startswith(teaser.category):
                title = title[len(teaser.category):].strip()
        #self.log.info("settings.mergeCategoryAndTitle: {} - cat: {}, title: {}, starts: {}.", settings.mergeCategoryAndTitle, teaser.category, title, title.startswith(teaser.category))

        if teaser.label is not None and teaser.label != "" and settings.showTagsInTitle:
            label = teaser.label
            if teaser.type is not None:
                label = teaser.type.capitalize() + ": " + label
            title = '[' + label + '] ' + title
        title.strip()
        
        if teaser.season is not None and teaser.episode is not None and settings.showEpisodeInTitle:
            title = str(self._(32047, teaser.season, teaser.episode)) + " - " + title

        if teaser.playable and settings.showPlayableInTitle:
            title = '(>) ' + title
        if genre is not None and genre != "" and settings.showGenreInTitle:
            title = '[' + genre + '] ' + title
        title = title.strip()

        if teaser.date is not None and settings.showDateInTitle:
            title = teaser.date + " " + title
           
        isFolder = False
        #self.log.info("_createItem: title='{}' contentName='{}' playable='{}'", title, teaser.contentName, teaser.playable)
        if teaser.contentName is not None and teaser.playable:
            params = {'contentName': teaser.contentName, 'title': title}
            if teaser.apiToken is not None:
                params['apiToken'] = teaser.apiToken
            if teaser.url is not None:
                params['videoUrl'] = teaser.url
            if teaser.date is not None:
                params['date'] = teaser.date
            if teaser.duration is not None:
                params['duration'] = teaser.duration
            if genre is not None:
                params['genre'] = genre
            action = Action(pagelet='PlayVideo', params=params)
            isFolder = False
        else:   
            action = Action(pagelet='RubricPage', params={'rubricUrl': teaser.url})
            self.info("redirecting to rubric-url  '{}' and teaser-title '{}' ...", teaser.url, title)
            isFolder = True
            #return None
        item = Item(title, action, teaser.image, teaser.text, genre, teaser.date, teaser.duration, isFolder, teaser.playable)
        return item

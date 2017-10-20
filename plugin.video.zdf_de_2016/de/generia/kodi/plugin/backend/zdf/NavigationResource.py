from sets import Set
from de.generia.kodi.plugin.backend.zdf.AbstractPageResource import AbstractPageResource

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import compile

leftNavPattern = getTagPattern('ul', 'left-nav')
dropdownLinksPattern = compile('<a\s*class="[^"]*dropdown-link[^"]*"[^>]*href="([^"]*)"[^>]*data-title="([^"]*)"')
dropdownListPattern = compile('<ul\s*class="[^"]*dropdown-list[^"]*"[^>]*>')
menuItemPattern = compile('<li\s*class="[^"]*menu-item[^"]*"[^>]*>')

class Rubric(object):

    def __init__(self, title, url):
        self.title = title
        self.url = url
                        
    def __str__(self):
        return "<Rubric '%s' url='%s'>" % (self.title, self.url)
    
    
class NavigationResource(AbstractPageResource):

    def __init__(self, url):
        super(NavigationResource, self).__init__(url)

    def parse(self):
        super(NavigationResource, self).parse()
        leftNavMatch = leftNavPattern.search(self.content)
        if leftNavMatch is None:
            self.warn("can't find navigation in page '{}', no rubrics will be available ...", self.url)
            return

        pos = leftNavMatch.end(0)
        self.rubrics = []

        # find first dropdown-list
        dropdownListMatch = dropdownListPattern.search(self.content, pos)
        if dropdownListMatch is None:
            self.warn("can't find first dropdown-list for navigation in page '{}', no rubrics will be available ...", self.url)
            return

        # find next menu-item
        pos = dropdownListMatch.end(0)
        menuItemMatch = menuItemPattern.search(self.content, pos)
        while menuItemMatch is None:
            self.warn("can't find second menu-item for navigation in page '{}', no rubrics will be available ...", self.url)
            return
        
        # reduce content to first dropdown-list
        navigationStart = pos
        navigationEnd = menuItemMatch.end(0)
        self.content = self.content[navigationStart:navigationEnd]
        
        self._parseDropDownList(0)
        
    def _parseDropDownList(self, pos):
        dropdownLinksMatch = dropdownLinksPattern.search(self.content, pos)
        urls = Set([]);
        while dropdownLinksMatch is not None:
            url = self._parseUrl(dropdownLinksMatch.group(1))
            if url not in urls:
                urls.add(url)
                title = stripHtml(dropdownLinksMatch.group(2))
                rubric = Rubric(title, url)
                self.rubrics.append(rubric)
            pos = dropdownLinksMatch.end(0)
            dropdownLinksMatch = dropdownLinksPattern.search(self.content, pos)
            
    # strip blanks and possible anchor hash
    def _parseUrl(self, url):
        parsed = url.strip()
        i = url.find('#')
        if i != -1:
            parsed = parsed[0:i]
        return parsed
        
        

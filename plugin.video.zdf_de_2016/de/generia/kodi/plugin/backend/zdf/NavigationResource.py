from de.generia.kodi.plugin.backend.web.HtmlResource import HtmlResource

from de.generia.kodi.plugin.backend.zdf import stripHtml
from de.generia.kodi.plugin.backend.zdf.Regex import getTagPattern
from de.generia.kodi.plugin.backend.zdf.Regex import getTag
from de.generia.kodi.plugin.backend.zdf.Regex import compile

leftNavPattern = getTagPattern('ul', 'left-nav')
dropdownLinksPattern = compile('<a\s*class="[^"]*dropdown-link[^"]*"[^>]*href="([^"]*)"[^>]*data-title="([^"]*)"')

class Rubric(object):

    def __init__(self, title, url):
        self.title = title
        self.url = url
                        
    def __str__(self):
        return "<Rubric '%s' url='%s'>" % (self.title, self.url)
    
    
class NavigationResource(HtmlResource):

    def __init__(self, url):
        super(NavigationResource, self).__init__(url)

    def parse(self):
        super(NavigationResource, self).parse()
        leftNavMatch = leftNavPattern.search(self.content)
        if leftNavMatch is None:
            self.warn("can't find navigation in page '{}', no rubrics will be available ...", self.url)
            return

        leftNav = getTag('ul', self.content, leftNavMatch)     

        pos = leftNavMatch.end(0)
        dropdownLinksMatch = dropdownLinksPattern.search(self.content, pos)
        self.rubrics = []
        while dropdownLinksMatch is not None:
            url = dropdownLinksMatch.group(1).strip()
            title = stripHtml(dropdownLinksMatch.group(2))
            rubric = Rubric(title, url)
            self.rubrics.append(rubric)
            pos = dropdownLinksMatch.end(0)
            dropdownLinksMatch = dropdownLinksPattern.search(self.content, pos)

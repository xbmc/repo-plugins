import urllib

from xbmcaddon import Addon


class Context(object):
    def __init__(self, log, settings):
        self.log = log
        self.settings = settings
    
    def getLog(self):
        return self.log
    
class Request(object):
    def __init__(self, context, baseUrl, handle, params):
        self.context = context
        self.baseUrl = baseUrl
        self.handle = handle
        self.params = params
    
    def getParam(self, name, default=None):
        if name in self.params:
            return self.params[name]
        return default
    
class Response(object):
    def __init__(self, context, baseUrl, handle):
        self.context = context
        self.baseUrl = baseUrl
        self.handle = handle

    def addItem(self, item):
        pass
    
    def addFolder(self, title, action, image='DefaultFolder.png', text=None, genre=None, date=None):
        item = Item(title, action=action, image=image, text=text, genre=genre, date=date, isFolder=True)
        self.addItem(item);
        
    def sendError(self, message, action):
        pass
        
    def sendInfo(self, message, action):
        pass
    
    def encodeUrl(self, action):
        if action is None:
            return None
        query = ''
        url = ''
        if action.params is not None and len(action.params) >  0:
            query = urllib.urlencode(action.params)
        if action.pagelet is not None:
            if query != '':
                query = '&' + query
            url = self.baseUrl + '?pagelet=' + action.pagelet + query
        else:
            url = action.url
        return url 
    
class Item(object):
    def __init__(self, title, action, image=None, text=None, genre=None, date=None, isFolder=False, isPlayable=False):
        self.title = title
        self.action = action
        self.image = image
        self.text = text
        self.genre = genre
        self.date = date
        self.isFolder = isFolder
        self.isPlayable = isPlayable

class Action(object):
    def __init__(self, pagelet=None, params={}, url=None):
        self.pagelet = pagelet
        self.params = params
        self.url = url


class Pagelet(object):
    logPrefix = "[{}] - "
    
    def __init__(self):
        pass
         
    def init(self, context):
        self.context = context
        self.addon = Addon()
        self.log = context.log
        self.settings = context.settings

    def service(self, request, response):
        pass
        
    def _(self, id, *args):
        msg = self.addon.getLocalizedString(id)
        msg2 = msg
        if len(args) > 0:
            i = 0
            for arg in args:
                s = None
                if isinstance(arg, basestring):
                    s = arg.decode('utf-8')
                else:
                    s = str(arg)
                msg = msg.replace('{' + str(i) + '}', s)
                i += 1
        #self.info("localize string '{}' args='{}' -> '{}' ('{}')", id, len(args), msg, msg2)
        return msg
    
    def _parse(self, resource):
        log = self.context.log
        self.info("Timer - parsing url='{}' ...", resource.url)
        start = log.start()
        resource.log = log
        resource.parse()
        resource.log = None
        self.info("Timer - parsing url='{}' ... done. [{} ms]", resource.url, log.stop(start))

    def debug(self, message, *args):
        self.context.log.debug(self.logPrefix + message, type(self).__name__, *args)
    
    def info(self, message, *args):
        self.context.log.info(self.logPrefix + message, type(self).__name__, *args)

    def warn(self, message, *args):
        self.context.log.warn(self.logPrefix + message, type(self).__name__, *args)
    
    def error(self, message, *args):
        self.context.log.error(self.logPrefix + message, type(self).__name__, *args)

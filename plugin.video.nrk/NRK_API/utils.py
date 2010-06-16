#
#
#   NRK plugin for XBMC Media center
#
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

import sys, os
import re
from urllib import quote_plus, unquote_plus
import xbmcaddon

WINDOWS = 0; LINUX = 1; XBOX = 2
platform_dict = { WINDOWS: 'Windows', LINUX: 'Linux', XBOX: 'xbox' }
    

try:
    import xbmcgui, xbmcplugin, xbmc
except:
    DEBUG = 1
else:
    DEBUG = 0

__version__ = '0.0.9'   
__author__ = 'Victor Vikene'
try:
    __plugin__ = sys.modules["__main__"].__plugin__
except:
    __plugin__ = 'DEBUG MODE'

__settings__ = xbmcaddon.Addon(id='plugin.video.nrk')
__language__ = __settings__.getLocalizedString

print "PLUGIN::LOADED -> '%s'" % __name__

   
from htmlentitydefs import name2codepoint as n2cp


def substitute_entity(match):
    ent = match.group(2)
    if match.group(1) == "#":
        return unichr(int(ent))
    else:
        cp = n2cp.get(ent)

        if cp:
            return unichr(cp)
        else:
            return match.group()

def decode_htmlentities(string):
    entity_re = re.compile("&(#?)(\d{1,5}|\w{1,8});")
    return entity_re.subn(substitute_entity, string)[0]


        
class Log:
    @staticmethod
    def out(logmsg, level=None):
        if not level:
            if DEBUG: level = 'NOTICE'
            else: level = xbmc.LOGNOTICE
        if DEBUG: print level, logmsg
        else: 
            if type(logmsg) == type([]):
                for msg in logmsg:
                    xbmc.log(msg, level)
            else:
                xbmc.log(logmsg, level)
        return
    
    @staticmethod
    def debug(msg):
        xbmc.log(msg, xbmc.LOGDEBUG)
    
    @staticmethod
    def notice(msg):
        xbmc.log(msg, xbmc.LOGNOTICE)



     
class PluginBase:
    def __repr__(self):
        return self.__class__.__name__
        
    def __str__(self):
        return self.__repr__()
     


        
FATAL_ERROR = 0
NON_FATAL_ERROR = 1

class PluginError(Exception):

    if DEBUG: 
        level = 0
    else: 
        level = xbmc.LOGERROR
    
    
    def __init__(self, head, *body):
        self.head = '%s::%s' % (self.__class__.__name__, head)
        self.body = body
        self._get_stack()
        self._handle()
        self.onexit()
       
       
    def _get_stack(self):
        import traceback
        self.stack = traceback.extract_stack()[0:-2]
        
        
    def _handle(self):
        self.display()
        self.output()
        
        
    def __repr__(self):
        msg = "(%s)\n\t'%s'" % (self.head, self.body[0])
        return msg
    
    def __str__(self):
        return self.__repr__()
    
    
    def onexit(self):
        pass
        
        
    def display(self):   
        body = '"%s"' % '","'.join(self.body)
        
        if DEBUG:
            print 'Dialog(%s, %s)' % (self.head, body)
        else:
            exec "xbmcgui.Dialog().ok('%s', %s)" % (self.head, body)
   
   
    def output(self):
        stackcount = 0
        cwd  = os.getcwd()
        line = '-'*60
        
        logmsg = '%s: (%s)' % (self.__class__.__name__, self.head)
        Log.out(logmsg, self.level)
        total = len( self.stack )
        Log.out('Traceback(%d) - most recent call last:' % total, self.level)
        Log.out(line, self.level)
        
        for item in self.stack:
            pre = ' '*5
            file, lineno, name, action = item
            file   = file.replace(cwd, 'plugin:/').replace('\\', '/')
            entry  = '%s%s, line %d, in %s' % (pre, file, lineno, name)
            action = '%s%s' % (pre, action)
            
            Log.out(entry, self.level)
            Log.out(action, self.level)   
            stackcount += 1
            
        Log.out(line, self.level)
        for msg in self.body:
            Log.out(msg, self.level)
        
        
class PluginKeyError(PluginError):
    pass
    
class PluginIOError(PluginError):
    pass
    
class PluginConnectionError(PluginError):
    pass
    
    
class PluginHTTPError(PluginError):

    def __init__(self, url, httpcode):
        from urlparse import urlparse
        import httpstatus
        
        httpmsg = httpstatus.lookup[httpcode].status_phrase
        upart   = urlparse(url); path = upart[2]; host = upart[1]
        
        main = 'connection to %s returned %d' % (host, httpcode) 
        info = 'url: %s' % url
        stat = 'status code: %d' % httpcode
        desc = 'description: %s' % httpmsg
        
        PluginError.__init__(self, main, info, stat, desc)
        
        
class PluginNetworkError(PluginError):

    def __init__(self):
        head = 'No network detected'
        body = 'This plugin can not continue without a network connection'
        PluginError.__init__(self, head, body)
       
       
class PluginScriptError(PluginError):

    def __init__(self):
        hndl = int(sys.argv[1])
        xbmcplugin.endOfDirectory(hndl, False)
        self.settings = PluginSettings('extended_errormsg')
        self.format()
        if self.settings['extended_errormsg'] == True:
            self.get_ext_err_info()
        else:
            self.head = 'Plugin script Error'
            self.body = ('Error', 'Python script failing',)
        self._handle()
        self.onexit()
        
    
    def get_frame(self):
        tb = sys.exc_info()[2]
        while tb.tb_next: 
            tb = tb.tb_next
        self.stack = [] 
        f = tb.tb_frame
        while f:
            self.stack.append(f)
            f = f.f_back
        self.stack.reverse()
    
    
    def get_ext_err_info(self):
        cwd    = os.getcwd()
        frame  = self.stack[-1]
        filenm = frame.f_code.co_filename.replace(cwd, 'plugin:/')
        filenm = filenm.replace('\\', '/')
        lineno = frame.f_lineno
        frmnme = frame.f_code.co_name
        
        self.head = str( sys.exc_info()[0] )
        self.body = (
                '%s in %s at line %d in file' % (self.head, frmnme, lineno), 
                filenm, '%s%s' % (' '*10, str( sys.exc_info()[1] ) ),
            )
        
        
    def display(self):
        if self.settings('extended_errormsg') == False:
            PluginError.display(self)
            return
            
        body = '"%s"' % '","'.join(self.body)
        print body, self.head
        yes = 'View Log'; no = 'Ok'
        if DEBUG:
            print 'Dialog(%s, %s)' % (self.head, body)
            ans = False
        else: 
            exec "ans = xbmcgui.Dialog().yesno('%s', %s, '%s', '%s')" % (
                                                    self.head, body, no, yes)
        if ans == True: 
            self.log_window()

            
    def log_window(self):
        import logview as win
        XML = "logview.xml"
        gui = win.LogViewer(XML, os.getcwd(), "default", stack=self.stackframes)
        gui.doModal()
        del gui
        
        
    def format(self):
        import traceback
        self.get_frame()
        
        tot = len( self.stack )
        fco = 0; out = []; sep = '-'*100
        
        out.extend( [sep, ' ::PLUGIN ERROR::', sep] )
        for line in str( traceback.format_exc() ).split('\n'):
            out.append( line.replace(os.getcwd(), 'Plugin::') )
            
        out.extend( [sep, ' ::PLUGIN FRAME STACK::', sep] )
        for frame in self.stack:
            fco += 1
            base, file = os.path.split(frame.f_code.co_filename)
            out.append( 'FRAME NUM(%d/%d) %s in File: %s at lineno[%s]' % ( 
                                    fco, tot, frame.f_code.co_name, 
                                    file, frame.f_lineno ) )
                                    
            for key, value in frame.f_locals.items():
                try: 
                    sval = repr(value)
                except: 
                    sval = 'error printing value'
                valstr =  ''.join(( ' '*10, key, '  =  ', sval ))
                #if len(valstr) > 100: 
                #    valstr = valstr[0:70] + '...!...' + valstr[-30:-1]
                out.append( valstr )
            out.append(sep)
        self.stackframes = out
    
    
    def output(self):
        Log.out(self.stackframes, self.level)
        
 




 
EQL_S  = '='
SEP_S  = '&'
    
class Key(PluginBase):

    _prefix  = '__key__'
    _verbose = 1
    
    
    @staticmethod
    def build_url(prefix, path=None, words=None, **kwargs):
    
        if not path: 
            path = "plugin://plugin.video.nrk"
        if words: 
            for kw in kwargs:
                words[kw] = kwargs[kw]
            kwargs = words
            
        key = Key.build_key(prefix, kwargs)
        url = '%s?%s' % (path, key)
        
        return url
    # - EOM -
    
    
    @staticmethod
    def build_key(prefix, words=None, **kwargs):

        if words: kwargs = words
        key = '%s%s' % (prefix, (SEP_S*2))
        
        for kw in kwargs:
            val = quote_plus(repr(kwargs[kw]))
            key = '%s%s%s%s%s' % (key, kw, EQL_S, val, SEP_S)
            
        return key
    # - EOM -   

    
    def __init__(self, key=None, **kwargs):
    
        if key and key != 'new':
            self.open(key)
            
        for kw in kwargs:
            if kwargs[kw] is '': kwargs[kw] = None
            
        self.__dict__.update(kwargs)
    # - EOM -

    
    def __getattr__(self, name):
        return None
    # - EOM -
   
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            self.__dict__[name] = value
            return
        if value == None: 
            return
        else: self.__dict__[name] = value
    # - EOM -
    
    
    def __repr__(self):
        return self.build_url(self._prefix, words=self.__dict__)
    # - EOM -
        
        
    def __str__(self):
        val = []
        for var in self.__dict__:
            if var.startswith('_') or self.__dict__[var] == None: 
                continue
            else:   
                val.append( '%s[%s]' % ( var, repr(self.__dict__[var]) ) )
        return ', '.join(val)
    # - EOM -  
      
    
    def __hash__(self):
        return hash( repr( self ) )
    # - EOM -
    
    
    def open(self, key):
            
        key = unquote_plus(key)
        if key.startswith('?'): key = key[1:]
        
        try:
            prefix, key = key.split(SEP_S * 2)
            key = key.replace(SEP_S, ', ')
            
        except: raise PluginKeyError(
                    'Key Error', 
                    'Could not generate plugin key',
                    'Invalid key string given. Aborting..'
                )
            
        else:
            try: exec 'key = Key(%s)' % (key)
            except: raise PluginKeyError(
                        'Key Error', 
                        'Could not create key object',
                        'Plugin state-less. Aborting..'
                    )
                
            else:
                self.__dict__.update(key.__dict__)
                self._prefix = prefix
                if self._verbose: 
                    Log.debug( 'PLUGIN KEY >> %s' % str( self ) )
                return True
    # - EOM -

    
    def getkey(self, prefix='__key__'):
        return self.build_key(prefix, words=self.__dict__)
    # - EOM -


    def geturl(self, prefix='__key__', path=None):
        return self.build_url(prefix, words=self.__dict__)
    # - EOM
    

class State:
    
    class __impl(Key):
        pass

    __inst = None

    
    def __init__(self, key=None):
        if State.__inst is None:
            if not key: raise Exception
            State.__inst = State.__impl(key)
        self.__dict__['_State__inst'] = State.__inst

        
    def __getattr__(self, attr):
        return getattr(self.__inst, attr)

        
    def __setattr__(self, attr, value):
        return setattr(self.__inst, attr, value)

        
        

        
   
   
class PluginPlayList(xbmc.PlayList):
    
    
    def __repr__(self):
        paths = []
        total = len(self)
        for i in range(total):
            paths.append( self[i].getfilename() )
        return 'playlist length: %d items[%s]' % ( total, ', '.join(paths) )

        
      
class PluginPlayer(xbmc.Player):
    
    playlist = PluginPlayList(xbmc.PLAYLIST_VIDEO)
    verbose = 1
    
    
    def __init__ ( self ):
        xbmc.Player.__init__( self )
        self.started = self.isPlaying()
        self.playlist.clear()
        self.index = 0
        

        
    def playbackEnd(self):
        self.index += 1
        if self.started == False:
            if self.verbose:
                Log.out('Error playing file')
            
            
    def queue(self, url, listitem):
        self.playlist.add(url, listitem)
        
        
    def playQueue(self):
        if self.verbose:
            Log.out( str(self.playlist) )
        self.play(self.playlist)
    
    
    def doPlay(self, item=None, listitem=None, windowed=False):
        if not item and not listitem:
            if self.index >= len(self.stack):
                self.index = 0
            self.playQueue()
            return self.index
            
        elif item and not listitem:
            listitem = xbmcgui.Listitem()

        elif not item and listitem:
            if self.verbose:
                Log.out('Player.play() :: Useless parameters given')
            return
            
        self.play(item, listitem, windowed)
        
        
        
class PluginSettings:

    _getset  = __settings__.getSetting
    _verbose = 1
    
    
    def __init__(self, *args):
        for arg in args:
            self.add(arg)
    
    
    def __getitem__(self, name):
        if self.__dict__.has_key(name):
            return self.__dict__[name]
        else:
            raise PluginKeyError(
                    'Settings Key Error',
                    'Plugin could not find setting with key: %s' % name
                )
    
    
    def __call__(self, name):
        return self.__getitem__(name)
    
    
    def __setitem__(self, key, value):
        self.__dict__[key] = value
        
        
    def __len__(self):
        return len( self.__dict__ )
        
        
    def add(self, name, type='bool', options=None, index=None, fallback=None):
        
        if type == 'bool':
            try: self.__dict__[name] = self._getset( name ) == 'true'
            except: 
                if self._verbose:
                    Log.out('Error getting setting. Use default/fallback value')
                self.__dict__[name] = fallback or False
                
        elif type == 'int':
            try: self.__dict__[name] = int( self._getset( name ) )
            except: self.__dict__[name] = fallback or 0
        
        elif type == 'values':
            try:
                id = int( self._getset( name ) )
                self.__dict__[name] = options[id]
            except:
                try:
                    if index < 30000: index += 30000
                    id = int( self._getset( name ) ) - (index + psi)
                    self.__dict__[name] = options[id]
                except:
                    try: 
                        self.__dict__[name] = fallback or options[0]
                    except: 
                        raise PluginError(
                                'Error getting setting',
                                'Could not get value for setting %s' % name
                            )
                            
        else: #handle setting as a string
            try: self.__dict__[name] = self._getset( name ) 
            except:
                if fallback: self.__dict__[name] = fallback
                else: raise PluginError(
                            'Error getting setting',
                            'Could not get value for setting %s' % name
                        )
         
        Log.debug('%s -> %s: %s' % ( 
                self.__class__.__name__, name, repr(self.__dict__[name]) ))

                    
      

      
class PluginDirectory:

    FILES    = 'files';    SONGS        = 'songs';      ARTIST = 'artists'
    ALBUMS   = 'albums';   MOVIES       = 'movies';     TVSHOWS = 'tvshows'
    EPISODES = 'episodes'; MUSICVIDEOS  = 'musicvideos'
    
    ok = False
    hndl = int(sys.argv[1])
    is_open = False
    category = 'Plugin'
    sort_methods = []
    
    end_dir = xbmcplugin.endOfDirectory
    add_dir = xbmcplugin.addDirectoryItem
    
    
    def __init__(self, total=None, cache=None, update=None, content=None):
        self.cache = cache or True
        self.total = total or 0
        self.update = update or False
        self.added = 0
        
        if content: 
            self.set_content(content)
              
              
    def add(self, url, listitem, isdir=True, hndl=int(sys.argv[1])):
        self.is_open = True
        self.ok = self.add_dir(hndl, url, listitem, isdir, self.total)
        if self.ok:
            self.added += 1
        else: 
            Log.out('PLUGIN::DIRECTORY -> No success')
        return self.ok
    
    
    def end(self, hndl=int(sys.argv[1])):
        if self.is_open == False:
            return 
            
        Log.out('PLUGIN::DIRECTORY -> added: %d success: %s handle: %i' % (
                                self.added, repr(self.ok), int(sys.argv[1]) ))
        
        if self.ok == True: self._add_sort_methods()
            
        self.end_dir(hndl, self.ok, self.update, self.cache)
    
    
    def set_content(self, content, hndl=int(sys.argv[1])):
        xbmcplugin.setContent(hndl, content)

    
    def resolve_url(self, listitem, success=None):
        if not success: success = self.ok 
        xbmcplugin.setResolvedUrl(self.hndl, success, listitem)
    
    
    def _add_sort_methods(self):
        if len(self.sort_methods) == 0:
            xbmcplugin.addSortMethod(self.hndl, xbmcplugin.SORT_METHOD_NONE)
        else:
            for sm in self.sort_methods:
                xbmcplugin.addSortMethod(self.hndl, sm)
      
    
    
class Plugin(PluginBase):
    
    cwd      = os.getcwd()
    dir      = PluginDirectory()
    hndl     = int( sys.argv[1] )
    plugin   = __plugin__
    category = ''
    
    
    def __init__(self):
        self.cachepath = self.get_cachepath()
        self.state     = Key( sys.argv[2] )
        Log.debug('%s -> cachepath: %s' % (self.__class__.__name__, self.cachepath) )
        Log.debug('%s' % repr( self.state ))
        if self.state.refresh: 
            self.cache = False
        else: 
            self.cache = True
        
        if self.state.sessionkey: 
            self.session_key = self.state.sessionkey
            Log.debug('PLUGIN::%s -> Found session key in argv "%s"' % (
                        self.__class__.__name__, self.session_key ))
        else: 
            self.session_key = None
        
        self.platform = self.get_platform()
            
            
    def close(self):
        self.dir.end()
        
    
    def set_category(self):
        xbmcplugin.setPluginCategory(self.hndl, self.category)
      
      
    def get_category(self):
        return self.category
    
    
    @staticmethod
    def get_platform():
        if xbmc.getCondVisibility('system.platform.windows') == True:
            return WINDOWS
        elif xbmc.getCondVisibility('system.platform.linux') == True:
            return LINUX
        elif xbmc.getCondVisibility('system.platform.xbox') == True:
            return XBOX

            
    @staticmethod
    def has_network():
        if xbmc.getCondVisibility(System.hasNetwork):
            return True
            
            
    @staticmethod
    def get_cachepath():
        cpath = os.path.join(
                xbmc.translatePath("special://profile/"), 
                "plugin_data", 
                "video", 
                os.path.basename(Plugin.cwd), 
                "cache"
            )
        if os.path.isdir(os.path.dirname(cpath)) == False:
            os.makedirs(os.path.dirname(cpath))  
        return cpath
    
    
    @staticmethod
    def get_special_cachepath(file):
        cpath = '/'.join((
                "special://profile/", 
                "plugin_data", 
                "video", 
                os.path.basename(Plugin.cwd), 
                "cache", 
                file
            ))
        return cpath
        
        
    @staticmethod
    def resource(file):
        return os.path.join( Plugin.cwd, 'resources', file )
    
    
    @staticmethod
    def image(file):
        return os.path.join( Plugin.cwd, 'resources', 'images', file )

        
    @staticmethod
    def videopath(file):
        return os.path.join( Plugin.cwd, 'resources', 'video', file )

        
#Test procedure        
if (__name__ == "__main__"):
    s = State('key&&test=123')
    print "\n\ts = State('key&&test=123') - %s" % str(s.test == 123)
    s2 = State()
    print '\ts1 == s2 (singularity) - %s' % str(s.test == s2.test)
    s3 = Key('key&&test=321')
    print "\tKey.open('key&&test=321') - %s" % str(s3.test == 321)
    print '\tinvalid attribute return None: - %s' % str(s3.invalid == None)
    k = Key(test1='test1',test2='test2')
    print "\tk = Key(test1='test1',test2='test2')\n\ts.getkey() = %s"%k.getkey()
    print '\tk.geturl() = %s' % k.geturl()
    
    
    
    
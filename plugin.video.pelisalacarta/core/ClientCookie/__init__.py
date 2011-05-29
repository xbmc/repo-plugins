import sys

try: True
except NameError:
    True = 1
    False = 0

# If you hate the idea of turning bugs into warnings, do:
# import ClientCookie; ClientCookie.USE_BARE_EXCEPT = False
USE_BARE_EXCEPT = True
WARNINGS_STREAM = sys.stdout

# Import names so that they can be imported directly from the package, like
# this:
#from ClientCookie import <whatever>

# These work like equivalents from logging.  Use logging direct if you
# have 2.3.
from _Debug import getLogger, StreamHandler, NOTSET, INFO, DEBUG

from _ClientCookie import VERSION, __doc__, \
     Cookie, \
     CookiePolicy, DefaultCookiePolicy, \
     CookieJar, FileCookieJar, LoadError, request_host
from _LWPCookieJar import LWPCookieJar, lwp_cookie_str
from _MozillaCookieJar import MozillaCookieJar
try:
    from _MSIECookieJar import MSIECookieJar
except:
    pass
try:
    import bsddb
except ImportError:
    pass
else:
    from _BSDDBCookieJar import BSDDBCookieJar, CreateBSDDBCookieJar
#from _MSIEDBCookieJar import MSIEDBCookieJar
from _ConnCache import ConnectionCache
try:
    from urllib2 import AbstractHTTPHandler
except ImportError:
    pass
else:
    from ClientCookie._urllib2_support import \
         Request, \
         OpenerDirector, build_opener, install_opener, urlopen, \
         OpenerFactory, urlretrieve, BaseHandler
    from ClientCookie._urllib2_support import \
         HTTPHandler, HTTPRedirectHandler, \
         HTTPRequestUpgradeProcessor, \
         HTTPEquivProcessor, SeekableProcessor, HTTPCookieProcessor, \
         HTTPRefererProcessor, \
         HTTPRefreshProcessor, HTTPErrorProcessor, \
         HTTPResponseDebugProcessor, HTTPRedirectDebugProcessor

    try:
        import robotparser
    except ImportError:
        pass
    else:
        from ClientCookie._urllib2_support import \
             HTTPRobotRulesProcessor, RobotExclusionError
        del robotparser

    import httplib
    if hasattr(httplib, 'HTTPS'):
        from ClientCookie._urllib2_support import HTTPSHandler
    del AbstractHTTPHandler, httplib
from _Util import http2time
str2time = http2time
del http2time

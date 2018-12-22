# -*- coding: utf-8 -*-
"""Simplest possible router utility class.

This class provides Kodi plugin routing using the following methods.
route - a decorator to be used as follows:
@router.route("/")
def index():
    pass
Maps the route "plugin://<plugin>/" to index()

@router.route("/say")
def say(hello):
    print "Saying " + hello
Maps the route "plugin://<plugin>/say?hello=Hi" to say("Hi")

parameters are always strings.

dispatch - perform the actual dispatching, from a url to the callable registered earlier.

make_url - utility function to create a url from a path and a dictionary of query parameters
"""
from urllib import urlencode
from urlparse import parse_qsl, urlparse, urlunparse


class Router(object):
    def __init__(self, handle, base_url, xbmc):
        self.handle = handle
        self.base_url = base_url
        self.xbmc = xbmc
        self.routes = {}

    def _urljoin(self, base_url=None, scheme=None, netloc=None, path=None,
                 params=None, query=None, fragment=None):
        """Join new url parts with the base url."""
        if base_url is None:
            base_url = self.base_url
        newtuple = [u if u else b
                    for (b, u) in zip(urlparse(base_url),
                                      (scheme, netloc, path,
                                       params, query, fragment))] 
        return urlunparse(newtuple)

    def route(self, path):
        """A decorator to add a route path to a function.

        Use like this:
        @route("/route")
        def route():
            print "Hello, I'm function route() found through /route!"

        The url query parameters are the function parameters:
        @route("/routewithparams")
        def routewithparams(a, b):
            print "Hello, I'm function routewithparams(a,b) found through /routewithparams?a=ape&b=bear"
            print "a =", a, "b =", b

        To add a route to a bound method, use add_route.
        """
        def decorator(f):
            self.add_route(path, f)
            return f
        return decorator

    def add_route(self, path, f):
        """Add a route path to a callable f.

        Use like this:
        class Thing(object):
            def bound(self):
                print "Inside thing!"
        t = Thing()
        router.add_route("/inside", t.bound)

        (to create a route to a bound method.)

        The url query parameters are the function parameters.
        The route decorator calls this, and is easier to use for functions.

        It is not possible to create a route to an unbound method: the
        router wouldn't know which object to use.
        """
        url = self._urljoin(path=path)
        if url in list(self.routes.values()):
            old_f = self._find_callable(url)
            raise ValueError(
                "Cannot add callable {0} for url '{1}'. There is already a callable registered for that url: {2}"
                    .format( f.__name__, url, old_f.__name__))
        else:
            self.xbmc.log("Adding callable '{0}' for url '{1}'".format(f.__name__, url))
            self.routes[f] = url
    
    def dispatch(self, url, query=""):
        """Route to the callable registered for url, with params from query.

        if index(name) is the callable for "/", then
            dispatch("/", "?name=roger")
        will call
            index(name="roger")
        """
        if query == "":
            kwargs = {}
        else:
            if not query.startswith('?'):
                raise ValueError("'" + query + "' doesn't start with '?'")
            # using this instead of parse_qs gives us the last value for each 
            # parameter instead of lists, which is easier.
            kwargs = dict(parse_qsl(query[1:], strict_parsing=True))
        # This is cumbersome but only done once. make_url is called more often.
        f = self._find_callable(url)
        if f is None:
            raise KeyError("no callable registered for url {0}".format(url))
        f(**kwargs)

    def make_url(self, f, **kwargs):
        """Make a url for this callable with params.

        if index(name) is the callable for "/", then
            make_url(index, name="rabbit")
        will return
            /?name=rabbit
        """
        url = self.routes[f]
        return self._urljoin(base_url=url, query=urlencode(kwargs))

    def _find_callable(self, url):
        """Find the dictionary key that goes with this value."""
        for (f, mapped_url) in list(self.routes.items()):
            if url == mapped_url:
                return f
        return None

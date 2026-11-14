"""Each plugin action's view and what Kodi is told of it: whether it lists a folder, where it is in the menu."""

import collections

# module: its module in resources.lib.views; view: the class there, whose do_<action> runs it;
# listing: it lists a folder, so failing ends that listing as failed (see call.Call.end);
# category: where the list is in the menu, as string ids, for the skin's breadcrumb (else just "Videos").
Route = collections.namedtuple("Route", "module view listing category", defaults=(False, ()))

ROUTES = {
    "root": Route("menu", "MainMenu", listing=True),
    "login": Route("account", "AccountViews"),
    "logout": Route("account", "AccountViews"),
    "devices": Route("account", "AccountViews"),
    "parental": Route("account", "AccountViews"),
    "channels": Route("channels", "ChannelViews", listing=True, category=(30001,)),
    "deactivated": Route("channels", "ChannelViews"),
    "not_subscribed": Route("channels", "ChannelViews"),
    "mychannels": Route("mychannels", "MyChannelsViews", listing=True, category=(30175,)),
    "channel_menu": Route("mychannels", "MyChannelsViews"),
    "deactivate": Route("mychannels", "MyChannelsViews"),
    "move": Route("mychannels", "MyChannelsViews"),
    "reset_order": Route("mychannels", "MyChannelsViews"),
    "favourite": Route("mychannels", "MyChannelsViews"),
    "watchlist": Route("programmes", "ProgrammeViews", listing=True, category=(30168,)),
    "watch": Route("programmes", "ProgrammeViews"),
    "seasons": Route("programmes", "ProgrammeViews", listing=True, category=(30168,)),
    "pick": Route("programmes", "ProgrammeViews"),
    "continue": Route("continuing", "ContinueViews", listing=True, category=(30188,)),
    "continue_pick": Route("continuing", "ContinueViews"),
    "continue_remove": Route("continuing", "ContinueViews"),
    "play": Route("play", "PlayViews"),
    "tv_toggle": Route("tv", "TvViews"),
    "tv_on": Route("tv", "TvViews"),
    "tv_off": Route("tv", "TvViews"),
    "tv_refresh": Route("tv", "TvViews"),
}


def is_listing(action):
    """Return whether an action lists a folder (see Route)."""
    route = ROUTES.get(action)
    return bool(route and route.listing)

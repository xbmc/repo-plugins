# -*- coding: utf-8 -*-
"""Simplest possible language utility class.

Goes with pypo_strings.py, which generates kodi_strings, local_strings and strings.
the call: lang.get_string(language.string.resourceid)
will return a localized string, either from the addon resources, or from
the official Kodi resources (tried in that order.) It will use
kodi_strings and local_strings to look up the variable used, so your IDE can be helpful.

So you can use this class like this:
- Use the following in your plugin:
      po = Po(addon, xbmc)
      s = po.get_string
- Use resources in the form s(pypo.strings.mystring)
- add entries in .po files
- If you add new resources in your strings.po, re-run pypo.py and check the pypo.strings.variables used
"""
# Require strings to exist.
from . import local_strings
from . import kodi_strings
from . import strings


class Po(object):
    def __init__(self, addon, xbmc):
        """Create a Language object for this addon."""
        self.addon = addon
        self.xbmc = xbmc

    def get_string(self, key):
        """Return the localized string for a key."""
        if key in list(local_strings.__dict__.values()):
            get_localized_string = self.addon.getLocalizedString
        elif key in list(kodi_strings.__dict__.values()):
            get_localized_string = self.xbmc.getLocalizedString
        else:
            # en_gb doesn't have it, error!
            return "<{0}!>".format(key)
        ls = get_localized_string(key)
        if ls is not None:
            return ls
        else:
            # no localization, return <key>
            return "<{0}>".format(key)

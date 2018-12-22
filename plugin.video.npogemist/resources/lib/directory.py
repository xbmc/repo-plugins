"""Kodi directory of ListItems. Abstracting xbmcplugin Directory operations.

Use it like this:
directory = Directory(handle, xbmcplugin)
directory.add(url, item)
directory.add(url, item)
directory.add(url, item)
sort_methods = (xbmcplugin.SORT_METHOD_DURATION, xbmcplugin.SORT_METHOD_DATEADDED)
directory.display(sort_methods)
"""


class Directory(object):
    def __init__(self, handle, xbmc, xbmcplugin):
        """Create a Directory object for this handle, with this xbmc and xbmcplugin object."""
        self.handle = handle
        self.xbmc = xbmc
        self.xbmcplugin = xbmcplugin
        self.directory = []

    def add(self, url, list_item, is_folder=True):
        """Add a list_item to this directory."""
        self.directory.append((url, list_item, is_folder))

    def display(self, sort_methods=()):
        """Display this directory, and add sort methods."""
        self.xbmcplugin.addDirectoryItems(self.handle, self.directory, len(self.directory))
        if sort_methods:
            for sort_method in sort_methods:
                self.xbmcplugin.addSortMethod(self.handle, sort_method)
        else:
            self.xbmcplugin.addSortMethod(self.handle, self.xbmcplugin.SORT_METHOD_UNSORTED)
        self.xbmcplugin.endOfDirectory(self.handle)

"""
This module contains actions
 - to run tasks in the background of user navigation or
 - to update the current view in Kodi from a context menu for instance
"""


def background(url):
    """This action will run an addon in the background for the provided URL.

    See 'XBMC.RunPlugin()' at
    http://wiki.xbmc.org/index.php?title=List_of_built-in_functions.
    """
    return f"RunPlugin({url})"


def update_view(url):
    """This action will update the current container view with provided url.

    See 'XBMC.Container.Update()' at
    http://wiki.xbmc.org/index.php?title=List_of_built-in_functions.
    """
    return f"Container.Update({url})"

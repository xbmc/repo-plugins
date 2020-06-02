# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Standard Library Imports
from hashlib import sha1
import pickle

# Package imports
from resources.lib.codequick.storage import PersistentDict
from resources.lib.codequick.support import dispatcher
from resources.lib.codequick.listing import Listitem
from resources.lib.codequick.utils import keyboard, ensure_unicode, unicode_type
from resources.lib.codequick.route import Route, validate_listitems

# Localized string Constants
ENTER_SEARCH_STRING = 16017
REMOVE = 1210
SEARCH = 137

# Name of the database file
SEARCH_DB = u"_new_searches.pickle"


def hash_params(data):
    # type: (dict) -> unicode_type

    # Convert dict of params into a sorted list of key, value pairs
    sorted_dict = sorted(data.items())

    # Pickle the sorted dict so we can hash the contents
    content = pickle.dumps(sorted_dict, protocol=2)
    return ensure_unicode(sha1(content).hexdigest())


@Route.register
class SavedSearches(Route):
    """
    Class used to list all saved searches for the addon that called it.

    Useful to add search support to addon that will also keep track of previous searches.
    Also contains option via context menu to remove old search terms.
    """

    def __init__(self):
        super(SavedSearches, self).__init__()

        # Persistent list of currently saved searches
        self.search_db = PersistentDict(SEARCH_DB)
        self.register_delayed(self.close)
        self.session_data = None  # type: list

    def run(self, remove_entry=None, search=False, first_load=False, **extras):
        """List all saved searches."""

        # Create session hash from givin arguments
        session_hash = hash_params(extras)
        self.session_data = session_data = self.search_db.setdefault(session_hash, [])

        # Remove search term from saved searches
        if remove_entry and remove_entry in session_data:
            session_data.remove(remove_entry)
            self.update_listing = True
            self.search_db.flush()

        # Show search dialog if search argument is True, or if there is no search term saved
        # First load is used to only allow auto search to work when first loading the saved search container.
        # Fixes an issue when there is no saved searches left after removing them.
        elif search or (first_load is True and not session_data):
            search_term = keyboard(self.localize(ENTER_SEARCH_STRING))
            if search_term:
                return self.redirect_search(search_term, extras)
            elif not session_data:
                return False
            else:
                self.update_listing = True

        # List all saved search terms
        return self.list_terms(extras)

    def redirect_search(self, search_term, extras):
        """
        Checks if searh term returns valid results before adding to saved searches.
        Then directly farward the results to kodi.

        :param str search_term: The serch term used to search for results.
        :param dict extras: Extra parameters that will be farwarded on to the callback function.
        :return: List if valid search results
        """
        self.params[u"_title_"] = search_term.title()
        self.category = self.params[u"_title_"]
        callback_params = extras.copy()
        callback_params["search_query"] = search_term

        # We switch selector to redirected callback to allow next page to work properly
        route = callback_params.pop("_route")
        dispatcher.selector = route

        # Fetch search results from callback
        func = dispatcher.get_route().function
        listitems = func(self, **callback_params)

        # Check that we have valid listitems
        valid_listitems = validate_listitems(listitems)

        # Add the search term to database and return the list of results
        if valid_listitems:
            if search_term not in self.session_data:  # pragma: no branch
                self.session_data.append(search_term)
                self.search_db.flush()

            return valid_listitems
        else:
            # Return False to indicate failure
            return False

    def list_terms(self, extras):
        """
        List all saved searches.

        :param dict extras: Extra parameters that will be farwarded on to the context.container.

        :returns: A generator of listitems.
        :rtype: :class:`types.GeneratorType`
        """
        # Add listitem for adding new search terms
        search_item = Listitem()
        search_item.label = u"[B]%s[/B]" % self.localize(SEARCH)
        search_item.set_callback(self, search=True, **extras)
        search_item.art.global_thumb("search_new.png")
        yield search_item

        # Set the callback function to the route that was given
        callback_params = extras.copy()
        route = callback_params.pop("_route")
        callback = dispatcher.get_route(route).callback

        # Prefetch the localized string for the context menu lable
        str_remove = self.localize(REMOVE)

        # List all saved searches
        for search_term in self.session_data:
            item = Listitem()
            item.label = search_term.title()

            # Creatre Context Menu item for removing search term
            item.context.container(self, str_remove, remove_entry=search_term, **extras)

            # Update params with full url and set the callback
            item.params.update(callback_params, search_query=search_term)
            item.set_callback(callback)
            yield item

    def close(self):
        """Close the connection to the search database."""
        self.search_db.close()

# SPDX-License-Identifier: CC-BY-NC-SA-4.0

from resources.lib import menu

with menu.Menu("All Favourites") as m:
    m.favourites(all_favorites=True)

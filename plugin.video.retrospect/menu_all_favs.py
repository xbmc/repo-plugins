# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import menu

with menu.Menu("All Favourites") as m:
    m.favourites(all_favorites=True)

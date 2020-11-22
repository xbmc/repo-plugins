# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import menu

with menu.Menu("Un-cloak Item") as m:
    m.toggle_cloak()

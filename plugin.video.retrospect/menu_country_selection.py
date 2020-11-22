# SPDX-License-Identifier: GPL-3.0-or-later

from resources.lib import menu

with menu.Menu("Country Selection") as c:
    c.show_country_settings()

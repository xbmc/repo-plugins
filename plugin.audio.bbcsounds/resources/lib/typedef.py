# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Generator

from xbmcgui import ListItem


ListItemTuple = tuple[str, ListItem, bool]
ListItemGenerator = Generator[ListItemTuple | None, None, None]
ContextMenuItem = tuple[str, str]

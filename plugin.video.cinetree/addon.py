# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt.
# ------------------------------------------------------------------------------

import sys
# Ensure to apply patches before any import of codequick
from resources.lib import cc_patch
from resources.lib import main
from resources.lib.addon_log import logger, shutdown_log


if __name__ == "__main__":
    logger.debug('script called with args %s', sys.argv)
    main.run()
    shutdown_log()

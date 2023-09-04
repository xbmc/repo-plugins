# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import sys
from resources.lib import main
from resources.lib.addon_log import logger, shutdown_log
from resources.lib import cc_patch


cc_patch.patch_cc_route()


if __name__ == "__main__":
    logger.debug('script called with args %s', sys.argv)
    main.run()
    shutdown_log()

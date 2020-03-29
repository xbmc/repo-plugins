# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import sys
from datetime import datetime


class Initializer:
    StartTime = datetime.now()  # : Used for duration determination

    def __init__(self):
        """ It is a static method, so we con't get here """
        raise NotImplementedError("Static class only")

    @staticmethod
    def set_unicode():
        """Forces the environment to UTF-8"""

        if sys.version_info[0] > 2:
            return

        # noinspection PyUnresolvedReferences,PyCompatibility
        reload(sys)
        # noinspection PyUnresolvedReferences
        sys.setdefaultencoding("utf-8")  # @UndefinedVariable
        return

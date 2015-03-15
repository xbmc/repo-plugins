__author__ = 'bromix'

from resources.lib.kodion import runner
from resources.lib import clipfish

__provider__ = clipfish.Provider()
runner.run(__provider__)
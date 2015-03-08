__author__ = 'bromix'

from resources.lib.kodion import runner
from resources.lib import vimeo

__provider__ = vimeo.Provider()
runner.run(__provider__)

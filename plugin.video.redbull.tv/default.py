__author__ = 'bromix'

from resources.lib.kodion import runner
from resources.lib import redbull_tv

__provider__ = redbull_tv.Provider()
runner.run(__provider__)
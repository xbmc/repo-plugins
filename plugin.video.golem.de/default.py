__author__ = 'bromix'

from resources.lib.kodion import runner
from resources.lib import golem_de

__provider__ = golem_de.Provider()
runner.run(__provider__)

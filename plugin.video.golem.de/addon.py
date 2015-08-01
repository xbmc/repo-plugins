__author__ = 'bromix'

from resources.lib import nightcrawler
from resources.lib import content

nightcrawler.run(content.Provider())

import sys

from yogaglo.yogaglo import YogaGlo
from yogaglo.xbmc_util import get_yoga_glo_input_parameters

# parse parameters and give yogaglo plugin dictionary
plugin_parameters = get_yoga_glo_input_parameters(sys.argv[2])

yg = YogaGlo(sys.argv[0], int(sys.argv[1]), plugin_parameters)
yg.processParameters()

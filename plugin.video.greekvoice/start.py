#  Greek Voice Add-on
#  Author: threshold84
#  SPDX-License-Identifier: GPL-3.0
#  See LICENSES/GPL-3.0 for more information.
import sys
from urllib.parse import parse_qsl
from resources.lib import runner
from resources.lib.url_dispatcher import urldispatcher


def main(argv=None):

    if sys.argv:
        argv = sys.argv

    params = dict(parse_qsl(argv[2][1:]))
    action = params.get('action', 'root')
    urldispatcher.dispatch(action, params)


if __name__ == '__main__':

    sys.exit(main())

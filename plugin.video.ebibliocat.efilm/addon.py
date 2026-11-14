# Kodi plugin entry point. Never log plugin arguments or resolved URLs.

import sys
from urllib.parse import parse_qs

from resources.lib.ui.ui import UI


def main(argv=None):
    base_url, handle, query = (sys.argv if argv is None else argv)[:3]
    try:
        arguments = parse_qs(query.lstrip("?"), keep_blank_values=True, max_num_fields=20)
    except ValueError:
        arguments = {"mode": ["invalid"]}
    UI(base_url, int(handle), arguments).run()


if __name__ == "__main__":
    main()

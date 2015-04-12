#!/usr/bin/env python

import urlparse, sys
from resources.lib.kanaalz import handle_event

def main():
    myself = sys.argv[0]
    handle = int(sys.argv[1])
    qs     = sys.argv[2]

    if len(qs) > 1:
        params = urlparse.parse_qs(qs[1:])
    else:
        params = {}

    handle_event(myself, handle, params)

if __name__ == "__main__":
    main()

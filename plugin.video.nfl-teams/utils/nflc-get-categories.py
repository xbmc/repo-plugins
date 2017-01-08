#!/usr/bin/env python3

import argparse
import json
from urllib.request import urlopen


def get_data(domain):
    response = urlopen('http://{}/media/nflc-playlist-video.json'.format(domain)).read()
    return json.loads(response.decode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description='Get the category names and IDs for a NFLC site')
    parser.add_argument('domain', type=str, nargs=1, help='Domain name to query for')
    args = parser.parse_args()

    data = get_data(args.domain[0])
    result = {}
    strip_left = [
        'Podcast - ',
        'Video - ',
        'Videos - ',
        'Show - ',
        'Shows - ',
    ]

    for category_id, category in data.items():
        name = category['name']
        for strip in strip_left:
            if name.startswith(strip):
                name = name[(len(strip)):]

        result[name.strip()] = category_id

    for category_name in sorted(result, key=str.lower):
        print('({}, "{}"),'.format(result[category_name], category_name))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import argparse
from urllib.request import urlopen

from bs4 import BeautifulSoup


def get_categories(url):
    response = urlopen(url).read()
    soup = BeautifulSoup(response, 'html.parser')
    category_tags = soup.find('select', attrs={'name': 'channelKey'}).find_all('option')

    result = []
    for category in category_tags:
        if category['value']:
            result.append(category['value'])

    return result


def main():
    parser = argparse.ArgumentParser(description='Get the categories for a NFLCS site')
    parser.add_argument('url', type=str, nargs=1, help='URL of a video for site to parse')
    args = parser.parse_args()

    for category in sorted(get_categories(args.url[0]), key=str.lower):
        print('"{}",'.format(category))


if __name__ == '__main__':
    main()

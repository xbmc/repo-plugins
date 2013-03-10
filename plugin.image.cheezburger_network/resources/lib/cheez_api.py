#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2012 Tristan Fischer
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from urllib2 import urlopen, Request, HTTPError, URLError
import xmltodict


class NetworkError(Exception):
    pass


class AuthError(Exception):
    pass


class CheezburgerApi():

    API_URL = 'http://api.cheezburger.com/xml/'

    def __init__(self, developer_key, client_id, default_count=None):
        self.client_id = client_id
        self.developer_key = developer_key
        self.default_count = default_count or 25

    def get_sites(self):
        tree = self.__get_tree('site')
        sites = [{
            'id': self.__id(site['SiteId']),
            'api_url': site['SiteId'],
            'title': site['Name'],
            'description': site['Description'],
            'logo': site['SquareLogoUrl'],
            'page_url': site['Url'],
        } for site in tree['Sites']['Sites']['Site']]
        return sites

    def get_categories(self):
        tree = self.__get_tree('category')
        categories = [{
            'id': self.__id(category['CategoryId']),
            'api_url': category['CategoryId'],
            'title': category['CategoryName'],
        } for category in tree['ArrayOfCategoryDetail']['CategoryDetail']]
        return categories

    def get_featured_content(self, site_id, page=1, count=None):
        count = count or self.default_count
        url = 'site/%d/featured/%d/%d' % (
            site_id, (page - 1) * count, count
        )
        tree = self.__get_tree(url)
        asset_generator = (
            a for a in tree['Assets']['Assets']['Asset']
            if a['AssetType'] == 'Image'
        )
        assets = [{
            'id': self.__id(asset['AssetId']),
            'type': asset['AssetType'],
            'api_url': asset['AssetId'],
            'title': asset['Title'],
            'description': asset['FullText'],
            'image': asset['ImageUrl'],
        } for asset in asset_generator]
        return assets

    def get_random_lols(self, category_id, count=None):
        count = count or self.default_count
        url = 'category/%d/lol/random/%d' % (
            category_id, count
        )
        tree = self.__get_tree(url)
        pictures = [{
            'id': self.__id(picture['LolId']),
            'api_url': picture['LolId'],
            'title': picture['Title'],
            'description': picture['FullText'],
            'image': picture['LolImageUrl'],
        } for picture in tree['Lols']['Random']['Picture']]
        return pictures

    def __get_tree(self, path):
        url = CheezburgerApi.API_URL + path
        self.log('opening url: %s' % url)
        req = Request(url)
        req.add_header('DeveloperKey', self.developer_key)
        req.add_header('ClientID', self.client_id)
        req.add_header('User-Agent', 'Python CheezburgerApi')
        try:
            response = urlopen(req).read()
        except HTTPError, error:
            if error.code == 403:
                raise AuthError('Invalid Developer Key')
            else:
                raise NetworkError(error)
        except URLError, error:
            raise NetworkError(error)
        print response
        self.log('got %d bytes' % len(response))
        tree = xmltodict.parse(response)
        return tree

    @staticmethod
    def __id(url):
        return url.split('/')[-1]

    @staticmethod
    def log(text):
        print 'CheezburgerApi: %s' % text


if __name__ == '__main__':
    api = CheezburgerApi()
    assert api.get_sites()
    assert api.get_categories()
    assert api.get_featured_content(1)
    assert api.get_random_lols(1)

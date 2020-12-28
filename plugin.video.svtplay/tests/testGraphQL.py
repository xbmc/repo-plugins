from __future__ import absolute_import
import inspect
import os
import sys
import unittest
# Manipulate path first to add stubs
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/lib")

from resources.lib.api import graphql

class TestGraphQLModule(unittest.TestCase):

    def assertItems(self, items):
        self.assertIsNotNone(items)
        self.assertTrue(items)

    def test_getPopular(self):
        sut = graphql.GraphQL()
        items = sut.getPopular()
        self.assertItems(items)

    def test_getLatest(self):
        sut = graphql.GraphQL()
        items = sut.getLatest()
        self.assertItems(items)

    def test_getLastChance(self):
        sut = graphql.GraphQL()
        items = sut.getLastChance()
        self.assertItems(items)

    def test_getLive(self):
        sut = graphql.GraphQL()
        items = sut.getLive()
        self.assertItems(items)

    def test_getAtoO(self):
        sut = graphql.GraphQL()
        items = sut.getAtoO()
        self.assertItems(items)

    def test_getProgramsByLetter(self):
        sut = graphql.GraphQL()
        items = sut.getProgramsByLetter("A")
        self.assertItems(items)

    def test_getGenres(self):
        sut = graphql.GraphQL()
        items = sut.getGenres()
        self.assertItems(items)
    
    def test_getProgramsForGenre(self):
        sut = graphql.GraphQL()
        items = sut.getProgramsForGenre("drama")
        self.assertItems(items)
    
    def test_get_video_content(self):
        slug = "agenda"
        sut = graphql.GraphQL()
        items = sut.getVideoContent(slug)
        self.assertItems(items)
  
    def test_get_latest_news(self):
        sut = graphql.GraphQL()
        items = sut.getLatestNews()
        self.assertItems(items)
    
    def test_search_results(self):
        search_term = "agenda"
        sut = graphql.GraphQL()
        items = sut.getSearchResults(search_term)
        self.assertItems(items)
        if len(items) < 1:
            # the hard coded search term needs
            # to be changed if it doesn't yield
            # any results => raise error to alert
            self.fail("search returned no results")

    def test_get_video_data_for_legacy_id(self):
        """
        This test is using an actual video ID.
        https://www.svtplay.se/video/22789702/babblarna/sov-gott-babblarna-sasong-5-avsnitt-9
        Might break in Match 4th 2021... 
        """
        legacy_id = "22789702"
        expected_id = "ew17zDY"
        sut = graphql.GraphQL()
        video_data = sut.getVideoDataForLegacyId(legacy_id)
        self.assertEqual(video_data["svtId"], expected_id)
        self.assertEqual(video_data["blockedForChildren"], False)

    def test_get_thumbnail_url(self):
        image_id = "1234"
        image_changed = 5678
        expected_url = "https://www.svtstatic.se/image/medium/800/1234/5678"
        sut = graphql.GraphQL()
        actual_url = sut.get_thumbnail_url(image_id, image_changed)
        self.assertEqual(expected_url, actual_url)

    def test_getChannels(self):
        sut = graphql.GraphQL()
        channels = sut.getChannels()
        self.assertItems(channels)

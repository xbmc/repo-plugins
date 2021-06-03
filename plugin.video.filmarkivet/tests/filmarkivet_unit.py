import unittest
import sys, os
import xbmcaddon, xbmcvfs
addon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.append(addon_path)
from urllib.parse import parse_qs
from resources.lib.filmarkivet import Filmarkivet
from resources.lib.kodiutils import AddonUtils


class FakeAddonUtils():
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self.name = self.addon.getAddonInfo("name")
        self.id = "plugin.video.filmarkivet"
        self.handle = 0
        self.profile_dir = xbmcvfs.translatePath(self.addon.getAddonInfo("Profile"))
        self.path = addon_path
        self.cache_file = xbmcvfs.translatePath(os.path.join(self.profile_dir,
                                                             "requests_cache"))

    def localize(self, *args):
        if len(args) < 1:
            raise ValueError("String id missing")
        elif len(args) == 1:
            string_id = args[0]
            return self.addon.getLocalizedString(string_id)
        else:
            return [self.addon.getLocalizedString(string_id) for string_id in args]


    def url_for(self, url):
        return "plugin://{0}{1}".format(self.id, url)


class TestFilmarkivet(unittest.TestCase):
    """
        Unittest for detecting API changes on https://filmarkivet.se.
    """

    def setUp(self):
        self.addon_utils = FakeAddonUtils()
        self.filmarkivet = Filmarkivet(self.addon_utils)


    def test_get_categories(self):
        categories = []
        error_msg = "Possible API change detected for categories"
        try:
            for category in self.filmarkivet.get_categories():
                categories.append(category)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        error_msg = "{0}; error: {1}.".format(error_msg, "no categories found")
        self.assertGreater(len(categories), 0, error_msg)


    def test_get_category_movies(self):
        category_url = "https://www.filmarkivet.se/category" \
            "/samhalle-och-politik"
        error_msg = "Possible API change detected for category movies"
        movie_urls = []
        try:
            for movie_item in self.filmarkivet.get_url_movies(category_url,
                    mode="category", page=2):
                item_params = parse_qs(movie_item.url)
                try:
                    movie_url = item_params["url"][0]
                except (AttributeError, KeyError, IndexError) as e:
                    continue

                movie_urls.append(movie_url)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        error_msg = "{0}; error: {1}.".format(error_msg, "no movies found for" \
            "the category 'samhälle och politik'.")
        self.assertGreater(len(movie_urls), 0, error_msg)


    def test_get_themes(self):
        themes = []
        error_msg = "Possible API change detected for themes"
        try:
            for theme in self.filmarkivet.get_themes():
                themes.append(theme)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        error_msg = "{0}; error: {1}.".format(error_msg, "no themes found")
        self.assertGreater(len(themes), 0, error_msg)


    def test_get_theme_categories(self):
        theme_url = "https://www.filmarkivet.se/teman/demokrati"
        error_msg = "Possible API change detected for theme categories"
        theme_categories = []
        try:
            for theme_category in self.filmarkivet.get_theme_categories(theme_url):
                theme_categories.append(theme_category)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        error_msg = "{0}; error: {1}.".format(error_msg, "no theme categories found")
        self.assertGreater(len(theme_categories), 0, error_msg)


    def test_get_theme_category_movies(self):
        theme_movies_url = "https://www.filmarkivet.se/theme/filmstaden-100-ar/"
        error_msg = "Possible API change detected for theme category movies"
        theme_movies = []
        try:
            for theme_movie in self.filmarkivet.get_url_movies(
                    theme_movies_url, page=1, mode="category"):
                theme_movies.append(theme_movie)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        error_msg = "{0}; error: {1}.".format(error_msg, "no movies found")
        self.assertGreater(len(theme_movies), 0, error_msg)


    def test_get_letter_movies(self):
        error_msg = "Possible API change detected for theme categories"
        movies = []
        try:
            for movie in self.filmarkivet.get_letter_movies("K"):
                movies.append(movie)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        error_msg = "{0}; error: {1}.".format(error_msg, "no movies found for \
            the letter K")
        self.assertGreater(len(movies), 0, error_msg)


    def test_get_media_url(self):
        movie_urls = (
            "https://www.filmarkivet.se/movies/talarfilm-bokforlaggaren-k-o-bonnier-1940",
            "https://www.filmarkivet.se/movies/skrot-blir-stal",
            "https://www.filmarkivet.se/movies/svenska-veckan-i-eskilstuna-1911-goteborgsbilder-1912-motorcyckeltavling",
            )

        error_msg = "Possible API change detected for get_media_url"
        media_urls = []
        try:
            for movie_url in movie_urls:
                media_url = self.filmarkivet.get_media_url(movie_url)
                if media_url is not None:
                    media_urls.append(media_url)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        error_msg = "{0}; error: {1}.".format(error_msg,
            "urls found ({0}/{1})".format(len(media_urls), len(movie_urls)))
        self.assertGreater(len(media_urls), 0, error_msg)


    def test_search(self):
        error_msg = "Possible API change detected for search"
        key = "kungar"
        try:
            movie_items = self.filmarkivet.get_url_movies(
                "/sokresultat/?q={0}".format(key),
                mode="search&key={0}".format(key), page=1, limit=True)
        except Exception as e:
            error_msg = "{0}; exception caught: {1}".format(error_msg, str(e))
            self.fail(error_msg)

        media_urls = []
        for movie_item in movie_items:
            item_params = parse_qs(movie_item.url)
            try:
                media_url = item_params["url"][0]
                if media_url is not None:
                    media_urls.append(media_url)
            except (AttributeError, KeyError, IndexError) as e:
                continue

        error_msg = "{0}; error: {1}.".format(error_msg, "no movies found for "
            "search 'kungar'")
        self.assertGreater(len(media_urls), 0, error_msg)


if __name__ == "__main__":
    unittest.main()

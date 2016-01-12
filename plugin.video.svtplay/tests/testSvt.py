import inspect
import sys
import unittest
# Manipulate path first
sys.path.append("../")
sys.path.append("./lib")

import resources.lib.svt as svt
import CommonFunctions as common

# Set up the CommonFunctions module
common.plugin = "TestSvt"
common.dbg = True

class TestSvtModule(unittest.TestCase):

  def assertHasContent(self, list):
    if list == None:
      self.fail("List is None")

    if list == []:
      self.fail("List is empty")

  def test_alphabetic(self):
    programs = svt.getAtoO()

    self.assertHasContent(programs)

    for program in programs:
      for key in program.keys():
        self.assertIsNotNone(program[key])

  def test_categories(self):

    categories = svt.getCategories()

    self.assertHasContent(categories)

    for category in categories:
      for key in category.keys():
        self.assertIsNotNone(category[key])

  def test_programs_for_category(self):

    categories = svt.getCategories()
    for category in categories:
      programs = svt.getProgramsForCategory(category["url"])

      self.assertHasContent(programs)

      for program in programs:
        for key in program.keys():
          self.assertIsNotNone(program[key])

  def test_get_alphas(self):

    alphas = svt.getAlphas()

    self.assertHasContent(alphas)

  def test_programs_by_letter(self):

    letter = u'A' # "A" should always have programs...

    programs = svt.getProgramsByLetter(letter)

    self.assertHasContent(programs)

    for program in programs:
      for key in program.keys():
        self.assertIsNotNone(program[key])

  def test_search_results(self):

    url = "/sok?q=agenda" # Agenda should have some items

    items = svt.getSearchResults(url)

    self.assertHasContent(items)

    for item in items:
      for key in item.keys():
        self.assertIsNotNone(item[key])

  def test_get_channels(self):
    items = svt.getChannels()

    self.assertHasContent(items)

  def test_get_latest_news(self):
    items = svt.getLatestNews()

    self.assertHasContent(items)

  def test_get_episodes(self):
    url = "/agenda"
    articles = svt.getEpisodes(url)

    self.assertHasContent(articles)

  def test_get_clips(self):
    url = "/agenda"
    articles = svt.getClips(url)

    self.assertHasContent(articles)

if __name__ == "__main__":
  unittest.main()

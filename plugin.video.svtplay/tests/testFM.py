import os
import os.path
import sys
import unittest

# Manipulate path to include addon source and stubs
sys.path.append("../")
sys.path.append("./lib")

import resources.lib.FavoritesManager as fm
import CommonFunctions as common

# Set up the CommonFunctions module
common.plugin = "TestFm"
common.dbg = True
log = common.log

FILE_PATH = "favorites.json"


class TestFmModule(unittest.TestCase):

  def test_add(self):
    print("\n")
    log("Starting test")
    # Add item
    title = "Test add"
    url = "http://apa.com"
    fav_id = fm.add(title, url)
    # Check that item is in file
    file_handle = open(FILE_PATH, "r")
    lines = file_handle.readlines()
    file_handle.close()
    lines = "".join(lines)
    if not fav_id in lines:
      self.fail("Test object was not written to file!")

  def test_get(self):
    print("\n")
    log("Starting test")
    # Add item
    title = "Test get"
    url = "http://apa.com"
    fav_id = fm.add(title, url)

    # Get item
    fav_obj = fm.get(fav_id)
    self.assertIsNotNone(fav_obj, "Could not retrieve item!")
    fav_obj = None
    fav_obj = fm.get_by_title(title)
    self.assertIsNotNone(fav_obj, "Could not retrieve item!")


  def test_remove(self):
    print("\n")
    log("Starting test")
    #Add item
    title = "Test remove"
    url = "http://apa.com"

    fav_id = fm.add(title, url)
    self.assertIsNotNone(fm.get(fav_id), "Could not retrieve item!")

    # Remove item
    removed = fm.remove(fav_id)
    self.assertTrue(removed, "Item could not be removed!")
    self.assertIsNone(fm.get(fav_id), "Item is still in collection!")

  def test_get_all(self):
    print("\n")
    log("Starting test")
    nr_items = 5
    for i in range(nr_items):
      title = "Test get all %d" % i
      url = "Url %d" % i
      fm.add(title, url)

    all_items = fm.get_all()
    print str(all_items)
    self.assertEqual(len(all_items), nr_items)

  def setUp(self):
    # Test if file is empty
    if os.path.isfile(FILE_PATH) and os.stat(FILE_PATH).st_size != 0:
      self.fail("Old favorites file exists!")

  def tearDown(self):
    log("Clear FM")
    fm.clear()
    if os.path.exists(FILE_PATH):
      log("Removing favorites file '%s'" % FILE_PATH)
      os.remove(FILE_PATH)

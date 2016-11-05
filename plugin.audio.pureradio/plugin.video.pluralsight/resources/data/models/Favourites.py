import sys
import Catalogue
import xbmc

if len(sys.argv) == 4:
    course_name = sys.argv[1]
    course_title = sys.argv[2]
    g_database_path = sys.argv[3]
    Catalogue.Catalogue.add_favourite(course_name, course_title, g_database_path)

if len(sys.argv) == 3:
    course_name = sys.argv[1]
    g_database_path = sys.argv[2]
    Catalogue.Catalogue.remove_favourite(course_name,g_database_path)
    xbmc.executebuiltin('XBMC.Container.Update(%s?mode=favourites)' % ('plugin://plugin.video.pluralsight'))
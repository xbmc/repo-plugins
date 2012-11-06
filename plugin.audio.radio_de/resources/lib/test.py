from api import RadioApi

DEPTH = 3
SEARCH_STRING = 'WDR'
STATION_IDS = (2279, 3643)


def do_nothing(*args, **kwargs):
    pass

print 'Get Instance'
ra = RadioApi()
ra.log = do_nothing

print 'Checking get_category_types'
cat_types = ra.get_category_types()
assert cat_types

for cat_type in cat_types:
    print 'Checking get_categories by category_type=%s' % repr(cat_type)
    categories = ra.get_categories(cat_type)
    assert categories
    for category in categories[0:DEPTH]:
        print ('Checking get_stations_by_category category_type=%s category=%s'
               % (repr(cat_type), repr(category)))
        stations = ra.get_stations_by_category(cat_type, category)
        assert stations

print 'Checking get_recommendation_stations'
assert ra.get_recommendation_stations()

print 'Checking get_top_stations'
assert ra.get_top_stations()

print 'Checking get_local_stations'
assert ra.get_local_stations()

print 'Checking _get_most_wanted'
assert ra._get_most_wanted()

print 'Checking search_stations_by_string'
assert ra.search_stations_by_string('WDR')

for station in STATION_IDS:
    print 'Checking get_station_by_station_id'
    assert ra.get_station_by_station_id(station)

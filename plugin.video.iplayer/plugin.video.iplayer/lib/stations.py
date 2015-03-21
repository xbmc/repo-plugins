##
## Data on TV Channels, Radio Stations & Programme Categories
##
##

channels_tv_list = [
    ('bbc_one', 'BBC One'),
    ('bbc_two', 'BBC Two'),
    ('bbc_three', 'BBC Three'),
    ('bbc_four', 'BBC Four'),
    ('cbbc', 'CBBC'),
    ('cbeebies', 'CBeebies'),
    ('bbc_webonly', 'BBC Web Only'),
    ('bbc_news24', 'BBC News Channel'),
    ('bbc_parliament', 'BBC Parliament'),
    ('bbc_alba', 'BBC Alba'),
    ('s4cpbs', 'S4C'),
    ('bbc_sport', 'BBC Sport'),
]

channels_tv_live_mapping = {
    'bbc_one': 'bbc_one_hd',
    'bbc_two': 'bbc_two_hd',
    'bbc_three': 'bbc_three_hd',
    'bbc_four': 'bbc4',
    'cbbc': 'cbbc',
    'cbeebies': 'cbeebies',
    'bbc_news24': 'news_ch',
    'bbc_parliament': 'parliament',
    'bbc_alba': 'alba',
}

radio_station_info = [
    {'id': 'bbc_radio_one',
     'name': 'Radio 1',
     'logo': None,
     'type': 'national',
     'webcam' : 'http://www.bbc.co.uk/radio1/webcam/images/live/webcam.jpg'},

    {'id': 'bbc_1xtra',
     'name': 'Radio 1 Xtra',
     'logo': None,
     'type': 'national',
     'webcam': 'http://www.bbc.co.uk/1xtra/webcam/live/1xtraa.jpg'},

    {'id': 'bbc_radio_two',
     'name': 'Radio 2',
     'logo': None,
     'type': 'national',
     'webcam': 'http://www.bbc.co.uk/radio2/webcam/live/radio2.jpg'},

    {'id': 'bbc_radio_three',
     'name': 'Radio 3',
     'logo': None,
     'type': 'national'},

    {'id': 'bbc_radio_four',
     'name': 'Radio 4',
     'logo': None,
     'type': 'national'},

    {'id': 'bbc_radio_four_extra',
     'name': 'Radio 4 Extra',
     'logo': None,
     'type': 'national'},

    {'id': 'bbc_radio_five_live',
     'name': 'Radio 5 Live',
     'logo': None,
     'type': 'national',
     'webcam': 'http://www.bbc.co.uk/fivelive/inside/webcam/5Lwebcam1.jpg'},

    {'id': 'bbc_radio_five_live_sports_extra',
     'name': 'Radio 5 Live Sports Extra',
      'logo': None,
     'type': 'national'},

    {'id': 'bbc_6music',
     'name': 'Radio 6 Music',
      'logo': None,
     'type': 'national',
     'webcam': 'http://www.bbc.co.uk/6music/webcam/live/6music.jpg'},

    {'id': 'bbc_asian_network',
     'name': 'Asian Network',
     'logo': None,
     'type': 'national',
     'webcam': 'http://www.bbc.co.uk/asiannetwork/webcams/birmingham.jpg'},
     
    {'id': 'bbc_world_service',
     'name': 'World Service',
     'logo': None,
     'type': 'national'},

    {'id': 'bbc_school_radio',
     'name': 'School Radio',
     'logo': None,
     'type': 'national'},

    {'id': 'bbc_radio_scotland',
     'name': 'BBC Scotland',
     'logo': None,
     'type': 'regional'},

    {'id': 'bbc_radio_ulster',
     'name': 'BBC Ulster',
     'logo': None,
     'type': 'regional'},

    {'id': 'bbc_radio_foyle',
     'name': 'Radio Foyle',
     'logo': None,
     'type': 'regional'},

    {'id': 'bbc_radio_wales',
     'name': 'BBC Wales',
     'logo': None,
     'type': 'regional'},

    {'id': 'bbc_radio_cymru',
     'name': 'BBC Cymru',
     'logo': None,
     'type': 'regional'},

    {'id': 'bbc_radio_nan_gaidheal',
     'name': 'BBC nan Gaidheal',
     'logo': None,
     'type': 'regional'},

    {'id': 'bbc_radio_berkshire',
     'name': 'BBC Berkshire',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_berks.gif',
     'type': 'local'},

    {'id': 'bbc_radio_bristol',
     'name': 'BBC Bristol',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/bristol.gif',
     'type': 'local'},

    {'id': 'bbc_radio_cambridge',
     'name': 'BBC Cambridge',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/cambridgeshire.gif',
     'type': 'local'},

    {'id': 'bbc_radio_cornwall',
     'name': 'BBC Cornwall',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/cornwall.gif',
     'type': 'local'},

    {'id': 'bbc_radio_coventry_warwickshire',
     'name': 'BBC Coventry Warwickshire',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/cov_warks.gif',
     'type': 'local'},

    {'id': 'bbc_radio_cumbria',
     'name': 'BBC Cumbria',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/cumbria.gif',
     'type': 'local'},

    {'id': 'bbc_radio_derby',
     'name': 'BBC Derby',
     'logo': 'http://www.bbc.co.uk/englandcms/derby/images/rh_nav170_derby.gif',
     'type': 'local'},

    {'id': 'bbc_radio_devon',
     'name': 'BBC Devon',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_devon.gif',
     'type': 'local'},

    {'id': 'bbc_radio_essex',
     'name': 'BBC Essex',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_essex.gif',
     'type': 'local'},

    {'id': 'bbc_radio_gloucestershire',
     'name': 'BBC Gloucestershire',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/gloucestershire.gif',
     'type': 'local'},

    {'id': 'bbc_radio_guernsey',
     'name': 'BBC Guernsey',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/guernsey.gif',
     'type': 'local'},

    {'id': 'bbc_radio_hereford_worcester',
     'name': 'BBC Hereford/Worcester',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/hereford_worcester.gif',
     'type': 'local'},

    {'id': 'bbc_radio_humberside',
     'name': 'BBC Humberside',
     'logo': 'http://www.bbc.co.uk/radio/images/home/r-home-nation-regions.gif',
     'type': 'local'},

    {'id': 'bbc_radio_jersey',
     'name': 'BBC Jersey',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/jersey.gif',
     'type': 'local'},

    {'id': 'bbc_radio_kent',
     'name': 'BBC Kent',
     'logo': 'http://www.bbc.co.uk/radio/images/home/r-home-nation-regions.gif',
     'type': 'local'},

    {'id': 'bbc_radio_lancashire',
     'name': 'BBC Lancashire',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_lancs.gif',
     'type': 'local'},

    {'id': 'bbc_radio_leeds',
     'name': 'BBC Leeds',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_leeds.gif',
     'type': 'local'},

    {'id': 'bbc_radio_leicester',
     'name': 'BBC Leicester',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/leicester.gif',
     'type': 'local'},

    {'id': 'bbc_radio_lincolnshire',
     'name': 'BBC Lincolnshire',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/lincs.gif',
     'type': 'local'},

    {'id': 'bbc_london',
     'name': 'BBC London',
     'logo': None,
     'type': 'local'},

    {'id': 'bbc_radio_manchester',
     'name': 'BBC Manchester',
     'logo': None,
     'type': 'local'},

    {'id': 'bbc_radio_merseyside',
     'name': 'BBC Merseyside',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/merseyside.gif',
     'type': 'local'},

    {'id': 'bbc_radio_newcastle',
     'name': 'BBC Newcastle',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/newcastle.gif',
     'type': 'local'},

    {'id': 'bbc_radio_norfolk',
     'name': 'BBC Norfolk',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/norfolk.gif',
     'type': 'local'},

    {'id': 'bbc_radio_northampton',
     'name': 'BBC Northampton',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/northampton.gif',
     'type': 'local'},

    {'id': 'bbc_radio_nottingham',
     'name': 'BBC Nottingham',
     'logo': None,
     'type': 'local'},

    {'id': 'bbc_radio_oxford',
     'name': 'BBC Oxford',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_oxford.gif',
     'type': 'local'},

    {'id': 'bbc_radio_sheffield',
     'name': 'BBC Sheffield',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_sheffield.gif',
     'type': 'local'},

    {'id': 'bbc_radio_shropshire',
     'name': 'BBC Shropshire',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/shropshire.gif',
     'type': 'local'},

    {'id': 'bbc_radio_solent',
     'name': 'BBC Solent',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/solent.gif',
     'type': 'local'},

    {'id': 'bbc_radio_somerset_sound',
     'name': 'BBC Somerset',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_somerset.gif',
     'type': 'local'},

    {'id': 'bbc_radio_stoke',
     'name': 'BBC Stoke',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/stoke.gif',
     'type': 'local'},

    {'id': 'bbc_radio_suffolk',
     'name': 'BBC Suffolk',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/suffolk.gif',
     'type': 'local'},

    {'id': 'bbc_radio_surrey',
     'name': 'BBC Surrey',
     'logo': None,
     'type': 'local'},

    {'id': 'bbc_radio_sussex',
     'name': 'BBC Sussex',
     'logo': None,
     'type': 'local'},

    {'id': 'bbc_radio_wiltshire',
     'name': 'BBC Wiltshire',
     'logo': None,
     'type': 'local'},

    {'id': 'bbc_radio_york',
     'name': 'BBC York',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/york.gif',
     'type': 'local'},

    {'id': 'bbc_tees',
     'name': 'BBC Tees',
     'logo': 'http://www.bbc.co.uk/englandcms/localradio/images/tees.gif',
     'type': 'local'},

    {'id': 'bbc_three_counties_radio',
     'name': 'BBC Three Counties Radio',
     'logo': 'http://www.bbc.co.uk/englandcms/images/rh_nav170_3counties.gif',
     'type': 'local'},

    {'id': 'bbc_wm',
     'name': 'BBC WM',
     'logo': None,
     'type': 'local'},
]

# build a list of radio channel IDs
channels_radio_list = []
channels_radio_type_list = {}
for i in radio_station_info:
    channels_radio_list.append((i['id'], i['name']))
    rtype = i['type']
    if rtype != None:
        if not channels_radio_type_list.has_key(rtype):
            # initialize radio type list
            channels_radio_type_list[rtype] = []
        channels_radio_type_list[rtype].append((i['id'], i['name']))

channels = dict(channels_tv_list + channels_radio_list)
channels_tv = dict(channels_tv_list)
channels_radio = dict(channels_radio_list)

# build a dict of available logos
channels_logos = {}
for i in radio_station_info:
    channels_logos[i['id']] = i['logo']

live_webcams_list = []
for i in radio_station_info:
    if i.has_key('webcam'):
        live_webcams_list.append((i['name'], i['webcam']))
live_webcams = dict(live_webcams_list)

categories_list = [
    ('childrens', 'Children\'s'),
    ('comedy', 'Comedy'),
    ('drama', 'Drama'),
    ('entertainment', 'Entertainment'),
    ('factual', 'Factual'),
    ('music', 'Music'),
    ('news', 'News'),
    ('religion_and_ethics', 'Religion & Ethics'),
    ('sport', 'Sport'),
    ('olympics', 'Olympics'),
    ('wales', 'Wales'),
    ('signed', 'Sign Zone')
]
categories = dict(categories_list)



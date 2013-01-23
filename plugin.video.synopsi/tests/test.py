import json
import datetime

from PIL import Image, ImageDraw, ImageOps

jsfile = [ 

         {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-960.jpg',
          'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-267.jpg',
          'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-223.jpg',
          'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-134.jpg',
          'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-075.jpg',
          
          'genres': ['Sci-Fi', 'Adventure', 'Action'],
          'id': 136558,
          'image': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-075.jpg',
          'link': '/movies/136558/the-time-machine-2002/',
          'name': u'The Time Machine',
          'plot': u'Based on the classic sci-fi novel by H.G. Wells, scientist and inventor, Alexander Hartdegen, is determined to prove that time travel is possible. His determination is turned to desperation by a personal tragedy that now drives him to want to change the past. Testing his theories&hellip;',
          
          'released': False,
          'slug': u'the-time-machine-2002',
          'trailer': u'https://www.youtube.com/embed/ZJuHV3BXGm0',
          'type': u'movie',
          'url': '/movies/136558/the-time-machine-2002/',
          'year': 2002},
 {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-960.jpg',
          'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-267.jpg',
          'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-223.jpg',
          'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-134.jpg',
          'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-075.jpg',
          
          'genres': ['Action', 'Adventure', 'Fantasy', 'Sci-Fi'],
          'id': 230206,
          'image': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-075.jpg',
          'link': '/movies/230206/star-wars-episode-vi-return-of-the-jedi-1983/',
          'name': u'Star Wars: Episode VI - Return of the Jedi',
          'plot': u'Darth Vader and the Empire are building a new, indestructible Death Star. Meanwhile, Han Solo has been imprisoned, and Luke Skywalker has sent R2-D2 and C-3PO to try and free him. Princess Leia - disguised as a bounty hunter - and Chewbacca go along as well. The final battle takes&hellip;',
          
          'released': False,
          'slug': u'star-wars-episode-vi-return-of-the-jedi-1983',
          'trailer': u'https://www.youtube.com/embed/pIuNQWFb31Q',
          'type': u'movie',
          'url': '/movies/230206/star-wars-episode-vi-return-of-the-jedi-1983/',
          'year': 1983},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-960.jpg',
          'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-267.jpg',
          'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-223.jpg',
          'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-134.jpg',
          'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-075.jpg',
          
          'genres': ['Action', 'Adventure', 'Crime', 'Mystery', 'Thriller'],
          'id': 654591,
          'image': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-075.jpg',
          'link': '/movies/654591/sherlock-holmes-a-game-of-shadows-2011/',
          'name': u'Sherlock Holmes: A Game of Shadows',
          'plot': u"Sherlock Holmes (Robert Downey, Jr.) and his longtime trusted associate, Doctor Watson (Jude Law), take on their arch-nemesis, Professor Moriarty (Jared Harris), with the help of Holmes's older brother Mycroft Holmes (Stephen Fry) and a gypsy named Sim (Noomi Rapace).",
          
          'released': False,
          'slug': u'sherlock-holmes-a-game-of-shadows-2011',
          'trailer': u'https://www.youtube.com/embed/XFQOqofpwPg',
          'type': u'movie',
          'url': '/movies/654591/sherlock-holmes-a-game-of-shadows-2011/',
          'year': 2011},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-960.jpg',
           'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-267.jpg',
           'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-223.jpg',
           'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-134.jpg',
           'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-075.jpg',
           
           'genres': ['Action', 'Drama', 'Thriller'],
           'id': 2382712,
           'image': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-075.jpg',
           'link': '/movies/2382712/clear-and-present-danger-1994/',
           'name': u'Clear and Present Danger',
           'plot': u"Jack Ryan is back and this time the bad guys are in his own government. When Admiral James Greer becomes sick with cancer, Ryan is appointed acting CIA Deputy Director of Intelligence. Almost before he can draw a breath in his new position, one of the president's closest friends&hellip;",
           
           'released': False,
           'slug': u'clear-and-present-danger-1994',
           'trailer': u'https://www.youtube.com/embed/MNzWYVWfRIc',
           'type': u'movie',
           'url': '/movies/2382712/clear-and-present-danger-1994/',
           'year': 1994},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-960.jpg',
           'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-267.jpg',
           'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-223.jpg',
           'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-134.jpg',
           'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-075.jpg',
           
           'genres': ['Comedy', 'Drama', 'Fantasy', 'Sci-Fi', 'Thriller'],
           'id': 2455949,
           'image': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-075.jpg',
           'link': '/movies/2455949/southland-tales-2006/',
           'name': u'Southland Tales',
           'plot': u"Southland Tales is an ensemble piece set in the futuristic landscape of Los Angeles on July 4, 2008, as it stands on the brink of social, economic and environmental disaster. Boxer Santaros is an action star who's stricken with amnesia. His life intertwines with Krysta Now, an adult&hellip;",
           
           'released': False,
           'slug': u'southland-tales-2006',
           'trailer': u'https://www.youtube.com/embed/vtp14ikRvxo',
           'type': u'movie',
           'url': '/movies/2455949/southland-tales-2006/',
           'year': 2006},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-960.jpg',
           'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-267.jpg',
           'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-223.jpg',
           'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-134.jpg',
           'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-075.jpg',
           
           'genres': ['Action', 'Sci-Fi', 'Thriller'],
           'id': 3094553,
           'image': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-075.jpg',
           'link': '/movies/3094553/terminator-2-judgment-day-1991/',
           'name': u'Terminator 2: Judgment Day',
           'plot': u'Nearly 10 years have passed since Sarah Connor was targeted for termination by a cyborg from the future. Now her son, John, the future leader of the resistance, is the target for a newer, more deadly terminator. Once again, the resistance has managed to send a protector back to attem&hellip;',
           
           'released': False,
           'slug': u'terminator-2-judgment-day-1991',
           'trailer': '',
           'type': u'movie',
           'url': '/movies/3094553/terminator-2-judgment-day-1991/',
           'year': 1991},
{'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-960.jpg',
          'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-267.jpg',
          'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-223.jpg',
          'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-134.jpg',
          'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-075.jpg',
          
          'genres': ['Sci-Fi', 'Adventure', 'Action'],
          'id': 136558,
          'image': u'https://s3.amazonaws.com/titles.synopsi.tv/00136558-075.jpg',
          'link': '/movies/136558/the-time-machine-2002/',
          'name': u'The Time Machine',
          'plot': u'Based on the classic sci-fi novel by H.G. Wells, scientist and inventor, Alexander Hartdegen, is determined to prove that time travel is possible. His determination is turned to desperation by a personal tragedy that now drives him to want to change the past. Testing his theories&hellip;',
          
          'released': False,
          'slug': u'the-time-machine-2002',
          'trailer': u'https://www.youtube.com/embed/ZJuHV3BXGm0',
          'type': u'movie',
          'url': '/movies/136558/the-time-machine-2002/',
          'year': 2002},
 {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-960.jpg',
          'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-267.jpg',
          'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-223.jpg',
          'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-134.jpg',
          'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-075.jpg',
          
          'genres': ['Action', 'Adventure', 'Fantasy', 'Sci-Fi'],
          'id': 230206,
          'image': u'https://s3.amazonaws.com/titles.synopsi.tv/00230206-075.jpg',
          'link': '/movies/230206/star-wars-episode-vi-return-of-the-jedi-1983/',
          'name': u'Star Wars: Episode VI - Return of the Jedi',
          'plot': u'Darth Vader and the Empire are building a new, indestructible Death Star. Meanwhile, Han Solo has been imprisoned, and Luke Skywalker has sent R2-D2 and C-3PO to try and free him. Princess Leia - disguised as a bounty hunter - and Chewbacca go along as well. The final battle takes&hellip;',
          
          'released': False,
          'slug': u'star-wars-episode-vi-return-of-the-jedi-1983',
          'trailer': u'https://www.youtube.com/embed/pIuNQWFb31Q',
          'type': u'movie',
          'url': '/movies/230206/star-wars-episode-vi-return-of-the-jedi-1983/',
          'year': 1983},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-960.jpg',
          'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-267.jpg',
          'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-223.jpg',
          'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-134.jpg',
          'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-075.jpg',
          
          'genres': ['Action', 'Adventure', 'Crime', 'Mystery', 'Thriller'],
          'id': 654591,
          'image': u'https://s3.amazonaws.com/titles.synopsi.tv/00654591-075.jpg',
          'link': '/movies/654591/sherlock-holmes-a-game-of-shadows-2011/',
          'name': u'Sherlock Holmes: A Game of Shadows',
          'plot': u"Sherlock Holmes (Robert Downey, Jr.) and his longtime trusted associate, Doctor Watson (Jude Law), take on their arch-nemesis, Professor Moriarty (Jared Harris), with the help of Holmes's older brother Mycroft Holmes (Stephen Fry) and a gypsy named Sim (Noomi Rapace).",
          
          'released': False,
          'slug': u'sherlock-holmes-a-game-of-shadows-2011',
          'trailer': u'https://www.youtube.com/embed/XFQOqofpwPg',
          'type': u'movie',
          'url': '/movies/654591/sherlock-holmes-a-game-of-shadows-2011/',
          'year': 2011},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-960.jpg',
           'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-267.jpg',
           'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-223.jpg',
           'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-134.jpg',
           'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-075.jpg',
           
           'genres': ['Action', 'Drama', 'Thriller'],
           'id': 2382712,
           'image': u'https://s3.amazonaws.com/titles.synopsi.tv/02382712-075.jpg',
           'link': '/movies/2382712/clear-and-present-danger-1994/',
           'name': u'Clear and Present Danger',
           'plot': u"Jack Ryan is back and this time the bad guys are in his own government. When Admiral James Greer becomes sick with cancer, Ryan is appointed acting CIA Deputy Director of Intelligence. Almost before he can draw a breath in his new position, one of the president's closest friends&hellip;",
           
           'released': False,
           'slug': u'clear-and-present-danger-1994',
           'trailer': u'https://www.youtube.com/embed/MNzWYVWfRIc',
           'type': u'movie',
           'url': '/movies/2382712/clear-and-present-danger-1994/',
           'year': 1994},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-960.jpg',
           'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-267.jpg',
           'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-223.jpg',
           'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-134.jpg',
           'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-075.jpg',
           
           'genres': ['Comedy', 'Drama', 'Fantasy', 'Sci-Fi', 'Thriller'],
           'id': 2455949,
           'image': u'https://s3.amazonaws.com/titles.synopsi.tv/02455949-075.jpg',
           'link': '/movies/2455949/southland-tales-2006/',
           'name': u'Southland Tales',
           'plot': u"Southland Tales is an ensemble piece set in the futuristic landscape of Los Angeles on July 4, 2008, as it stands on the brink of social, economic and environmental disaster. Boxer Santaros is an action star who's stricken with amnesia. His life intertwines with Krysta Now, an adult&hellip;",
           
           'released': False,
           'slug': u'southland-tales-2006',
           'trailer': u'https://www.youtube.com/embed/vtp14ikRvxo',
           'type': u'movie',
           'url': '/movies/2455949/southland-tales-2006/',
           'year': 2006},
  {'cover_full': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-960.jpg',
           'cover_large': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-267.jpg',
           'cover_medium': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-223.jpg',
           'cover_small': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-134.jpg',
           'cover_thumbnail': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-075.jpg',
           
           'genres': ['Action', 'Sci-Fi', 'Thriller'],
           'id': 3094553,
           'image': u'https://s3.amazonaws.com/titles.synopsi.tv/2371b5d0b29c0ab4d0c7e65b5fc0cd91-075.jpg',
           'link': '/movies/3094553/terminator-2-judgment-day-1991/',
           'name': u'Terminator 2: Judgment Day',
           'plot': u'Nearly 10 years have passed since Sarah Connor was targeted for termination by a cyborg from the future. Now her son, John, the future leader of the resistance, is the target for a newer, more deadly terminator. Once again, the resistance has managed to send a protector back to attem&hellip;',
           
           'released': False,
           'slug': u'terminator-2-judgment-day-1991',
           'trailer': '',
           'type': u'movie',
           'url': '/movies/3094553/terminator-2-judgment-day-1991/',
           'year': 1991}


           ]


#jsfile = open("recco.js","r")
#data = json.loads(jsfile.read())
"""
for film in jsfile:
	#print film
	print film.get('cover_medium'), film.get('name')

"""


# import urllib2
# import urllib
# import time

# class Timer():
#     def __enter__(self):
#         self.start = time.time()

#     def __exit__(self, *args):
#         print str(time.time() - self.start)

# def list_img(x, y):
#     im = Image.new("RGBA", (3*x, y), "white")
#     for i in range(6):
#         with Timer():
#             urllib.urlretrieve (jsfile[i].get('cover_medium').replace("https://","http://"), "tmp.jpg")
#         _im = Image.open("tmp.jpg")
#         y = ImageOps.expand(_im, border=5, fill='white')
#         im.paste(y, (0 + (x // 2) * i, 0))
#     im.save("list.png","PNG")

# def list_imgB(x, y):
#     im = Image.new("RGBA", (6*x, y), "white")
#     for i in range(12):
#         urllib.urlretrieve (jsfile[i].get('cover_medium'), "tmp.jpg")
#         _im = Image.open("tmp.jpg")
#         y = ImageOps.expand(_im, border=5, fill='white')
#         im.paste(y, (0 + (x // 2) * i, 0))
#     im.save("list.png","PNG")

# with Timer():
#     list_img(150, 223)
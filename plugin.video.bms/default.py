#/*
# *      Copyright (C) 2011 Team XBMC
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */


import string,os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

__addonid__       = 'plugin.video.bms'
__settings__      = xbmcaddon.Addon(id=__addonid__)
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__     = "Bluray Movie Streamer"
__author__        = "Team XBMC"

BASE_URL = "http://mirrors.xbmc.org/rr.avi"

def INDEX(items):
  for stat in items:
    addLink(stat)
    log()

def PLAY():
  xbmc.Player().play(BASE_URL)

def addLink(info):
  ok=True
  url = "%s?play=hehe%s" % (sys.argv[0], info[0],)
  liz=xbmcgui.ListItem(info[0], iconImage="DefaultVideo.png", thumbnailImage=os.path.join( xbmc.translatePath( __cwd__ ),"images",info[1]))
  liz.setInfo( type="video", infoLabels={ "Title": info[0], "Tagline": info[2], "Plot": info[3], "Director": info[4], "Year": info[5], "Rating": info[6], "Genre": info[7]} )
  liz.setProperty("IsPlayable","false");
  xbmcplugin.setContent(int( sys.argv[ 1 ]) ,'movies');
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,isFolder=False)
  return ok

def get_params():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
  return param

def log():
  xbmc.output("### [%s] - %s" % (__addonname__,"OMG!! Can't believe you fell for that?:)",),level=xbmc.LOGINFO )
  xbmc.output("### [%s] - %s" % (__addonname__,"Happy April Fools Day! :)",),level=xbmc.LOGINFO )


params=get_params()
try:
  id = params["id"]
except:
  id = "0";
  pass
try:
  play = params["play"]
except:
  play = "0";
  pass  

iid = len(id);
iplay = len(play)

if iplay > 1:
  PLAY()
else:
  items = (("The Green Hornet", "7.jpg", "Breaking The Law To Protect It", "Britt Reid is the son of LA's most prominent and respected media magnate and perfectly happy to maintain a directionless existence on the party scene until his father mysteriously dies, leaving Britt his vast media empire. Striking an unlikely friendship with one of his father's more industrious and inventive employees, Kato, they see their chance to do something meaningful for the first time in their lives: fight crime. But in order to do this, they decide to become criminals themselves, protecting the law by breaking it, Britt becomes the vigilante The Green Hornet as he and Kato hit the streets. The Green Hornet and Kato quickly start making a name for themselves, and with the help of Britt's new secretary, Lenore Case, they begin hunting down the man who controls LA's gritty underworld: Benjamin Chudnofsky. But Chudnofsky has plans of his own: to swat down The Green Hornet once and for all.", "Michel Gondry", 2011, 7, "Action / Crime / Thriller / Comedy"),
         ("Little Fockers", "2.jpg", "Kids bring everyone closer, right?", "It has taken 10 years, two little Fockers with wife Pam (Polo) and countless hurdles for Greg (Stiller) to finally get in with his tightly wound father-in-law, Jack (De Niro). After the cash-strapped dad takes a job moonlighting for a drug company, Jack's suspicions about his favorite male nurse come roaring back. When Greg and Pam's entire clan -- including Pam's lovelorn ex, Kevin (Wilson) -- descends for the twins' birthday party, Greg must prove to the skeptical Jack that he's fully capable as the man of the house. But with all the misunderstandings, spying and covert missions, will Greg pass Jack's final test and become the family's next patriarch...or will the circle of trust be broken for good?", "Paul Weitz", 2010, 7.4, "Comedy"), 
         ("The Dilemma","4.jpg", "A little knowledge is a dangerous thing.", "Longtime friends Ronny and Nick are partners in an auto-design firm. They are hard at work on a presentation for a dream project that would really launch their company. Ronny spots Nick's wife out with another man and in the process of investigating the possible affair he learns Nick has a few secrets of his own. As the presentation nears, Ronny agonizes over what might happen if the truth gets out.", "Ron Howard", 2010, 5.6, "Comedy / Drama"),
         ("True Grit", "8.jpg", "Punishment Comes One Way or Another", "Following the murder of her father by hired hand Tom Chaney, 14-year-old farm girl Mattie Ross sets out to capture the killer. To aid her, she hires the toughest U.S. marshal she can find, a man with 'true grit,' Reuben J. 'Rooster' Cogburn. Mattie insists on accompanying Cogburn, whose drinking, sloth, and generally reprobate character do not augment her faith in him. Against his wishes, she joins him in his trek into the Indian Nations in search of Chaney. They are joined by Texas Ranger LaBoeuf, who wants Chaney for his own purposes. The unlikely trio find danger and surprises on the journey, and each has his or her 'grit' tested.", "Ethan Coen / Joel Coen", 2010, 8.4, "Action / Adventure / Drama / Thriller / Western" ),
         ("The King's Speech", "9.jpg", "God save the king.", "Tells the story of the man who became King George VI, the father of Queen Elizabeth II. After his brother abdicates, George ('Bertie') reluctantly assumes the throne. Plagued by a dreaded stutter and considered unfit to be king, Bertie engages the help of an unorthodox speech therapist named Lionel Logue. Through a set of unexpected techniques, and as a result of an unlikely friendship, Bertie is able to find his voice and boldly lead the country into war.", "Tom Hooper", 2010, 8.6, "Drama / History"), 
         ("Tron Legacy","10.jpg", "The Game Has Changed", "Sam Flynn, the tech-savvy 27-year-old son of Kevin Flynn, looks into his father's disappearance and finds himself pulled into the same world of fierce programs and gladiatorial games where his father has been living for 25 years. Along with Kevin's loyal confidant, father and son embark on a life-and-death journey across a visually-stunning cyber universe that has become far more advanced.", "Joseph Kosinski", 2010, 7.8, "Science Fiction" ),
         ("The Fighter", "5.jpg", "Everyone deserves a fighting chance.", "The Fighter, is a drama about boxer 'Irish' Micky Ward's unlikely road to the world light welterweight title. His Rocky-like rise was shepherded by half-brother Dicky, a boxer-turned-trainer who rebounded in life after nearly being KO'd by drugs and crime.", "David O. Russell", 2010, 8.0, "Drama / Sports Film"),
         ("Black Swan", "1.jpg", "Natalie Portman, need we say more?", "Nina is a ballerina in a New York City ballet company whose life, like all those in her profession, is completely consumed with dance. She lives with her obsessive former ballerina mother Erica who exerts a suffocating control over her. When artistic director Thomas Leroy decides to replace prima ballerina Beth MacIntyre for the opening production of their new season, Swan Lake, Nina is his first choice. But Nina has competition: a new dancer, Lily, who impresses Leroy as well. Swan Lake requires a dancer who can play both the White Swan with innocence and grace, and the Black Swan, who represents guile and sensuality. Nina fits the White Swan role perfectly but Lily is the personification of the Black Swan. As the two young dancers expand their rivalry into a twisted friendship, Nina begins to get more in touch with her dark side - a recklessness that threatens to destroy her.", "Darren Aronofsky", 2010, 8.0, "Drama / Suspense / Thriller / Mystery"), 
         ("Yogi Bear","6.jpg", "Life's a Pic-A-Nic", "Jellystone Park has been losing business, so greedy Mayor Brown decides to shut it down and sell the land. That means families will no longer be able to experience the natural beauty of the outdoors -- and, even worse, Yogi and Boo Boo will be tossed out of the only home they've ever known. Faced with his biggest challenge ever, Yogi must prove that he really is 'smarter than the average bear' as he and Boo Boo join forces with their old nemesis Ranger Smith to find a way to save Jellystone Park from closing forever.", "Eric Brevig", 2010, 6.8, "Animation / Comedy / Family / Adventure"),
         ("Season of the Witch", "3.jpg", "", "Nicolas Cage stars as a 14th century Crusader who returns with his comrade (Ron Perlman) to a homeland devastated by the Black Plague. A beleaguered church, deeming sorcery the culprit of the plague, commands the two knights to transport an accused witch (Claire Foy) to a remote abbey, where monks will perform a ritual in hopes of ending the pestilence.", "Dominic Sena", 2011, 6.4, "Adventure / Drama / Fantasy / Horror / Science Fiction")
         ) 
  INDEX(items)
  xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
  xbmcplugin.endOfDirectory(int(sys.argv[1]))



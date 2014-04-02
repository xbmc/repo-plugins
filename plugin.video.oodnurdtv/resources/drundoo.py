#drundoo class for handling web site

from requests import session
import bs4, requests

URL = 'http://www.drundoo.com/users/login/'

#username=''

class drundoo:
	
	def __init__(self,username,password):
		self.c = session()
		self.payload = [('email',username),('password',password),('submit','\xd0\x98\xd0\xb7\xd0\xbf\xd1\x80\xd0\xb0\xd1\x82\xd0\xb8')]
		self.c.post(URL,data=self.payload)
		self.username = username
		if not self.check_login():
			plugin.log.error('Wrong Username and/or Password!')

	def check_login(self):
		if self.c.get('http://www.drundoo.com/profile').text.find(self.username) != -1:
			return True
		else:
			return False
	def logIn(self):
		self.c.post(URL,data=self.payload)

	def open_site(self,url):
		if not self.check_login():
			self.logIn()
		temp = self.c.get(url)
		temp.encoding = 'utf-8'
		return temp.text
		#return self.c.get(url).text
	
	def play_url(self,url):
		
		link = url
		play_list = []
                play_title = []
               	
		startposition = self.open_site(link).find('playlistUrl') + 15
                endposition = self.open_site(link).find('",\n')
                temp_link = 'http://www.drundoo.com'+ self.open_site(link)[startposition:endposition]

                temp2 = self.open_site(temp_link)
                startposition = temp2.find('http')
                endposition = temp2.find('","title')
                play_link = temp2[startposition:endposition]
                play_link = play_link.replace('\\','').replace('manifest.f4m','master.m3u8')
                play_list.append(play_link)

                return play_list[0]    
			
	def make_shows(self,url,my_mode):

		#timeshift_url = 'http://www.drundoo.com/channels/97/btv_hd/'
		
		timeshift_url = url
		
		if my_mode == 'list':
			temp = self.open_site(timeshift_url)
			links = bs4.BeautifulSoup(temp).findAll(class_='player_start')
		elif my_mode == 'timeshift':
			temp = self.open_site(timeshift_url)
			links = bs4.BeautifulSoup(temp).findAll(class_='action vod player_start')
		elif my_mode == 'live':
			temp = self.open_site(timeshift_url)
			links = bs4.BeautifulSoup(temp).findAll(class_='button watch-now player_start cf')
		
	
		time_list = []
		
		for link in links:
			time_list.append((link.get('data-ga-label'),'http://www.drundoo.com' + link.get('href')))

		play_list = []
                play_title = []
                for title,link in time_list:
                        #build the .m3u8 link for the live content
                        startposition = self.open_site(link).find('playlistUrl') + 15
                        endposition = self.open_site(link).find('",\n')
                        temp_link = 'http://www.drundoo.com'+ self.open_site(link)[startposition:endposition]

                        temp2 = self.open_site(temp_link)
                        startposition = temp2.find('http')
                        endposition = temp2.find('","title')
                        play_link = temp2[startposition:endposition]
                        play_link = play_link.replace('\\','').replace('manifest.f4m','master.m3u8')
                        play_list.append(play_link)

                        #get the title of the live station associated with the play link above
			play_title.append(title)

                return play_list,play_title    


	def get_list(self,url,my_op=1):
		
		my_title = []
		my_link = []
		
		#use this option to get a list of channels
		if my_op == 1:
			temp = self.open_site(url)
                	links = bs4.BeautifulSoup(temp).findAll(class_='item')
			for link in links:
				my_link.append('http://www.drundoo.com' + link.find('a').get('href'))
				#my_title.append(link.find('span',{'class':'title'}).renderContents().decode('unicode_escape').encode('utf-8'))	
				my_title.append(link.find('span',{'class':'title'}).renderContents())
		
		#use this option to get recorded shows list
		elif my_op == 2:
			temp = self.open_site(url)
                	links = bs4.BeautifulSoup(temp).findAll(class_='inner right')
			
			for link in links:
				if link.findAll(class_='button vod-ico cf'):
					my_link.append('http://www.drundoo.com' + link.findAll(class_='button vod-ico cf')[0].get('href'))
					#my_title.append(link.find('span',{'class':'title'}).renderContents().decode('unicode_escape').encode('utf-8'))	
					my_title.append(link.findAll(class_='button watch-now player_start cf')[0].get('data-ga-label'))
		
		#use this option for timeshift list. Needed a channel web site
		elif my_op == 3:
			temp = self.open_site(url)
			links = bs4.BeautifulSoup(temp).findAll(class_='action vod player_start')
		
			for link in links:
				my_title.append(link.get('data-ga-label'))
				my_link.append('http://www.drundoo.com' + link.get('href'))
		
		#use this option for live list
		else:	
			temp = self.open_site(url)
                	links = bs4.BeautifulSoup(temp).findAll(class_='inner right')
			
			for link in links:
				if link.findAll(class_='button watch-now player_start cf'):
					my_link.append('http://www.drundoo.com' + link.findAll(class_='button watch-now player_start cf')[0].get('href'))
					#my_title.append(link.find('span',{'class':'title'}).renderContents().decode('unicode_escape').encode('utf-8'))	
					my_title.append(link.findAll(class_='button watch-now player_start cf')[0].get('data-ga-label'))
				else:
					my_link.append('http://www.drundoo.com' + link.findAll(class_='button watch-now cf')[0].get('href'))
					my_title.append('BG International')

		return dict(zip(my_title,my_link))
			

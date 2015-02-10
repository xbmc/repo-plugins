import urllib2,os,sys

def SaveFile(filename, data, dir):
    path = os.path.join(dir, filename)
    try:
        file = open(path,'w')
    except:
	file = open(path,'w+')
    file.write(data)
    file.close()
def main(ADDONDATA):
	try:
		req = urllib2.Request('http://www.godtube.com/artists-directory/')
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		link=response.read()
		SaveFile('Artist_Directory.html',link,ADDONDATA)
		response.close()
	except:
		pass

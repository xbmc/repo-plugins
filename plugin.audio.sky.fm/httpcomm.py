import zlib
import httplib
import urllib
import urllib2
import gzip
import StringIO
import cookielib
import socket
import urllib2

class HTTPComm :
	def testStream( self, url ) :
		timeout = 10
		socket.setdefaulttimeout(timeout)
		try :
			# Set useragent, sites don't like to interact with scripts
			headers = { 'User-Agent':'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'en-us,en;q=0.5','Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7'}
			req = urllib2.Request(url=url, headers=headers)
			f = urllib2.urlopen(req)
			CHUNK = 16 * 1024
			#CHUNK = 8 * 1024
			chunk = f.read(CHUNK)
			# if we actually got some data = we got a stream
			if len(chunk) == CHUNK :
				return True
			else :
				return False
		except Exception:
			print "Something went horribly wrong in testStream in HTTPComm"
			return False

	# Login
	def post( self, url, postdata, cookiefile=None ) :
		
		timeout = 10
		socket.setdefaulttimeout(timeout)

		cj = cookielib.LWPCookieJar()
		# create an opener
		opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

		# Add useragent, sites don't like to interact with scripts
		opener.addheaders = [
			('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
			('Accept-Language', 'en-gb,en;q=0.5'),
			('Accept-Encoding', 'gzip,deflate'),
			('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
			('Keep-Alive', '115'),
			('Connection', 'keep-alive'),
			('Cache-Control', 'max-age=0'),
			]
		
		resp = opener.open(url, postdata)
		# Compressed (gzip) response...
		if resp.headers.get( "content-encoding" ) == "gzip":
			htmlGzippedData = resp.read()
			stringIO        = StringIO.StringIO( htmlGzippedData )
			gzipper         = gzip.GzipFile( fileobj = stringIO )
			htmlData        = gzipper.read()
		else :
			htmlData = resp.read()
		
		if cookiefile != None :
			cj.save(cookiefile, True)
		resp.close()

		# Return html
		return htmlData
		
	# GET
	def get( self, url, cookiefile=None ):
		timeout = 10
		socket.setdefaulttimeout(timeout)
		print "cookie" + str(cookiefile)
		opener = urllib2.build_opener()
		cj = cookielib.LWPCookieJar()
		#create an opener
		if cookiefile!=None :
			print "using cookie"
			cj = cookielib.LWPCookieJar(cookiefile)
			cj.load(ignore_discard=True)
			opener = urllib2.build_opener( urllib2.HTTPCookieProcessor(cj) )
			urllib2.install_opener(opener)
	
		#Add useragent, sites don't like to interact with scripts
		opener.addheaders = [
			('User-Agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8'),
			('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
			('Accept-Language', 'en-gb,en;q=0.5'),
			('Accept-Encoding', 'gzip,deflate'),
			('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
			('Keep-Alive', '115'),
			('Connection', 'keep-alive'),
			('Cache-Control', 'max-age=0'),
			]
		try :
			resp = opener.open(url)

			# Compressed (gzip) response...
			if resp.headers.get( "content-encoding" ) == "gzip":
				htmlGzippedData = resp.read()
				stringIO        = StringIO.StringIO( htmlGzippedData )
				gzipper         = gzip.GzipFile( fileobj = stringIO )
				htmlData        = gzipper.read()
			else :
				htmlData = resp.read()
		
			resp.close()
		
			# Return html
			return htmlData
		except Exception:
			return False

	def getImage( self, url, path ) :
		timeout = 10
		socket.setdefaulttimeout(timeout)

		try :
			# Set useragent, sites don't like to interact with scripts
			headers = { 'User-Agent':'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8','Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8','Accept-Language':'en-us,en;q=0.5','Accept-Charset':'ISO-8859-1,utf-8;q=0.7,*;q=0.7'}
			req = urllib2.Request(url=url, headers=headers)
			f = urllib2.urlopen(req)
			imagedata = f.read()		# Downloads imagedata

			open(path, 'wb').write(imagedata)

			# Return true
			return True
		except Exception:
			return False

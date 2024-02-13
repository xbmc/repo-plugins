# -*- coding: utf-8 -*-
import sys
import xbmc
import urllib
import resources.lib.utils as utils
import re
import json

PY3 = sys.version_info.major >= 3

if PY3:
    import urllib.request as urllib2
    import urllib.parse as urlparse
    from urllib.parse import urlencode

else:
    import urllib2
    import urlparse
    from urllib import urlencode

    
class Relinker:
    # Firefox 52 on Android
    # UserAgent = "Mozilla/5.0 (Android; Mobile; rv:52.0) Gecko/52.0 Firefox/52.0"
    # Firefox 52 ESR on Windows 7
    # UserAgent = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:52.0) Gecko/20100101 Firefox/52.0"
    # Firefox 52 ESR on Linux
    # UserAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0"
    # Chrome 64 on Windows 10
    #UserAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"
    UserAgent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36&Accept=*/*&Accept-Encoding=gzip,deflate,br&Accept-Language=it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7&Connection=keep-alive&Origin=https://www.raiplay.it&Referer=https://www.raiplay.it/&sec-ch-ua="Not A(Brand";v="99","Google Chrome";v="121","Chromium";v="121"&sec-ch-ua-mobile=?0&sec-ch-ua-platform="Linux"'
    # Raiplay android app
    #UserAgent = "Android 4.2.2 (smart) / RaiPlay 2.1.3 / WiFi"
    
    def __init__(self):
        opener = urllib2.build_opener()
        # Set User-Agent
        opener.addheaders = [('User-Agent', self.UserAgent)]
        urllib2.install_opener(opener)

    def getURL(self, url):
        scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
        qs = urlparse.parse_qs(query)
    
        # output=20 url in body
        # output=23 HTTP 302 redirect
        # output=25 url and other parameters in body, space separated
        # output=44 XML (not well formatted) in body
        # output=47 json in body
        # pl=native,flash,silverlight
        # A stream will be returned depending on the UA (and pl parameter?)
        
        if "output" in qs:
            del(qs['output'])
        
        qs['output'] = "56" # xml stream data  
        
        query = urlencode(qs, True)
        url = urlparse.urlunparse((scheme, netloc, path, params, query, fragment))
                
        try:
            response = utils.checkStr(urllib2.urlopen(url).read())
            #mediaUrl = response.strip()
            #xbmc.log(response)
            
            #find real url
            content = re.findall("<url type=\"content\">(.*?)</url>", response)
            if content:
                #<![CDATA[https://dashaz-dc-euwe.akamaized.net/subtl_proxy/6ed6fac0-ae71-4dd7-b4be-d8921d4948b9/20200713102433_12778339.ism/manifest(format=mpd-time-csf,filter=medium_1200-2400).mpd?hdnea=st=1599391792~exp=1599391942~acl=/*~hmac=27e952b0f784662684fe65fb4717152d8644e2a9f3ad575ece21738dfbe88263]]>
                url = re.findall("<!\[CDATA\[(.*?)\]\]>",content[0]) 
                if url:
                    #find type of stream
                    ct = re.findall("<ct>(.*?)</ct>", response)
                    if ct:
                        #find license key
                        #<license_url><![CDATA[{"drmLicenseUrlValues":[{"drm":"WIDEVINE","licenceUrl":"https://mediaservicerainet02.keydelivery.northeurope.media.azure.net/Widevine/?kid=5ca7736f-7e27-49fc-80b2-bde49c8c0259&token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cm46bWljcm9zb2Z0OmF6dXJlOm1lZGlhc2VydmljZXM6Y29udGVudGtleWlkZW50aWZpZXIiOiI1Y2E3NzM2Zi03ZTI3LTQ5ZmMtODBiMi1iZGU0OWM4YzAyNTkiLCJpc3MiOiJodHRwOi8vcmFpcGxheSIsImF1ZCI6InVybjpyYWlwbGF5X2hkY3BfdjFfc2wxX3NkIiwiZXhwIjoxNTk5MzkyOTc0fQ.ZwmxivCnx8Gz-GRVu5twKIrjsAdK6jczAT2JZLnO9mw","name":"Widevine Token Restricted JWT HDCP_V1_SL1_SD","audience":"urn:raiplay_hdcp_v1_sl1_sd"},{"drm":"PLAYREADY","licenceUrl":"https://mediaservicerainet02.keydelivery.northeurope.media.azure.net/PlayReady/?kid=5ca7736f-7e27-49fc-80b2-bde49c8c0259&token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1cm46bWljcm9zb2Z0OmF6dXJlOm1lZGlhc2VydmljZXM6Y29udGVudGtleWlkZW50aWZpZXIiOiI1Y2E3NzM2Zi03ZTI3LTQ5ZmMtODBiMi1iZGU0OWM4YzAyNTkiLCJpc3MiOiJodHRwOi8vcmFpcGxheSIsImF1ZCI6InVybjpyYWlwbGF5IiwiZXhwIjoxNTk5MzkyOTc0fQ.pih3hCVRTJyNkgYGj42oCb8-Tya-4-PPC-PlZn38n2M","name":"Playready Token Restricted JWT","audience":"urn:raiplay"}]}]]></license_url>
                        licenseUrl = re.findall("<license_url>(.*?)</license_url>", response) 
                        if licenseUrl:
                            #xbmc.log(licenseUrl[0])
                            licenseJson = re.findall("<!\[CDATA\[(.*?)\]\]>",licenseUrl[0])
                            if licenseJson:
                                #xbmc.log(licenseJson[0])
                                try:
                                    licenseJson = json.loads(licenseJson[0])
                                
                                    xbmc.log(str(licenseJson))
                                    licenseData = licenseJson.get('drmLicenseUrlValues',[])
                                    key = ''  
                                    for l in licenseData:
                                        if "WIDEVINE" in l.get("drm",""):
                                            key = l.get("licenceUrl",'')
                                            
                                    return {'url': url[0],'ct': ct[0],'key': key}
                                    
                                except:
                                    return {'url': url[0],'ct': ct[0],'key':''}
                        else:
                            return {'url': url[0],'ct': ct[0],'key':''}
                    
                    else:
                        return {'url': url[0],'ct':'','key':''}
                    
                else:
                    return {'url':'','ct':'','key':''}
            else:    
                return {'url':'','ct':'','key':''}
                
            # Workaround to normalize URL if the relinker doesn't
            try: 
                mediaUrl = urllib.quote(mediaUrl, safe="%/:=&?~#+!$,;'@()*[]")
            except: 
                mediaUrl = urllib.parse.quote(mediaUrl, safe="%/:=&?~#+!$,;'@()*[]")
            return mediaUrl

        except:
            return {'url':'','type':'','key':''}

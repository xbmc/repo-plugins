import struct
import urllib2,urllib
import re
import json
import math
CRYPT_XXTEA_DELTA= 0x9E3779B9
headers = [('Accept','text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),( 'Connection','Keep-Alive')]
 
class Crypt_XXTEA:
    _key=None

    def setKey(self,key):
        if isinstance(key, basestring):
            k = self._str2long(key, False);
        elif isinstance(key, list):
            k = key;
        else:
            print "The secret key must be a string or long integer array"

        if (len(k) > 4):
            print "The secret key cannot be more than 16 characters or 4 long values"
        elif (len(k) == 0):
            print "The secret key cannot be empty"
        elif (len(k) < 4):
            for i in range(len(k),4):
                k.append(0)
                #k[i] = 0;
        #print k
        self._key = k;

    def encrypt(self,plaintext):

        if (self._key == None):
            print "Secret key is undefined"

        if isinstance(plaintext, basestring):
            return self._encryptString(plaintext)
        elif isinstance(plaintext, list):
            return self._encryptArray(plaintext)
        else:
            print "The plain text must be a string or long integer array"
        

    def decrypt(self,ciphertext):
        if (self._key == None):
            print "Secret key is undefined"
        #print 'dec',isinstance(ciphertext, basestring)
        if isinstance(ciphertext, basestring):
            return self._decryptString(ciphertext)
        elif isinstance(ciphertext, list):
            return self._decryptArray(ciphertext)
        else:
            print "The plain text must be a string or long integer array"

    def _encryptString(self,str):
        if (str == ''):
            return ''
        v = self._str2long(str, False);
        v = self._encryptArray(v);
        return self._long2str(v, False);

    def _encryptArray(self,v):

        n   = len(v) - 1;
        z   = v[n];
        y   = v[0];
        q   = math.floor(6 + 52 / (n + 1));
        sum = 0;
        while (0 < q):
            q-=1
    
            sum = self._int32(sum + CRYPT_XXTEA_DELTA);
            e   = sum >> 2 & 3;
            
            for p in range(0,n):
                
                y  = v[p + 1];
                mx = self._int32(((z >> 5 & 0x07FFFFFF) ^ y << 2) + ((y >> 3 & 0x1FFFFFFF) ^ z << 4)) ^ self._int32((sum ^ y) + (self._key[p & 3 ^ e] ^ z));
                z  = v[p] = self._int32(v[p] + mx);
            p+=1#due to range
            y  = v[0];
            mx = self._int32(((z >> 5 & 0x07FFFFFF) ^ y << 2) + ((y >> 3 & 0x1FFFFFFF) ^ z << 4)) ^ self._int32((sum ^ y) + (self._key[p & 3 ^ e] ^ z));
            z  = v[n] = self._int32(v[n] + mx);
            
        return v;


    def _decryptString(self,str):
        if (str == ''):
            return '';

        v = self._str2long(str, False);
        
        v = self._decryptArray(v);
        
        return self._long2str(v, False);
        

    def _decryptArray(self,v):

        n   = len(v) - 1;
        z   = v[n];
        y   = v[0];
        q   = math.floor(6 + 52 / (n + 1));
        sum = self._int32(q * CRYPT_XXTEA_DELTA);

        
        while (sum != 0):
            e = sum >> 2 & 3;
            for p in range( n, 0, -1):
                
                z  = v[p - 1];
                mx = self._int32(((z >> 5 & 0x07FFFFFF) ^ y << 2) + ((y >> 3 & 0x1FFFFFFF) ^ z << 4)) ^ self._int32((sum ^ y) + (self._key[p & 3 ^ e] ^ z));
                y  = v[p] = self._int32(v[p] - mx);

            p=p-1 #due to range    
            z   = v[n];
            mx  =    self._int32(((z >> 5 & 0x07FFFFFF) ^ y << 2) + ((y >> 3 & 0x1FFFFFFF) ^ z << 4)) ^ self._int32((sum ^ y) + (self._key[p & 3 ^ e] ^ z));
            y   = v[0] = self._int32(v[0] - mx);
            sum = self._int32(sum - CRYPT_XXTEA_DELTA);

        return v;
        

    def _long2str(self,v, w):
     
        ln = len(v);
        s   = '';
        for i in range(0,ln):
            s += struct.pack('<I', v[i]&0xFFFFFFFF);
        if (w):
            return substr(s, 0, v[ln - 1]);
        else:
            return s;
        

    def _str2long(self,s, w):
        #return (s + ("\0" *( (4 - len(s) % 4) & 3))).encode("hex")
    

        i=int(math.ceil((len(s)/4)))
        if (len(s)%4)>0 :
            i+=1
        
        #print  struct.unpack('<I',(s + ("\0" *( (4 - len(s) % 4) & 3))))
        v = list(struct.unpack(('I'*i),(s + ("\0" *( (4 - len(s) % 4) & 3)))))
        
        if (w):
            v[0] = len(s); #prb
        
        return v;
        

    def _int32(self,n):
        while (n >= 2147483648):
            n -= 4294967296;
        while (n <= -2147483649):
            n += 4294967296;
        return int(n);
 

def getUrl(url, cookieJar=None,post=None, timeout=20, headers=None):

    cookie_handler = urllib2.HTTPCookieProcessor(cookieJar)
    opener = urllib2.build_opener(cookie_handler, urllib2.HTTPBasicAuthHandler(), urllib2.HTTPHandler())
    #opener = urllib2.install_opener(opener)
    req = urllib2.Request(url)
    req.add_header('User-Agent','Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36')
    if headers:
        for h,hv in headers:
            req.add_header(h,hv)

    response = opener.open(req,post,timeout=timeout)
    link=response.read()
    response.close()
    return link;
def HexToByte( hexStr ):
    """
    Convert a string hex byte values into a byte string. The Hex Byte values may
    or may not be space separated.
    """
    # The list comprehension implementation is fractionally slower in this case    
    #
    #    hexStr = ''.join( hexStr.split(" ") )
    #    return ''.join( ["%c" % chr( int ( hexStr[i:i+2],16 ) ) \
    #                                   for i in range(0, len( hexStr ), 2) ] )
 
    bytes = []

    hexStr = ''.join( hexStr.split(" ") )

    for i in range(0, len(hexStr), 2):
        bytes.append( chr( int (hexStr[i:i+2], 16 ) ) )

    return ''.join( bytes )
 

def get_url(player_id):
    v=Crypt_XXTEA()
    import time
    # Retrieve channel id and primary key
    timestamp = time.time();
    #player_id = '69T7MabZ47';
    init = getUrl("http://tvplayer.playtv.fr/js/"+player_id+".js?_="+str(timestamp),headers=headers);
    #print init
    pat="b:(\{\"a.*\"})}"
    init =re.compile(pat).findall(init)[0]
    init = json.loads(init);   
        
    from binascii import unhexlify
    from binascii import hexlify
    a =  init['a'];
    b =   init['b'];

    b=b.decode("hex")

    a=a.decode("hex")
    bb=""

    v.setKey("object");

    #b=v._long2str(b,False)

    b_s=v.decrypt(b).rstrip('\0')

    params = json.loads(b_s)
    pack_k=params['k'].decode("hex")#  pack("H*", params['k'])#init['a']
    key = v.decrypt(pack_k).rstrip('\0');
    v.setKey(key);
    a_d=v.decrypt(a).rstrip('\0')
    params     = json.loads(a_d);

    channel_id = params['i'];
    api_url    = params['u'];
    req={"i": channel_id, "t": timestamp,"h":"playtv.fr","a":5}

    req = json.dumps(req)

    req_en=v.encrypt(req)

    req_en=req_en.encode("hex");#  struct.unpack("H"*(len(req_en)/4),req_en);
    if not req_en.endswith( '/'):
        req_en += '/';
    headers2 =headers.append( [('Referer','http://static.playtv.fr/swf/tvplayer.swf?r=22'),( 'x-flash-version','11,6,602,180')])
    init = getUrl(api_url+req_en,headers=headers2);
    init=init.decode("hex")
    params   = json.loads(v.decrypt(init).rstrip('\0'));

    if params['s'][1] and params['s'][1] <>'' :
        streams =params['s'][0] if params['s'][0]['bitrate'] > params['s'][1]['bitrate'] else params['s'][1];
    else:
        streams = params['s'][0];
      
    scheme   = streams['scheme'];
    host     = streams['host'];
    port     = streams['port'];
    app      = streams['application'];
    playpath = streams['stream'];
    token    = streams['token'];
    title    = streams['title'];

    t = params['j']['t'];
    k = params['j']['k'];
    v.setKey("object");
    key=v.decrypt(k.decode("hex"))# pack("H*", k));
    v.setKey(key);
    auth = v.encrypt(t).encode("hex") #unpack("H*", $xxtea->encrypt($t));

          
    if (scheme == "http"):
        final_url = scheme+"://"+host + ( ":" +port if port and len(port)>0 else  "") +  "/" + playpath
    else:
        final_url = scheme + "://" + host +( ":" +port if port and len(port)>0 else  "") +  "/" + app +" app=" + app +" swfUrl=http://static.playtv.fr/swf/tvplayer.swf pageUrl=http://playtv.fr/television Conn=S:" + auth +  (" token=" + token  if token and len(token)>0 else  "") + " playpath=" + playpath +' live=1 timeout=20'
    print final_url
    return final_url

#print get_url('69T7MabZ47')

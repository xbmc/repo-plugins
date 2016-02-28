from fivehundredpx.utils   import Util
from fivehundredpx.errors  import *
import urllib, re, httplib, time, simplejson

re_path_template = re.compile('{\w+}')

def bind_api(**config):
    
    class APIMethod(object):
        '''common parameters for a api action'''
        path   		   = config['path']
        method 		   = config.get('method','GET')
        allowed_params = config.get('allowed_params',[])
        model_class    = config.get('model_class',None)
        response_type  = config.get('response_type','list')
        require_auth   = config.get('require_auth',False)
        as_query       = config.get('as_query',False)

        def __init__(self, api, *args, **kwargs):
            '''parameters for every request'''
            if self.require_auth and not api.auth_handler: raise FiveHundredClientError('auth handler is required')

            self.api 		  = api
            self.parameters   = {}
            self.as_generator = kwargs.pop("as_generator", False)
            self.max_pages 	  = kwargs.pop("max_pages", 3)
            self.headers      = kwargs.pop('headers', {})
            self.body         = kwargs.pop('http_body', {})
            self.protocol     = 'https://' if self.api.secure else 'http://'
            if 'method'       in kwargs: self.method = kwargs.pop('method')
            if 'require_auth' in kwargs: self.require_auth = kwargs.pop('require_auth')
            self._build_parameters(args, kwargs)
            self._build_path()
	
        def _build_parameters(self, args, kwargs):
            for index,value in enumerate(args):
                if value is None: continue
                try:
                    self.parameters[self.allowed_params[index]] = value
                except IndexError:
                    raise FiveHundredsClientError("Too many arguments supplied")

            for key,value in kwargs.iteritems():
                if value is None: continue
                if type(value) in (list, tuple):
                    self.parameters[key + "[]"] = value
                else:
                    self.parameters[key] = value

        def _build_path(self):
            for variable in re_path_template.findall(self.path):
                name = variable.strip('{}')			
                try:
                    value = urllib.quote(str(self.parameters[name]))
                    del self.parameters[name]
                    self.path = self.path.replace(variable,value)
                except KeyError:
                    raise FiveHundredsClientError('No parameter value found for path variable: %s' % name)

        def _execute(self):
            url = "%s%s%s%s" % (self.protocol,self.api.host,self.api.version,self.path)

            if self.method == "GET" or self.as_query == True:
                param_list = []
                for key, value in self.parameters.iteritems():
                    if type(value) in (list, tuple):
                        for v in value:
                            param_list.append("%s=%s" % (key, v))                   
                    else:
                        param_list.append("%s=%s" % (key, Util.replace_space(value)))

                if len(param_list) != 0 : url = "%s?%s" % (url, "&".join(param_list))

            elif self.method == "POST" or self.method == "PUT":
                if self.headers.has_key('Content-Type') == False:
                    self.headers['Content-Type'] = "application/x-www-form-urlencoded; charset=UTF-8"

            postdata = None
            if self.require_auth and self.api.auth_handler:
                request = self.api.auth_handler.apply_auth(url, self.method, self.headers, self.parameters)
                if not self.method == "GET": postdata = request.to_postdata()

            if self.path == "/upload": postdata = self.body

            for count in xrange(self.api.retry_count):
                conn = httplib.HTTPSConnection(self.api.host) if self.api.secure else httplib.HTTPConnection(self.api.host)
                try:
                    conn.request(self.method, url, body=postdata, headers=self.headers)
                    response = conn.getresponse()
                except Exception, e:
                    conn.close()
                    raise FiveHundredClientError('Failed to send request: %s' % e)

                if self.api.retry_errors:
                    if response.status not in self.api.retry_errors: break
                else:
                    if response.status == 200: break
                conn.close()
                time.sleep(self.api.retry_delay)

            if response.status > 199 and response.status < 300:
                result = response.read()
                conn.close()
                return simplejson.loads(result)
            else:
                try:
                    error_msg = self.api.parser.parse_error(response.read())
                except Exception:
                    error_msg = "500PX error response: status code = %s" % response.status
                finally:
                    conn.close()
                raise FiveHundredClientError(error_msg,status=response.status)

        def _generator(self):
            base = self.parameters['page'] if 'page' in self.parameters else 1    
            for count in xrange(self.max_pages):
                self.parameters['page'] = base + count
                yield self._execute()
            return

        def execute(self):
            return self._generator() if self.as_generator else self._execute()

    def _call(api, *args, **kwargs):
        method = APIMethod(api, *args, **kwargs)
        return method.execute()

    return _call

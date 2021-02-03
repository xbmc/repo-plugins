import httplib2
import json

def request(url):
    h = httplib2.Http(".cache")
    (resp_headers, body) = h.request(url, "GET")
    return body.decode('utf-8')

CONFIG_URL="https://weareone.fm/js/config_stream.js"
CONFIG_CODE = request(CONFIG_URL)

def parse(code):
    return json.loads(code
        .replace("/** stream configuration **/", "", 1)
        .replace("/** list of possible streams**/", "", 1)
        .replace("/** configuration of AmplitudeJS **/", "", 1)
        .replace("/** stream qualities **/", "", 1)
        .replace("/** API url **/", "", 1)

        .replace("streams", "\"streams\"", 1)
        .replace("parameters", "\"parameters\"", 1)
        .replace("qualities", "\"qualities\"", 1)
        .replace("api_url", "\"api_url\"", 1)
        
        .replace("var Config = ", "", 1)
        .replace(";", "", 1)
        .replace("'", "\"")
        .replace(",\n}", "}")
    )

def get_all():
    return parse(CONFIG_CODE)["streams"]

print(get_all())
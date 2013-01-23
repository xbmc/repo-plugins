import re
from ClientForm import ParseResponse
from BeautifulSoup import SoupStrainer, MinimalSoup as BeautifulSoup
import urllib2

URLPROFILE = 'http://www.ted.com/profiles/'
URLLOGIN = 'http://www.ted.com/session/new'

class User:
    """
    For user interactions.
    """

    def __init__(self, get_HTML):
        """
        get_HTML Takes a URL and optionally HTTP headers, also handles cookies.
        """
        self.get_HTML = get_HTML
    
    def login(self, username, password):
        """
        return (userID, realName) or None if unsuccessful.  
        """
        if username and password:
            return self.__getUserDetails(username, password)
        else:
            return None, None

    def __getUserDetails(self, username, password):
        html = self.__getLoginResponse(username, password)
        userContainer = SoupStrainer(attrs = {'class':re.compile('notices')})
        for aTag in BeautifulSoup(html, parseOnlyThese = userContainer).findAll('a'):
            if aTag['href'].startswith(URLPROFILE):
                userID = aTag['href'].split('/')[-1]
                realName = aTag.string.strip()
                return userID, realName
        return None, None

    def __getLoginResponse(self, username, password):
        # (???) clientform doesn't like HTML, and I don't want to monkey patch it
        try:
            response = urllib2.urlopen(URLLOGIN)
            forms = ParseResponse(response, backwards_compat=False)
        finally:
            response.close()
        #set username & password in the sign in form
        form = forms[0]
        form["user[email]"] = username
        form["user[password]"] = password
        form.find_control(name="user[remember_me]", type="checkbox", id="user_remember_me").selected = True
        #click submit
        return self.get_HTML(form.click())

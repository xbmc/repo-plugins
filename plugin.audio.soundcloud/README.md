XBMC SoundCloud Plugin
======================

About
-----
The XBMC SoundCloud Plugin integrates music from [SoundCloud] [2] right into your XBMC media center. 

In the current version (0.1.0) it supports browsing and searching individual tracks, users and groups, 
and provides access to publicly available resources only. User authentication and access to private 
resources like favorites and private tracks are planned for future releases.

Since XBMC only supports Python 2.4, I couldn't use the existing [Python API Wrapper] [3] 
and had to roll my own in terms of the RESTful communication interface and will have to do the same 
for the OAuth-based authentication.

Third-party Libraries
---------------------
The XBMC SoundCloud plugin makes use of the following third-party Python libraries:
	* httplib2
	* oauth2
	* simplejson
	
License
-------
This software is released under the [GPL 3.0 license] [1].
	
[1]: http://www.gnu.org/licenses/gpl-3.0.html
[2]: http://soundcloud.com
[3]: http://wiki.github.com/soundcloud/python-api-wrapper/
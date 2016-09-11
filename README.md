<<<<<<< HEAD
![Kodi logo](https://raw.githubusercontent.com/xbmc/xbmc-forum/master/xbmc/images/logo-sbs-black.png)
# Kodi Home Theater Software


## Contents

This branch contains a certain category of add-ons from which our back-end script creates .zip files which are made available to each Kodi client.
* Plugins

## How to submit your add-on and subsequent updates ##

Your add-on must follow our strict repository rules to be considered for inclusion. Please consult the [Add-on rules] (http://kodi.wiki/view/Add-on_Rules) wiki page for further details. Please review these rules carefull before submitting your add-on. Should you have any questions regarding them please start a forum thread in one of the following locations
* [Python add-ons] (http://forum.kodi.tv/forumdisplay.php?fid=26)
* [Skins] (http://forum.kodi.tv/forumdisplay.php?fid=12)

After you have read the repository guidelines and made sure your addon is compliant with them, you may begin the submission process. By forking this repository and creating a pull-request to the correct repository branch you ask permissing to included you add-on to the official Kodi repository. Subsequent updates can be done in a similar way by updating the code and creating a new pull-request again. Make sure that your local git clone is always rebased before send a pull-request.

* Fork this repository
* Create a branch
* Commit your new add-on or any subsequent update in a single commit
* Push the branch to your own forked repository
* Create pull request
* Await commments if any changes are deemed necessary

A short guide on forking and creating a pull request can be found here: [contributing] (https://github.com/xbmc/repo-plugins/blob/master/CONTRIBUTING.md).

Keep in mind that add-ons in the official repository should be considered stable. This means that they should be well-tested before you submit them for inclusion. Because they are for stable users, they should avoid being updated too often. Too often is of course subjective. If your add-on is in rapid development, and features are constantly being added, hold off until you have hit a good stopping point and tested the current version.
This means that you should not submit a request every time you change your code. If you are submitting updates more than once per week something is wrong. Once or twice per month is probably a better goal, barring unforeseen conditions (like a content source changing its paths). With good reasons provided we will of course make exceptions as we strive to prove the best user experience.

## Compatibility

This branch is used for add-ons that are coded for Kodi v16 Jarvis builds and higher only. From these code repositories and branches our back-end uploades .zip files of the compatible add-ons to our main mirror server.
* [Mirror of Kodi v16 Jarvis compatible add-ons] (http://mirrors.kodi.tv/addons/jarvis/)

## Status

* New add-on additions: **Accepted**
* Updating already present add-ons: **Accepted**

## Disclaimer ##

The contents of this repository mainly consist of add-on created by third party developers. Team Kodi holds no responsibility for it's contents.
Team Kodi reserves the right to update or remove add-ons at any time as we deem necessary.

## Quick Kodi development links

* [Add-on rules] (https://github.com/xbmc/xbmc/blob/master/CONTRIBUTING.md)
* [Submitting an add-on details] (http://kodi.wiki/view/Submitting_Add-ons)
* [Code guidelines] (http://kodi.wiki/view/Official:Code_guidelines_and_formatting_conventions)
* [Kodi development] (http://kodi.wiki/view/Development)

## Other useful links

* [Kodi wiki] (http://kodi.wiki/)
* [Kodi bug tracker] (http://trac.kodi.tv)
* [Kodi community forums] (http://forum.kodi.tv/)
* [Kodi website] (http://kodi.tv)

**Enjoy Kodi and help us improve it today. :)**
=======
plugin.video.last_played
------------------------
Lists what was played most recently, allowing to resume watching directly from the addon.

Before if you wanted to finish viewing something you stopped, you had to remember it and then search, or go through a number of menus to get back to where you were.
Now just open this addon and it will display a list with the last things you watched. Click and it will resume playing directly from the addon.

Usage
-----
When you start playing anything in KODI it will be added to the list of last played.

To remove from the played list something you watched:
Open the list of last played, select the line to remove, and choose "Remove from list" form the context menu. 

Settings:
---------
Number of lines: How many lines to display on screen<br />
Single List: Shows everything on a single list, no matter what or where is was played<br />
Group by Type: Display on separate groups Movies, Shows, Videos, etc<br />
Group by Source: Display separate groups for each addon used to play<br />
Number of lines on top: If grouping is active, display before the groups some of the last played movies or shows<br />
Show Date: Display for each item the date when it was played<br />
Show Time: Display time of play<br />
Play History at 5 Star Movies: The play history can be viewed privately on the www.5star.movies site<br />
Custom Path: Location of non-library play history. Point all devices to the same location to synch non-library history<br />
Enable Debug: Display an extra menu option allowing to clear the full list, and logs information to help solve eventual errors<br />

Installation
------------
- Download the 5 star repo
https://github.com/5-star/repository.5st...p?raw=true
- Open Kodi
- Go to `System -> Settings -> Add-ons
- Select Install from zip file` -> Select the downloaded zip file
- Then select -> Install from repository -> Last played addon and Install
- Enjoy Smile
 
Release history
---------------
1.0.8 - New replay method and some minor improvements<br />
1.0.7 - New list format and add 5star-movies<br />
1.0.6 - Configuration options<br />
1.0.5 - Add debug options<br />
1.0.4 - New options: Split by addon and display date and time<br /> 
1.0.3 - Improve metadata info. Aloow item removal. Make it kodi repo compliant<br />
1.0.2 - Set media type on list items<br />
1.0.1 - Initial Release<br />
>>>>>>> 7e36e41c9960add4e6203145447ce1870b782af3

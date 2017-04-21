### Introduction

**Kodi** uses Github for development only, i.e. for *pull requests* and the review of such code.  
**Do not open** an issue on Github for your questions or bug reports.  
**Do not comment** on a *pull request* unless you are involved in the testing of such or have something meaningful to contribute.  
Not familiar with git? Start by looking at Github's [collaborating pages](https://help.github.com/categories/collaborating/).

#### Questions about Kodi?

To get your questions answered, please ask in the [Kodi community forum's](http://forum.kodi.tv/) or on **IRC:** [#kodi](http://webchat.freenode.net?nick=kodi-contrib&channels=%23kodi&prompt=1&uio=OT10cnVlde) on freenode.net

#### Issue or bug reports and discussions

Issue or bug reports must be send towards the add-on creator which can be found in each [addon.xml] (http://kodi.wiki/view/Addon.xml) file.

If you can, we encourage you to investigate the issue yourself and create a [pull request](https://help.github.com/articles/creating-a-pull-request/) towards the original source of the code. We try to ask each add-on aythor to include this in the [addon.xml] (http://kodi.wiki/view/Addon.xml) file. Should this not be present then we advise you to find the dedicated add-on thread on the forum and ask there.

For bug reports and related discussions, feature requests and all other support, please go to [Kodi community forum's](http://forum.kodi.tv/) and find the dedicated add-on thread.

#### Pull Requests

Before [creating a pull request](https://help.github.com/articles/creating-a-pull-request/), please read our general code guidelines that can be found at:

- [Kodi add-on development](http://kodi.wiki/view/Add-on_development)

###### General guidelines for creating pull requests:
- **Create separate branches**. Don't ask us to pull from your master branch. 
- **One pull request per add-on**. If you want to do more than one, send multiple *pull requests*. 
- **Do not send us multiple commits**. Make sure each add-on only consists of a single commit in your *pull
  request*.  
  If you had to make multiple intermediate commits while developing, please squash them before sending them to us.  
  In the end before merging you may be asked to squash your commit even some more.

###### Please follow these guidelines; it's the best way to get your work included in the repository!

- [Click here](https://github.com/xbmc/repo-plugins/fork/) to fork the Kodi script repository,
   and [configure the remote](https://help.github.com/articles/configuring-a-remote-for-a-fork/):

   ```bash
   # Clone your fork of kodi's repo into the current directory in terminal
   git clone git@github.com:<your github username>/repo-plugins.git repo-plugins
   # Navigate to the newly cloned directory
   cd repo-plugins
   # Assign the original repo to a remote called "upstream"
   git remote add upstream https://github.com/xbmc/repo-plugins.git
   ```

- If you cloned a while ago, get the latest changes from upstream:

   ```bash
   # Fetch upstream changes
   git fetch upstream
   # Make sure you are on your 'master' branch
   git checkout master
   # Merge upstream changes
   git merge upstream/master
   ```
   'master' is only used as example here. Please replace it with the correct branch you want to submit your add-on towards.

- Create a new branch to contain your new add-on or subsequent update:

   ```bash
   git checkout -b <add-on-branch-name>
   ```
   
   The branch name isn't really relevant however a good suggestion is to name it like the addon ID.
   
- Commit your changes in a single commit, or your *[pull request](https://help.github.com/articles/using-pull-requests)* is unlikely to be merged into the main repository.  
   Use git's [interactive rebase](https://help.github.com/articles/interactive-rebase)
   feature to tidy up your commits before making them public.
   The commit for your add-on should have the following naming convention as the following example:

   ```bash
   [metadata.themoviedb.org] 3.0.0
   ```
   
   Your addon ID between brackets followed by the version number.
   
- Push your topic branch up to your fork:

   ```bash
   git push origin <add-on-branch-name>
   ```

-  Open a [pull request](https://help.github.com/articles/using-pull-requests) with a 
   clear title and description.

-  Updating your [pull request](https://help.github.com/articles/using-pull-requests) can be done by applying your changes and squashing them in the already present commit. Afterwards you can force push these change and your pull request will be updated. 

   ```bash
   git push --force origin <add-on-branch-name>
   ```

These examples use git command line. There are also git tools available that have a graphic interface and the steps above should be done in a similar way. Please consult the manual of those programs.
   

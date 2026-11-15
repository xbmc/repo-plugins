# KODI weather forecast from HomeAssistant

## Wiki
This repo has a [Wiki section](https://github.com/Eugeniusz-Gienek/kodi_weather_ha/wiki/Manual) describing the installation and configuring steps
## ...or you may use these quick instructions
In order to make it work there are a couple of actions which have to be performed on both HomeAssistant and Kodi.

1. In Home Assistant you have to [create a token](https://community.home-assistant.io/t/how-to-get-long-lived-access-token/162159/5) for this plugin.
   -  get to your Profile page on Home Assistant by clicking on your username in the bottom left panel of the HA page (under Notifications)
   -  then click on Create Token all the way at the bottom
   -  give it a meaningful name and then copy it for use in your application.
2. In Kodi you have to do the following:
   - Install plugin
   - In settings put the long live token and url to your Home Assistant server
   - Check the entity IDs
   - Done. Enjoy :) 

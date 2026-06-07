# CBC TV App

This is the CBC TV application. The app has been reverse engineered from their
online services.

## What is supported

* Live Stations
* Live events
* Shows

## Setup Instructions

Install this add-on via Kodi's GUI using the [Add-on Manager](https://kodi.wiki/view/Add-ons).
Once installed, you will have immediate access to live programming. If you wish
to access TV shows and other on-demand content, you need a CBC Gem account.

Sign up for CBC Gem [here](https://gem.cbc.ca/join-now). It is suggested to
first login to your account via web browser and you should see a prompt for your
name and postal code. After confirming your information via web browser, you
should then be able to use your login email and password on the add-on
configuration page in Kodi.

## API Details

Content is keyed off of the following links:
* [Authorization](https://api-cbc.cloud.clearleap.com/cloffice/client/identities)
* [Live channels](http://tpfeed.cbc.ca/f/ExhSPC/t_t3UKJR6MAT?pretty=true&sort=pubDate%7Cdesc)
* [Live](https://tpfeed.cbc.ca/f/ExhSPC/FNiv9xQx_BnT?q=id:*&pretty=true&sort=pubDate%7Cdesc)
* [Show](https://api-cbc.cloud.clearleap.com/cloffice/client/web/browse/babb23ae-fe47-40a0-b3ed-cdc91e31f3d6)

### Authorization

Authorization details are available at the authorization link above. Step one is
to register the device. The second step, if a login is provided, is to log the
user in.

## Test Examples
The following is for a season one episode of still standing that requies both
device registration and user authorization.

```
./test.py -s
./test.py -C shows-categories-comedy
./test.py -S crawford

...
crawford/s01e01 - I'm Not Crazy, I Love You - https://services.radio-canada.ca/media/validation/v2?appCode=gem&idMedia=932390&manifestType=desktop&output=json&tech=hls
...

./test.py -e https://services.radio-canada.ca/media/validation/v2?appCode=gem&idMedia=932390&manifestType=desktop&output=json&tech=hls
```
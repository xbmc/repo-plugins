# KODI weather forecast from HomeAssistant

## Instructions
In order to make it work there are a couple of actions which have to be performed on both HomeAssistant and Kodi.

1. In Home Assistant you have to create template for the weather forecast.
For example, like this:
- Add the following in `configuration.yaml`:
  - `template: !include forecasts.yaml`
- then create `forecasts.yaml` file
- in `forecasts.yaml` file create the following:
    <pre><code>- trigger:
        - platform: event #update at startup#
          event_type: homeassistant_started
        - platform: event
          event_type:
            - automation_reloaded
            - scene_reloaded
        - platform: time_pattern
          minutes: /15 #then update every hour#
      action:
        - service: weather.get_forecasts #update hourly forecasts#
          target:
            entity_id: weather.forecast_home #replace with your own weather integration
          data:
            type: hourly
          response_variable: hourly
        - service: weather.get_forecasts #update daily forecasts#
          target:
            entity_id: weather.forecast_home
          data:
            type: daily
          response_variable: daily
      sensor:
        - name: "DailyWeather"
          state: "{{ states('weather.forecast_home') }}"
          unique_id: weather_daily_all_in_one
          attributes:
            day0_date: "{{ daily['weather.forecast_home'].forecast[0].datetime }}"
            day0_condition: "{{ daily['weather.forecast_home'].forecast[0].condition }}"
            day0_wind_bearing: "{{ daily['weather.forecast_home'].forecast[0].wind_bearing }}"
            day0_wind_speed: "{{ daily['weather.forecast_home'].forecast[0].wind_speed }}"
            day0_precipitation: "{{ daily['weather.forecast_home'].forecast[0].precipitation }}"
            day0_humidity: "{{ daily['weather.forecast_home'].forecast[0].humidity }}"
            day0_temperature: "{{ daily['weather.forecast_home'].forecast[0].temperature }}"
            day0_temperature_low: "{{ daily['weather.forecast_home'].forecast[0].templow }}"
            day1_date: "{{ daily['weather.forecast_home'].forecast[1].datetime }}"
            day1_condition: "{{ daily['weather.forecast_home'].forecast[1].condition }}"
            day1_wind_bearing: "{{ daily['weather.forecast_home'].forecast[1].wind_bearing }}"
            day1_wind_speed: "{{ daily['weather.forecast_home'].forecast[1].wind_speed }}"
            day1_precipitation: "{{ daily['weather.forecast_home'].forecast[1].precipitation }}"
            day1_humidity: "{{ daily['weather.forecast_home'].forecast[1].humidity }}"
            day1_temperature: "{{ daily['weather.forecast_home'].forecast[1].temperature }}"
            day1_temperature_low: "{{ daily['weather.forecast_home'].forecast[1].templow }}"
            day2_date: "{{ daily['weather.forecast_home'].forecast[2].datetime }}"
            day2_condition: "{{ daily['weather.forecast_home'].forecast[2].condition }}"
            day2_wind_bearing: "{{ daily['weather.forecast_home'].forecast[2].wind_bearing }}"
            day2_wind_speed: "{{ daily['weather.forecast_home'].forecast[2].wind_speed }}"
            day2_precipitation: "{{ daily['weather.forecast_home'].forecast[2].precipitation }}"
            day2_humidity: "{{ daily['weather.forecast_home'].forecast[2].humidity }}"
            day2_temperature: "{{ daily['weather.forecast_home'].forecast[2].temperature }}"
            day2_temperature_low: "{{ daily['weather.forecast_home'].forecast[2].templow }}"
            day3_date: "{{ daily['weather.forecast_home'].forecast[3].datetime }}"
            day3_condition: "{{ daily['weather.forecast_home'].forecast[3].condition }}"
            day3_wind_bearing: "{{ daily['weather.forecast_home'].forecast[3].wind_bearing }}"
            day3_wind_speed: "{{ daily['weather.forecast_home'].forecast[3].wind_speed }}"
            day3_precipitation: "{{ daily['weather.forecast_home'].forecast[3].precipitation }}"
            day3_humidity: "{{ daily['weather.forecast_home'].forecast[3].humidity }}"
            day3_temperature: "{{ daily['weather.forecast_home'].forecast[3].temperature }}"
            day3_temperature_low: "{{ daily['weather.forecast_home'].forecast[3].templow }}"
            day4_date: "{{ daily['weather.forecast_home'].forecast[4].datetime }}"
            day4_condition: "{{ daily['weather.forecast_home'].forecast[4].condition }}"
            day4_wind_bearing: "{{ daily['weather.forecast_home'].forecast[4].wind_bearing }}"
            day4_wind_speed: "{{ daily['weather.forecast_home'].forecast[4].wind_speed }}"
            day4_precipitation: "{{ daily['weather.forecast_home'].forecast[4].precipitation }}"
            day4_humidity: "{{ daily['weather.forecast_home'].forecast[4].humidity }}"
            day4_temperature: "{{ daily['weather.forecast_home'].forecast[4].temperature }}"
            day4_temperature_low: "{{ daily['weather.forecast_home'].forecast[4].templow }}"
            day5_date: "{{ daily['weather.forecast_home'].forecast[5].datetime }}"
            day5_condition: "{{ daily['weather.forecast_home'].forecast[5].condition }}"
            day5_wind_bearing: "{{ daily['weather.forecast_home'].forecast[5].wind_bearing }}"
            day5_wind_speed: "{{ daily['weather.forecast_home'].forecast[5].wind_speed }}"
            day5_precipitation: "{{ daily['weather.forecast_home'].forecast[5].precipitation }}"
            day5_humidity: "{{ daily['weather.forecast_home'].forecast[5].humidity }}"
            day5_temperature: "{{ daily['weather.forecast_home'].forecast[5].temperature }}"
            day5_temperature_low: "{{ daily['weather.forecast_home'].forecast[5].templow }}"
            days_num: "{{ 6 }}"
        - name: "HourlyWeather"
          state: "{{ states('weather.forecast_home') }}"
          unique_id: weather_hourly_all_in_one
          attributes:
            hour0_date: "{{ hourly['weather.forecast_home'].forecast[0].datetime }}"
            hour0_condition: "{{ hourly['weather.forecast_home'].forecast[0].condition }}"
            hour0_wind_bearing: "{{ hourly['weather.forecast_home'].forecast[0].wind_bearing }}"
            hour0_wind_speed: "{{ hourly['weather.forecast_home'].forecast[0].wind_speed }}"
            hour0_precipitation: "{{ hourly['weather.forecast_home'].forecast[0].precipitation }}"
            hour0_humidity: "{{ hourly['weather.forecast_home'].forecast[0].humidity }}"
            hour0_temperature: "{{ hourly['weather.forecast_home'].forecast[0].temperature }}"
            hour0_cloud_coverage: "{{ hourly['weather.forecast_home'].forecast[0].cloud_coverage }}"
            hour1_date: "{{ hourly['weather.forecast_home'].forecast[1].datetime }}"
            hour1_condition: "{{ hourly['weather.forecast_home'].forecast[1].condition }}"
            hour1_wind_bearing: "{{ hourly['weather.forecast_home'].forecast[1].wind_bearing }}"
            hour1_wind_speed: "{{ hourly['weather.forecast_home'].forecast[1].wind_speed }}"
            hour1_precipitation: "{{ hourly['weather.forecast_home'].forecast[1].precipitation }}"
            hour1_humidity: "{{ hourly['weather.forecast_home'].forecast[1].humidity }}"
            hour1_temperature: "{{ hourly['weather.forecast_home'].forecast[1].temperature }}"
            hour1_cloud_coverage: "{{ hourly['weather.forecast_home'].forecast[1].cloud_coverage }}"
            hour2_date: "{{ hourly['weather.forecast_home'].forecast[2].datetime }}"
            hour2_condition: "{{ hourly['weather.forecast_home'].forecast[2].condition }}"
            hour2_wind_bearing: "{{ hourly['weather.forecast_home'].forecast[2].wind_bearing }}"
            hour2_wind_speed: "{{ hourly['weather.forecast_home'].forecast[2].wind_speed }}"
            hour2_precipitation: "{{ hourly['weather.forecast_home'].forecast[2].precipitation }}"
            hour2_humidity: "{{ hourly['weather.forecast_home'].forecast[2].humidity }}"
            hour2_temperature: "{{ hourly['weather.forecast_home'].forecast[2].temperature }}"
            hour2_cloud_coverage: "{{ hourly['weather.forecast_home'].forecast[2].cloud_coverage }}"
            hour3_date: "{{ hourly['weather.forecast_home'].forecast[3].datetime }}"
            hour3_condition: "{{ hourly['weather.forecast_home'].forecast[3].condition }}"
            hour3_wind_bearing: "{{ hourly['weather.forecast_home'].forecast[3].wind_bearing }}"
            hour3_wind_speed: "{{ hourly['weather.forecast_home'].forecast[3].wind_speed }}"
            hour3_precipitation: "{{ hourly['weather.forecast_home'].forecast[3].precipitation }}"
            hour3_humidity: "{{ hourly['weather.forecast_home'].forecast[3].humidity }}"
            hour3_temperature: "{{ hourly['weather.forecast_home'].forecast[3].temperature }}"
            hour3_cloud_coverage: "{{ hourly['weather.forecast_home'].forecast[3].cloud_coverage }}"
            hour4_date: "{{ hourly['weather.forecast_home'].forecast[4].datetime }}"
            hour4_condition: "{{ hourly['weather.forecast_home'].forecast[4].condition }}"
            hour4_wind_bearing: "{{ hourly['weather.forecast_home'].forecast[4].wind_bearing }}"
            hour4_wind_speed: "{{ hourly['weather.forecast_home'].forecast[4].wind_speed }}"
            hour4_precipitation: "{{ hourly['weather.forecast_home'].forecast[4].precipitation }}"
            hour4_humidity: "{{ hourly['weather.forecast_home'].forecast[4].humidity }}"
            hour4_temperature: "{{ hourly['weather.forecast_home'].forecast[4].temperature }}"
            hour4_cloud_coverage: "{{ hourly['weather.forecast_home'].forecast[4].cloud_coverage }}"
            hour5_date: "{{ hourly['weather.forecast_home'].forecast[5].datetime }}"
            hour5_condition: "{{ hourly['weather.forecast_home'].forecast[5].condition }}"
            hour5_wind_bearing: "{{ hourly['weather.forecast_home'].forecast[5].wind_bearing }}"
            hour5_wind_speed: "{{ hourly['weather.forecast_home'].forecast[5].wind_speed }}"
            hour5_precipitation: "{{ hourly['weather.forecast_home'].forecast[5].precipitation }}"
            hour5_humidity: "{{ hourly['weather.forecast_home'].forecast[5].humidity }}"
            hour5_temperature: "{{ hourly['weather.forecast_home'].forecast[5].temperature }}"
            hour5_cloud_coverage: "{{ hourly['weather.forecast_home'].forecast[5].cloud_coverage }}"
            hours_num: "{{ 6 }}"
    #Sensors for current weather data#
    - name: "WeatherCurrent"
      unique_id: weather_state_current
      state: "{{ states('weather.forecast_home') }}"
    - name: "TempCurrent"
      unique_id: weather_temperature_current
      unit_of_measurement: '°C'
      state: >
        {{ state_attr('weather.forecast_home', 'temperature') }}
    - name: "HumidityCurrent"
      unique_id: weather_humidity_current
      unit_of_measurement: '%'
      state: >
        {{ state_attr('weather.forecast_home', 'humidity') }}
    - name: "WindSpeedCurrent"
      unique_id: weather_wind_speed_current
      unit_of_measurement: 'm/s'
      state: >
        {{ state_attr('weather.forecast_home', 'wind_speed') }}
    - name: "WindBearingCurrent"
      unique_id: weather_wind_bearing_current
      unit_of_measurement: '°'
      state: >
        {{ state_attr('weather.forecast_home', 'wind_bearing') }}
    - name: "PressureCurrent"
      unique_id: weather_pressure_current
      unit_of_measurement: 'hPa'
      state: >
        {{ state_attr('weather.forecast_home', 'pressure') }}
    </code></pre>
- Reboot Home Assistant
- [Create Long Live token](https://community.home-assistant.io/t/how-to-get-long-lived-access-token/162159/5):
  -  get to your Profile page on Home Assistant by clicking on your username in the bottom left panel of the HA page (under Notifications)
  -  then click on Create Token all the way at the bottom
  -  give it a meaningful name and then copy it for use in your application.
3. In Kodi You have to do the following:
  - Install plugin
  - In settings put the long live token and url to your Home Assistant server
  - Check the api urls
  - Done. Enjoy :) 

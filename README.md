# raspipool
**Swimming-Pool Automation Systen with Raspberry Pi + Home Assistant**

This branch is suppose to maintain a working RaspiPool with pH and chlorine

<img src="/help/media/raspipool_main2.png" height="256">

## Overview:

 A cost-effective, easy-to-build, easy-to-use "Swimming-Pool Automation System" with top functions to automate, control and monitorize (from web) small-medium size swimming pools.

- Automatic filter control (fixed and dual-speed pumps, 1 or 2 daily cycles) based on temperature.
- 3 sensors:
  - water temperature (one-wire [DS18B20 waterprof](https://aliexpress.com/item/32968031204.html))
  - [ph](https://www.atlas-scientific.com/product_pages/circuits/ezo_ph.html) and [orp](https://www.atlas-scientific.com/product_pages/circuits/ezo_orp.html) with [EZO circuits](https://www.atlas-scientific.com/product_pages/components/ezo-carrier-board.html). A custom UART sensor for HA has been developed.
- and minimun of [4 relays](https://aliexpress.com/item/32961638909.html) [or 6](https://aliexpress.com/item/32997012084.html) controlling :
  - pump on/off and pump speed (high/low)
  - muriatic acid injection (to regulate pH) and bleach injection (to mantain sanitization level)
 
 System is intended to monitoring and automagically control most important functions and notify to mobile all possible events.
 
 ## Build system:
 
 Follow instructions in wiki [howto build a bypass to connect sensors to the pool](https://github.com/segalion/raspipool/wiki/Bypass-for-sensors), [howto connect sensors to the raspberry pi](https://github.com/segalion/raspipool/wiki/Sensors-connection-(DS18B20,-and-EZO-pH-and-ORP)) and [howto connect relays between pumps and raspberry pi](https://github.com/segalion/raspipool/wiki/Connection-of-relays-for-pump-control)
 
 ## Install
 0. Install [hassbian](https://www.home-assistant.io/docs/installation/hassbian/installation/) in a raspberry pi (3 or 4), and give wifi connection. (If advanced user, you can instead install [raspbian](https://myhydropi.com/raspberry-pi-initial-setup) + [Home Assistant with this prefered method](https://www.home-assistant.io/docs/installation/raspberry-pi/))
 1. Copy 'custom_components', 'packages' folders (with all paths and contents) and 'ui-lovelace.yaml' frontend file in homeassistant conf_dir ( i.e. /home/homeassistant/.homeassistant/ ).
 2. Modify your 'configuration.yaml' (including '  packages: !include_dir_named packages', disabling automations, scripts and groups, discovery and lovelace in yaml mode) as example in code
 3. Create/modify proper 'secrets.yaml' for apis (latitude/longitude, pushbullet api, openweathermap api, etc).
 
 
 ## TODO:
 - Correction of FC-ORP based on CYA (actually only linear correction)
 - SWC – Salt Water Chlorinator (instead of bleach injections)
 - Control Variable Speed Motor based on 3 digital inputs (0 to 7 speeds)
 - Integrate [mega-io board](https://www.sequentmicrosystems.com/megaio.html) (relays and ACD with i2c control) instead of actual gpio-relay HATs
 
 ## Optional
 For pumps <= 1.5 HP, a external sensor to measure power consumption and [safe motor](https://en.wikipedia.org/wiki/Magnetic_starter) (based on sonoff POW)
 
 <sub>Thanks to Hidromaster, Piscidoc, and all DIY enthusiasts from [hablemosdepisicnas](http://www.hablemosdepiscinas.com/foro/viewtopic.php?f=11&t=3906) and [TFP](https://www.troublefreepool.com/threads/raspipool-pool-automation-system-with-raspberry-pi-home-assistant.188410/) forums.</sub>

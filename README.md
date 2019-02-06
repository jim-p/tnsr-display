# tnsr-display
Micropython TNSR status display (ESP8266+SH1106)

TNSR RESTCONF API status client demo in [micropython](https://docs.micropython.org/en/latest/index.html)

Intended for a Wemos D1 Mini (or similar) ESP8266 board and SH1106 1.3" OLED display

Compatible 3D printable case at https://www.thingiverse.com/thing:2934049

The code is far from complete, but serves as a good basic demo/POC to show how easy it can be to access status information using RESTCONF.

## Display Pin Connections

Wire together the following pin connections.

| Display | D1 Mini |
|---------|---------|
| SDA     | D2      |
| SCL     | D5      |
| VCC     | 5V+     |
| GND     | GND-    |

## Dependencies / Resources

1. Micropython: https://docs.micropython.org/en/latest/esp8266/tutorial/intro.html
2. SH1106 Micropython Driver: https://github.com/robert-hh/SH1106
3. esptool: https://learn.adafruit.com/building-and-running-micropython-on-the-esp8266/flash-firmware
4. ampy: https://github.com/pycampers/ampy
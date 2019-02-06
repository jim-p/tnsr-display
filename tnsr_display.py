# tnsr_display.py / main.py
# Copyright (c) 2019 Jim Pingle
# All rights reserved.

# TNSR RESTCONF API status client demo in micropython
# Intended for a Wemos D1 Mini (or similar) and SH1106 1.3" OLED display
# Compatible 3D printable case at https://www.thingiverse.com/thing:2934049

#TODO: Get ussl working with client certs
#import ussl
import urequests
from machine import I2C, Pin
# OLED Display driver from https://github.com/robert-hh/SH1106
# Copy sh1106.py to the device with ampy or webrpl
import sh1106
import network
import utime

################################################################################
# Settings: Edit in values specific to this network
################################################################################
# Info needed to connect to wireless
wifissid = "xxxx"
wifipsk  = "xxxx"

# URL to the TNSR device (http only currently, no auth for this demo)
tnsrurl = "http://x.x.x.x"
################################################################################

# Display dimensions, SH1106 is 128w x 64h
dwidth = 128
dheight = 64

# Logical mapping of the Wemos D1 mini pins to their ESP8266 counterparts
# From https://www.twobitarcade.net/article/wemos-d1-pins-micropython/
# Even though this code only uses two pins, keep this in place for reference.
# Could be removed to save a little memory, replace pin references in I2C call below.
wemos_d1_pins = {
    'D0': 16,  # GPIO
    'D1': 5,   # GPIO, I2C SCL
    'D2': 4,   # GPIO, I2C SDA
    'D3': 0,   # GPIO
    'D4': 2,   # GPIO
    'D5': 14,  # GPIO, SPI SCK (Serial Clock)
    'D6': 12,  # GPIO, SPI MISO (Master in, Slave out)
    'D7': 13,  # GPIO, SPI MOSI (Master out, Slave in)
    'D8': 15,  # GPIO, SPI SS (Slave select)
    'A0': 0,   # Analog in, via ADC
    'RX': 3,   # Receive
    'TX': 1    # Transmit
}

# Setup the I2C for the display and initialize
i2c = I2C(-1, sda=Pin(wemos_d1_pins["D2"]), scl=Pin(wemos_d1_pins["D5"]), freq=400000)
display = sh1106.SH1106_I2C(dwidth, dheight, i2c, Pin(16), 0x3c)

# Setup wifi and connect
wlan = network.WLAN(network.STA_IF) # Set wifi to station mode
wlan.active(True)                   # Mark the interface as active
wlan.scan()                         # Scan for access points (may not be needed)
wlan.connect(wifissid, wifipsk)     # connect to the AP configured above
# TODO: Should probably loop here waiting until wlan.isconnected() is True.
#       Maybe display wifi status, maybe attempt to reconnect.

# For loading files and debugging in a browser, otherwise use ampy
#import webrepl
#webrepl.start()

# Draw a progress bar from given dimensions and a fill percentage (0<pct<1)
def progress_bar(x, y, w, h, pct):
    # Fill with black to ensure a clean slate
    display.fill_rect( x, y, w, h, 0 )
    # Draw the bar outline
    display.rect(x, y, w, h, 1)
    # Draw the filled-in portion of the bar
    display.fill_rect( x, y, int(round((pct) * (w))), h, 1 )

# Animated wipe to the left, scrolling the screen away step pixels at a time
def wipe_left(step):
    j=dwidth
    while j >= 0:
        # Scroll the display left
        display.scroll(-step, 0)
        # The previous image is left in the framebuffer, so clear it.
        display.fill_rect( j-step, 0, step, dheight, 0 )
        display.show()
        j -= step
    # The above could leave some last slice on the screen at various step values
    #   Rather than use more complicated while loop logic, simply blank the
    #   entire display rather than calculate the last bit to clear.
    display.fill(0)
    display.show()

# For wifi signal strength, translate the S/N ratio to a more user-friendly value
def rssi_to_percent(rssi):
    if (rssi >= -55):
        pct = 100
    elif (rssi >= -66):
        pct = 75
    elif (rssi >= -77):
        pct = 50
    elif (rssi >= -88):
        pct = 25
    else:
        pct = 0
    return pct/100.0

# TNSR output is given in seconds, use this to convert it to a more user-friendly value
def uptime_to_dhms(sec):
   # Split off seconds, minutes are remainder
   m, s = divmod(sec, 60)
   # Split off minutes, hours are remainder
   h, m = divmod(m, 60)
   # Split off hours, days are remainder
   d, h = divmod(h, 24)
   # Output uptime similar to "11d 1:22:33" -- may be too long with many days,
   #   might need to check length in the future and round.
   return "%dd %d:%02d:%02d" % (d, h, m, s)

# To keep the display compact and human-readable, convert byte values to IEC units
def format_bytes(b):
    # IEC units are based on (2^10)^x
    exp = 2**10
    n = 0
    # IEC unit prefixes, see https://en.wikipedia.org/wiki/Mebibyte
    iec = {0 : 'B', 1: 'KiB', 2: 'MiB', 3: 'GiB', 4: 'TiB', 5: 'PiB', 6: 'EiB', 7: 'ZiB', 8: 'YiB'}
    # Loop until we reach the required prefix
    while b > exp:
        b /= exp
        n += 1
    # Return a value such as "20.43 MiB"
    return "%.2f %s" % (b, iec[n])


# Status of this esp8266 device, optional but useful
def self_status():
    # wifi signal strength
    rssi = rssi_to_percent(wlan.status('rssi'))
    display.sleep(False)
    display.fill(0)
    # Use row-based calculation to save having to keep track of Y pos in each line manually
    row = 0
    # Header
    display.text('Monitor Device:', 0, row*10, 5)
    # Display SSID
    row += 1
    display.text('WIFI:', 0, row*10, 5)
    display.text(wifissid, 40, row*10, 5)
    # Display signal strength
    row += 1
    display.text('SIG:', 0, row*10, 5)
    progress_bar(32, row*10, dwidth-40, 8, rssi)
    # Display the wifi IP Address -- skip subnet mask, not enough space
    row += 1
    display.text('IPA:', 0, row*10, 5)
    display.text(wlan.ifconfig()[0], 32, row*10, 5)
    # Display the default gateway
    row += 1
    display.text('GW :', 0, row*10, 5)
    display.text(wlan.ifconfig()[2], 32, row*10, 5)
    # Display the DNS server
    row += 1
    display.text('DNS:', 0, row*10, 5)
    display.text(wlan.ifconfig()[3], 32, row*10, 5)
    display.show()

# Basic TNSR host stats
def host_status():
    # Gather Data
    response = urequests.get(tnsrurl + '/restconf/data/netgate-system:system-state')
    parsed = response.json()
    # Display Data
    display.sleep(False)
    display.fill(0)
    # Header
    row = 0
    display.text('TNSR Host', 0, row*10, 5)
    # Display RAM Usage (total-free)/total
    row += 1
    display.text('RAM:', 0, row*10, 5)
    usedram = parsed['netgate-system:system-state']['total-ram'] - parsed['netgate-system:system-state']['free-ram']
    progress_bar(32, row*10, dwidth-40, 8, usedram / parsed['netgate-system:system-state']['total-ram'])
    # Display Swap Usage (total-free)/total
    row += 1
    display.text('SWP:', 0, row*10, 5)
    usedswp = parsed['netgate-system:system-state']['total-swap'] - parsed['netgate-system:system-state']['free-swap']
    progress_bar(32, row*10, dwidth-40, 8, usedswp / parsed['netgate-system:system-state']['total-swap'])
    display.show()
    # Display Uptime
    row += 1
    display.text('UP: ', 0, row*10, 5)
    display.text(uptime_to_dhms(parsed['netgate-system:system-state']['uptime']), 32, row*10, 5)
    # Update Display
    display.show()

def interface_status():
    # Gather Data
    response = urequests.get(tnsrurl + '/restconf/data/netgate-interface:interfaces-state')
    parsed = response.json()
    # Loop through and show each interface for a few seconds.
    t = 0
    while t < len(parsed['netgate-interface:interfaces-state']['interface']):
        # Display Data
        display.sleep(False)
        display.fill(0)
        # Header
        row = 0
        display.text('Interface', 0, row*10, 5)
        # Interface name (first 16 chars at most)
        row += 1
        display.text(parsed['netgate-interface:interfaces-state']['interface'][t]['name'], 0, row*10, 5)
        # If the interface name is longer than the display can output, wrap to the next line.
        if (len(parsed['netgate-interface:interfaces-state']['interface'][t]['name']) > 16):
            row += 1
            display.text(parsed['netgate-interface:interfaces-state']['interface'][t]['name'][16:], 0, row*10, 5)
        # Interface administrative and link status
        row += 1
        display.text('Status:', 0, row*10, 5)
        display.text(parsed['netgate-interface:interfaces-state']['interface'][t]['admin-status'] + '/' + parsed['netgate-interface:interfaces-state']['interface'][t]['link-status'], 56, row*10, 5)
        row += 1
        # RX Bytes
        display.text('RX: ', 0, row*10, 5)
        display.text(format_bytes(parsed['netgate-interface:interfaces-state']['interface'][t]['counters']['rx-bytes']), 32, row*10, 5)
        row += 1
        # TX Bytes
        display.text('TX: ', 0, row*10, 5)
        display.text(format_bytes(parsed['netgate-interface:interfaces-state']['interface'][t]['counters']['tx-bytes']), 32, row*10, 5)
        display.show()
        t += 1
        # Pause between displaying interface info
        utime.sleep(3)

# Function that dumps all the status info with wipes in between screens.
def all_status():
    # TODO: Check wifi status here, reconnect if disconnected
    # Host status
    host_status()
    utime.sleep(3)
    wipe_left(8)
    # Interfaces
    interface_status()
    wipe_left(8)
    # Monitor unit
    self_status()
    utime.sleep(3)
    wipe_left(8)

# Test Loop runs status display 10x. Access to the serial/web REPL will be active after.
i = 1
while i < 10:
    all_status()
    i += 1

# Real Loop -- Runs forever, but will never yield control to REPL
#while True:
#    all_status()

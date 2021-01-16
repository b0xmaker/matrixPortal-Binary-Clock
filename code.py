# modified from https://learn.adafruit.com/network-connected-metro-rgb-matrix-clock/code-the-matrix-clock

# matrix portal + RGB matrix binary clock
# Runs on Airlift Metro M4 with 64x32 RGB Matrix display & shield
# Add thermistor between pin A4 and 3V3, add 10K resistor between A4 and GND

import time
import board
import displayio
import terminalio
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix

BLINK = False
DEBUG = False

from analogio import AnalogIn
analog_in= AnalogIn(board.A4)

def get_voltage(pin):
    return (pin.value * 3.3) / 65536
    
lightThreshold = 1 # go above this threshold, and the display will turn ON
darkThreshold = 0.5 # go below this threshold, and the display will turn OFF
ledOn = 1

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
print("    Metro Minimal Clock")
print("Time will be set for {}".format(secrets["timezone"]))

# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=board.NEOPIXEL, debug=False)

# --- Drawing setup ---
group = displayio.Group(max_size=6)  # Create a Group
bitmap = displayio.Bitmap(32, 16, 2)  # Create a bitmap object,width, height, bit depth
color = displayio.Palette(4)  # Create a color palette
color[0] = 0x000000  # black background
color[1] = 0xFF0000  # nighttime color, red
color[3] = 0xFFFFFF  # daytime color, white

# Create a TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
group.append(tile_grid)  # Add the TileGrid to the Group
display.show(group)

if not DEBUG:
    font = bitmap_font.load_font("/Binary_font.bdf")
else:
    font = terminalio.FONT

clock_label = Label(font, max_glyphs=10)


def update_time(*, hours=None, minutes=None, seconds=None, show_colon=False):
    now = time.localtime()  # Get the time values we need
    if hours is None:
        hours = now[3]
    if hours >= 18 or hours < 6:  # evening hours to morning
        clock_label.color = color[1]
    else:
        clock_label.color = color[3]  # daylight hours
        
    if hours < 10:
        hours = "0" + str(now[3])
    
    

    if minutes is None:
        minutes = now[4]
        
    
    if seconds is None:
        seconds = now[5]
    
    if seconds < 10:
       seconds = "0" + str(now[5])

    if BLINK:
        colon = ":" if show_colon or now[5] % 2 else " "
    else:
        colon = " "

    clock_label.text = "{hours}{colon}{minutes:02d}{colon}{seconds}".format(
        hours=hours, minutes=minutes, seconds=seconds, colon=colon
    )
    bbx, bby, bbwidth, bbh = clock_label.bounding_box
    # Center the label
    clock_label.x = -1
    clock_label.y = display.height - 8
    if DEBUG:
        print("Label bounding box: {},{},{},{}".format(bbx, bby, bbwidth, bbh))
        print("Label x: {} y: {}".format(clock_label.x, clock_label.y))


last_check = None
update_time(show_colon=True)  # Display whatever time is on the board
group.append(clock_label)  # add the clock label to the group

# start with screen on
ledOn = 1

while True:
    
    if ledOn == 1:
        # if the ambient light is above the set threshold... work normally
        if get_voltage(analog_in) > darkThreshold:
            color[0] = 0x000000  # black background
            color[1] = 0xFF0000  # red
            color[3] = 0xFFFFFF  # white
            if last_check is None or time.monotonic() > last_check + 3600:
                try:
                    update_time(
                        show_colon=True
                    )  # Make sure a colon is displayed while updating
                    network.get_local_time()  # Synchronize Board's clock to Internet
                    last_check = time.monotonic()
                except RuntimeError as e:
                    print("Some error occured, retrying! -", e)
            update_time()
            time.sleep(1)
            print(get_voltage(analog_in))
            print("lights on, ambient bright.")
        
        else:
            ledOn = 0
            print("gone below dark threshold, going to dark mode.")
 

    else:
        if get_voltage(analog_in) < lightThreshold:
            ledOn = 0
            color[0] = 0x000000  # black background
            color[1] = 0x000000  # black font
            color[3] = 0x000000  # black font
            ledOn = 0
            update_time()
            time.sleep(1)
            print(get_voltage(analog_in))
            print("lights off, ambient dark")
        else:
            ledOn = 1
            print("gone above light threshold, going to light mode")
    

    update_time()
    time.sleep(1)
    print(get_voltage(analog_in))

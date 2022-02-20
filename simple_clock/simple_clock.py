import board
import busio
from digitalio import DigitalInOut, Pull
import os
import random
import rtc
import struct
import sys
import time
import wifi
import usb_cdc
import traceback
import supervisor

import adafruit_ht16k33.segments
import neopixel

SPEED_DELAY = 0.1
SYNC_DELAY = 2 * 60 * 60 # 2h

TZ_OFFSET = 3600 * 1  # 1 = winter
NTP_SERVER = "pool.ntp.org"
NTP_PORT = 123

####################################################################
# setup prints
####################################################################

def log_info(*args):
	# out = " ".join([arg if type(arg) == str else repr(arg) for arg in args]) + "\r\n"
	# usb_cdc.data.write(out.encode("utf8"))
	if usb_cdc.console is None and usb_cdc.data is None:
		pass
	else:
		print(*args)

####################################################################
# setup buttons
####################################################################

butA = DigitalInOut(board.IO38)
butA.switch_to_input(Pull.DOWN)
butB = DigitalInOut(board.IO33)
butB.switch_to_input(Pull.DOWN)
but1 = DigitalInOut(board.IO6)
but1.switch_to_input(Pull.DOWN)
but2 = DigitalInOut(board.IO5)
but2.switch_to_input(Pull.DOWN)

buttons = [
	[butA,"BUTA"],
	[butB,"BUTB"],
	[but1,"BUT1"],
	[but2,"BUT2"],
]

####################################################################
# setup displays and blinkies
####################################################################

pixels = neopixel.NeoPixel(board.IO7,5,auto_write = False)
pixels.fill((0,0,0))
pixels.show()

colors = [
	(0,255,16),
	(92,255,0),
	(160,160,0),
	(255,64,0),
	(255,0,0),
]

status = neopixel.NeoPixel(board.NEOPIXEL,1)
status.fill((0,0,0))

i2c = busio.I2C(sda=board.SDA, scl=board.SCL, frequency=400_000)
display = [
	adafruit_ht16k33.segments.Seg14x4(i2c, address=0x70, auto_write=False),
	adafruit_ht16k33.segments.Seg14x4(i2c, address=0x72, auto_write=False),
	adafruit_ht16k33.segments.Seg14x4(i2c, address=0x74, auto_write=False),
]

# display a cleaner 5 
CHARS = list(adafruit_ht16k33.segments.CHARS)
NUMBERS = list(adafruit_ht16k33.segments.NUMBERS)
CHARS[ord("5") * 2 - 64] = CHARS[ord("S") * 2 - 64]
CHARS[ord("5") * 2 - 64 + 1] = CHARS[ord("S") * 2 - 64 + 1]
NUMBERS[5] = 16 * CHARS[ord("S") * 2 - 64] + CHARS[1 + ord("S") * 2 - 64]
adafruit_ht16k33.segments.CHARS = tuple(CHARS)
adafruit_ht16k33.segments.NUMBERS = tuple(NUMBERS)

def seg_brightness(val):
	for s in display:
		s.brightness = val

def seg_show():
	for s in display:
		s.show()

def seg_print(label):
	buff = [" "] * 12
	for index,segment in enumerate(display):
		for char in range(4):
			pos = index*4+char
			if pos < len(label):
				buff[pos] = label[pos]
		segment.print("".join(buff[index*4:index*4+4]))
	seg_show()

be_bright = False
def update_brightness(now):
	if now.tm_hour < 8 and not be_bright:
		seg_brightness(0.01)
		pixels.brightness = 0.01
		status.brightness = 0.01
	else:
		seg_brightness(1)
		pixels.brightness = 1
		status.brightness = 1
	pixels.show()
	status.show()

####################################################################
# setup wifi
####################################################################

socket_pool = None

def connect_wifi(verbose=False):
	global socket_pool
	import wifi
	import socketpool
	try:
		from secrets import secrets
	except ImportError:
		log_info("WiFi secrets are kept in secrets.py, please add them there!")
		raise
	if verbose:
		log_info("Connecting to ", secrets["ssid"])
	wifi.radio.connect(ssid=secrets["ssid"], password=secrets["password"])
	socket_pool = socketpool.SocketPool(wifi.radio)
	if verbose:
		log_info("Connected with IP ", wifi.radio.ipv4_address)

def get_ntp_time(pool):
	packet = bytearray(48)
	packet[0] = 0b00100011

	for i in range(1, len(packet)):
		packet[i] = 0

	with pool.socket(pool.AF_INET, pool.SOCK_DGRAM) as sock:
		# have a timeout, or it might hang
		sock.settimeout(2)
		sock.sendto(packet, (NTP_SERVER, NTP_PORT))
		sock.recv_into(packet)
		destination = time.monotonic_ns()

	seconds = struct.unpack_from("!I", packet, offset=len(packet) - 8)[0]
	monotonic_start = seconds - 2_208_988_800 - (destination // 1_000_000_000)
	return time.localtime(time.monotonic_ns() // 1_000_000_000 + monotonic_start + TZ_OFFSET)

def update_NTP():
	pixels.fill((0,128,255))
	pixels.show()
	seg_print(" UPDATE NTP ")
	log_info("Update from NTP")
	try:
		wifi.radio.enabled = True
		log_info("Connect Wifi")
		connect_wifi(verbose=True)
		rtc.RTC().datetime = get_ntp_time(socket_pool)
		time.sleep(0.1)
	except Exception as ex:
		print("Exception")
		print(ex)
		seg_print(" NTP FAILED ")
		time.sleep(2)
	finally:
		log_info("Turn off Wifi")
		wifi.radio.enabled = False

####################################################################
# time functions
####################################################################

week_days = ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"]

def update_time(show_separator = True):
	now = time.localtime()

	if show_separator:
		sep = "."
	else:
		sep = ""

	day = week_days[now.tm_wday].upper()
	daynum = f"{now.tm_mday:2d}"

	display[0].print(f"{day}{daynum[0]}")
	display[1].print(f"{daynum[1]} {now.tm_hour:02d}{sep}")
	display[2].print(f"{now.tm_min:02d}{sep}{now.tm_sec:02d}")
	seg_show()

	return now

####################################################################
# startup animation
####################################################################

pixels.brightness = 1
pixels.show()
seg_brightness(1)
seg_show()

now = time.localtime()
if now.tm_year < 2021:
	update_NTP()
	now = time.localtime()

update_brightness(now)

log_info("Now is:",now)

y = 0
def pixcol():
	global y
	if pixels[4-y] == (0,0,0):
		pixels[4-y] = (0,255,255)
	else:
		pixels[4-y] = (0,0,0)
	pixels.show()
	y = (y+1) % 5

for x in range(2):
	pixcol()
	for segment in display:
		segment.fill(1)
		time.sleep(0.1)
		segment.show()
		pixcol()
	for segment in display:
		segment.fill(0)
		time.sleep(0.1)
		segment.show()
		pixcol()

####################################################################
# setup loop variables and parameters
####################################################################

defcon = 0
next_sync = time.monotonic() + SYNC_DELAY
last_b_update = 0

####################################################################
# loop-dee-loop
####################################################################

index = 0
try:
	while True:
		# scroll
		now = update_time(index // 4 % 2 == 0)
		defcon = now.tm_sec // 10

# 		if now.tm_sec % 2 == 0:
# 			status.fill(colors[now.tm_sec % 5])
# 		else:
# 			status.fill(0)

		pixels.fill(0)
		for x in range(5):
			if x < defcon:
				pixels[4 - x] = colors[x]
			else:
				pixels[4 - x] = 0
		pixels.show()

		index += 1
		time.sleep(SPEED_DELAY)

		if now.tm_min // 10 != last_b_update:
			last_b_update = now.tm_min // 10
			update_brightness(now)

		if but1.value:
			be_bright = not be_bright
			update_brightness(now)
			while but1.value:
				time.sleep(0.1)

		if but2.value or time.monotonic() > next_sync:
			update_NTP()
			next_sync = time.monotonic() + SYNC_DELAY

except Exception as ex:
	pixels.fill((255,0,0))
	pixels.brightness = 1
	pixels.show()
	for segment in display:
		segment.fill(1)

	while not but1.value and not but2.value:
		print("-"*70)
		traceback.print_exception(ex, ex, ex.__traceback__)
		print("----- Hold button to quit -----")
		time.sleep(5)

	supervisor.reload()

import board
import busio
from digitalio import DigitalInOut, Pull
import os
import random
import rtc
import struct
import time
import wifi

import adafruit_ht16k33.segments
import neopixel

SPEED_DELAY = 0.1
SYNC_DELAY = 2 * 60 * 60 # 2h

TZ_OFFSET = 3600 * 2
NTP_SERVER = "pool.ntp.org"
NTP_PORT = 123

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
pixels.brightness = 0.2
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
status_power = DigitalInOut(board.NEOPIXEL_POWER)
status_power.switch_to_output()
status_power.value = True

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
		print("WiFi secrets are kept in secrets.py, please add them there!")
		raise
	if verbose:
		print("Connecting to ", secrets["ssid"])
	wifi.radio.connect(ssid=secrets["ssid"], password=secrets["password"])
	socket_pool = socketpool.SocketPool(wifi.radio)
	if verbose:
		print("Connected with IP ", wifi.radio.ipv4_address)

def get_ntp_time(pool):
	packet = bytearray(48)
	packet[0] = 0b00100011

	for i in range(1, len(packet)):
		packet[i] = 0

	with pool.socket(pool.AF_INET, pool.SOCK_DGRAM) as sock:
		sock.settimeout(None)
		sock.sendto(packet, (NTP_SERVER, NTP_PORT))
		sock.recv_into(packet)
		destination = time.monotonic_ns()

	seconds = struct.unpack_from("!I", packet, offset=len(packet) - 8)[0]
	monotonic_start = seconds - 2_208_988_800 - (destination // 1_000_000_000)
	return time.localtime(time.monotonic_ns() // 1_000_000_000 + monotonic_start + TZ_OFFSET)

def update_NTP():
	seg_print(" UPDATE NTP ")
	wifi.radio.enabled = True
	connect_wifi(verbose=True)
	rtc.RTC().datetime = get_ntp_time(socket_pool)
	time.sleep(0.1)
	wifi.radio.enabled = False

if time.localtime().tm_year < 2021:
	update_NTP()

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

	display[0].print(f"{now.tm_hour:02d}{sep}{now.tm_min:02d}{sep}")
	display[1].print(f"{now.tm_sec:02d} {day[0]}")
	display[2].print(f"{day[1]}{day[2]}{now.tm_mday:02d}")
	seg_show()

	return now

####################################################################
# setup loop variables and parameters
####################################################################

defcon = 0
next_sync = time.monotonic() + SYNC_DELAY

####################################################################
# loop-dee-loop
####################################################################

for x in range(2):
	for segment in display:
		segment.fill(1)
		time.sleep(0.1)
		segment.show()
	for segment in display:
		segment.fill(0)
		time.sleep(0.1)
		segment.show()

index = 0
while True:
	# scroll
	now = update_time(index // 4 % 2 == 0)
	defcon = now.tm_sec // 10

	if now.tm_sec % 2 == 0:
		status.fill(colors[now.tm_sec % 5])
	else:
		status.fill(0)

	pixels.fill(0)
	for x in range(5):
		if x < defcon:
			pixels[4 - x] = colors[x]
		else:
			pixels[4 - x] = 0
	pixels.show()

	index += 1
	time.sleep(SPEED_DELAY)
	
	if but2.value or time.monotonic() > next_sync:
		update_NTP()

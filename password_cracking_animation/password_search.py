# SPDX-FileCopyrightText: Copyright 2023 Neradoc, https://neradoc.me
# SPDX-License-Identifier: MIT
"""
Pick random "passwords", scroll random characters, decode the password.
- The probability of a character being decoded in each loop is a function
  of TIME_DECODING and other parameters to get a reasonnable average time.
- Increases the probability of decoding the longer it goes above the target time.
- Button A decodes a character.
- Button B resets the decoding session (not the password).
"""
import board
import busio
import keypad
import os
import random
import time
import wifi

import adafruit_ht16k33.segments
import neopixel

"""
When the scrolling character matches a password character, reveal.
If False, just scrolls letters, pretty pointless.
"""
FIND_MODE = True
"""Progressively increase the probabilities of instant decoding for a character"""
ACCELERATE_WHEN_NOT_FOUND = True
"""Loop sleep."""
SPEED_DELAY = 0.01
"""Target time of decoding."""
TIME_DECODING = 30
"""
If no word list files are available, use the list of builtins.
If set to False, use completely a random word instead.
"""
USE_BUILTINS = True

####################################################################
# setup wifi
####################################################################

wifi.radio.enabled = False

####################################################################
# setup buttons
####################################################################

buttons = keypad.Keys(
	(board.IO38, board.IO33, board.IO6, board.IO5),
	value_when_pressed = True
)
BUT1, BUT2, BUTA, BUTB = range(4)

####################################################################
# setup displays and blinkies
####################################################################

i2c = busio.I2C(sda=board.SDA, scl=board.SCL, frequency=400_000)
display = adafruit_ht16k33.segments.Seg14x4(i2c, address=(0x70, 0x72, 0x74))

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

for x in "*.*.*.*.*.*.*.*.*.*.*.*.*.*.*.*.            ":
	display.print(x)
	time.sleep(0.01)
display.fill(0)

####################################################################
# setup words and passwords
####################################################################

vowels = "AEIOUY"
conson = "ZQWSXCDFRVBGTHNJKLPM"
lower_letters = "azertyuiopmlkjhgfdsqwxcvbn"
upper_letters = vowels + conson
digits = "0123456789"
symbols = "@#*$&+-=/:,?!"
charas = symbols + upper_letters + digits + lower_letters

passsymbols = "0123456789" "@*$+-="

import builtins
# get default passwords from builtins
# I don't think we can capture help("modules"), that's a shame
default_passwords = [x[:12].upper() for x in dir(builtins) if x[0] != "_"]


def pass_from_keywords():
	# pick words until they don't fit
	word = random.choice(default_passwords)
	words = [word]
	full_size = len(word)
	while len(words) < 3 and full_size < 12:
		word = random.choice(default_passwords)
		if len(word) + full_size > 12:
			break
		words.append(word)
		full_size += len(word)
	# add random characters
	while full_size < 12:
		words.append(random.choice(passsymbols))
		full_size += 1
	# stick words
	words.sort(key=lambda x: random.random())
	return "".join(words)


def make_password():
	passe = [ random.choice(conson) ]
	for x in range(11):
		if random.random() < 0.2: # 20% chances of number
			passe.append(random.choice(digits))
		elif passe[-1] in conson:
			passe.append(random.choice(vowels))
		elif passe[-1] in vowels:
			passe.append(random.choice(conson))
		else:
			if random.random() > 0.5:
				passe.append(random.choice(conson))
			else:
				passe.append(random.choice(vowels))
	return passe

# get the word files and organize them by size
password_files = [["",0]] * 14
password_sizes = set()
for x in range(14):
	filename = f"words/words-{x}.txt"
	try:
		n_passwords = os.stat(filename)[6] // (x+1) # is gonna fail if not exists
		password_files[x] = [filename, n_passwords]
		password_sizes.add(x)
	except OSError as err:
		password_files[x] = ["", 0]

def password_from_dict():
	# make sizes
	full_size = 0
	words = []
	# pick up to 3 random words that fit the size
	while full_size < 12:
		# pick a random word that fits in the remaining space
		size = random.choice([
			x for x in password_sizes
			if x <= 12 - full_size
		])
		# get the word from the file
		with open(password_files[size][0],"r") as fp:
			pos_word = random.randint(0,password_files[size][1])
			fp.seek( pos_word * ( size + 1 ) )
			word = fp.read(size).strip().upper()
		# append and count the word
		words.append(word)
		full_size += len(word)
		# stop when there's no space left or we already picked 3 words
		if (12 - full_size) < min(password_sizes): break
		if len(words) == 3: break
	# add random characters
	while full_size < 12:
		words.append(random.choice(passsymbols))
		full_size += 1
	# stick words
	words.sort(key=lambda x: random.random())
	return "".join(words)

def get_password():
	if password_sizes:
		# use files to get a password
		password = password_from_dict()
	elif USE_BUILTINS:
		# use builtin names for passwords
		password = pass_from_keywords()
	else:
		# no files, generate random password
		password = make_password()
	return [x for x in password]

####################################################################
# setup loop variables and parameters
####################################################################

# chances_decoding * num_charas * TIME_DECODING / SPEED_DELAY = 1
CHANCES_DECODING = len(charas) * SPEED_DELAY / (12 * TIME_DECODING)
average_time = 0

print("CHANCES_DECODING", CHANCES_DECODING)

# first password
# password = [x for x in "MOUTARDE 007"]
password = get_password()

chances_decoding = CHANCES_DECODING
screen_texte = [random.choice(charas) for x in range(12)]
ring = 0
not_decoded = set(range(12))
defcon = 0
start_time = time.monotonic_ns()

####################################################################
# loop-dee-loop
####################################################################

while True:
	current_time = time.monotonic_ns()
	took = (current_time - start_time) // 1000 // 1000 / 1000
	precent_time = (TIME_DECODING - took) / TIME_DECODING

	# scroll
	ring = (ring + 1) % 12
	screen_texte[ring] = random.choice(charas)
	#
	buff = ["."] * 12
	still_coded = False

	for char in range(12):
		# reveal password characters that match the scrolling text
		if FIND_MODE:
			if random.random() < chances_decoding:
				if char in not_decoded:
					not_decoded.remove(char)
					# a character can only match once
					screen_texte[(ring+char)%12] = "*"
					# force update the segment in case it's all decoded
					still_coded |= True
					# reset the autowin
					chances_decoding = CHANCES_DECODING

		# display scrolling or decoded character
		if char in not_decoded:
			still_coded |= True
			buff[char] = screen_texte[(ring+char)%12]
		else:
			buff[char] = password[char]

	# send I2C only if it's not finished
	if still_coded:
		display.print("".join(buff))

	################################################################
	# buttons
	while event := buttons.events.get():
		if event.pressed and event.key_number == BUTA:
			# decode one character
			num = random.choice(list(not_decoded))
			not_decoded.remove(num)
			screen_texte[(ring+num)%12] = "*"
			print("Decode", num)
		if event.pressed and event.key_number == BUTB:
			# reset
			not_decoded = set(range(12))
			print("Recode")

	################################################################
	# password decoded
	if len(not_decoded) == 0:
		end_time = time.monotonic_ns()
		took = (end_time - start_time) // 1000 // 1000 / 1000
		#
		if average_time == 0:
			average_time = took
		else:
			average_time = (average_time + 3 * took) / 4
		#
		print("The password was:","".join(password),f"decoded in {took:.3f} s")
		print(f"Average: {average_time}s")
		#
		for x in range(4):
			pixels.brightness = 0.01
			pixels.show()
			time.sleep(0.25)
			pixels.brightness = 1.0
			pixels.show()
			time.sleep(0.25)
		not_decoded = set(range(12))

		# new password
		password = get_password()
		chances_decoding = CHANCES_DECODING
		button_speedup = False

		start_time = time.monotonic_ns()
	else:
		############################################################
		
		# adapt the chances of decoding to make it not too long
		if ACCELERATE_WHEN_NOT_FOUND:
			if took > TIME_DECODING:
				chances_decoding += 0.001

	################################################################
	# display the progression of decoding via defcon LEDs
	dd = len(not_decoded) / 2
	if defcon != dd:
		defcon = dd
		pixels.fill(0)
		for x in range(5):
			if x >= defcon - 1:
				pixels[x] = colors[x]
		pixels.show()

	time.sleep(SPEED_DELAY)

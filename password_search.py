import board
from digitalio import DigitalInOut, Pull
import neopixel
import random
import time

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

i2c = board.I2C()
i2c.try_lock()
scan = [hex(x) for x in i2c.scan()]
print(scan)
i2c.unlock()

import adafruit_ht16k33.segments

display = [
	adafruit_ht16k33.segments.Seg14x4(i2c, address=0x70),
	adafruit_ht16k33.segments.Seg14x4(i2c, address=0x72),
	adafruit_ht16k33.segments.Seg14x4(i2c, address=0x74),
]

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

for x in range(2):
	for segment in display:
		segment.fill(1)
		time.sleep(0.1)
	for segment in display:
		segment.fill(0)
		time.sleep(0.1)

vowels = "AEIOUY"
conson = "ZQWSXCDFRVBGTHNJKLPM"
lower_letters = "azertyuiopmlkjhgfdsqwxcvbn"
upper_letters = vowels + conson
digits = "0123456789"
charas = "." "@#*$&+-=/:,?! " + upper_letters + digits + lower_letters

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

"""
REVEAL_REAL
	single real password, reveal one letter at each round
FIND_RANDOM
	put the scrolling character at the random position into the password and reveal
FIND_REAL
	single real password, reveal when the scrolling character matches the password
FIND_REAL_RANDOM
	FIND_REAL but when the password is decoded, generate new random password
"""
mode = "FIND_REAL_RANDOM"
CHANCES_DECODING = 0.4

# fixed password
password = [x for x in "MOUTARDE 007"]
if "RANDOM" in mode:
	password = make_password()
#
screen_texte = [random.choice(charas) for x in range(12)]
not_decoded = set(range(12))

while True:
	for x in range(6):
		# scroll
		screen_texte = screen_texte[1:] + [random.choice(charas)]
		#
		for index,segment in enumerate(display):
			for char in range(4):
				pos = index*4+char

				if "FIND_REAL" in mode:
					if screen_texte[pos] == password[pos]\
						and random.random() < CHANCES_DECODING:
						if pos in not_decoded:
							not_decoded.remove(pos)
							screen_texte[pos] = "*"

				if pos in not_decoded:
					segment[char] = screen_texte[pos]
				else:
					segment[char] = password[pos]

		# buttons do nothing for now
		for btn in buttons:
			if btn[0].value:
				if btn[0] == but2:
					num = random.choice(list(not_decoded))
					not_decoded.remove(num)
					while but2.value:
						time.sleep(0.01)
				print(btn[1])
		time.sleep(0.05)

	if len(not_decoded) == 0:
		print("The password was:","".join(password))
		for x in range(4):
			pixels.brightness = 0.01
			pixels.show()
			time.sleep(0.25)
			pixels.brightness = 1.0
			pixels.show()
			time.sleep(0.25)
		not_decoded = set(range(12))
		if mode == "FIND_REAL_RANDOM":
			password = make_password()
	else:
		if "FIND_REAL" not in mode:
			num = random.choice(list(not_decoded))
			not_decoded.remove(num)
			if mode == "FIND_RANDOM":
				# find random password:
				password[num] = screen_texte[num]

	defcon = len(not_decoded) / 2
	pixels.fill(0)
	for x in range(5):
		if x >= defcon - 1:
			pixels[x] = colors[x]
	pixels.show()

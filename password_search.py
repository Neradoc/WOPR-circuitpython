import board
import busio
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

# i2c = board.I2C()
i2c = busio.I2C(sda=board.SDA, scl=board.SCL, frequency=400_000)
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
FIND:
	when thea scrolling character matches a password character, reveal
RANDOM:
	randomly generate then password when revealed
AUTO:
	automatic reveal of a character from the password on every outer loop
"""
mode = ["FIND", "RANDOM"]
SPEED_DELAY = 0.01
FREQUENCY_DECODING = 1 # Hz
CHANCES_DECODING = len(charas) * FREQUENCY_DECODING * SPEED_DELAY / 4

print("CHANCES_DECODING",CHANCES_DECODING)

# fixed password
password = [x for x in "MOUTARDE 007"]
if "RANDOM" in mode:
	password = make_password()
#
screen_texte = [random.choice(charas) for x in range(12)]
ring = 0
not_decoded = set(range(12))
defcon = 0
start_time = time.monotonic_ns()

while True:
	# scroll
	ring = (ring + 1) % 12
	screen_texte[ring] = random.choice(charas)
	#
	buff = ["."] * 12
	for index,segment in enumerate(display):
		still_coded = False

		for char in range(4):
			pos = index*4+char

			# reveal password characters that match the scrolling text
			if "FIND" in mode:
				if screen_texte[(ring+pos)%12] == password[pos]\
					and random.random() < CHANCES_DECODING:
					if pos in not_decoded:
						not_decoded.remove(pos)
						# a character can only match once
						screen_texte[(ring+pos)%12] = "*"
						# force update the segment in case it's all decoded
						still_coded |= True

			# display scrolling or decoded character
			if pos in not_decoded:
				still_coded |= True
				buff[pos] = screen_texte[(ring+pos)%12]
			else:
				buff[pos] = password[pos]

		# send I2C only once per segment, if it's not finished
		if still_coded:
			segment.print("".join(buff[index*4:index*4+4]))

	# buttons
	for btn in buttons:
		if btn[0].value:
			# button 2 speeds up decoding
			if btn[0] == but2:
				num = random.choice(list(not_decoded))
				not_decoded.remove(num)
				screen_texte[(ring+num)%12] = "*"
				while but2.value:
					time.sleep(0.01)
			# button 1 resets
			if btn[0] == but1:
				not_decoded = set(range(12))
				while but1.value:
					time.sleep(0.01)
			print(btn[1])

	# password decoded
	if len(not_decoded) == 0:
		end_time = time.monotonic_ns()
		took = (end_time - start_time) // 1000 // 1000 / 1000
		print("The password was:","".join(password),f"decoded in {took:.3f} s")
		#
		for x in range(4):
			pixels.brightness = 0.01
			pixels.show()
			time.sleep(0.25)
			pixels.brightness = 1.0
			pixels.show()
			time.sleep(0.25)
		not_decoded = set(range(12))

		if "RANDOM" in mode:
			password = make_password()

		start_time = time.monotonic_ns()
	else:
		# decode a random character
		if "AUTO" in mode:
			num = random.choice(list(not_decoded))
			not_decoded.remove(num)

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

import os
import sys
if "LEAVE_USB_ENABLED" in os.listdir():
	# keep the drive enabled if there's a file, acting as flag
	print("Leave USB enabled")
elif sys.implementation.version >= (7,0,0):
	# disable some USB devices
	import usb_midi
	usb_midi.disable()
	import usb_hid
	usb_hid.disable()

	import board
	from digitalio import DigitalInOut, Pull

	butA = DigitalInOut(board.IO38)
	butA.switch_to_input(Pull.DOWN)
	butB = DigitalInOut(board.IO33)
	butB.switch_to_input(Pull.DOWN)

	# disable all USB unless one of the back buttons is pressed
	if not (butA.value or butB.value):
		import storage
		storage.disable_usb_drive()
		print("Boot without USB drive or CDC")
		import usb_cdc
		usb_cdc.enable(console=False, data=False)
	else:
		print("Boot with USB drive and Console")
		import usb_cdc
		usb_cdc.enable(console=True, data=False)
else:
	print("Boot in 6.x, no dynamic USB")

# give it a cute name
if sys.implementation.version >= (8,0,0):
	import supervisor
	supervisor.set_usb_identification(manufacturer="NORAD", product="WOPR")

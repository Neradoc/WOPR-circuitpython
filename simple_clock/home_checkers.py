from adafruit_datetime import datetime
from adafruit_datetime import timedelta
from secrets import secrets

NET_TEST = secrets["NET_TEST"]
requests = None

def check_nettest():
	ref_delta = timedelta(days=1)
	with requests.get(NET_TEST) as response:
		data = response.json()
		timing = data[0]["date"]
		last_time = datetime.fromisoformat(timing)
		delta = datetime.now() - last_time
		if delta > ref_delta:
			return (False, "nettest", "CHECK RASPI TWO")
	return (True, "nettest", "OK")

def check_demo():
	return (False, "demo", "CHECK RASPI DEMO")

def do_checks(reqs):
	global requests
	requests = reqs
	if requests:
		return [
			check_nettest(),
			# check_demo(),
		]
	return []

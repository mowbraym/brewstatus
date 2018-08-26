# Note this code is heavily based on the Thingspeak plugin by Atle Ravndal
# and I acknowledge his efforts have made the creation of this plugin possible
#
# TODO
#	* Check result of request() call and react

from modules import cbpi
from thread import start_new_thread
import logging
import requests
import datetime

DEBUG = False
drop_first = None

# Parameters
brewstatus_comment = None
brewstatus_url = None

def log(s):
    if DEBUG:
        s = "brewstat.us: " + s
        cbpi.app.logger.info(s)

@cbpi.initalizer(order=9000)
def init(cbpi):
    cbpi.app.logger.info("brewstat.us plugin Initialize")
    log("Brewstat.us params")
    global brewstatus_comment
    global brewstatus_url
    brewstatus_comment = cbpi.get_config_parameter("brewstatus_comment", None)
    log("Brewstat.us brewstatus_comment %s" % brewstatus_comment)
    brewstatus_url = cbpi.get_config_parameter("brewstatus_url", None)
    log("Brewstat.us brewstatus_url %s" % brewstatus_url)
    if brewstatus_comment is None:
	log("Init brewstat.us config Comment")
	try:
# TODO: is param2 a default value?
	    cbpi.add_config_parameter("brewstatus_comment", "", "text", "Brewstat.us comment")
	except:
	    cbpi.notify("Brewstat.us Error", "Unable to update config parameter", type="danger")
    if brewstatus_url is None:
	log("Init brewstat.us config url")
	try:
# TODO: is param2 a default value?
	    cbpi.add_config_parameter("brewstatus_url", "", "text", "Brewstat.us url")
	except:
	    cbpi.notify("Brewstat.us Error", "Unable to update config parameter", type="danger")
    log("Brewstat.us params ends")

# interval=900 is 900 seconds, 15 minutes, same as the Tilt Android App logs.
@cbpi.backgroundtask(key="brewstatus_task", interval=900)
def brewstatus_background_task(api):
    log("brewstat.us background task")
    global drop_first
    if drop_first is None:
        drop_first = False
        return False

    if brewstatus_url is None:
        return False

    now = datetime.datetime.now()
    for key, value in cbpi.cache.get("sensors").iteritems():
	log("key %s value.name %s value.instance.last_value %s" % (key, value.name, value.instance.last_value))
#
# TODO: IMPORTANT - Temp sensor must be defined preceeding Gravity sensor and 
#		    each Tilt must be defined as a pair without another Tilt
#		    defined between them, e.g.
#			RED Temperature
#			RED Gravity
#			PINK Temperature
#			PINK Gravity
#
	if (value.type == "TiltHydrometer"):
	    if (value.instance.sensorType == "Temperature"):
# A Tilt Temperature device is the first of the Tilt pair of sensors so
#    reset the data block to empty
		data = {}
# generate timestamp in "Excel" format
		data['Timepoint'] = now.toordinal() - 693594 + (60*60*now.hour + 60*now.minute + now.second)/float(24*60*60)
		data['Color'] = value.instance.color
		data['Temp'] = value.instance.last_value
# brewstat.us expects *F so convert back if we use C
		if (cbpi.get_config_parameter("unit",None) == "C"):
		    data['Temp'] = value.instance.last_value * 1.8 + 32
	    if (value.instance.sensorType == "Gravity"):
		data['SG'] = value.instance.last_value
		data['Comment'] = cbpi.get_config_parameter("brewstatus_comment", None)
		log("Data %s" % data)
		headers = {'content-type': '"application/x-www-form-urlencoded; charset=utf-8"'}
		url = cbpi.get_config_parameter("brewstatus_url", None)
		r = requests.post(url, headers=headers, data=data)
		log("Result %s" % r.text)
    log("brewstat.us done")

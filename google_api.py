import gdata.calendar
import gdata.calendar.service
import atom.service

import time
import urllib
import socket

import version
import logger
import consts

from ErminigGoogleError import *
from ErminigError import *

gd_client = gdata.calendar.service.CalendarService()
gd_client.source="Erminig ng %s" % (version.erminig_version)


def run_google_action(func, *args, **kwargs):
	# XXX Configurable...
	maxattempts = 4
	res = None
	for i in range(0,maxattempts):
		try:
			res = func(*args, **kwargs)
			break
		except gdata.service.RequestError, e:
			if i > maxattempts:
				logger.append("Maximum number of attempts to for a Google action reached; skipping entry")
				return None
			if e[0]['status'] == 302:
				logger.append("** Received spurious redirect - retrying in 2 seconds (attempt %s of %s)" % (i+1, maxattempts))
				time.sleep(2)
			elif e[0]['status'] == 401:
				logger.append("Invalid username or password!")
				logger.append(repr(e))
				raise ErminigGoogleError(e)
				return None
			elif e[0]['status'] == 403:
				logger.append("You don't have access to this calendar. Has it been deleted?")
				logger.append(repr(e))
				raise ErminigGoogleError(e)
				return None
			else:
				logger.append(repr(e))
				# XXX Temporary
				return None

	return res


def switch_account(credentials):
	gd_client.email = credentials[0]
	gd_client.password = credentials[1]
	try:
		gd_client.ProgrammaticLogin()
	except gdata.service.BadAuthentication, e:
		logger.append("Invalid username or password!")
		logger.append(repr(e))
		raise ErminigError(consts.INVALID_USER_PWD)
		return False

	except gdata.service.CaptchaRequired, e:
		logger.append(repr(e))
		return False
	except socket.gaierror, e:
		logger.append("Unable to connect! Check internet connection")
		raise ErminigError(consts.NO_INET_CONNECTION)
		return False

	return True


def get_all_calendars():
	cals = []

	feed = run_google_action(gd_client.GetAllCalendarsFeed)
	for i,cal in enumerate(feed.entry):
		title = cal.title.text
		# Get only the last part of the ID (and substitute the %'s):
		logger.append("raw calendar name:")
		logger.append(cal.id.text)
		id = urllib.unquote((cal.id.text.rpartition("/"))[2])
		cals.append((id, title))

	return cals

def create_new_calendar(cal_name):
	calendar = gdata.calendar.CalendarListEntry()
	calendar.title = atom.Title(text=cal_name)
	calendar.hidden = gdata.calendar.Hidden(value='false')
	calendar.selected = gdata.calendar.Selected(value='true')
	new_calendar = run_google_action(gd_client.InsertCalendar, \
			new_calendar=calendar)

	# XXX More error checking...
	id = urllib.unquote((new_calendar.id.text.rpartition("/"))[2])
	return id

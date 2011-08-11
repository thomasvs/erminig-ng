#!/usr/bin/python2.5
#
# Erminig-NG (A two-way synchronization tool for Google-Calendar and
#              "Fremantle-Calendar", the calendar of Maemo 5)
# 
# Copyright (c) 2010 Pascal Jermini <lorelei@garage.maemo.org>
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# version 2.1, as published by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to:
# 
#   Free Software Foundation, Inc.
#   51 Franklin Street, Fifth Floor,
#   Boston, MA 02110-1301 USA
# 


# !!!!!! All times must be handled in UTC !!!!!!

import random
import urllib
import time
import sys
import string
import os.path
import datetime

import gtk
import logger

import gdata.calendar
import gdata.calendar.service
import atom.service

import google_api

from Event import Event
import erminig_conf
import cwrapper
import iso8601
import dblayer

import error_win
from ErminigGoogleError import *

import re

currentTime = 0;
googleEventsTouched = []
localEventsTouched = []

# pre-compile regexp:
recur_start = re.compile("DTSTART(.*)", re.MULTILINE)
recur_end = re.compile("DTEND(.*)", re.MULTILINE)
recur_rrule = re.compile("RRULE:(.*)", re.MULTILINE)

def update_progress(progress, value):
	if not progress == None:
		progress.set_fraction(value)
		while gtk.events_pending():
			gtk.main_iteration()


def eventExistsLocally(id):
	cur = dblayer.run("SELECT lid FROM Xrefs WHERE gid=?", (id,))
	if cur:
		return dblayer.getValue(cur, 'lid')
	else:
		return None

def insertGoogleEventLocally(event, cid, pid):
	global googleEventsTouched
	# if event has already been touched, then skip it
	if event.get_id() in googleEventsTouched:
		return

	googleEventsTouched.append(event.get_id())
	# check if event doesn't exist already (if yes, just update it)
	localID = eventExistsLocally(event.get_id())
	if localID:	
		updateGoogleEventLocally(event, cid, localID)
	else:
		insertNewGoogleEventLocally(event, cid, pid)

def updateGoogleEventLocally(event, cid, localID):
	global localEventsTouched

	localEventsTouched.append(localID)
	# XXX Check for failed updates!
	cwrapper.updateLocalEvent(cid, event, localID)

def insertNewGoogleEventLocally(event, cid, pid):
	global localEventsTouched

	lastId = cwrapper.addLocalCalendarEntry(cid, event)

	if lastId == None:
		logger.append("Error when inserting event locally")
		return

	dblayer.run("INSERT INTO Xrefs (pid, lid, gid) VALUES (?, ?, ?)", (pid, lastId, event.get_id()))
	dblayer.commit()
	localEventsTouched.append(lastId)

def isEventFullDay(date):
	if (string.find(date, "T") == -1):
		return 1
	else:
		return 0

# iso8601 forms:
#     YYYY (eg 1997)
#     YYYY-MM (eg 1997-07)
#     YYYY-MM-DD (eg 1997-07-16)
#     YYYY-MM-DDThh:mmTZD (eg 1997-07-16T19:20+01:00) -> 17 or 21 chars
#     YYYY-MM-DDThh:mm:ssTZD (eg 1997-07-16T19:20:30+01:00) -> 20 or 24 chars
#     YYYY-MM-DDThh:mm:ss.sTZD (eg 1997-07-16T19:20:30.45+01:00) -> 22 or 26
# with TZD: Z or +hh:mm or -hh:mm)

def iso8601ToTimestamp(date):
	"""
	@type date: str
	"""
	# FIXME: Google passes dtstart like 2008-12-10T00:00:00
	if not date[-6] in ('+', '-') and not date.endswith('Z'):
		date += 'Z'

	return int(iso8601.parse(date))

def timestampToIso8601(date):
	d = iso8601.tostring(date)
	if (len(d) == 24 or string.find(d, "Z") == -1):
		# YYYY-MM-DDThh:mm:ss with +/-hh:mm
		# or any other with +/-hh:mm
		return d

	if (len(d) == 20):
		# YYYY-MM-DDThh:mm:ssZ
		return string.replace(d, "Z", ".000Z")

	return string.replace(d, "Z", ":00.000Z")

def removeCancelledEventLocally(cid, gid):
	# get local ID from googleId:
	lid = getLocalIdFromGoogleId(gid)
	if not lid:
		return

	logger.append("Removing local event (Deleted from Google -> %s)" % (gid))

	# purge Calendar entry:
	cwrapper.removeCancelledEventLocally(cid, lid)

	# purge entry in correspondance table:
	dblayer.run("DELETE FROM Xrefs WHERE lid=?", (lid, ))
	dblayer.commit()

def convert_date(d):
	if len(d) == 8:
		return d[:4] + "-" + d[4:6] + "-" + d[6:]
	else:
		return d[:4] + "-" + d[4:6] + "-" + d[6:11] + ":" + d[11:13] + \
			":" + d[13:]

def process_recurrence(rstring):
	logger.append(rstring)
	rrule = recur_rrule.search(rstring)
	if not rrule:
		return None

	rrule_array = rrule.group(1).split(";")
	rrule_final_array = []
	for rule in rrule_array:
		if not rule.startswith("DTEND") or not rule.startswith("DTSTART"):
			rrule_final_array.append(rule)

	recurrence = {}
	recurrence['rrule'] = ";".join(rrule_final_array)

	start = recur_start.search(rstring).group(1)
	end = recur_end.search(rstring).group(1)

	start_str = ""
	end_str = ""

	if start[0] == ":":
		start_str = start[1:]
	else:
		start_components = start[1:].split(":")
		start_str = start_components[1]
		# Shall we do something w/ VTIMEZONES?

	if end[0] == ":":
		end_str = end[1:]
	else:
		end_components = end[1:].split(":")
		end_str = end_components[1]

	recurrence['dtstart'] = convert_date(start_str)
	recurrence['dtend'] = convert_date(end_str)

	return recurrence
	
def getNewEventsFromGoogle(pid, localSource, remoteSource, lastSync, \
		                        progress):
	query = gdata.calendar.service.CalendarEventQuery(remoteSource, \
			'private', 'composite', None, {"ctz":"utc"})
	query.updated_min = timestampToIso8601(lastSync)
	query.updated_max = timestampToIso8601(int(time.time()))
	query.max_results = "100000"

	feed = None
	try:
		feed = google_api.run_google_action(google_api.gd_client.CalendarQuery, query)
	except ErminigGoogleError, e:
		error_win.display(e.title(), e.description())
		return

	if not feed:
		return

	feed_size = len(feed.entry)
	if feed_size == 0:
		return

	fraction = 1.0/feed_size
	current_fraction = 0.0;
	
	for i, e in enumerate(feed.entry):
		current_fraction = current_fraction + fraction
		update_progress(progress, current_fraction)

		title = e.title.text
		rstring = ""
		start_time = ""
		end_time = ""
		full_day = False
		alarm = -1
		if e.recurrence <> None:
			recurrence = process_recurrence(e.recurrence.text)
			if not recurrence:
				logger.append("Recurrence could not be parsed for")
				logger.append(title)
				logger.append("Skipping....")
				continue

			rstring = recurrence['rrule']
			start_time = iso8601ToTimestamp(recurrence['dtstart'])
			end_time = iso8601ToTimestamp(recurrence['dtend'])
			fullday = isEventFullDay(recurrence['dtstart'])

			if len(e.reminder) > 0:
				alarm = int(e.reminder[0].minutes)
		else:
			start_time = iso8601ToTimestamp(e.when[0].start_time)
			end_time = iso8601ToTimestamp(e.when[0].end_time)
			# An event is full-day if it doesn't have any
			# timing event (only date)
			fullday = isEventFullDay(e.when[0].start_time)

			if len(e.when[0].reminder) > 0:
				alarm = int(e.when[0].reminder[0].minutes)

		where = e.where[0].value_string
		description =  e.content.text
		id = urllib.unquote((e.id.text.rpartition("/"))[2])
		cdate = time.time()

		if (fullday == 1):
			start_time += time.timezone
			end_time += time.timezone
			if ((start_time - end_time) == 0):
				end_time = start_time + 24*3600

		event = Event(title, where, description, \
				start_time, end_time, fullday, id,\
				cdate, rrule=rstring, alarm=alarm)
		if e.event_status.value == "CANCELED":
			# remove event locally:
			removeCancelledEventLocally(localSource, id)
		else:
			insertGoogleEventLocally(event, int(localSource), pid)

def queryNewLocalEvents(lastSync, cid):
	global currentTime
	global localEventsTouched
	newEventsIDs = cwrapper.queryNewLocalEvents(cid, lastSync)
	if not newEventsIDs:
		return None

	ids_list = newEventsIDs.split(":")
	evt_list = []
	for evtId in ids_list:
		if evtId in localEventsTouched or evtId == None:
			continue

		evt = cwrapper.getNewEventById(cid, evtId, currentTime)
		if evt:
			evt_list.append(evt)

	return evt_list

def create_rrule(start_time, end_time, rrule):
	if len(start_time) == 10:
		# full-day; strip away symbols
		dt_start = ";VALUE=DATE:" + \
				filter(lambda c: c not in "-", start_time)
		dt_end = ";VALUE=DATE:" + \
				filter(lambda c: c not in "-", end_time)
	else:
		# strip away symbols
		dt_start = ":" + filter(lambda c: c not in "-:", start_time)
		dt_end = ":" + filter(lambda c: c not in "-:", end_time)

	rrules = rrule.split(";")
	rrules_t = ""
	for r in rrules:
		if r.startswith("UNTIL="):
			t_pos = r.find("T", 7)
			rrules_t = rrules_t + r[:t_pos] + ";"
		else:
			rrules_t = rrules_t + r + ";"

	rec_data = "DTSTART" + dt_start + "\r\n"
	rec_data = rec_data + "DTEND" + dt_end + "\r\n"
	rec_data = rec_data + "RRULE:" + rrules_t.strip(";") + "\r\n"

	return rec_data

def createNewGoogleEvent(evt, googleid, pid):

	start_time = timestampToIso8601(evt.get_start())
	end_time = timestampToIso8601(evt.get_end())

	# if it's a full-day event, then we can strip the start/end times:
	if evt.get_fullday() == 1:
		start_time = timestampToIso8601(int(evt.get_start())+evt.get_tzOffset())
		end_time = timestampToIso8601(int(evt.get_end())+evt.get_tzOffset())
		start_time = start_time[0:10]
		end_time = end_time[0:10]

		# Add artificially one day:
		td = datetime.timedelta(1)
		time_dt = datetime.datetime.strptime(end_time, "%Y-%m-%d")
		time_dt = time_dt + td
		end_time = time_dt.strftime("%Y-%m-%d")

	event = gdata.calendar.CalendarEventEntry()
	event.title = atom.Title(text=evt.get_title())
	event.content = atom.Content(text=evt.get_description())
	event.where.append(gdata.calendar.Where(value_string=evt.get_where()))
	# Differentiate for recurrence:
	if evt.get_rrule() <> "":
		rec_data = create_rrule(start_time, end_time, evt.get_rrule())
		event.recurrence = gdata.calendar.Recurrence(text=rec_data)
		event.reminder.append(gdata.calendar.Reminder(minutes=evt.get_alarm()));
	else:
		event.when.append(gdata.calendar.When(start_time=start_time, end_time=end_time))
		event.when[0].reminder.append(gdata.calendar.Reminder(minutes=evt.get_alarm()));

	new_event = None
	try:
		new_event = google_api.run_google_action(google_api.gd_client.InsertEvent, event, urllib.quote('/calendar/feeds/' + googleid + '/private/full'))
	except ErminigGoogleError, e:
		error_win.display(e.title(), e.description())
		return

	if new_event == None:
		logger.append("Got a None event....skipping")
		return

	gid = (new_event.id.text.rpartition("/"))[2]
	# insert correspondance table entry:
	dblayer.run("INSERT INTO Xrefs (pid, lid, gid) VALUES (?, ?, ?)", \
			(pid, evt.get_id(), gid))
	dblayer.commit()

def getNewEventsFromLocal(pid, localSource, remoteSource, lastSync, progress):
	# Those are new events to create in Google:
	evts = queryNewLocalEvents(lastSync, localSource)
	if not evts:
		update_progress(progress, 1.0/3)
		return

	progress_inc = 1.0/3.0/len(evts)
	progress_val = 0.0
	for e in evts:
		progress_val = progress_val + progress_inc
		update_progress(progress, progress_val)

		event = Event(e[3], e[4], e[5], e[1], e[2], e[6], \
				e[0], 0, rrule=e[8], alarm=e[9])
		event.set_tzOffset(e[7])
		gid = createNewGoogleEvent(event, remoteSource, pid)

def queryUpdatedLocalEvents(lastSync, cid):
	global currentTime
	global localEventsTouched
	updatedEventsIDs = cwrapper.queryUpdatedLocalEvents(cid, lastSync)

	if not updatedEventsIDs:
		return None

	ids_list = updatedEventsIDs.split(":")
	evt_list = []
	for evtId in ids_list:
		if evtId in localEventsTouched or evtId == None:
			continue
		evt = cwrapper.getUpdatedEventById(cid, evtId, currentTime)
		if evt:
			evt_list.append(evt)

	return evt_list

def getGoogleIdFromLocalId(lid):
	cur = dblayer.run("SELECT gid FROM Xrefs WHERE lid=?", (lid,))
	if cur:
		return dblayer.getValue(cur, 'gid')
	else:
		return None
	
def getLocalIdFromGoogleId(gid):
	cur = dblayer.run("SELECT lid FROM Xrefs WHERE gid=?", (gid,))
	if cur:
		return dblayer.getValue(cur, 'lid')
	else:
		return None

def updateGoogleEvent(evt, googleid, pid):
	"""
	@type  evt:      L{Event.Event}
	@param googleid: name of calendar ?
	@type  googleid: unicode
	@type  pid:      int
	"""
	# get Googleid of event:
	gid = getGoogleIdFromLocalId(evt.get_id())
	if not gid:
		return

	event = None
	try:
		event = google_api.run_google_action(google_api.gd_client.GetCalendarEventEntry, urllib.quote("/calendar/feeds/" + googleid + "/private/full/" + gid))
	except ErminigGoogleError, e:
		error_win.display(e.title(), e.description())
		return

	if event == None:
		logger.append("Unable to get event to update!")
		return

	start_time = timestampToIso8601(evt.get_start())
	end_time = timestampToIso8601(evt.get_end())

	# if it's a full-day event, then we can strip the start/end dates:
	if evt.get_fullday() == 1:
		start_time = timestampToIso8601(int(evt.get_start())+evt.get_tzOffset())
		end_time = timestampToIso8601(int(evt.get_end())+evt.get_tzOffset())
		start_time = start_time[0:10]
		end_time = end_time[0:10]

	event.title = atom.Title(text=evt.get_title())
	event.content = atom.Content(text=evt.get_description())
	event.where[0] = gdata.calendar.Where(value_string=evt.get_where())
	# Differentiate for recurrence:
	if evt.get_rrule() <> "":
		rec_data = create_rrule(start_time, end_time, evt.get_rrule())
		event.recurrence = gdata.calendar.Recurrence(text=rec_data)
		if len(event.reminder) > 0:
			event.reminder[0].minutes = evt.get_alarm()
		else:
			event.reminder.append(gdata.calendar.Reminder(minutes=evt.get_alarm()));
	else:
		event.when[0] = gdata.calendar.When(start_time=start_time, end_time=end_time)
		if len(event.when[0].reminder) > 0:
			event.when[0].reminder[0].minutes = evt.get_alarm()
		else:
			event.when[0].reminder.append(gdata.calendar.Reminder(minutes=evt.get_alarm()));

	try:
		google_api.run_google_action(google_api.gd_client.UpdateEvent, event.GetEditLink().href, event)
	except ErminigGoogleError, e:
		error_win.display(e.title(), e.description())
		return

def getUpdatedEventsFromLocal(pid, localSource, remoteSource, lastSync, progress):
	# Those are events to update in Google:
	evts = queryUpdatedLocalEvents(lastSync, localSource)
	if not evts:
		update_progress(progress, 1.0/3*2)
		return

	progress_inc = 1.0/3.0/len(evts)
	progress_val = 1.0/3.0
	for e in evts:
		progress_val = progress_val + progress_inc
		update_progress(progress, progress_val)

		event = Event(e[3], e[4], e[5], e[1], e[2], e[6], \
				e[0], 0, rrule=e[8], alarm=e[9])
		event.set_tzOffset(e[7])
		gid = updateGoogleEvent(event, remoteSource, pid)

def getDeletedEventsFromLocal(pid, localSource, remoteSource, lastSync, progress):
	# get all events in the Trash:
	rows = cwrapper.getAllDeletedEvents(localSource, lastSync)
	if not rows:
		update_progress(progress, 1.0)
		return

	progress_inc = 1.0/3.0/len(rows)
	progress_val = 1.0/3.0*2
	for e in rows:
		progress_val = progress_val + progress_inc
		update_progress(progress, progress_val)

		gid = getGoogleIdFromLocalId(e)
		if not gid:
			continue

		try:
			event = google_api.run_google_action(google_api.gd_client.GetCalendarEventEntry, urllib.quote("/calendar/feeds/" + remoteSource + "/private/full/" + gid))

			if event == None:
				logger.append("Unable to get event to delete!")
				return 

			google_api.run_google_action(google_api.gd_client.DeleteEvent, event.GetEditLink().href)
		except ErminigGoogleError, e:
			error_win.display(e.title(), e.description())
			return
		

def syncFromGoogle(pid, localSource, remoteSource, lastSync, progress=None):
	getNewEventsFromGoogle(pid, int(localSource), remoteSource, lastSync, \
			progress)

def local_sync(pid, localSource, remoteSource, lastSync, stime, progress=None):
	global currentTime
	currentTime = stime

	getNewEventsFromLocal(pid, int(localSource), remoteSource, lastSync, progress)
	getUpdatedEventsFromLocal(pid, int(localSource), remoteSource, lastSync, progress)
	getDeletedEventsFromLocal(pid, int(localSource), remoteSource, lastSync, progress)

def prepare():
	global localEventsTouched
	global googleEventsTouched

	localEventsTouched = []
	googleEventsTouched = []

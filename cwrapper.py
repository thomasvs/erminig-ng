# vi:si:noet:sw=4:sts=4:ts=8

from ctypes import *
import erminig_conf


def get_and_free(ptr):
	if ptr:
		s = string_at(ptr)
		libc.free(ptr)
		return s
	else:
		return None

lib = cdll.LoadLibrary(erminig_conf.libpath + "/libcalaccess.so")
libc = cdll.LoadLibrary("libc.so.6")

lib.getAllLocalCalendarsIDs.restype = get_and_free

lib.getLocalCalendarName.restype = get_and_free
lib.getLocalCalendarName.argtypes = [c_int]

lib.createLocalCalendar.argtypes = [c_char_p]

lib.addLocalCalendarEntry.argtypes = [c_int, c_int, c_int, c_char_p, c_char_p,\
		c_char_p, c_int, c_int, c_char_p, c_int]
lib.addLocalCalendarEntry.restype = c_char_p

lib.removeCancelledEventLocally.argtypes = [c_int, c_char_p]

lib.queryNewLocalEvents.restype = get_and_free
lib.queryNewLocalEvents.argtypes = [c_int, c_int]

lib.queryUpdatedLocalEvents.restype = get_and_free
lib.queryUpdatedLocalEvents.argtypes = [c_int, c_int]

lib.getAllDeletedEvents.restype = get_and_free
lib.getAllDeletedEvents.argtypes = [c_int, c_int]

lib.updateLocalEvent.argtypes = [c_int, c_char_p, c_char_p, c_char_p,\
		c_char_p, c_int, c_int, c_char_p, c_int, c_int]

class EVENT(Structure):
	_fields_ = [	("id", c_char_p),
			("start", c_int),
			("end", c_int),
			("title", c_char_p),
			("where", c_char_p),
			("descr", c_char_p),
			("allday", c_int),
			("ctime", c_int),
			("mtime", c_int),
			("tzOffset", c_int),
			("rrule", c_char_p),
			("alarm", c_int)]


def createLocalCalendar(name):
	return lib.createLocalCalendar(name)

def getAllLocalCalendarsIDs():
	return lib.getAllLocalCalendarsIDs()

def getCalendarNameByID(id):
	return lib.getLocalCalendarName(id)

def addLocalCalendarEntry(calId, evt):
	ret = (lib.addLocalCalendarEntry(calId, evt.get_start(), \
			evt.get_end(), evt.get_title(), evt.get_where(), \
			evt.get_description(), evt.get_fullday(),\
			evt.get_cdate(), evt.get_rrule(), evt.get_rtype(), \
			evt.get_alarm()))

	if not ret:
		return None
	elif ret == "":
		return None
	else:
		return int(ret)

def removeCancelledEventLocally(cid, lid):
	return lib.removeCancelledEventLocally(cid, str(lid))

def queryNewLocalEvents(cid, lastSync):
	return lib.queryNewLocalEvents(cid, lastSync)

def queryUpdatedLocalEvents(cid, lastSync):
	return lib.queryUpdatedLocalEvents(cid, lastSync)

def getAllDeletedEvents(cid, lastSync):
	res = lib.getAllDeletedEvents(cid, lastSync)
	if not res:
		return None
	else:
		return res.split(":")

def updateLocalEvent(cid, evt, lid):
	return lib.updateLocalEvent(cid, str(lid), evt.get_title(), \
			evt.get_description(), evt.get_where(), \
			evt.get_start(), evt.get_end(), evt.get_rrule(), \
			evt.get_rtype(), evt.get_until(), evt.get_alarm())

def getNewEventById(cid, lid, maxTimestamp):
	e = EVENT()
	lib.getEventById(cid, str(lid), pointer(e))
	if e.ctime < maxTimestamp:
		return (e.id, e.start, e.end, e.title, e.where, e.descr, e.allday, e.tzOffset, e.rrule, e.alarm)
	else:
		return None

def getUpdatedEventById(cid, lid, maxTimestamp):
	e = EVENT()
	lib.getEventById(cid, str(lid), pointer(e))
	if e.mtime < maxTimestamp:
		return (e.id, e.start, e.end, e.title, e.where, e.descr, e.allday, e.tzOffset, e.rrule, e.alarm)
	else:
		return None

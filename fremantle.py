# vi:si:noet:sw=4:sts=4:ts=8

import cwrapper

def getAllLocalCalendars():
	ids = cwrapper.getAllLocalCalendarsIDs()
	if not ids:
		return None

	ids_list = ids.split(":")
	cal_list = []
	for i in ids_list:
		cal_list.append((i, cwrapper.getCalendarNameByID(int(i))))

	return cal_list

def add_local_calendar(cal_name):
	last_id = cwrapper.createLocalCalendar(cal_name)
	return last_id

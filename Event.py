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

import iso8601
import logger

class Event:
	def __init__(self, title, where, descr, start_time, end_time, \
			full_day, id, cdate, rrule=None, alarm=-1):
		self.title = title
		self.where = where
		self.descr = descr
		self.start_time = start_time
		self.end_time = end_time
		self.full_day = full_day
		self.cdate = cdate
		self.id = id
		self.tzOffset = 0
		self.rrule = rrule
		self.alarm = alarm

	def set_tzOffset(self, o):
		self.tzOffset = o

	def get_tzOffset(self):
		return self.tzOffset

	def eval(self, var):
		if var:
			return var
		else:
			return ""

	def get_title(self):
		return self.eval(self.title)

	def get_where(self):
		return self.eval(self.where)

	def get_start(self):
		return int(self.start_time)

	def get_end(self):
		if self.full_day == 1:
			# we have to take off 1 second in case of full-day
			# events, to make Fremantle Calendar happy
			return int(self.end_time - 1)
		else:
			return int(self.end_time)

	def get_description(self):
		return self.eval(self.descr)

	def get_id(self):
		return self.eval(self.id)

	def get_fullday(self):
		return self.full_day

	def get_cdate(self):
		return int(self.cdate)

	def get_until(self):
		if self.rrule == None or self.rrule == "":
			return -1

		rules = self.rrule.split(";")
		print rules
		d = ""
		for r in rules:
			if r.startswith("UNTIL="):
				d = r[len("UNTIL="):]
				break

		if len(d) == 8:
			iso_date = d[:4] + "-" + d[4:6] + "-" + d[6:]
		elif len(d) == 15:
			iso_date = d[:4] + "-" + d[4:6] + "-" + d[6:11] \
					+ ":" + d[11:13] + ":" + d[13:]
		else:
			logger.append("event %s: strange until value: %s" % (self.title, d))
			return -1

		# ??
		return int(iso8601.parse(iso_date)) + 1

	def get_rrule(self):
		return self.rrule

	def get_rtype(self):
		if self.rrule.find("YEARLY") <> -1:
			return 5
		elif self.rrule.find("MONTHLY") <> -1:
			return 4
		elif self.rrule.find("DAILY") <> -1:
			return 1
		elif self.rrule.find("WEEKLY") <> -1:
			# look if all weekdays are listed:
			start = self.rrule.find("BYDAY=")
			end1 = self.rrule.find(";", start)
			end2 = self.rrule.find("!", start) 
			days = self.rrule[start+len(self.rrule):min(end1,end2)]
			days_a = days.split(",")

			if len(days_a) <> 5:
				return 3
			else:
				if days_a.count("MO") and days_a.count("TU") \
						and days_a.count("WE") \
						and days_a.count("TH") \
						and days_a.count("FR"):

							return 2
				else:
					return 3


		else:
			return 0

	def get_alarm(self):
		return self.alarm

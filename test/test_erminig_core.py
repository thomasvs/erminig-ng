# -*- Mode: Python; test_case_name: test.test_erminig_core -*-
# vi:si:et:sw=4:sts=4:ts=4

from test import common

import unittest

import erminig_core

class Functions(unittest.TestCase):
	def test_iso8601(self):
		# this date was passed by Google Calendar
		# not valid iso8601, since there is no TZD
		dtstart = '2008-12-10T00:00:00'
		start_time = erminig_core.iso8601ToTimestamp(dtstart)
		self.assertEquals(start_time, 1228867200)

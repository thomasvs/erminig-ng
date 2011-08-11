# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# hack to pretend we have hildon so we can run tests on PC
import sys
sys.modules['hildon'] = sys.modules['sys']

import atom

from gdata import calendar
from gdata.calendar import service

import Event

import unittest

class CalendarTestCase(unittest.TestCase):
    # See https://garage.maemo.org/tracker/index.php?func=detail&aid=6957&group_id=702&atid=2623
    def testBug2623(self):

        # I had a local event with two reminders.
        # One of them was breaking sync because minutes was int instead of str

        # this is the good one
        rem = calendar.Reminder(minutes='10', method='sms')
        self.failUnless(rem.ToString())

        # this is the bad one, but the constructor fixes it up
        rem = calendar.Reminder(minutes=0, method='alert')
        self.failUnless(rem.ToString())

        # if we set it to int manually, it will choke
        rem.minutes = 0
        self.assertRaises(AttributeError, rem.ToString)

    def testBug2623Two(self):
        # gotten with calendar_service.Get(urllib.quote("/calendar/feeds/" + googleid + "/private/full/" + gid), converter=sys.stdout.write)

        eventString = """<?xml version='1.0' encoding='UTF-8'?>
<entry xmlns='http://www.w3.org/2005/Atom' xmlns:gCal='http://schemas.google.com/gCal/2005' xmlns:gd='http://schemas.google.com/g/2005'>
<id>http://www.google.com/calendar/feeds/username%40gmail.com/private/full/deadbeefdeadbeefdeadbeefde</id>
<published>0001-12-31T00:00:00.000Z</published>
<updated>2011-04-20T14:21:26.000Z</updated>
<category scheme='http://schemas.google.com/g/2005#kind' term='http://schemas.google.com/g/2005#event'/><title type='text'>Workshop #16 - Inputs and Outputs - Arduino Basics </title><content type='text'>For details, link here: http://dhubfab-workshop16.eventbrite.com</content><link rel='alternate' type='text/html' href='http://www.google.com/calendar/event?eid=dGdrcWZoYXZuc2p1ZXFhYTZsbGhha2F0aWtfMjAxMTA0MjZUMTMwMDAwWiBzdnNhbW9odEBt' title='alternate'/><link rel='self' type='application/atom+xml' href='http://www.google.com/calendar/feeds/username%40gmail.com/private/full/deadbeefdeadbeefdeadbeefde'/><link rel='edit' type='application/atom+xml' href='http://www.google.com/calendar/feeds/username%40gmail.com/private/full/deadbeefdeadbeefdeadbeefde/63438992486'/><author><name>username@gmail.com</name><email>username@gmail.com</email></author><gd:eventStatus value='http://schemas.google.com/g/2005#event.confirmed'/><gd:where valueString='DHUB Montcada &gt; Sala DHUB FAB - Carrer de Montcada, 12 - 08005 Barcelona - Spain'/><gd:who email='username@gmail.com' rel='http://schemas.google.com/g/2005#event.organizer' valueString='username@gmail.com'/><gd:recurrence>DTSTART;TZID=Europe/Brussels:20110426T150000
DTEND;TZID=Europe/Brussels:20110426T190000
RRULE:FREQ=DAILY;COUNT=2;INTERVAL=2
BEGIN:VTIMEZONE
TZID:Europe/Brussels
X-LIC-LOCATION:Europe/Brussels
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE
</gd:recurrence><gd:reminder method='alert' minutes='10'/><gd:reminder method='sms' minutes='10'/><gd:transparency value='http://schemas.google.com/g/2005#event.opaque'/><gd:visibility value='http://schemas.google.com/g/2005#event.default'/><gCal:anyoneCanAddSelf value='false'/><gCal:guestsCanInviteOthers value='true'/><gCal:guestsCanModify value='false'/><gCal:guestsCanSeeGuests value='true'/><gCal:sequence value='2'/><gCal:uid value='deadbeefdeadbeefdeadbeefde@google.com'/></entry>
"""
        e = calendar.CalendarEventEntryFromString(eventString)
        self.failUnless(e.ToString())
        self.assertEquals(e.reminder[0].minutes, '10')

        # the local event
        evt = Event.Event('Workshop #16 - Inputs and Outputs - Arduino Basics ',            'DHUB Montcada > Sala DHUB FAB - Carrer de Montcada, 12 - 08005 Barcelona - Spain',
            'For details, link here: http://dhubfab-workshop16.eventbrite.com', 
            1303822800, 1303837200, 0, '3169', 0,
            rrule='FREQ=DAILY;COUNT=2;INTERVAL=2', alarm=0)

        e.reminder[0].minutes = evt.get_alarm()
        self.assertEquals(e.reminder[0].minutes, 0)

        self.assertRaises(AttributeError, e.ToString)

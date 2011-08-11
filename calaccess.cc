#include <CCalendar.h>
#include <CMulticalendar.h>
#include <CComponent.h>
#include <CRecurrence.h>
#include <CEvent.h>
#include <CAlarm.h>
#include <iostream>
#include <string>
#include <sstream>

using namespace std;

struct event_t {
	const char *id;
	int start;
	int end;
	const char *title;
	const char *where;
	const char *descr;
	int allday;
	int ctime;
	int mtime;
	int tzOffset;
	const char *rrule;
	int alarm;
};

extern "C" const char *getAllLocalCalendarsIDs()
{
	vector<CCalendar *>::iterator it;
	stringstream calIDs;
		
	CMulticalendar *mc = CMulticalendar::MCInstance();
	vector<CCalendar *> list = mc->getListCalFromMc();
	
	it = list.begin();
	
	while (it != list.end()) {
		CCalendar *cal = *it;
		calIDs << cal->getCalendarId() << ":";
		++it;
	}

	mc->releaseListCalendars(list);

	string calIDsString(calIDs.str());
	if (calIDsString.size() == 0) {
		return NULL;
	} else {
		return (const char *)strdup(calIDsString.erase(calIDsString.size()-1).c_str());
	}
}

extern "C" const char *getLocalCalendarName(int id)
{
	int error(0);
	CCalendar *cal = NULL;

	CMulticalendar *mc = CMulticalendar::MCInstance();
	cal = mc->getCalendarById(id, error);

	if (error == 0) {
		return NULL;
	} else {
		string calName(cal->getCalendarName());
		delete(cal);
		return (const char *)strdup(calName.c_str());
	}
}

extern "C" int createLocalCalendar(char *title)
{
	CCalendar *newCal;
	int error;

	CMulticalendar *mc = CMulticalendar::MCInstance();

	newCal = mc->addCalendar(string(title), COLOUR_NEXT_FREE, false, true, LOCAL_CALENDAR, "", "1.0", error);

	if (newCal == NULL) {
		return -1;
	} else {
		int newCalId = newCal->getCalendarId();
		delete newCal;
		return newCalId;
	}
}

extern "C" const char *addLocalCalendarEntry(int calId, int start, int end, 
		char *title, char *where, char *descr, 
		int fullday, int cdate, char *rrule, int rtype, int alarm)
{
	bool newEvtRes;
	int error;
	string newEvtId;
	CCalendar *cal;
	CEvent *newEvt;

	CMulticalendar *mc = CMulticalendar::MCInstance();

	newEvt = new CEvent(string(title), string(descr), string(where), 
			start, end);
	newEvt->setCreatedTime(cdate);
	newEvt->setLastModified(cdate);
	newEvt->setAllDay(fullday);
	newEvt->setTzOffset(CMulticalendar::MCInstance()->getSystemTimeShift());
	newEvt->setTzid(CMulticalendar::MCInstance()->getSystemTimeZone());

	cal = mc->getCalendarById(calId, error);
	if (cal == NULL) {
		delete newEvt;
		return (const char *)strdup(newEvtId.c_str());
	}
	// Recurrence handling
	string rrule_s = string(rrule);
	if (rrule_s.size() > 0) {
		CRecurrence *rec = new CRecurrence();
		rec->setRtype(rtype);
		vector<string> rrules;
		rrules.push_back(rrule_s);
		rec->setRrule(rrules);
		newEvt->setRecurrence(rec);
	}

	if (alarm >= 0)
		newEvt->setAlarm(new CAlarm(alarm*60, 1));
	else
		newEvt->removeAlarm();

	newEvtRes = cal->addEvent(newEvt, error);
	if (newEvtRes) {
		newEvtId = newEvt->getId();
	}

	delete newEvt;

	return (const char *)strdup(newEvtId.c_str());
}

extern "C" int updateLocalEvent(int cid, char *localId, char *summary,
		char *descr, char *where, int start, int end, char *rrule,
		int rtype, int until, int alarm)
{
	int error;

	CMulticalendar *mc = CMulticalendar::MCInstance();
	
	CCalendar *cal = mc->getCalendarById(cid, error);
	if (cal == NULL)
		return -1;

	CEvent *evt = cal->getEvent(string(localId), error);
	if (evt == NULL) {
		delete cal;
		return -1;
	}

	evt->setSummary(string(summary));
	evt->setDescription(string(descr));
	evt->setLocation(string(where));
	evt->setDateStart(start);
	evt->setDateEnd(end);

	// Recurrence handling
	string rrule_s = string(rrule);
	if (rrule_s.size() > 0) {
		CRecurrence *rec = new CRecurrence();
		rec->setRtype(rtype);
		vector<string> rrules;
		rrules.push_back(rrule_s);
		rec->setRrule(rrules);
		evt->setRecurrence(rec);
		evt->setUntil(until);
	}

	if (alarm >= 0)
		evt->setAlarm(new CAlarm(alarm*60, 1));
	else
		evt->removeAlarm();

	bool res = cal->modifyEvent(evt, error);

	delete cal;
	delete evt;

	if (!res) {
		return -1;
	}

	return 0;
}

extern "C" int removeCancelledEventLocally(int cid, char *lid)
{
	int error;
	bool ret;

	CMulticalendar *mc = CMulticalendar::MCInstance();
	CCalendar *cal = mc->getCalendarById(cid, error);

	if (cal == NULL)
		return -1;

	ret = cal->deleteEvent(string(lid), error);
	
	delete cal;
	
	return ret;
}

extern "C" const char *queryNewLocalEvents(int cid, int lastSync)
{
	int error;
	bool ret;
	vector<CEvent *>::iterator it;
	stringstream evtsString;

	CMulticalendar *mc = CMulticalendar::MCInstance();
	CCalendar *cal = mc->getCalendarById(cid, error);

	if (cal == NULL)
		return NULL;


	vector<CEvent*> newEvts = cal->getAllAddedEvents(lastSync, error);

	it = newEvts.begin();
	
	while (it != newEvts.end()) {
		CEvent *evt = *it;
		evtsString << evt->getId() << ":";
		delete evt;
		++it;
	}

	string evtsIDsString(evtsString.str());
	if (evtsIDsString.size() == 0) {
		return NULL;
	} else {
		return (const char *)strdup(evtsIDsString.erase(evtsIDsString.size()-1).c_str());
	}

}

extern "C" const char *queryUpdatedLocalEvents(int cid, int lastSync)
{
	int error;
	bool ret;
	vector<CEvent *>::iterator it;
	stringstream evtsString;

	CMulticalendar *mc = CMulticalendar::MCInstance();
	CCalendar *cal = mc->getCalendarById(cid, error);

	if (cal == NULL)
		return (const char *)strdup(evtsString.str().c_str());

	vector<CEvent*> modEvts = cal->getAllModifiedEvents(lastSync, error);

	it = modEvts.begin();
	
	while (it != modEvts.end()) {
		CEvent *evt = *it;
		evtsString << evt->getId() << ":";
		delete evt;
		++it;
	}


	string evtsIDsString(evtsString.str());
	if (evtsIDsString.size() == 0) {
		return NULL;
	} else {
		return (const char*)strdup(evtsIDsString.erase(evtsIDsString.size()-1).c_str());
	}

}

extern "C" const char *getAllDeletedEvents(int cid, int lastSync)
{
	int error;
	bool ret;
	vector<string>::iterator it;
	stringstream evtsString;

	CMulticalendar *mc = CMulticalendar::MCInstance();
	CCalendar *cal = mc->getCalendarById(cid, error);

	if (cal == NULL)
		return (const char*)strdup(evtsString.str().c_str());

	vector<string> delEvts = cal->getAllDeletedEvents(lastSync, error);

	it = delEvts.begin();
	
	while (it != delEvts.end()) {
		string evt = *it;
		evtsString << evt << ":";
		++it;
	}

	string evtsIDsString(evtsString.str());
	if (evtsIDsString.size() == 0) {
		return NULL;
	} else {
		return (const char*)strdup(evtsIDsString.erase(evtsIDsString.size()-1).c_str());
	}
}

extern "C" int getEventById(int cid, char *lid, event_t *e)
{
	int error;
	CMulticalendar *mc = CMulticalendar::MCInstance();
	CCalendar *cal = mc->getCalendarById(cid, error);

	if (cal == NULL)
		return -1;

	CEvent *evt = cal->getEvent(string(lid), error);
	if (evt == NULL)
		return -1;

	e->id = lid;
	e->start = evt->getDateStart();
	e->end = evt->getDateEnd();
	e->title = (const char*)strdup(evt->getSummary().c_str());
	e->where = (const char*)strdup(evt->getLocation().c_str());
	e->descr = (const char*)strdup(evt->getDescription().c_str());
	e->allday = evt->getAllDay();
	e->ctime = evt->getCreatedTime();
	e->mtime = evt->getLastModified();
	e->tzOffset = evt->getTzOffset();

	CRecurrence *recurrence = evt->getRecurrence();

	if (recurrence == NULL)
		e->rrule = "";
	else {
		vector<string> rrules = recurrence->getRrule();
		stringstream rruleStream;
		for (unsigned int i=0; i < rrules.size(); ++i)
			rruleStream << rrules[i] << ";";

		string rrule(rruleStream.str());
		e->rrule = (const char*)strdup(rrule.erase(rrule.size()-1).c_str());
	}

	CAlarm *alrm = evt->getAlarm();
	if (alrm != NULL) {
		int alarm = alrm->getTrigger();
		e->alarm = (alarm == -1 ? -1 : alarm/60);
	}

	delete evt;
	
	return 0;
}

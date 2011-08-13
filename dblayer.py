# vi:si:noet:sw=4:sts=4:ts=8

import sqlite3
import os


def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]

	return d

def initializeDB():
	erminigCur.execute("CREATE TABLE IF NOT EXISTS Prefs (name TEXT PRIMARY KEY, value TEXT)")
	erminigCur.execute("CREATE TABLE IF NOT EXISTS GoogleAccounts (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)")
	erminigCur.execute("CREATE TABLE IF NOT EXISTS Profiles (id INTEGER PRIMARY KEY AUTOINCREMENT, type INTEGER, datasource INTEGER, localSource TEXT, localSourceTitle TEXT, remoteAccountId INTEGER, remoteSource TEXT, remoteSourceTitle TEXT , enabled INTEGER, direction INTEGER, lastUpdate INTEGER, lastLocalUpdate INTEGER)")
	erminigCur.execute("CREATE TABLE IF NOT EXISTS Xrefs (pid INTEGER, lid TEXT, gid TEXT)")

def commit():
	erminigConn.commit()

def run(query, args=None):
	if args:
		erminigCur.execute(query, args)
	else:
		erminigCur.execute(query)

	return erminigCur

def getValue(cur, variable):
	t = cur.fetchone()
	if t:
		return t[variable]
	else:
		return None

def getRows(cur):
	return cur.fetchall()

erminigConn = sqlite3.connect(os.path.expanduser("~/.erminig.db"))
erminigConn.row_factory = dict_factory
erminigCur = erminigConn.cursor()

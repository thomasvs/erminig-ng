# vi:si:noet:sw=4:sts=4:ts=8

import dblayer

def update_profile(profile):
	dblayer.run("UPDATE Profiles SET type=?, datasource=?, localSource=?, "\
			"localSourceTitle=?, remoteAccountId=?, remoteSource=?, "\
			"remoteSourceTitle=?, enabled=?, direction=? WHERE "\
			"id=?", profile)
	dblayer.commit()

def add_profile(profile):
	dblayer.run("INSERT INTO Profiles (type, datasource, localSource, "\
			"localSourceTitle, remoteAccountId, remoteSource, "\
			"remoteSourceTitle, enabled, direction, "\
			"lastUpdate, lastLocalUpdate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)", \
			profile)
	dblayer.commit()

def get_all():
	cur = dblayer.run("SELECT * FROM Profiles")
	rows = dblayer.getRows(cur)

	profiles = []
	for i in rows:
		profiles.append([i['id'], i['type'], i['localSource'], i['localSourceTitle'], i['remoteSource'], i['remoteSourceTitle'], i['enabled'], i['direction'], i['lastUpdate'], i['lastLocalUpdate']])

	return profiles

def get_titles_by_id(id):
	cur = dblayer.run("SELECT localSourceTitle, remoteSourceTitle FROM "\
			"Profiles WHERE id=?", (id,))
	rows = dblayer.getRows(cur)

	return (rows[0]['localSourceTitle'], rows[0]['remoteSourceTitle'])

def remove_by_id(id):
	dblayer.run("DELETE FROM Profiles WHERE id=?", (id,))
	dblayer.run("DELETE FROM Xrefs WHERE pid=?", (id,))
	dblayer.commit()

def get_profile_by_id(id):
	cur = dblayer.run("SELECT * FROM Profiles WHERE id=?", (id,))
	rows = dblayer.getRows(cur)
	if len(rows) == 0:
		return None

	return {'localSource': rows[0]['localSource'], 'localSourceTitle': rows[0]['localSourceTitle'], 'remoteAccountId': rows[0]['remoteAccountId'], 'remoteSource': rows[0]['remoteSource'], 'remoteSourceTitle': rows[0]['remoteSourceTitle'], 'enabled': rows[0]['enabled'], 'direction': rows[0]['direction'], 'lastUpdate': rows[0]['lastUpdate'], 'id': rows[0]['id'], 'lastLocalUpdate': rows[0]['lastLocalUpdate']}

def set_last_sync(pid, t, t2):
	dblayer.run("UPDATE Profiles SET lastUpdate=? WHERE id=?", (t, pid))
	dblayer.run("UPDATE Profiles SET lastLocalUpdate=? WHERE id=?", (t2, pid))
	dblayer.commit()

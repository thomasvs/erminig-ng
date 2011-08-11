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

import dblayer

def get_registered_accounts_count():
	cur = dblayer.run("SELECT COUNT(id) AS X FROM GoogleAccounts")
	count = dblayer.getValue(cur, "X")
	return count

def register_new_account(username, password):
	dblayer.run("INSERT INTO GoogleAccounts (username, password) VALUES "\
			"(?, ?)", (username, password))
	dblayer.commit()

def update_account(username, password, id):
	dblayer.run("UPDATE GoogleAccounts SET username=?, password=? WHERE "\
			"id=?", (username, password, id))
	dblayer.commit()

def check_username_existence(username):
	cur = dblayer.run("SELECT COUNT(id) AS X FROM GoogleAccounts WHERE "\
			"username = ?", (username,))

	count = dblayer.getValue(cur, "X")
	if count > 0:
		return True
	else:
		return False

def get_registered_accounts():
	cur = dblayer.run("SELECT id, username FROM GoogleAccounts")
	rows = dblayer.getRows(cur)

	accts = []
	for i in rows:
		accts.append([i['id'], i['username']])

	return accts

def get_account_by_id(id):
	cur = dblayer.run("SELECT username, password FROM GoogleAccounts "\
			"WHERE id = ?", (id,))
	row = dblayer.getRows(cur)[0]
	return (row['username'], row['password'], id)

def delete_account_by_id(id):
	dblayer.run("DELETE FROM GoogleAccounts WHERE id=?", (id,))
	dblayer.run("DELETE FROM Profiles WHERE remoteAccountId=?", (id,))
	dblayer.commit()

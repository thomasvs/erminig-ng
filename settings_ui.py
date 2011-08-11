import hildon, alarm, time, os, sys
import gtk
import string

import google_accounts
import dblayer

def get_google_acct_id():
	global acct_tree
        ts = acct_tree.get_selection()
        (model, iter) = ts.get_selected()
        return model.get_value(iter, 0)

def del_google_acct(widget, data):
	id = get_google_acct_id()
	account = google_accounts.get_account_by_id(id)
	text = "Are you sure that you want to delete account \"%s\"?\n" \
			"Deleting it will remove all links between the data "\
			"stored on your device and data stored in Google.\n"\
			"Please note that no actual data will be deleted, "\
			"only their relationships." % (account[0])
	dialog = hildon.Note("confirmation", data, text)
	dialog.set_button_texts("Yes", "No")
	ans = dialog.run()
	dialog.destroy()

	if ans == gtk.RESPONSE_OK:
		google_accounts.delete_account_by_id(id)
		read_accounts_list()
		update_gaccts_button()

def edit_google_acct(widget, data):
	id = get_google_acct_id()
	account = google_accounts.get_account_by_id(id)
	add_google_acct_dialog(widget, data, account)

def check_wizard_input(nb, current, data):
	if current == 1 or current == 2:
		entry = nb.get_nth_page(current)
		return len(entry.get_text()) != 0
	else:
		return True

def add_google_acct(widget, data):
	add_google_acct_dialog(widget, data)

def add_google_acct_dialog(widget, data, oldData=None, external=False):
	dialog = gtk.Dialog()

	if not oldData:
		dialog.set_title("Add Google Account")
	else:
		dialog.set_title("Edit Google Account")

	dialog.connect("delete-event", lambda w,d: w.destroy())

	username_label = gtk.Label("Username: ")
	username_entry = hildon.Entry(gtk.HILDON_SIZE_AUTO)
	username_entry.set_placeholder("Please enter your Google username")

	password_label = gtk.Label("Password: ")
	password_entry = hildon.Entry(gtk.HILDON_SIZE_AUTO)
	password_entry.set_placeholder("Please enter your Google password")
	password_entry.set_input_mode(gtk.HILDON_GTK_INPUT_MODE_FULL | \
			(not gtk.HILDON_GTK_INPUT_MODE_AUTOCAP))
	password_entry.set_visibility(False)

	if oldData:
		username_entry.set_text(oldData[0])
		password_entry.set_text(oldData[1])

	ubox = gtk.HBox()
	ubox.pack_start(username_label)
	ubox.pack_start(username_entry)

	pbox = gtk.HBox()
	pbox.pack_start(password_label)
	pbox.pack_start(password_entry)

	dialog.vbox.add(ubox)
	dialog.vbox.add(pbox)

	if not oldData:
		dialog.add_button("Add", gtk.RESPONSE_OK)
	else:
		dialog.add_button("Save", gtk.RESPONSE_OK)

	while True:
		dialog.show_all()
		resp = dialog.run()

		if resp == gtk.RESPONSE_OK:
			username = username_entry.get_text()
			password = password_entry.get_text()
			if not oldData:
				if store_google_profile(username, password, \
						dialog):
					dialog.destroy()
					if not external:
						read_accounts_list()
						update_gaccts_button()
					break
			else:
				if update_google_profile(username, password, \
						oldData[2], dialog):
					dialog.destroy()
					read_accounts_list()
					update_gaccts_button()
					break
		else:
			break

def read_accounts_list():
	global liststore

	liststore.clear()
	for entry in google_accounts.get_registered_accounts():
		liststore.append(entry)

def update_google_profile(username, password, id, win):
	if (username == "" or password == ""):
		note = hildon.hildon_note_new_information(win, \
				"You must provide both the Google username "\
				"and password!")
		note.connect("delete-event", lambda w,d: w.destroy())
		gtk.Dialog.run(note)
		return False

	google_accounts.update_account(username, password, id)
	return True

def store_google_profile(username, password, win):
	if (username == "" or password == ""):
		note = hildon.hildon_note_new_information(win, \
				"You must provide both the Google username "\
				"and password!")
		note.connect("delete-event", lambda w,d: w.destroy())
		gtk.Dialog.run(note)
		return False

	if (check_username_existence(username)):
		note = hildon.hildon_note_new_information(win, "The username"\
				" \"%s\" is already defined in Erminig." \
				" It will not be added a second time." \
				% (username))
		note.connect("delete-event", lambda w,d: w.destroy())
		gtk.Dialog.run(note)
		return False

	google_accounts.register_new_account(username, password)
	return True

def check_username_existence(username):
	return google_accounts.check_username_existence(username)


def google_accounts_win(widget, data):
	global liststore
	global acct_tree

	win = hildon.Dialog()
	win.set_title("Manage Google Accounts")
	vbox = gtk.VBox(False, 0)

	liststore = gtk.ListStore(int, str)
	acct_tree = hildon.GtkTreeView(gtk.HILDON_UI_MODE_EDIT, liststore)

	read_accounts_list()

	cell = gtk.CellRendererText()
	col = gtk.TreeViewColumn()
	col.pack_start(cell, True)
	col.set_attributes(cell, text=1)
	acct_tree.append_column(col)


	pannableArea = hildon.PannableArea()
	pannableArea.add(acct_tree)
	pannableArea.set_size_request_policy(hildon.SIZE_REQUEST_CHILDREN)
	vbox.pack_start(pannableArea, True, True, 0)

	bbox = gtk.HButtonBox()
	bbox.set_layout(gtk.BUTTONBOX_SPREAD)

	newBtn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	newBtn.set_text("Add Account", "")
	newBtn.connect("clicked", add_google_acct, win)
	bbox.pack_start(newBtn, False, False, 0)

	editBtn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	editBtn.set_text("Edit Account", "")
	editBtn.connect("clicked", edit_google_acct, win)
	bbox.pack_start(editBtn, False, False, 0)

	delBtn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	delBtn.set_text("Remove Account", "")
	delBtn.connect("clicked", del_google_acct, win)
	bbox.pack_start(delBtn, False, False, 0)

	doneBtn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	doneBtn.set_text("Done", "")
	doneBtn.connect("clicked", lambda w,d: d.destroy(), win)
	bbox.pack_start(doneBtn, False, False, 20)

	vbox.pack_end(bbox, False, True, 0)
	win.vbox.add(vbox)
	win.connect("delete-event", lambda w,d: w.destroy())
	win.show_all()
	win.run()



def create_settings_buttons(win):
	global google_accts_btn

	google_accts_btn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
		gtk.HILDON_SIZE_FINGER_HEIGHT, \
		hildon.BUTTON_ARRANGEMENT_VERTICAL)
	google_accts_btn.connect("clicked", google_accounts_win, win)
	update_gaccts_button()


def update_gaccts_button():
	count = google_accounts.get_registered_accounts_count()

	text = ""
	if (count == 1):
		text = "1 account registered"
	else:
		text = "%s accounts registered" % (count)

	google_accts_btn.set_text("Google Accounts", text)

# auto sync functions
def auto_sync_get_syncid():
	cur = dblayer.run("SELECT value FROM Prefs where name='auto_sync_id'")
	count = dblayer.getValue(cur, "value")
	return count

def auto_sync_update_syncid(sync_id):
	if auto_sync_get_syncid() is None:
		dblayer.run("INSERT INTO Prefs (name, value) values ('auto_sync_id', '%d')" % sync_id)
	else:
		dblayer.run("UPDATE Prefs SET value='%d' where name='auto_sync_id'" % sync_id)
	dblayer.commit()

def auto_sync_get_synctime():
	cur = dblayer.run("SELECT value FROM Prefs where name='auto_sync_time'")
	time = dblayer.getValue(cur, "value")
	if not time is None:
		return time.split(':')
	else:
		return None

def auto_sync_update_synctime(sync_hour, sync_min):
	if auto_sync_get_synctime() is None:
		dblayer.run("INSERT INTO Prefs (name, value) values ('auto_sync_time', '%d:%d')" % (sync_hour,sync_min))
	else:
		dblayer.run("UPDATE Prefs SET value='%d:%d' where name='auto_sync_time'" % (sync_hour,sync_min))
	dblayer.commit()

def auto_sync_toggled(auto_button, time_button):
	active = auto_button.get_active()
	if active:
		(hours, minutes) = time_button.get_time()
		event = alarm.Event()
		event.appid = "erminig"
		event.title = "Synchronization with erminig"
		#event.flags |= alarm.EVENT_RUN_DELAYED
		action = event.add_actions(1)[0]
		action.flags |= alarm.ACTION_WHEN_TRIGGERED | alarm.ACTION_WHEN_DELAYED | alarm.ACTION_TYPE_EXEC
		action.command = os.path.abspath(sys.argv[0]) + " -a -d"
		recur = event.add_recurrences(1)[0]
		# let's see what this does...
		recur.mask_min = 1 << minutes
		recur.mask_hour = 1 << hours
		# initialize alarm time to somewhere in the future
		event.alarm_time = time.time() + 5
		# lt = time.localtime(time.time() + 5)
		# tz = time.tzname[lt.tm_isdst]
		# event.alarm_time = time.mktime(recur.next(lt, tz))
		event.recurrences_left = -1
		sync_id=alarm.add_event(event)
		auto_sync_update_syncid(sync_id)
		auto_sync_update_synctime(hours, minutes)
	else:
		alarm.delete_event(int(auto_sync_get_syncid()))
		dblayer.run("DELETE FROM Prefs where name='auto_sync_id'")
		dblayer.commit()

def auto_sync_time_changed(time_button):
	(hours, minutes) = time_button.get_time()
	auto_sync_update_synctime(hours, minutes)

	sync_id=auto_sync_get_syncid()
	if not sync_id is None:
		event = alarm.get_event(int(sync_id))
		recur = event.get_recurrence(0)
		recur.mask_min = 1 << minutes
		recur.mask_hour = 1 << hours
		sync_id = alarm.update_event(event)
		auto_sync_update_syncid(sync_id)

def auto_sync_loadtime(time_button):
	time = auto_sync_get_synctime()
	if not time is None:
		time_button.set_time(int(time[0]), int(time[1]))

def display(win):

	dialog = gtk.Dialog()
	dialog.set_title("Settings")


	create_settings_buttons(dialog)
	dialog.vbox.add(google_accts_btn)


	# daily sync setting
	auto_button = hildon.CheckButton(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT)
	auto_button.set_label("Automatically synchronize daily")
	auto_button.set_active(not auto_sync_get_syncid() is None)
	dialog.vbox.add(auto_button)

	time_button = hildon.TimeButton(gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT, hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
	time_button.set_title("Daily synchronization time")
	time_button.set_alignment(0.25, 0.5, 0.5, 0.5)
	dialog.vbox.add(time_button)

	auto_sync_loadtime(time_button)
	auto_button.connect("toggled", auto_sync_toggled, time_button)
	time_button.connect("value-changed", auto_sync_time_changed)


	dialog.connect("delete-event", lambda w,d: w.destroy())
	dialog.show_all()
	dialog.run()

liststore = None
acct_tree = None
google_accts_btn = None

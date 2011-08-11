import hildon
import gtk

import consts
import fremantle
import google_accounts
import settings_ui
import google_api
import profiles
import logger

from ErminigError import *
import error_win

def display_google_auth_error(win):
	note = hildon.hildon_note_new_information(win, \
		"Could not connect to your Google account. Check username "\
		"and password. (And do you have Internet connectivity?)")
	note.connect("delete-event", lambda w,d: w.destroy())
	gtk.Dialog.run(note)


def display_add_cal_error(win):
	note = hildon.hildon_note_new_information(win, \
		"Could not create new local calendar. Does it already exist?")
	note.connect("delete-event", lambda w,d: w.destroy())
	gtk.Dialog.run(note)

def get_sync_direction():
	global direction_selector

	selection = direction_selector.get_current_text()
	model = direction_selector.get_model(0)
	iter = model.get_iter_first()

	direction = 0

	while iter:
		if model.get_value(iter, 1) == selection:
			direction = model.get_value(iter, 0)
			break
		iter = model.iter_next(iter)

	return direction

def get_profile_enabled():
	global enable_chk

	return enable_chk.get_active()

def get_local_source():
	global local_selector

	selection = local_selector.get_current_text()
	model = local_selector.get_model(0)
	iter = model.get_iter_first()

	id = 0

	while iter:
		if model.get_value(iter, 1) == selection:
			id = model.get_value(iter, 0)
			break
		iter = model.iter_next(iter)

	return (id, selection)

def get_remote_source():
	global remote_selector

	selection = remote_selector.get_current_text()
	model = remote_selector.get_model(0)
	iter = model.get_iter_first()

	id = 0

	while iter:
		if model.get_value(iter, 1) == selection:
			id = model.get_value(iter, 0)
			break
		iter = model.iter_next(iter)

	return (id, selection)


def add_profile(widget, data):
	global editing
#	sync_type = get_sync_type()
#	datasource = get_datasource()
	# XXX Temporary:
	sync_type = consts.SYNC_TYPE_CAL
	datasource = consts.DATASOURCE_BUILTIN
	# XXX
	local_source, local_source_title = get_local_source()
	remote_source, remote_source_title = get_remote_source()
	remote_acct_id = current_google_account_selected
	enabled = get_profile_enabled()
	direction = get_sync_direction()

	if editing:
		profiles.update_profile((sync_type, datasource, local_source, \
			local_source_title, remote_acct_id, remote_source, \
			remote_source_title, enabled, direction, \
			current_profile_id))
	else:
		profiles.add_profile((sync_type, datasource, local_source, \
			local_source_title, remote_acct_id, remote_source, \
			remote_source_title, enabled, direction))

	data.destroy()

def new_remote_source(widget, hint):
	global current_google_account_selected
	global local_selector

	dialog = gtk.Dialog()
	dialog.set_title("New Google Calendar")

	dialog.connect("delete-event", lambda w,d: w.destroy())

	label = gtk.Label("Please enter the name of a new Google calendar")
	new_cal_entry = hildon.Entry(gtk.HILDON_SIZE_AUTO)
	new_cal_entry.set_placeholder("Calendar name")
	hint = local_selector.get_current_text()
	if not hint:
		hint = ""
	new_cal_entry.set_text(hint)
	new_cal_entry.select_region(0, len(hint))

	dialog.vbox.add(label)
	dialog.vbox.add(new_cal_entry)

	dialog.add_button("Add", gtk.RESPONSE_OK)
	dialog.show_all()
	resp = dialog.run()

	if resp == gtk.RESPONSE_OK:
		cal_name = new_cal_entry.get_text().strip()
		if not cal_name == "":
			cal_id = google_api.create_new_calendar(cal_name)
			update_remote_data_source(consts.SYNC_TYPE_CAL,\
					current_google_account_selected)
			select_remote_source(cal_id)
		
	dialog.destroy()

def new_local_source(widget, hint):
	global remote_selector

	dialog = gtk.Dialog()
	dialog.set_title("New Local Calendar")

	dialog.connect("delete-event", lambda w,d: w.destroy())

	label = gtk.Label("Please enter the name of a new local calendar")
	new_cal_entry = hildon.Entry(gtk.HILDON_SIZE_AUTO)
	new_cal_entry.set_placeholder("Calendar name")
	hint = remote_selector.get_current_text()
	if not hint:
		hint = ""
	new_cal_entry.set_text(hint)
	new_cal_entry.select_region(0, len(hint))

	dialog.vbox.add(label)
	dialog.vbox.add(new_cal_entry)

	dialog.add_button("Add", gtk.RESPONSE_OK)
	dialog.show_all()
	resp = dialog.run()

	if resp == gtk.RESPONSE_OK:
		cal_name = new_cal_entry.get_text().strip()
		if not cal_name == "":
			last_id = fremantle.add_local_calendar(cal_name)
			if last_id == -1:
				display_add_cal_error(dialog)
			else:
				update_local_data_source(\
						consts.DATASOURCE_BUILTIN)
				select_local_source(last_id)
		
	dialog.destroy()

def create_type_selector():
	selector = hildon.TouchSelector()

	type_list = gtk.ListStore(int, str)
	type_list.append([consts.SYNC_TYPE_CAL, "Calendar"])
	renderer = gtk.CellRendererText()
	column = selector.append_column(type_list, renderer, text=1)
	column.set_property("text-column", 1)

	picker = hildon.PickerButton(gtk.HILDON_SIZE_AUTO | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, 
			hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
	picker.set_title("Synchronization item")
	picker.set_selector(selector)

	# default on Calendar
	picker.set_active(0)

	return picker

def create_direction_selector():
	global direction_selector

	direction_selector = hildon.TouchSelector()

	type_list = gtk.ListStore(int, str)
	type_list.append([consts.DIRECTION_BOTH, "Both"])
	type_list.append([consts.DIRECTION_FROM_GOOGLE_ONLY, "From Google Only"])
	type_list.append([consts.DIRECTION_TO_GOOGLE_ONLY, "To Google Only"])
	renderer = gtk.CellRendererText()
	column = direction_selector.append_column(type_list, renderer, text=1)
	column.set_property("text-column", 1)

	picker = hildon.PickerButton(gtk.HILDON_SIZE_AUTO | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, 
			hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
	picker.set_title("Synchronization direction")
	picker.set_selector(direction_selector)

	# default on Built-In
	picker.set_active(0)

	return picker

def update_local_data_source(source_id):
	global local_source_list

	if not local_source_list:
		return

	if source_id == consts.DATASOURCE_BUILTIN:
		local_source_list.clear()
		for id, title in fremantle.getAllLocalCalendars():
			local_source_list.append([int(id), title])

def create_local_selector(win):
	global local_source_list
	global local_selector

	local_selector = hildon.TouchSelector()
	local_source_list = gtk.ListStore(int, str)

	renderer = gtk.CellRendererText()
	column = local_selector.append_column(local_source_list, renderer, text=1)
	column.set_property("text-column", 1)

	picker = hildon.PickerButton(gtk.HILDON_SIZE_AUTO | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, 
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	picker.set_title("Local Source")
	picker.set_selector(local_selector)

	new_btn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
	new_btn.set_label("New...")
	new_btn.connect("clicked", new_local_source, "hint")

	hbox = gtk.HBox()
	hbox.pack_start(picker)
	hbox.pack_start(new_btn, False, False, 30)

	return hbox

def update_remote_data_source(sync_type, google_acct_id):
	global dialog
	remote_sources.clear()

	if sync_type == consts.SYNC_TYPE_CAL:
		hildon.hildon_gtk_window_set_progress_indicator(dialog, 1)
		try:
			if not google_api.switch_account(\
					google_accounts.get_account_by_id(\
					google_acct_id)):
				display_google_auth_error(dialog)
				google_new_btn.set_sensitive(False)
				google_item_picker.set_sensitive(False)
				hildon.hildon_gtk_window_set_progress_indicator(dialog, 0)
				return
		except ErminigError, e:
			error_win.display(e.title(), e.description())
			return

		google_new_btn.set_sensitive(True)
		google_item_picker.set_sensitive(True)
		for id, title in google_api.get_all_calendars():
			logger.append("ID->")
			logger.append(id)
			logger.append("title->")
			logger.append(title)
			remote_sources.append([id, title])
		hildon.hildon_gtk_window_set_progress_indicator(dialog, 0)

def create_remote_selector(win):
	global remote_sources
	global google_new_btn
	global google_item_picker
	global remote_selector

	remote_selector = hildon.TouchSelector()

	remote_sources = gtk.ListStore(str, str)
	renderer = gtk.CellRendererText()
	column = remote_selector.append_column(remote_sources, renderer, text=1)
	column.set_property("text-column", 1)

	google_item_picker = hildon.PickerButton(gtk.HILDON_SIZE_AUTO | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	google_item_picker.set_title("Remote Source")
	google_item_picker.set_selector(remote_selector)
	google_item_picker.set_sensitive(False)

	google_new_btn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
	google_new_btn.set_label("New...")
	google_new_btn.connect("clicked", new_remote_source, "hint")
	google_new_btn.set_sensitive(False)

	hbox = gtk.HBox()
	hbox.pack_start(google_item_picker)
	hbox.pack_start(google_new_btn, False, False, 30)

	return hbox

def source_selector_changed(selector, user_data):
	# Brrrrr
	selection = selector.get_current_text()
	model = selector.get_model(0)
	iter = model.get_iter_first()

	local_source_id = 0

	while iter:
		if model.get_value(iter, 1) == selection:
			local_source_id = model.get_value(iter, 0)
			break
		iter = model.iter_next(iter)

	update_local_data_source(local_source_id)
	

def create_source_selector():
	source_selector = hildon.TouchSelector()

	type_list = gtk.ListStore(int, str)
	type_list.append([consts.DATASOURCE_BUILTIN, "Built-in"])
	renderer = gtk.CellRendererText()
	column = source_selector.append_column(type_list, renderer, text=1)
	column.set_property("text-column", 1)

	source_selector.connect("changed", source_selector_changed)

	picker = hildon.PickerButton(gtk.HILDON_SIZE_AUTO | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, 
			hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
	picker.set_title("Local Data Source")
	picker.set_selector(source_selector)

	# default on Built-In
	picker.set_active(0)

	return picker

def account_selector_changed(selector, user_data):
	global current_google_account_selected
	# Brrrrr
	selection = selector.get_current_text()
	model = selector.get_model(0)
	iter = model.get_iter_first()

	account_id = 0

	while iter:
		if model.get_value(iter, 1) == selection:
			account_id = model.get_value(iter, 0)
			break
		iter = model.iter_next(iter)

	# XXX Forcing for the moment...
	current_google_account_selected = account_id
	update_remote_data_source(consts.SYNC_TYPE_CAL, account_id)

def create_account_selector():
	global account_selector
	global account_list

	account_selector = hildon.TouchSelector()

	account_list = gtk.ListStore(int, str)

	renderer = gtk.CellRendererText()
	column = account_selector.append_column(account_list, renderer, text=1)
	column.set_property("text-column", 1)

	account_selector.connect("changed", account_selector_changed)

	picker = hildon.PickerButton(gtk.HILDON_SIZE_AUTO | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, 
			hildon.BUTTON_ARRANGEMENT_HORIZONTAL)
	picker.set_title("Google Account")
	picker.set_selector(account_selector)

	for id, acct in google_accounts.get_registered_accounts():
		account_list.append([int(id), acct])

	return picker

def create_enable_button():
	global enable_chk

	enable_chk = hildon.CheckButton(gtk.HILDON_SIZE_AUTO | \
			gtk.HILDON_SIZE_FINGER_HEIGHT)
	enable_chk.set_label("Enabled")
	enable_chk.set_active(True)
	return enable_chk

def create_ui(win):

	vbox = gtk.VBox()
	pannableArea = hildon.PannableArea()

	vbox.pack_start(create_type_selector())
	vbox.pack_start(create_source_selector())
	vbox.pack_start(create_account_selector())
	vbox.pack_start(create_local_selector(win))
	vbox.pack_start(create_remote_selector(win))
	vbox.pack_start(create_enable_button())
	vbox.pack_start(create_direction_selector())

	pannableArea.set_size_request_policy(hildon.SIZE_REQUEST_CHILDREN)
	pannableArea.add_with_viewport(vbox)

	win.vbox.pack_start(pannableArea)

	bbox = gtk.HButtonBox()
	bbox.set_layout(gtk.BUTTONBOX_SPREAD)

	addBtn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	addBtn.set_text("Save profile", "")

	addBtn.connect("clicked", add_profile, win)
	bbox.pack_end(addBtn, False, False, 0)

	cancelBtn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	cancelBtn.set_text("Cancel", "")
	cancelBtn.connect("clicked", lambda d,w: w.destroy(), win)
	bbox.pack_start(cancelBtn, False, False, 0)
	
	win.vbox.pack_end(bbox, False, False, 0)

def select_local_source(localSource):
	model = local_selector.get_model(0)
	iter = model.get_iter_first()
	# XXX Temporary!
	while iter:
		if model.get_value(iter, 0) == localSource:
			local_selector.select_iter(0, iter, True)
			break
		iter = model.iter_next(iter)

def select_remote_source(remoteSource):
	model = remote_selector.get_model(0)
	iter = model.get_iter_first()
	while iter:
		if model.get_value(iter, 0) == remoteSource:
			remote_selector.select_iter(0, iter, True)
			break
		iter = model.iter_next(iter)

def fill_form(pid):
	profile = profiles.get_profile_by_id(pid)
	enable_chk.set_active(profile['enabled'])

	# Google Account
	model = account_selector.get_model(0)
	iter = model.get_iter_first()
	googleAcct = profile['remoteAccountId']
	while iter:
		if model.get_value(iter, 0) == googleAcct:
			account_selector.select_iter(0, iter, True)
			break
		iter = model.iter_next(iter)

	# Local source
	select_local_source(int(profile['localSource']))

	# Remote source
	select_remote_source(profile['remoteSource'])


	# Sync direction
	model = direction_selector.get_model(0)
	iter = model.get_iter_first()
	direction = profile['direction']
	while iter:
		if model.get_value(iter, 0) == direction:
			direction_selector.select_iter(0, iter, True)
			break
		iter = model.iter_next(iter)

def ask_for_google_account_creation(parent):
	dialog = gtk.MessageDialog(parent=parent, flags=0, \
			type=gtk.MESSAGE_INFO, buttons=gtk.BUTTONS_NONE)
	dialog.set_title("No Google Account defined")
	dialog.format_secondary_text("No Google account has been defined yet.\n You will now have the possibility to add an account.")
	dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
	dialog.run()
	dialog.destroy()
	settings_ui.add_google_acct_dialog(parent, None, external=True)

	for id, acct in google_accounts.get_registered_accounts():
		account_list.append([int(id), acct])

def display(win, pid = None):
	global dialog
	global editing
	global current_profile_id
	global account_selector
	
	dialog = gtk.Dialog()
	dialog.set_title("Add new Profile")

	create_ui(dialog)
	update_local_data_source(consts.DATASOURCE_BUILTIN)

	dialog.connect("delete-event", lambda w, d: w.destroy())

	# editing profile
	if pid is not None:
		dialog.set_title("Edit Profile")
		fill_form(pid)
		current_profile_id = pid
		editing = True
	else:
		if google_accounts.get_registered_accounts_count() == 0:
			ask_for_google_account_creation(dialog)
		if google_accounts.get_registered_accounts_count() == 1:
			# Pre-select the only Google account available:
			account_selector.set_active(0, 0)

	dialog.show_all()
	dialog.run()

local_source_list = None
local_selector = None
remote_selector = None
remote_sources = None
google_new_btn = None
account_list = None
google_item_picker = None
account_selector = None
direction_selector = None
enable_chk = None
dialog = None
current_google_account_selected = None
editing = False
current_profile_id = 0

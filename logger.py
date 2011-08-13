# vi:si:noet:sw=4:sts=4:ts=8

import gtk
import hildon


ringSize = 200

ring = [None for i in xrange(ringSize)]

def append(str):
	ring.pop(0)
	ring.append(str)
	print str

def dump():
	for i in ring:
		if i <> None:
			print i

def display_ring_buffer():
	global text_area

	for i in ring:
		if i <> None:
			text_area.get_buffer().insert_at_cursor(repr(i) + "\n")
	
def display(win):
	global text_area

	dialog = gtk.Dialog()
	dialog.set_title("Log")
	
	text_area = hildon.TextView()
	text_area.set_editable(False)
	text_area.set_cursor_visible(False)

	pannableArea = hildon.PannableArea()
	pannableArea.add(text_area)
	pannableArea.set_property("mov-mode", hildon.MOVEMENT_MODE_BOTH)
	pannableArea.set_size_request_policy(hildon.SIZE_REQUEST_CHILDREN)
	# WTF?
	pannableArea.set_size_request(300, 300)

	dialog.vbox.pack_start(pannableArea, True, True, 10)

	close_btn = hildon.Button(gtk.HILDON_SIZE_AUTO_WIDTH | \
			gtk.HILDON_SIZE_FINGER_HEIGHT, \
			hildon.BUTTON_ARRANGEMENT_VERTICAL)
	close_btn.connect("clicked", lambda w,d: d.destroy(), dialog)
	close_btn.set_text("Close", "")

	dialog.vbox.add(close_btn)

	dialog.connect("delete-event", lambda w,d: w.destroy())
	display_ring_buffer()
	dialog.show_all()
	dialog.run()

text_area = None

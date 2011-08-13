# vi:si:noet:sw=4:sts=4:ts=8

import gtk
import hildon

def display(title, description):

	dialog = gtk.MessageDialog(parent=None, flags=0, type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_NONE)
	dialog.set_title("Erminig - Error!")
	dialog.set_markup(title)
	dialog.format_secondary_text(description)
	dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)

	dialog.run()

	dialog.destroy()


PYFILES = erminig_conf.py gtkexcepthook.py profile_ui.py erminig_core.py iso8601.py consts.py settings_ui.py cwrapper.py Event.py logger.py version.py dblayer.py fremantle.py google_accounts.py google_api.py profiles.py ErminigError.py ErminigGoogleError.py error_win.py 
PYEXEC = erminig
PNG = pixmaps/abook.png pixmaps/bidirection.png pixmaps/calendar.png pixmaps/erminig.png pixmaps/lr.png pixmaps/rl.png pixmaps/sync_one.png pixmaps/add.png pixmaps/edit.png pixmaps/refresh.png pixmaps/delete.png

CXXFLAGS = `pkg-config calendar-backend --cflags`
LDFLAGS = `pkg-config calendar-backend --libs`

binary:
	$(CXX) calaccess.cc $(CXXFLAGS) $(LDFLAGS) -shared -o libcalaccess.so
clean: 
	$(RM) -f libcalaccess.so
install: binary
	mkdir -p $(DESTDIR)/usr/share/erminig
	install -m0644 $(PYFILES) $(DESTDIR)/usr/share/erminig
	install -m755 $(PYEXEC) $(DESTDIR)/usr/share/erminig
	install -m755 libcalaccess.so $(DESTDIR)/usr/share/erminig
	mkdir -p $(DESTDIR)/usr/share/applications/hildon
	install -m0644 erminig.desktop $(DESTDIR)/usr/share/applications/hildon
	mkdir -p $(DESTDIR)/usr/share/icons/hicolor/48x48/apps/
	install -m0644 pixmaps/erminig.png $(DESTDIR)/usr/share/icons/hicolor/48x48/apps/
	mkdir -p $(DESTDIR)/usr/share/erminig/pixmaps
	install -m0644 $(PNG) $(DESTDIR)/usr/share/erminig/pixmaps

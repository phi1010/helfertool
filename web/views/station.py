# -*- coding: utf-8 -*-

from web.utils import render_template, expose, url_for, run_command_output, invalid_form_error
from web.login_utils import require_login, require_admin
from werkzeug import redirect
import db
import config

## neue station anlegen
@require_login
@require_admin
@expose('/station/new')
def neue_station(request):
	if request.method == "GET":
		## formular anzeigen
		return render_template('station_anlegen.xml',
				session=request.session)

	## else: neue station entgegennehmen

	station_name = request.form.get('name')
	station_desc = request.form.get('beschreibung')
	
	if not db.sane_str(station_name, True) or not db.sane_str(station_desc):
		return invalid_form_error(request.session,
				msg=u"Name leer oder irgendwo ungültige Zeichen drin..")

	db.insert('INSERT INTO station (name, description) VALUES (?, ?)',
			(station_name, station_desc))

	return redirect('/station')


## dinge über diese eine station
@expose('/station/<int:station_id>')
def stationsinfo(request, station_id):
	matches = db.select('SELECT * FROM station WHERE id=?', station_id)

	if len(matches) == 0:
		return render_template('error.xml', error_short='stationsid ungueltig',
				error_long="die angegebene stationsid wurde in der datenbank nicht gefunden",
				config=config, session=request.session)

	return render_template('stationinfo.xml', station_id=station_id,
			session=request.session)

## übersicht über alle
@expose('/station')
def stationsuebersicht(request):
	matches = db.select('SELECT * FROM station')

	return render_template('stationsuebersicht.xml', stationen=matches,
			session=request.session)


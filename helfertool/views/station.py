# -*- coding: utf-8 -*-

from ..utils.utils import run_command_output, invalid_form_error
from ..utils.login_utils import require_login, require_admin
from flask import redirect, request, render_template, session
import helfertool.db as db
import config

from helfertool import app

## neue station anlegen
@require_login
@require_admin
@app.route('/station/new', methods=["GET", "POST"])
def neue_station():
	if request.method == "GET":
		## formular anzeigen
		return render_template('station_anlegen.xml',
				session=session)

	## else: neue station entgegennehmen

	station_name = request.form.get('name')
	station_desc = request.form.get('beschreibung')
	
	if not db.sane_str(station_name, True) or not db.sane_str(station_desc):
		return invalid_form_error(session,
				msg=u"Name leer oder irgendwo ungültige Zeichen drin..")

	db.insert('INSERT INTO station (name, description) VALUES (?, ?)',
			(station_name, station_desc))

	return redirect('/station')


## dinge über diese eine station
@app.route('/station/<int:station_id>')
def stationsinfo(station_id):
	matches = db.select('SELECT * FROM station WHERE id=?', station_id)

	if len(matches) == 0:
		return render_template('error.xml', error_short='stationsid ungueltig',
				error_long="die angegebene stationsid wurde in der datenbank nicht gefunden",
				config=config, session=session)

	return render_template('stationinfo.xml', station_id=station_id,
			session=session)

## übersicht über alle
@app.route('/station')
def stationsuebersicht():
	matches = db.select('SELECT * FROM station')

	return render_template('stationsuebersicht.xml', stationen=matches,
			session=session)


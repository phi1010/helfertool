# -*- coding: utf-8 -*-

from web.utils import render_template, expose, url_for, run_command_output, invalid_form_error
from web.session_utils import create_session, is_user_admin
from web.login_utils import require_login, require_admin, check_login_credentials, _find_userid_byname, _find_username_byid

from werkzeug import redirect
from werkzeug.wrappers import Request, Response

import web.utils
import db
import config

from Crypto.Random import random
from passlib.hash import sha256_crypt
import datetime

##fuer ical
from icalendar import Calendar, Event
import pytz

## neuen helfer eintragen
@expose('/helfer/new')
def neuerhelfer(request):
	if not is_user_admin(request.session):
		return redirect('/')
	if request.method == 'GET':
		## formular anzeigen, weil noch kein POST-foo
		return render_template('helfer_anlegen.xml',
				session=request.session)

	## we got a request, handle it
	username = request.form.get('username')
	password = request.form.get('password')

	email = request.form.get('email')
	mobile = request.form.get('mobile')
	comment = request.form.get('comment')

	tshirt = request.form.get('shirt_size')
	pullover = request.form.get('pullover_size')
	want_participant_shirt = request.form.get('want_participant_shirt')

	## einzeln für spezifischere fehlermeldungen
	if not db.sane_str(username, True):
		return  invalid_form_error(request.session,
				msg=u"username leer oder enthält ungültige zeichen")

	if not db.sane_str(password, True):
		return  invalid_form_error(request.session,
				msg=u"passwort leer oder enthält ungültige zeichen")

	if not db.sane_str(email):
		return  invalid_form_error(request.session,
				msg=u"email enthält ungültige zeichen")
	if not db.sane_str(mobile):
		return  invalid_form_error(request.session,
				msg=u"handynummer enthält ungültige zeichen")
	if not db.sane_str(comment):
		return  invalid_form_error(request.session,
				msg=u"kommentartext enthält ungültige zeichen")
	if not db.sane_str(tshirt):
		return invalid_form_error(request.session,
				msg=u"T-Shirt-Größe enthält ungültige Zeichen")
	if not db.sane_str(pullover):
		return invalid_form_error(request.session,
				msg=u"Pullover-Größe enthält ungültige Zeichen")
	

	db_uid, found = _find_userid_byname(username)
	if found:
		return invalid_form_error(request.session,
				msg=u'ein benutzer mit diesem name existiert bereits. ich fürchte du musst dir einen anderen namen ausdenken')

	crypted = sha256_crypt.encrypt(password)

	userid = db.insert("INSERT INTO person (username, password, email, mobile, comment, is_admin, tshirt_size, pullover_size, want_participant_shirt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (username, crypted, email, mobile, comment, 0, tshirt, pullover, want_participant_shirt))

	## man ist auch gleich eingeloggt, wenn man sich registriert hat
	create_session(request.session, userid, username, False)

	return render_template('helfer_eingetragen_infos.xml',
			username=username, email = email, session=request.session)

## der eine helfer -- was er macht, zur not delete-knopf
@require_login
@expose('/helfer/<int:helferid>')
def helferinfo(request, helferid):
	admin_mode = is_user_admin(request.session)

	if (request.session["userid"] != helferid) and not admin_mode:
		return render_template('error.xml', error_short='unauthorized',
			error_long="du kannst nur deine eigenen schichten anschauen. entweder du bist nicht eingeloggt, oder du versuchst schichten anderer leute anzuzeigen",
			config=config, session=request.session)

	if admin_mode:
		helfer_name, found = _find_username_byid(helferid)
	else:
		helfer_name=request.session['username']

	helfer = db.select('''SELECT
		id,
		username,
		signed_fire,
		signed_hygiene,
		email,
		mobile,
		want_participant_shirt AS shirt
	FROM
		person
	WHERE
		id=?''', (helferid,))

	if len(helfer) != 1:
		return render_template('error.xml', error_short='invalid user',
			error_long="irgendwas ist faul. du bist als benutzer #%d eingeloggt, aber nicht in der db." % (helferid,),
			config=config, session=request.session)

	rows = db.select('''SELECT
			schicht.id AS id,
			schicht.name AS name,
			schicht.description AS description,
			station.name AS station_name,
			schicht.from_day AS from_day,
			schicht.from_hour AS from_hour,
			schicht.until_day AS until_day,
			schicht.until_hour AS until_hour
		FROM
			person_schicht
		LEFT JOIN
			schicht on person_schicht.schicht_id = schicht.id
		JOIN
			station ON schicht.station_id = station.id
		WHERE
			person_schicht.pers_id=?
		ORDER BY
			schicht.from_day ASC, schicht.from_hour ASC''', (helferid,))
	
	#fuer welche schichten die zeit zum austragen abgelaufen ist
	daysSinceStart =  (datetime.date.today()-config.start_date).days
	curHours = datetime.datetime.time(datetime.datetime.now()).hour
	showButton = [res["from_day"]*24 + res["from_hour"] > daysSinceStart*24 + curHours + config.user_shift_unclaim_timeout_hours + 1 for res in rows]

	return render_template('helferinfo.xml',
			schichten=rows,
			helfer=helfer[0],
			showButton=showButton,
			session=request.session)


@require_login
@expose('/helfer/changepw')
def passwort_aendern(request):
	if request.method != 'POST':
		return redirect('/helfer')

	old_pw = request.form.get('old_pw')
	new_first = request.form.get('new_first')
	new_second = request.form.get('new_second')

	if not check_login_credentials(request.session['username'], old_pw):
		error_long = u"Das alte Passwort, das du eingegeben hast, stimmt nicht. Du kannst dein Passwort auch bei einem Admin ändern lassen, frag am besten per Mail bei %s" % config.admin_email
		return render_template('error.xml', error_short=u"altes passwort falsch",
				error_long=error_long,
				session=request.session)

	if new_first != new_second:
		error_long = u"Die beiden neuen Passwörter sind nicht gleich. Du hast dich sehr wahrscheinlich vertippt. Du kannst dein Passwort auch bei einem Admin ändern lassen, frag am besten per Mail bei %s" % config.admin_email
		return render_template('error.xml',
				error_short=u"Neue Passwörter sind unterschiedlich",
				error_long=error_long,
				session=request.session)

	crypted = sha256_crypt.encrypt(new_first)
	db.update('UPDATE person SET password=? WHERE id=?', (crypted,
		request.session['userid']))

	return redirect('/redirect/my_page')


@require_login
@expose('/helfer/change_data')
def dinge_aendern(request):
	if request.method != 'POST':
		return redirect('/helfer')

	userid = request.session['userid']
	new_email = request.form.get('email')
	new_mobile = request.form.get('mobile')
	want_shirt = request.form.get('want_participant_shirt') == "on"

	old_want_shirt = db.select('SELECT want_participant_shirt FROM person WHERE id=?', (userid,))
	if len(old_want_shirt) != 1:
		## this should never happen, if the @require_login works as expected
		## (i.e. if you ever trigger this assertion, go fix @require_login)
		assert False
	old_want_shirt= old_want_shirt[0]['want_participant_shirt']

	## XXX: this feels redundant, but also sql-injection-exploitable if
	## shortened too much..
	if config.shirt_stuff_changeable:
		db.update('''UPDATE
			person
		SET
			email=?,mobile=?,want_participant_shirt=?
		WHERE
			id=?''', (new_email, new_mobile, want_shirt, userid))
	else:
		db.update('''UPDATE
			person
		SET
			email=?,mobile=?
		WHERE
			id=?''', (new_email, new_mobile, userid))


	return redirect('/helfer/%d' % (userid,))


@require_admin #we expose sensitive user information here!
@expose('/helfer.csv')
def alle_helfer_csv(request, helferid=None):
	columns = "username, email, mobile, tshirt_size, pullover_size, want_participant_shirt, signed_hygiene, signed_fire, COUNT(person_schicht.pers_id) as shiftCount, min(schicht.from_day * 24 + schicht.from_hour) / 24 AS firstday, min(schicht.from_day * 24 + schicht.from_hour) % 24 AS firsthour "
	
	persons = db.select("SELECT {} FROM person LEFT OUTER JOIN person_schicht ON person_schicht.pers_id = person.id LEFT OUTER JOIN schicht ON schicht.id = person_schicht.schicht_id GROUP BY person.id ORDER BY LOWER(username)".format(columns))
		
	#No need for a template, as this is technical data
	csv = ','.join(map(lambda x: x.split()[-1], columns.split(', ')))+" \r\n"
	csv += u"\r\n".join(",".join('"'+unicode(column).replace('"', '""')+'"' for column in person) for person in persons)
	
	response = Response(csv)
	response.headers['content-type'] = 'text/csv; charset=utf-8'
	return response

@expose('/helfer/<int:helferid>.ics')
def helfer_ical(request,helferid):
	rows = db.select('''SELECT
			schicht.id AS id,
			schicht.name AS name,
			schicht.description AS description,
			station.name AS station_name,
			schicht.from_day AS from_day,
			schicht.from_hour AS from_hour,
			schicht.until_day AS until_day,
			schicht.until_hour AS until_hour,
			GROUP_CONCAT(s2.username, ", ") as mithelfer
		FROM
			person_schicht
		LEFT JOIN
			schicht on person_schicht.schicht_id = schicht.id
		JOIN
			station ON schicht.station_id = station.id
		JOIN
			person_schicht as ps ON ps.schicht_id = person_schicht.schicht_id
		LEFT JOIN
			person as s2 ON ps.pers_id = s2.id AND s2.id != ?
		WHERE
			person_schicht.pers_id=?
		GROUP BY
			schicht.id
		ORDER BY
			schicht.from_day ASC, schicht.from_hour ASC''', (helferid,helferid))

	cal = Calendar()
	cal.add('prodid', '-//fsi//kiftool//DE')
	cal.add('version', '2.0')

	for termin in rows:
		event = Event()
		event.add('summary', termin['name'])
		event.add('description', termin['description'] + (" " + termin['mithelfer'] if termin['mithelfer'] else ""))

		until_hour = termin['until_hour']
		until_min = 0
		if until_hour == 24:
			until_hour = 23
			until_min = 59

		if termin['from_day'] < 3:
			event.add('dtstart', datetime.datetime(2013,10,29+termin['from_day'],termin['from_hour'],0,0,tzinfo=pytz.timezone('Europe/Berlin')))
		else:
			event.add('dtstart', datetime.datetime(2013,11,termin['from_day']-2,termin['from_hour'],0,0,tzinfo=pytz.timezone('Europe/Berlin')))

		if termin['until_day'] < 3:
			event.add('dtend', datetime.datetime(2013,10,29+termin['until_day'],until_hour,until_min,0,tzinfo=pytz.timezone('Europe/Berlin')))
		else:
			event.add('dtend', datetime.datetime(2013,11,termin['until_day']-2,until_hour,until_min,0,tzinfo=pytz.timezone('Europe/Berlin')))

		event.add('dtstamp', datetime.datetime(2013,9,4,0,0,0,tzinfo=pytz.timezone('Europe/Berlin')))
		event['uid'] =  "2013uid"+str(termin['id'])+"@kif.fsi.informatik.uni-erlangen.de"
		event.add('priority', 5)
		cal.add_component(event)

	response = Response(cal.to_ical())
	response.headers['content-type'] = 'text/calendar; charset=utf-8'
	return response

## übersicht ueber alle
@expose('/helfer')
def helfer_overview(request):
	helfer = db.select('SELECT id, username FROM person')

	schichten = {}
	for h in helfer:
		schichten[h[1]] = db.select('''SELECT schicht.name AS schichtname FROM
			person_schicht
		JOIN
			schicht ON person_schicht.schicht_id = schicht.id
		WHERE
			person_schicht.pers_id=?''', (h[0],))

	return render_template('helferuebersicht.xml', schichten=schichten,
			session=request.session)



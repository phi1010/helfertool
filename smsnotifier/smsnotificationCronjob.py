#!/usr/bin/env python2.7

from python_crontab.crontab import CronTab
import os,sys

if len(sys.argv) == 1 or sys.argv[1] not in ["start", "stop", "reset"]:
	print "Usage: {} {{start|stop|reset}} [vorlaufzeit=15]".format(sys.argv[0])
	print "0 < Vorlaufzeit < 60"
	sys.exit(1)

interval = 15
try:
	if len(sys.argv) == 3:
		interval = int(sys.argv[2])
	if not ( 60 > interval > 0 ):
		raise ValueError
except ValueError:
	print "Vorlaufzeit must be an 0 < int < 60"
	sys.exit(1)


crontab = CronTab()

job = crontab.find_comment("SMS notification fuer das uber-Kif-Helfertool")

if len(job) == 0:
	job = crontab.new(command = "cd {}; ./notifyBySMS.py;".format(os.getcwd()),
				comment = "SMS notification fuer das uber-Kif-Helfertool")
	job.minute.on(60-interval)
else:
	if sys.argv[1] == "start":
		print "Warning: An old job was found. Reusing it. To change vorlaufzeit use reset"
	if len(job) > 1:
		print "Warning: Multiple jobs matched. Please adjust crontab by hand"
	job = job[0]

if sys.argv[1] == "stop":
	job.enable(False)
elif sys.argv[1] == "reset":
	job.minute.every(interval)
	job.enable()
elif sys.argv[1] == "start":
	job.enable()

crontab.write()

print "Crontab successfully altered"
print job

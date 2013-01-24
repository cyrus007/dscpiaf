#!/usr/bin/python
# Copyright 2013 Swapan Sarkar <swapan@yahoo.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''A script to interpret ContactID codes and send them onwards from
   asterisk'''

__author__ = 'swapan@yahoo.com'
__version__ = '0.0.3'

import os, sys, time, shutil
import glob, getopt
import ConfigParser
import twitter
from email.mime.text import MIMEText

execfile("alarm.inc")
folder  = '/var/spool/asterisk/alarm'
outfile = '/var/spool/asterisk/alarm/latest.txt'
confile = '/root/.alarmconf'
logfile = sys.stderr


''' Class UsingTwitter interface is used to send notifications to
    the configured twitter account.'''
class UsingTwitter(object):
    def __init__(self, key, secret, token_key, token_secret):
	self.api = twitter.Api(consumer_key=key,
			  consumer_secret=secret,
			  access_token_key=token_key,
			  access_token_secret=token_secret)

    def send(self, alarm_out):
	try:
		sendfile = open(alarm_out)
		status = self.api.PostUpdates(sendfile.read())
	except:
		logfile.write("Could not send via twitter.")



''' Class UsingSendmail interface is used to send notifications by
    email.'''
class UsingSendmail(object):
    def __init__(self, fromuser, touser):
	self.from_address = fromuser
	self.to_address = touser

    def send(self, alarm_out):
	try:
		sendfile = open(alarm_out)
		msg = MIMEText(sendfile.read())
		msg["From"] = self.from_address
		msg["To"] = self.to_address
		msg["Subject"] = "PIAF:Alarm notification"
		handle = os.popen("/usr/sbin/sendmail -t", "w")
		handle.write(msg.as_string())
		status = handle.close()
		if status != 0:
			logfile.write("Sendmail exit status - %s" % status)
	except:
		logfile.write("Could not send via email.")


''' Class UsingScreen interface is used to display the notifications
    on standard output.'''
class UsingScreen(object):
    def __init__(self):
	pass

    def send(self, alarm_out):
	sendfile = open(alarm_out)
	for line in sendfile:
		sys.stdout.write( line )
	sendfile.close()


''' Class Alarm is the main object to handle the event file parsing
    and substitute them with human readable strings.'''
class Alarm(object):
    def __init__(self, conf_file):
	parser = ConfigParser.ConfigParser(allow_no_value=True)
	parser.read(conf_file)
	self.protocol = parser.get('general', 'protocol')
	self.callerid = parser.get('general', 'callerid')
	self.callername = parser.get('general', 'callername')
	self.account = parser.get('general', 'account')
	astconf = parser.get('general', 'alarmreceiverconf')
	parser.read(glob.glob(astconf))
	self.stampfmt = parser.get('general', 'timestampformat')      #"%a %b %d, %Y @ %H:%M:%S %Z"
	self.payload = object
	if( parser.get('general', 'payload-type') == 'twitter' ):
		self.payload = UsingTwitter(parser.get('payload', 'consumerkey'), parser.get('payload', 'consumersecret'),
				       parser.get('payload', 'tokenkey'), parser.get('payload', 'tokensecret'))
	elif ( parser.get('general', 'payload-type') == 'email' ):
		self.payload = UsingSendmail(parser.get('payload', 'fromemail'), parser.get('payload', 'toemail'))
	else:
		self.payload = UsingScreen()
	self.zones = []
	for i in range(1, 32):
		try:
			zone_text = parser.get('zones', 'Zone['+str(i)+']')
			self.zones.append( zone_text )
		except ConfigParser.NoOptionError:
			pass

    def parseEvents(self, alarm_dir, alarm_out):
	try:
		eventfiles = glob.glob(alarm_dir + '/event-*')
	
		notifs = []
		for file in eventfiles:
			parser = ConfigParser.ConfigParser(allow_no_value=True)
       		 	parser.read(file)
			protocol = parser.get('metadata', 'PROTOCOL')
			if( protocol != self.protocol):
				logfile.write( "Protocol mismatch: %s vs %s" % (protocol, self.protocol) ) 
			callerid = parser.get('metadata', 'CALLINGFROM')
			if( callerid != self.callerid):
				logfile.write( "Calling from mismatch: %s vs %s" % (callerid, self.callerid) ) 
			callername = parser.get('metadata', 'CALLERNAME')
			if( callername != self.callername):
				logfile.write( "Callername mismatch: %s vs %s" % (callerid, self.callerid) ) 
			events = [];  events = parser.options('events')
			if (len(events) > 0):
				notifs.append([time.strptime( parser.get('metadata', 'TIMESTAMP'), self.stampfmt), events])

		if (len(notifs) > 0):
			notifs.sort()
			alarmfile = open(alarm_out, 'w')
			alarmfile.write("# Your security panel generated the following alarms\n")
			for notif in notifs: 
				tstamp = notif[0]
				for event in notif[1]:
					if( event[0:4] != self.account):
						logfile.write( "Account number mismatch: %s vs %s" % (event[0:3], self.account) ) 
					if( event[4:6] != '18'):
						logfile.write( "Message type mismatch: %s vs 18" % event[4:5] ) 
					event_type  = int(event[6])
					event_code  = event[7:10]
					try:
						event_group = event[10:12]	#always 01 if present
					except:
						pass
					try:
						event_zone  = int(event[12:15])	#from 000 to 040
					except:
						pass
#print( "Event=%s (Type=%s : Zone=%s : Code=%s)\n" % (event, event_type, event_zone, event_code) )
					if( event_zone ):
						event_str = "@ %s -> %s - %s in zone: %s\n" % (time.strftime("%H:%M:%S", tstamp), coid_action[event_type], coid_codes[event_code], self.zones[event_zone])
					else:
						event_str = "@ %s -> Supervisory alarm type: %s\n" % (time.strftime("%H:%M:%S", tstamp), coid_codes[event_code]) 
					alarmfile.write(event_str[0:140])
			alarmfile.close();
		for file in eventfiles:
			shutil.move( file, alarm_dir + '/archive/' )
	except IOError as e:
		logfile.write( "Could not write to file '%s':I/O error(%i): %s\n" % (alarm_out, format(e.errno,e.strerror)) )

    def send(self, alarmfile):
	self.payload.send(alarmfile)


#def main():
try:
	opts, args = getopt.getopt(sys.argv[1:], "hc:d:o:l:", ["help", "config=", "folder=", "outfile=", "logfile="])
except getopt.GetoptError:
	pass
for opt, arg in opts:
	if opt in ("-h", "--help"):
		print( "%s [-h|--help] [-c|--config <file>] [-d|--folder <folder>] [-o|--outfile <file>] [-l|--logfile <file>]\n" % sys.argv[0] )
		sys.exit()                  
	elif opt in ("-d", "--folder"):
		folder = arg
	elif opt in ("-o", "--outfile"):
		outfile = arg
	elif opt in ("-c", "--config"):
		confile = arg
	elif opt in ("-l", "--logfile"):
		logfile = arg
myalarm = Alarm(confile)
myalarm.parseEvents(folder, outfile)
myalarm.send(outfile)

#if __name__ == '__main__':
#	main()

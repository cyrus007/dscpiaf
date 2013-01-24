dscpiaf
=======

Setup PIAF (asterisk) to send alarm events

This project holds a python script sendalarm.py which can be used within asterisk based installations to send alarm notifications via twitter, email or local file. The script is driven by a configuration file which should reside at /root/.alarmconf by default. Copy the script and the include file alarm.inc and change the permission bits to make it an executable or load it by the python interpretter.
> Usage: python ./sendalarm.py -c config_file -d alarm_folder -o output_file -l log_file

Example configuration file
    #Alarm configuration file to post from PiAF
    [general]
    protocol=ADEMCO_CONTACT_ID
    callerid=<callerid defined in asterisk extension>
    callername=<callername defined in asterisk extension>
    account=<account number in alarm panel>
    alarmreceiverconf=/etc/asterisk/alarmreceiver.conf
    #payload-type=twitter
    payload-type=email
    
    [payload]
    consumerkey=<consumer key from dev.twitter>
    consumersecret=<consumer secret>
    tokenkey=<token key from dev.twitter>
    tokensecret=<token secret>
    
    fromemail=from_email
    toemail=to_email
    
    [zones]
    Zone[1]=Entrance Doors
    Zone[2]=Living Area
    Zone[3]=Patio Doors
    Zone[4]=Bedroom windows
    Zone[5]=--NA--
    Zone[6]=MBR windows
    Zone[7]=
    Zone[8]=


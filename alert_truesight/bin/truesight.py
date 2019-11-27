import sys
import os
import json
import logging
import requests
import splunk.entity as entity

def getCredentials(sessionKey):                            #Function to retrieve password from Splunk
   myapp = 'alert_truesight'
   try:                                                    #List all credentials
      entities = entity.getEntities(['admin', 'passwords'], namespace=myapp,
                                    owner='nobody', sessionKey=sessionKey)
   except Exception as e:
       logging.critical('Could not get credential from Splunk ' + str(e))
       sys.exit(3)

   for i, c in entities.items():                           #Return first set of credentials
        return c['username'], c['clear_password']

def set_logfile():
    logfile=os.path.abspath(os.path.join(os.path.dirname( __file__ ), '..', '..', '..', '..', 'var', 'log', 'splunk', 'truesight.log'))
    return logfile

def set_url(destination):                                  #Function to supply TSPS or TSIM URLs
    if os.environ['COMPUTERNAME'] == '<NON-PROD HOSTNAME>':#FIT
        tsps_server = '<presentation_server>.<domain>.com'
        tsim_server = '<tsim_server>.<domain>.com'
    else:                                                  #PROD
        tsps_server = '<presentation_server>.<domain>.com'
        tsim_server = '<tsim_server>.<domain>.com'

    token_url = 'https://' + tsps_server + '/tsws/10.0/api/authenticate/login'
    event_url = 'https://' + tsim_server + ':443/bppmws/api/Event/create?routingId=ext_cell&routingIdType=CELL_NAME'
    if destination == 'token':                             #Return TSPS or TSIM URL as requested
        return token_url
    else:
        return event_url

def get_token(token_url, username, password):              #Get authorization token from TrueSight Presentation Server
    logging.info('Sending POST request for token to url=%s', token_url)
    try:
        payload = { "username" : username , "password" : password , "tenantName" : "BmcRealm" }
        r = requests.post(url=token_url, data=payload, verify=False)
        response = r.json()
        authtoken = response['response']['authToken']
        return authtoken
    except Exception as e:
        logging.critical('Unable to get Authentication Token via TSPS Server through SSO: ' + str(e))
        sys.exit(3)

def send_event(authtoken, dest_url, event_host, event_parameter, event_msg, event_severity, gcc_display, custom_timer):    #Function to send event to TSIM server
    myheaders = {'content-type': 'application/json' , 'Authorization': 'authtoken ' + authtoken }
    payload = [{
        "eventSourceHostName": event_host,
        "attributes": { 
            "CLASS": "SPLUNK_EVENT",
            "company": "MYCOMPANY",
            "custom_timer": custom_timer,
            "do_notify": "NO",
            "environment": "PROD",
            "GCC_display": gcc_display,
            "mc_tool": "Splunk",
            "mc_object": "Splunk",
            "mc_object_class": "Alert",
            "mc_parameter": event_parameter,
            "msg": event_msg,
            "severity": event_severity
        }
    }]
    try:
        logging.info('Sending POST request for event to url=%s, payload=%s', dest_url, payload)
        r = requests.post(url=dest_url, data=json.dumps(payload), headers=myheaders, verify=False)
    except Exception as e:
        logging.critical('Unable to create event via TSIM Server on ext_cell: ' + str(e))
        sys.exit(3)

def main():
    if len(sys.argv) < 2 or sys.argv[1] != "--execute":    #Splunk sends first argument as --exectute to ensure proper call
        logging.critical('FATAL Unsupported execution mode (expected --execute flag)')
        sys.exit(1)
    try:
        logfile = set_logfile()
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=logfile, level=logging.CRITICAL)

        settings = json.loads(sys.stdin.read())            #Splunk calls script with JSON, need to parse to extract info.

        sessionKey = settings['session_key']               #sessionKey is unique per Splunk server, and used to retrieve password
        config = settings['configuration']                 #Relevant JSON data for the event
        event_host = str(config.get('event_host'))         #Configured in Splunk alert
        event_msg = str(config.get('event_msg'))           #Configured in Splunk alert
        event_parameter = str(config.get('event_parameter'))#Default is Splunk alert name
        gcc_display = config.get('gcc_display')
        if gcc_display  == "1":                            #If checked, set gcc_display and no auto-close timer
            gcc_display = "YES"
            custom_timer = 0
        else:                                              #If not checked, set auto-close timer to 60 seconds
            gcc_display = "NO"
            custom_timer = 60

        event_severity = str(config.get('event_severity')) #Splunk and TrueSight define severity opposite (eg: Splunk 5 == TS Critical; Splunk 1 == TS Info)
        if event_severity == "5":
            event_severity = "CRITICAL"
        elif event_severity == "4":
            event_severity = "MAJOR"
        elif event_severity == "3":
            event_severity = "MINOR"
        elif event_severity == "2":
            event_severity = "WARNING"
        else:
            event_severity = "INFO"

        username, password = getCredentials(sessionKey)     #Call function to retrieve password from Splunk
        token_url = set_url('token')                        #Call function to retrieve TSPS URL
        authtoken = get_token(token_url, username, password)#Call function to get authorization token from TSPS URL
        dest_url = set_url('event')                         #Call function to retrieve TSIM URL
        send_event(authtoken, dest_url, event_host, event_parameter, event_msg, event_severity, gcc_display, custom_timer) #Call function to send event to TSIM URL
    except Exception as e:
        logging.critical('Execution terminated abnormally: ' + str(e))
        sys.exit(3)

if __name__ == '__main__':
    main()
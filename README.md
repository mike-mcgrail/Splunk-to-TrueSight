# Splunk-to-TrueSight
Trigger Splunk alerts to TrueSight events
Tested on Splunk 7.2 and TrueSight 10.3 (all Windows machines)

**Installation:**

*TrueSight*
1. Copy dedup_splunk_event.mrl to cell (ext_cell in this code) on TrueSight server, run mcompile and reload

*Splunk*
2. Update /bin/truesight.py to correct server names, company name, any other cell or slot updates as needed
3. Copy alert_truesight to $SPLUNK_HOME/etc/apps/
4. Restart Splunk
5. Login to the Splunk web UI
6. Setup the App.
7. Enter the TrueSight API username and password, then click Save
Note: The password is stored locally encrypted on the server

8. The Apps list is shown with a confirmation of successful installation
9. Next to TrueSight Alert Action, click Permissions
10. At the bottom set sharing to All apps and click Save
11. For Search Head Cluster, copy alert_truesight to Deployer shcluster-apps directory and follow Splunk procedures to apply bundle.


**Configuring an Alert**

1. Perform a search and click Save as > Alert
2. Click + Add Actions and select Add to Triggered Alerts
3. Select the appropriate Severity (this will map to TrueSight)
4. Click + Add Actions and select TrueSight Alert
5. Configure Host, Severity, Message and whether to show in GCC Console and click Save Note: The following are the default values which can be modified. Reference Splunk documentation for dynamic token values based on search results.
a. Host: $result.host$ (the host of the search, if applicable. If the search will not return a distinct host, be sure to specify a static host name)
b. Severity: $alert.severity$, mapped to the Severity as set above in step 3
c. Msg: Splunk alert $name$ for $result.host$ $name$ is the Splunk Alert name
d. GCC Event: check the box to set GCC_display to “YES” and show in the TrueSight GCC Console


**Updating Credentials**

If credentials need to be updated

Non-Prod:

1. Navigate to $SPLUNK_HOME/etc/apps/alert_truesight/local/ and delete passwords.conf
2. In the Splunk UI, navigate to Apps > Manage Apps, and next to TrueSight Alert Action click Set Up
3. Enter the username and password, then click Save
4. For Search Head Cluster, perform the above on Deployer and redistribute bundle to cluster members


**Integration Details**

1. The script executed is $SPLUNK_HOME/etc/apps/alert_truesight/bin/truesight.py

2. Parameters are passed from Splunk to the script in JSON format. The script then prepares slot values for TrueSight:

"eventSourceHostName": event_host, (see ‘Configuring an Alert’ above, step #5)
"CLASS": "SPLUNK_EVENT", (custom event class SPLUNK_EVENT)
"company": "MYCOMPANY",
"custom_timer": custom_timer, (see # 6 below)
"do_notify": "NO",
"environment": "PROD",
"GCC_display": gcc_display, (see ‘Configuring an Alert’ above, step #5)
"mc_tool": "Splunk",
"mc_object": "Splunk",
"mc_object_class": "Alert",
"mc_parameter": event_parameter, (Splunk alert name)
"msg": event_msg, (see ‘Configuring an Alert’ above, step #5)
"severity": event_severity (see ‘Configuring an Alert’ above, step #5)

3. Logging is set to $SPLUNK_HOME/var/log/splunk/truesight.log
4. The script is hard-coded for a server to contact TrueSight non-prod, otherwise contact TrueSight PROD
5. The script leverages the TrueSight API (reference https://api.truesight.bmc.com/documentation) to:
a. Contact TSPS to retrieve authToken
b. Send event to TSIM server ext_cell
6. If GCC Event is selected, GCC_display is set to “YES” and custom close timer is set to 0.

Otherwise, custom close timer is set to 300 seconds to auto-close event (this leverages the custom_timer_auto_close.mrl in ext_cell)

7. In ext_cell, dedup_splunk_event.mrl is used to deduplicate events (and also update severity of open event if alert severity is modified in Splunk UI)
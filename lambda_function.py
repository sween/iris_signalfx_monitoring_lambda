import json
import os
import sys
import time
import socket
import logging
import signalfx

def lambda_handler(event, context):
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    
    # Stand Up SignalFX
    sfx = signalfx.SignalFx(api_endpoint='https://api.us1.signalfx.com',
        ingest_endpoint='https://ingest.us1.signalfx.com',
        stream_endpoint='https://stream.us1.signalfx.com')
    
    ingest = sfx.ingest(os.environ["SPLUNK_ACCESS_TOKEN"])

    ################# IRIS Check Number 1, Super Server on applicable IRIS Machines
    BASE = ["iris1"]
    
    if os.environ["MIRRORED"] == "yes":
      BASE.append("iris2")
    if os.environ["BANK"]:
      BASE.append("bank")
      
    superservercheck = 0

    for box in BASE:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.settimeout(2)
      result = sock.connect_ex(('iris1',1972))
      if result == 0:
        superservercheck = 0
        print('port OPEN')
      else:
        superservercheck = 1
        print('port CLOSED, connect_ex returned: '+ str(result))
        
      try:
        ingest.send(
          gauges=[{
            'metric': 'portal.servicedesk.iris.ss',
            'value': superservercheck,
            'timestamp': time.time() * 1000,
            'dimensions': {
              'host': 'iris1',
              'service': os.environ["SERVICE"],
              'instance': 'myinstance'
            }
          
          }],
)
      finally:
        ingest.stop()

    ################# IRIS Check Number 2, Web Servers
    WEBBASE = ["cspgwa"]
    
    if os.environ["MIRRORED"] == "yes":
      WEBBASE.append("cspgwb")

      
    webservercheck = 0

    for box in WEBBASE:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.settimeout(2)
      result = sock.connect_ex((box,443))
      if result == 0:
        webservercheck = 0
        print('port OPEN')
      else:
        webservercheck = 1
        print('port CLOSED, connect_ex returned: '+ str(result))
        
      try:
        ingest.send(
          gauges=[{
            'metric': 'portal.servicedesk.web.httpd',
            'value': webservercheck,
            'timestamp': time.time() * 1000,
            'dimensions': {
              'host': box,
              'service': os.environ["SERVICE"],
              'instance': 'myinstance'
            }
          
          }])
      finally:
        ingest.stop()

    return {
        'statusCode': 200,
        'body': json.dumps('Sent Metrics')
    }

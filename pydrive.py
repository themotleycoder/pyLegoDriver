import argparse
import json
import logging
import time
import legodrive

import nxt.locator
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from nxt.motor import *

AllowedActions = ['both', 'publish', 'subscribe']


# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    msg = json.loads(message.payload)
    
    if msg["message"].lower() == "drive":
        if "direction" in msg and msg["direction"].lower() == "forward":
            legodrive.runmotorthread(legodrive.motorb, 100, 1440)
            legodrive.runmotorthread(legodrive.motorc, 100, 360)
        elif "direction" in msg and msg["direction"].lower() == "forward":
            legodrive.runmotorthread(legodrive.motorb, -100, 1440)
            legodrive.runmotorthread(legodrive.motorc, -100, 360)# motors[motorid], 100, 360
        elif msg["car"].lower() == "drive":
            legodrive.runwheels(100)  
        elif msg["car"].lower() == "stop":
            legodrive.stopwheels()        
        else:
            legodriver.stop()    
    else:   
        print(msg)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")

# Read in command-line parameters
parser = argparse.ArgumentParser()
parser.add_argument("-e", "--endpoint", action="store", dest="host", default="a1s0itke26s9j7-ats.iot.us-west-2.amazonaws.com", help="Your AWS IoT custom endpoint")
parser.add_argument("-r", "--rootCA", action="store", dest="rootCAPath", default="aws/root-CA.crt", help="Root CA file path")
parser.add_argument("-c", "--cert", action="store", dest="certificatePath", default="aws/LegoBot1.cert.pem", help="Certificate file path")
parser.add_argument("-k", "--key", action="store", dest="privateKeyPath", default="aws/LegoBot1.private.key", help="Private key file path")
parser.add_argument("-p", "--port", action="store", dest="port", type=int, help="Port number override")
parser.add_argument("-w", "--websocket", action="store_true", dest="useWebsocket", default=False, help="Use MQTT over WebSocket")
parser.add_argument("-id", "--clientId", action="store", dest="clientId", default="legoRobot", help="Targeted client id")
parser.add_argument("-t", "--topic", action="store", dest="topic", default="lego/robot/Driver", help="Targeted topic")
parser.add_argument("-m", "--mode", action="store", dest="mode", default="subscribe", help="Operation modes: %s"%str(AllowedActions))
parser.add_argument("-M", "--message", action="store", dest="message", default="Alive!",help="Message to publish")

args = parser.parse_args()
host = args.host
rootCAPath = args.rootCAPath
certificatePath = args.certificatePath
privateKeyPath = args.privateKeyPath
port = args.port
useWebsocket = args.useWebsocket
clientId = args.clientId
topic = args.topic

if args.mode not in AllowedActions:
    parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
    exit(2)

if args.useWebsocket and args.certificatePath and args.privateKeyPath:
    parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
    exit(2)

if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
    parser.error("Missing credentials for authentication.")
    exit(2)

# Port defaults
if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
    port = 443
if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
    port = 8883

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTClient = AWSIoTMQTTClient(clientId)
    myAWSIoTMQTTClient.configureEndpoint(host, port)
    myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
if args.mode == 'both' or args.mode == 'subscribe':
    myAWSIoTMQTTClient.subscribe(topic, 1, customCallback)
time.sleep(2)

# Publish to the same topic in a loop forever
loopCount = 0
while True:
    if args.mode == 'both' or args.mode == 'publish':
        message = {}
        message['message'] = args.message
        message['sequence'] = loopCount
        messageJson = json.dumps(message)
        myAWSIoTMQTTClient.publish(topic, messageJson, 1)
        if args.mode == 'publish':
            print('Published topic %s: %s\n' % (topic, messageJson))
        loopCount += 1
    time.sleep(5)

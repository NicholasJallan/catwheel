from prometheus_client import start_http_server
import random
import time
from prometheus_client import Counter
from prometheus_client import Info
import RPi.GPIO as GPIO

from prometheus_client import Gauge
import datetime as dt

import psycopg2
import yaml

config = None
with open(r'/home/pi/projects/catwheel/config.yaml') as file:
    config = yaml.full_load(file)

if config == None:
    raise('Config.yaml not found or invalid')
 
#for item, doc in config.items():
#    print(item, ":", doc)


conn = psycopg2.connect(host="localhost", port = 5432, database="postgres", user="postgres", password="myPassword")
conn.autocommit = True
cur = conn.cursor()

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(24, GPIO.IN,pull_up_down=GPIO.PUD_UP)

WHEEL_DIAMETER = config['wheel']['inner_diameter']

# number of sensors installed on the wheel
SENSOR_NUMBERS = config['wheel']['sensors']

WHEEL_RUNNING_LENGTH_TOTAL = 2 * 3.141592653589793 * WHEEL_DIAMETER
WHEEL_RUNNING_LENGTH_SEGMENT = WHEEL_RUNNING_LENGTH_TOTAL / SENSOR_NUMBERS

# var to read only one time each activation of a magnetic switch.
# Python goes so fast that it will go through the loop many times when one switch is passing.
isOn = False

prevLastSeen = dt.datetime.now()


c = Counter('wheel_tick', 'Tick of the wheel')

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    print('Starting Catwheel')
    
    i = Info('Wheel_info', 'Description of the wheel')
    i.info({'length_of_segment': str(WHEEL_RUNNING_LENGTH_SEGMENT), 'number_of_segments': str(SENSOR_NUMBERS)})
    
    g = Gauge('wheel_speed', 'Speed of the wheel')
    
    # this variable is true when there is a running session ongoing. It stops after 3sec without any magnet tick
    isRunning = False
    lastSeen = dt.datetime.now()
    
    # abritrary picking left side as the activated one. Don't care if it's switched.
    lastInsertedSide = True
    
#    i = 0
#    session = 0
    while True:
        # this test is true when a magnet is nearby one of the 2 sensors
        leftSide = (GPIO.input(18) == False)
        if leftSide or (GPIO.input(24) == False):
            
            lastSeen = dt.datetime.now()
            if isRunning == False:
                # insert a 0 value prior to any new value. This will allow to have a flat line when the wheel isn't running
                # reusing prevLastSeen variable also to avoid a very low first speed value, even if wrong.
                prevLastSeen = lastSeen - dt.timedelta(seconds=2)
                cur.execute('INSERT into ticker (tick_date, tick_date_long, speed) VALUES (%s, %s, %s)', (prevLastSeen, prevLastSeen.timestamp(), 0))
            isRunning = True            
            if isOn == False :
                isOn = True
#                print('seen ', leftSide)
                
                # ensure that we alternate left and right side
                if lastInsertedSide != leftSide:
                    lastInsertedSide = leftSide
#                    print('tick number ', i)
#                    i+=1
                    elapsed_time = lastSeen.timestamp() - prevLastSeen.timestamp()
                    speed = (WHEEL_RUNNING_LENGTH_SEGMENT*3.6) / (elapsed_time*1000)
                    g.set(speed)
#                    print('insert ', leftSide)
                
                    cur.execute('INSERT into ticker (tick_date, tick_date_long, speed) VALUES (%s, %s, %s)', (lastSeen, lastSeen.timestamp(), speed))
                    c.inc()
                
                    prevLastSeen = lastSeen            
        else :
            isOn = False
            now = dt.datetime.now()
            delta = now.timestamp() - lastSeen.timestamp()
            if (delta > 3) and (isRunning==True):
#                print('end session running ', session)
#                session = session +1
#                i = 0
                isRunning = False
                cur.execute('INSERT into ticker (tick_date, tick_date_long, speed) VALUES (%s, %s, %s)', (now, now.timestamp(), 0))
                g.set(0)
                
#        time.sleep(0.05)
    

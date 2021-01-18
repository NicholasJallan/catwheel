from prometheus_client import start_http_server
import random
import time
from prometheus_client import Counter
from prometheus_client import Info
import  RPi.GPIO as GPIO

from prometheus_client import Gauge
from datetime import datetime

import psycopg2


conn = psycopg2.connect(host="localhost", port = 5432, database="postgres", user="postgres", password="myPassword")
conn.autocommit = True
cur = conn.cursor()

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN,pull_up_down=GPIO.PUD_UP)

WHEEL_DIAMETER = 1200

# number of sensors installed on the wheel
SENSOR_NUMBERS = 12

WHEEL_RUNNING_LENGTH_TOTAL = 2 * 3.141592653589793 * WHEEL_DIAMETER
WHEEL_RUNNING_LENGTH_SEGMENT = WHEEL_RUNNING_LENGTH_TOTAL / SENSOR_NUMBERS

# var to read only one time each activation of the switch
isOn = False

prevLastSeen = datetime.now()


# Create a metric to track time spent and requests made.
#REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')

c = Counter('wheel_tick', 'Tick of the wheel')

# Decorate function with metric.
#@REQUEST_TIME.time()
#def process_request(t):
#    """A dummy function that takes some time."""
#    time.sleep(t)    
#    c.inc()     # Increment by 1

if __name__ == '__main__':
    # Start up the server to expose the metrics.
    start_http_server(8000)
    
    i = Info('Wheel_info', 'Description of the wheel')
    i.info({'length_of_segment': str(WHEEL_RUNNING_LENGTH_SEGMENT), 'number_of_segments': str(SENSOR_NUMBERS)})
    
    g = Gauge('wheel_speed', 'Speed of the wheel')
    
    isRunning = False
    lastSeen = datetime.now()
    i = 0
    session = 0
    while True:
        if (GPIO.input(18) == False):
            
            isRunning = True            
            lastSeen = datetime.now()
            if isOn == False :
                print('tick number ', i)
                i+=1
                elapsed_time = lastSeen.timestamp() - prevLastSeen.timestamp()
                speed = (WHEEL_RUNNING_LENGTH_SEGMENT*3.6) / (elapsed_time*1000)
                g.set(speed)
                
                cur.execute('INSERT into ticker (tick_date, tick_date_long, speed) VALUES (%s, %s, %s)', (lastSeen, lastSeen.timestamp(), speed))
                c.inc()
                isOn = True
                prevLastSeen = lastSeen
        else :
            isOn = False
            now = datetime.now()
            delta = now.timestamp() - lastSeen.timestamp()
            if (delta > 3) and (isRunning==True):
                print('end session running ', session)
                session = session +1
                i = 0
                isRunning = False
                cur.execute('INSERT into ticker (tick_date, tick_date_long, speed) VALUES (%s, %s, %s)', (now, now.timestamp(), 0))
                g.set(0)
                
        time.sleep(0.01)
    

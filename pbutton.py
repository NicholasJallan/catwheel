import  RPi.GPIO as GPIO
import time
from datetime import datetime


GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN,pull_up_down=GPIO.PUD_UP)


# var to read only one time each activation of the switch
isOn = False

while True:
   if (GPIO.input(18) == False):
       now = datetime.now()
       if isOn == False :
           with open("output.txt", "a") as text_file:
               text_file.write(now.strftime("%m/%d/%Y %H:%M:%S.%f") + ';\n')
           isOn = True
   else :
       isOn = False    
   time.sleep(0.001)

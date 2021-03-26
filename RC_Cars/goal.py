import time
import adafruit_datetime
import board
import adafruit_hcsr04
from analogio import AnalogOut
'''
https://github.com/adafruit/Adafruit_CircuitPython_datetime/releases/download/1.1.2/adafruit-circuitpython-datetime-6.x-mpy-1.1.2.zip
To install adafruit_datetime, download the file from this link, extract it, and copy the 
adafruit-datetime.mpy file from the lib folder to the lib folder on the circuit python device
'''
next_score_time = adafruit_datetime.datetime.now()
time_between_scores = adafruit_datetime.timedelta(seconds=9)
analog_out = AnalogOut(board.A1)
sonar = adafruit_hcsr04.HCSR04(trigger_pin=board.D10, echo_pin=board.D12)

while True:
    try:
        dist = sonar.distance
        # print(dist)

        if dist < 8:
            time.sleep(2)
            analog_out.value = 65535

            if adafruit_datetime.datetime.now() > next_score_time:
                print('GOAL RED')
                next_score_time = adafruit_datetime.datetime.now() + time_between_scores

            time.sleep(1)
            analog_out.value = 0
        else:
            analog_out.value = 0

    except RuntimeError:
        print("Retrying!")
        pass
    time.sleep(0.1)


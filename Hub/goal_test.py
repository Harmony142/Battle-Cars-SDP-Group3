"""
#!/usr/bin/python
import os, sys
import serial
import time


ser = serial.Serial(port='COM10',baudrate=115200, timeout=1)

# listen for the input, exit if nothing received in timeout period



while True:

   if ser.in_waiting:
       line = ser.readline()
       print(line)
"""

import sys
import glob
import serial

#taken from https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(11)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


if __name__ == '__main__':
    ports = serial_ports()
    print(ports)

    for i, port in enumerate(ports):
        ports[i] = serial.Serial(port=port, baudrate=115200, timeout=1)
    print('connected on all ports')

    # listen for the input, exit if nothing received in timeout period

    score_blue, score_red = 0, 0

    while True:
        for port in ports:
            if port.in_waiting:
                line = port.readline().decode('utf-8').strip()
                if line == 'GOAL BLUE':
                    score_blue += 1
                    print('GOAL BLUEEEEEE', score_blue)
                elif line == 'GOAL RED':
                    score_red += 1

                #print(str(line)[2:-1])
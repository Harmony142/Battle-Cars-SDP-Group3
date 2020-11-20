import time
import board
import pulseio
import busio
import digitalio
from digitalio import DigitalInOut, Direction
from analogio import AnalogIn

class MotorDriver:
    def __init__(self):
        # motor 1 will most likely be the direction controller

        # ---------------- Set Speed Controller for Motors -------------------
        # motor1, motor2 = front wheels, back wheels
        # high for throttle, low for short brake - ranges from 0 to 65535
        self.M1_SC = pulseio.PWMOut(board.D3, frequency=5000, duty_cycle=0)
        self.M2_SC = pulseio.PWMOut(board.D9, frequency=5000, duty_cycle=0)
        # ------------------- Set Direction for Motors -----------------------
        # High, Low for CW --- Low, High for CWW --- Low, Low for Stop

        self.M1D_AI1 = DigitalInOut(board.D4)
        self.M1D_AI1.direction = Direction.OUTPUT
        self.M1D_AI2 = DigitalInOut(board.D5)
        self.M1D_AI2.direction = Direction.OUTPUT
        self.M1D_AI1.value, self.M1D_AI2.value = False, False

        self.M2D_BI1 = DigitalInOut(board.D7)
        self.M2D_BI1.direction = Direction.OUTPUT
        self.M2D_BI2 = DigitalInOut(board.D8)
        self.M2D_BI2.direction = Direction.OUTPUT
        self.M2D_BI1.value, self.M2D_BI2.value = False, False

        self.standby = DigitalInOut(board.D6)
        self.standby.direction = Direction.OUTPUT

    def turn_left(self):
        self.M1D_AI1.value, self.M1D_AI2.value = True, False

    def turn_right(self):
        self.M1D_AI1.value, self.M1D_AI2.value = False, True

    def straight(self):
        self.M1D_AI1.value, self.M1D_AI2.value = False, False

    def forward(self):
        self.M2D_BI1.value, self.M2D_BI2.value = True, False  # counter clock wise

    def backward(self):
        self.M2D_BI1.value, self.M2D_BI2.value = False, True  # clock wise

    def stop(self):
        self.M2D_BI1.value, self.M2D_BI2.value = False, False

    def m1_speed(self, speed):
        self.M1_SC.duty_cycle = speed

    def m2_speed(self, speed):
        self.M2_SC.duty_cycle = speed

    def set_stand_by(self, standby):  # True = active
        self.standby.value = not standby


speedController = MotorDriver()
speedController.set_stand_by(False)
speedController.m1_speed(65535)
uart = busio.UART(board.TX, board.RX, baudrate=9600)

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT


threshold = 33620
analog_in = AnalogIn(board.A0)

def get_voltage(pin):
    return pin.value


while True:
    if get_voltage(analog_in) > threshold:  # gyroscope
        led.value = True
    else:
        led.value = False

    # Read data from uart coming from the bluetooth module
    data = uart.read(1)
    # print(data)
    if data is not None:
        command_flags = int.from_bytes(data, 'little')
        print(command_flags)
        '''
        Interpret the commands coming from the hub
        Bit Positions
        76543210
        0: Y pressed
        1: B pressed
        2: A pressed
        3: X pressed
        4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
        6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
        '''
        forward_backwards = (command_flags & (0b11 << 4)) >> 4
        left_right = (command_flags & (0b11 << 6)) >> 6
        boost = command_flags & 0b1111

        # Control forwards or backwards
        if forward_backwards == 0b10:
            speedController.forward()
        elif forward_backwards == 0b01:
            speedController.backward()
        else:
            speedController.stop()

        # Control steering
        if left_right == 0b10:
            speedController.turn_left()
        elif left_right == 0b01:
            speedController.turn_right()
        else:
            speedController.straight()

        # Control speed boost. Logic is handled by the hub to avoid having to send the data back from the
        # car if we ever want to show fuel tank capacity
        # TODO tweak these speeds until they feel appropriate
        if boost:
            speedController.m1_speed(65535)
            speedController.m2_speed(65535)
        else:
            speedController.m1_speed(65535)
            speedController.m2_speed(65535)


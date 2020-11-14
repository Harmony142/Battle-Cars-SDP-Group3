
import time
import board
import pulseio
from digitalio import DigitalInOut, Direction


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
        self.M1D_AI1.value, self.M1D_AI1.value = True, False

    def turn_right(self):
        self.M1D_AI1.value, self.M1D_AI1.value = False, True

    def straight(self):
        # TODO check why we're setting the same value twice
        # TODO check if this should be True, True
        self.M1D_AI1.value, self.M1D_AI1.value = False, False

    def forward(self):
        self.M2D_BI1.value, self.M2D_BI2.value = True, False  # counter clock wise

    def backward(self):
        self.M2D_BI1.value, self.M2D_BI2.value = False, True  # clock wise

    def m1_speed(self, speed):
        self.M1_SC.duty_cycle = speed
        
    def m2_speed(self, speed):
        self.M2_SC.duty_cycle = speed
    
    def set_stand_by(self, standby):  # True = active
        self.standby.value = standby


speedController = MotorDriver()

# you need to write a function for speed
# decide how to increment/decrement it
while True:
    # Read data from uart coming from the bluetooth module
    # TODO need the board + bluetooth module to test loading data from uart,
    #  probably need a if(data available) then read statement
    command_flags = 0x00

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

    # TODO test if these are the proper driver board commands, I just had to guess
    # Control forwards or backwards
    if forward_backwards == 0b10:
        speedController.forward()
    elif forward_backwards == 0b01:
        speedController.backward()
    else:
        speedController.set_stand_by(True)

    # Control steering
    if left_right == 0b10:
        speedController.turn_left()
    elif left_right == 0b01:
        speedController.turn_right()
    else:
        # TODO see if there's a better way to do this
        speedController.straight()

    # Control speed boost. Logic is handled by the hub to avoid having to send the data back from the
    # car if we ever want to show fuel tank capacity
    # TODO tweak these speeds until they feel appropriate
    # TODO check that this is the correct motor (forward/backwards), it's my best guess from the comments
    if boost:
        speedController.m2_speed(65535)
    else:
        speedController.m2_speed(65535/2)

    # speedController.turn_left()
    # speedController.m1_speed(65535)
    # speedController.set_stand_by(True)
    # time.sleep(0.1)


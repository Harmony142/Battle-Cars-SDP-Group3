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
        

    def turnleft(self):
        self.M1D_AI1.value, self.M1D_AI1.value = True, False

    def turnright(self):
        self.M1D_AI1.value, self.M1D_AI1.value = False, True

    def forward(self):
        self.M2D_BI1.value, self.M2D_BI2.value = True, False  # counter clock wise

    def backward(self):
        self.M2D_BI1.value, self.M2D_BI2.value = False, True  # clock wise

    def m1_speed(self, speed):
        self.M1_SC.duty_cycle = speed
        
    def m2_speed(self, speed):
        self.M2_SC.duty_cycle = speed
    
    def setstandby(self, standby):  # True = active
        self.standby.value = standby
        
speedController = MotorDriver()

# you need to write a function for speed
# decide how to increment/decrement it
while True:
    speedController.turnleft()
    speedController.m1_speed(65535)
    speedController.setstandby(True)
    # time.sleep(0.1)


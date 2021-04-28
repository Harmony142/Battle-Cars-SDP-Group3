import time
import board
import pulseio
import busio
import digitalio
import adafruit_datetime
from digitalio import DigitalInOut, Direction
from analogio import AnalogIn
import neopixel

# Variables for fine tuning the cars
car_index = 2
boost_speed = 65535 // 2
turning_speed = 65535


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


# Color Logic
pixel_pin = board.A1
num_pixels = 49
pixels = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=.05, auto_write=False)

OFF = (0, 0, 0)
RED = (255, 0, 0)
ORANGE = (255, 75, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)

"""
PATTERNS:
000 - Solid - All LEDs current_color
001 - Flashing - All LEDs current_color then ALL LEDs off
010 - Alternating - Every other LED current_color and off, swaps
011 - Snake - snake_length LEDs current_color, then snake_length LEDs off, cycles down strip
100 - Pulse - 1 LED current_color with pulse_gap off LEDs in between
101 - Wave - Increases and decreases brightness each for wave_values LEDs
110 - Rainbow - LEDs pass colors of the rainbow
111 - Party - All LEDs cycle through the colors of the rainbow
Anything else - Off - All LEDs off
"""
update_rate = adafruit_datetime.timedelta(seconds=1)
next_update_time = adafruit_datetime.datetime.now() + update_rate
current_color = RED
current_pattern = 0
pattern_state = 0

# Cycles between flashes in the Flashing pattern
flash_pause = 1
flash_interval = flash_pause + 1

# Length of the snakes in the Snake pattern
snake_length = 5
snake_interval = snake_length * 2

# Length of the gap between pulses in the Pulse pattern
pulse_gap = 3
pulse_interval = pulse_gap + 1

# Number of different fade values in the Wave pattern
wave_values = 5
wave_interval = wave_values * 2

# Number of colors in the rainbow function for the Rainbow and Party patterns
rainbow_interval = 7

speedController = MotorDriver()
speedController.set_stand_by(False)
speedController.m1_speed(turning_speed)
speedController.m2_speed(boost_speed)
uart = busio.UART(board.TX, board.RX, baudrate=9600)

led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT


def rainbow(i):
    if i == 0:
        return RED
    elif i == 1:
        return ORANGE
    elif i == 2:
        return YELLOW
    elif i == 3:
        return GREEN
    elif i == 4:
        return CYAN
    elif i == 5:
        return BLUE
    elif i == 6:
        return PURPLE
    else:
        return RED


def cycle_colors(color):
    for i in reversed(range(1, num_pixels)):
        pixels[i] = pixels[i - 1]

    pixels[0] = color
    pixels.show()


def update_pattern():
    global current_color, current_pattern, pattern_state

    # Solid
    if current_pattern == 0:
        pass

    # Flashing
    elif current_pattern == 1:
        if pattern_state == 0:
            pixels.fill(current_color)
        else:
            pixels.fill(OFF)

        pattern_state = (pattern_state + 1) % flash_interval
        pixels.show()

    # Alternating
    elif current_pattern == 2:
        if pattern_state == 0:
            cycle_colors(OFF)
        else:
            cycle_colors(current_color)

        pattern_state = (pattern_state + 1) % 2

    # Snake
    elif current_pattern == 3:
        if pattern_state < 5:
            cycle_colors(OFF)
        else:
            cycle_colors(current_color)

        pattern_state = (pattern_state + 1) % snake_interval

    # Pulse
    elif current_pattern == 4:
        if pattern_state == 0:
            cycle_colors(current_color)
        else:
            cycle_colors(OFF)

        pattern_state = (pattern_state + 1) % pulse_interval

    # Wave
    elif current_pattern == 5:
        if pattern_state < wave_values:
            cycle_colors(tuple(color // wave_values * (wave_values - pattern_state) for color in current_color))
        else:
            cycle_colors(tuple(color // wave_values * (pattern_state % wave_values) for color in current_color))

        pattern_state = (pattern_state + 1) % wave_interval

    # Rainbow
    elif current_pattern == 6:
        cycle_colors(rainbow(pattern_state))
        pattern_state = (pattern_state + 1) % rainbow_interval

    # Party
    elif current_pattern == 7:
        pixels.fill(rainbow(pattern_state))
        pattern_state = (pattern_state + 1) % rainbow_interval
        pixels.show()

    # Off
    else:
        pass

    """
    # Vapor Wave. Didn't look good, too similar colors and not fast enough
    if pattern_state < 5:
            pixels.fill(tuple(color // 5 * (5 - pattern_state) for color in current_color))
        else:
            pixels.fill(tuple(color // 5 * (pattern_state % 5) for color in current_color))

    pattern_state = (pattern_state + 1) % 10
    pixels.show()
    """


def initialize_pattern(pattern, color):
    global current_pattern, current_color, pattern_state

    current_pattern = pattern
    current_color = color
    pattern_state = 0

    # Solid
    if current_pattern == 0:
        pixels.fill(current_color)

    # Flashing
    elif current_pattern == 1:
        pixels.fill(OFF)

    # Alternating
    elif current_pattern == 2:
        pixels.fill(current_color)
        pixels[1::2] = [OFF] * (num_pixels // 2)

    # Snake
    elif current_pattern == 3:
        for i in range(num_pixels):
            pixels[i] = current_color if i % snake_interval < snake_length else OFF

    # Pulse
    elif current_pattern == 4:
        for i in range(num_pixels):
            pixels[i] = current_color if i % pulse_interval == pulse_gap else OFF

    # Wave
    elif current_pattern == 5:
        for i in range(num_pixels):
            j = (i + 1) % wave_interval
            if j < wave_values:
                pixels[i] = tuple(color // wave_values * (wave_values - j) for color in current_color)
            else:
                pixels[i] = tuple(color // wave_values * (j % wave_values) for color in current_color)

    # Rainbow
    elif current_pattern == 6:
        for i in range(num_pixels):
            pixels[i] = rainbow((rainbow_interval - 1 - i) % rainbow_interval)

    # Party
    elif current_pattern == 7:
        pixels.fill(PURPLE)

    # Off
    else:
        pixels.fill(OFF)

    pixels.show()


initialize_pattern(6, RED)

while True:
    # Check if we need to update the animations
    if adafruit_datetime.datetime.now() > next_update_time:
        update_pattern()
        next_update_time = adafruit_datetime.datetime.now() + update_rate

    # Read data from uart coming from the bluetooth module
    data = uart.read(1)

    if data is not None:
        command_flags = int.from_bytes(data, 'little')
        # print(command_flags)
        """
        Bit Positions
        76543210
        0-1: Unused
        2: Ensuing Customization Data
        3: Boost Enabled
        4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
        6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
        """
        ensuing_customization = (command_flags & (0b1 << 2)) >> 2

        # Check if we need to read customization data
        customization_data = []
        if ensuing_customization:
            # print('Waiting for customization data')
            # Customization data comes over bluetooth one byte at a time in the order Pattern - R - G - B
            while len(customization_data) < 4:
                packet = uart.read(1)
                if packet is not None:
                    # print('Received:', int.from_bytes(packet, 'little'))
                    customization_data.append(int.from_bytes(packet, 'little'))

        # Customization Control
        if ensuing_customization:
            initialize_pattern(customization_data[0], tuple(customization_data[1:]))
        # else:
        #     print('Message Received by Car', car_index)

        # Car Controls
        forward_backwards = (command_flags & (0b11 << 4)) >> 4
        left_right = (command_flags & (0b11 << 6)) >> 6
        boost = (command_flags & (0b1 << 3)) >> 3

        # Control speed boost. Logic is handled by the hub to avoid having to send the data back from the
        # car if we ever want to show fuel tank capacity
        if boost:
            # Can only go forward while boosting
            speedController.m2_speed(boost_speed)

            speedController.forward()
            speedController.straight()
        else:
            speedController.m2_speed(boost_speed // 2)

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

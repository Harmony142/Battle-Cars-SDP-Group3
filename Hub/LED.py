
import multiprocessing
from hub_common import connect_to_bluetooth
import time

mac_addresses = [
    '20:20:03:19:06:58',
    '20:20:03:19:31:96'
]

"""
Bit Positions
76543210
0-1: Car Number
2: Ensuing Customization Data
3: Boost Enabled
4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
"""


def a(mac_address):
    bluetooth_socket = connect_to_bluetooth(mac_address)
    while 1:
        time.sleep(4)
        command_flags = 0b00000100

        bluetooth_socket.send(command_flags.to_bytes(1, "little"))
        bluetooth_socket.send(0x07.to_bytes(1, "little"))
        bluetooth_socket.send(0xff.to_bytes(1, "little"))
        bluetooth_socket.send(0x00.to_bytes(1, "little"))
        bluetooth_socket.send(0xff.to_bytes(1, "little"))


def b(mac_address):
    bluetooth_socket = connect_to_bluetooth(mac_address)
    while 1:
        time.sleep(4)
        command_flags = 0b00000100

        bluetooth_socket.send(command_flags.to_bytes(1, "little"))
        bluetooth_socket.send(0x00.to_bytes(1, "little"))
        bluetooth_socket.send(0xff.to_bytes(1, "little"))
        bluetooth_socket.send(0xff.to_bytes(1, "little"))
        bluetooth_socket.send(0xff.to_bytes(1, "little"))


if __name__ == '__main__':
    car_1 = multiprocessing.Process(target=a,
                                    kwargs={'mac_address': mac_addresses[0]},
                                    daemon=True)
    car_2 = multiprocessing.Process(target=b,
                                    kwargs={'mac_address': mac_addresses[1]},
                                    daemon=True)
    car_1.start()
    car_2.start()

    while 1:
        time.sleep(10)


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
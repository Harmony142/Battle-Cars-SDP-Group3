
import bluetooth
from time import sleep
import keyboard
from inputs import devices

"""
----- TO INSTALL PYBLUEZ ON WINDOWS -----
https://visualstudio.microsoft.com/downloads/
Download and run visual studio community edition installer
Select Visual C++ build tools workload and install

https://github.com/pybluez/pybluez/issues/180
Install anaconda
create a python 3.7 env using conda create -n <name> python==3.7
find conda env file, mine was C:\\Users\\logan\\.conda\\envs\\pybluez

Install git
create a file anywhere, open it and run powershell as admin using file in top left
git clone https://github.com/pybluez/pybluez
cd pybluez
<conda env file>/python.exe setup.py install
"""
# TODO test if updates only happen on state change
# TODO test if boost bug is fixed
# TODO test if WASD bug is fixed
# TODO test if we can control the car with controller if plugged in
# TODO investigate multithreading/REST interfaces to allow streaming commands to multiple cars
# TODO see if we can connect to HC-05's without passwords disabled, not vital

# Pair HC-05 with PC first
target_name = "HC-05"
target_address = None

# Variables for controlling boost logic.
# TODO tweak these until they are reasonable, like a couple seconds of boost then a longer recharge
# TODO maybe change it to an all or nothing thing, ie can only boost when tank full, goes until empty
boost_tank_max_capacity = 100
boost_tank = boost_tank_max_capacity
boost_tank_depletion_rate = 10

# Try reconnecting if it fails to connect or the connection is lost
previous_command_flags = 0x00
while True:
    try:
        # Scan for nearby devices
        print('Scanning for nearby devices...')
        nearby_devices = bluetooth.discover_devices()

        # Try and find our bluetooth module
        print('Searching for our bluetooth module...')
        for bluetooth_device_address in nearby_devices:
            print(bluetooth.lookup_name(bluetooth_device_address))
            if target_name == bluetooth.lookup_name(bluetooth_device_address):
                target_address = bluetooth_device_address
                break

        # Connect to our bluetooth module if we found it
        if target_address is not None:
            print("Found target bluetooth device with address ", target_address)
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

            print("Attempting to connect")
            # Loop over ports until we find one that works (kinda hacky but it works)
            i = 0
            max_port = 3
            for port in range(i, max_port + 1):
                print("Checking Port ", i)
                try:
                    sock.connect((target_address, port))
                    break
                except Exception as e:  # TODO figure out what type of exception sock raises
                    pass

            # Retry connection if we failed to connect
            if i > max_port:
                raise OSError('Failed to connect')

            '''
            Send user commands over the network, reading from a plugged in controller or WASD on the keyboard
            Bit Positions
            76543210
            0: Y pressed
            1: B pressed
            2: A pressed
            3: X pressed
            4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
            6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
            '''
            while True:
                command_flags = 0x00

                try:
                    # Try to find a controller if plugged in
                    events = devices.gamepads[0].read()
                    for event in events:
                        # Ignore sync messages, no interesting information
                        if event.ev_type == 'Sync':
                            continue

                        # Interpret buttons
                        if event.code == 'BTN_NORTH':
                            command_flags |= event.state << 0
                        elif event.code == 'BTN_EAST':
                            command_flags |= event.state << 1
                        elif event.code == 'BTN_SOUTH':
                            command_flags |= event.state << 2
                        elif event.code == 'BTN_WEST':
                            command_flags |= event.state << 3

                        # Interpret d-pad
                        elif event.code == 'ABS_HAT0Y':
                            event.state = 2 if event.state < 0 else event.state
                            command_flags |= event.state << 4
                        elif event.code == 'ABS_HAT0X':
                            event.state = 2 if event.state < 0 else event.state
                            command_flags |= event.state << 6

                        # Interpret left joystick
                        elif event.code == 'ABS_Y':
                            if event.state > 4000:
                                command_flags |= 1 << 5
                            elif event.state < -4000:
                                command_flags |= 1 << 4
                        elif event.code == 'ABS_X':
                            if event.state > 4000:
                                command_flags |= 1 << 7
                            elif event.state < -4000:
                                command_flags |= 1 << 6

                except IndexError:
                    # Read keyboard commands since we couldn't find a controller
                    if keyboard.is_pressed('s'):
                        command_flags |= 1 << 4
                    if keyboard.is_pressed('w'):
                        command_flags |= 1 << 5
                    if keyboard.is_pressed('a'):
                        command_flags |= 1 << 6
                    if keyboard.is_pressed('d'):
                        command_flags |= 1 << 7

                    if keyboard.is_pressed('shift'):
                        command_flags |= 0b1111

                # Boost logic
                if boost_tank < boost_tank_max_capacity:
                    boost_tank += 1
                if command_flags & 0b1111:
                    if boost_tank < boost_tank_depletion_rate:
                        command_flags &= 0b1111 << 4
                    else:
                        boost_tank -= boost_tank_depletion_rate

                # Send the data over bluetooth if the state has changed
                if command_flags != previous_command_flags:
                    print('Sending: {0:#010b}'.format(command_flags))
                    sock.send(command_flags)
                    previous_command_flags = command_flags

                    # Limit how fast we can send updates to once every 10th of a second
                    # as not to overwhelm the receiver's message buffer
                    sleep(.1)

        else:
            print("Failed to find target bluetooth device nearby")
    except OSError:
        print('Disconnected from bluetooth receiver, attempting to reconnect')

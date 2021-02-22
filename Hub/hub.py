from time import sleep
import keyboard
from hub_common import connect_to_database, connect_to_bluetooth,\
    read_keyboard_commands, read_controller_commands, read_database_commands

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
client, shard_iterator = connect_to_database()

# TODO check if relative imports are going to work properly or if they will bug out when running hub.py
# TODO test if updates only happen on state change
# TODO test if boost bug is fixed
# TODO test if WASD bug is fixed
# TODO add controls to webpage
# TODO add score feedback to webpage
# TODO test if we can control the car with controller if plugged in
# TODO investigate multithreading/REST interfaces to allow streaming commands to multiple cars
# TODO see if we can connect to HC-05's without passwords disabled, not vital

# Pair HC-05 with PC first
target_name = 'HC-06'
target_address = None

# Variables for controlling boost logic.
# TODO tweak these until they are reasonable, like a couple seconds of boost then a longer recharge
# TODO probably should re-implement this using time so we can precisely say x seconds of boost
# TODO maybe change it to an all or nothing thing, ie can only boost when tank full, goes until empty
# TODO add boost tank feedback to webpage
boost_tank_max_capacity = 100
boost_tank = boost_tank_max_capacity
boost_tank_depletion_rate = 10

# List of cars in the format [car index, target name/MAC address, port, socket, boost_tank]
targets = [
    ['HC-05', None, boost_tank_max_capacity],
    ['HC-06', None, boost_tank_max_capacity]
]
# TODO update the command flags scheme to indicate car number

# Try reconnecting if it fails to connect or the connection is lost
previous_command_flags = 0x00
while True:
    #try:
    for target in targets:
        target[2] = connect_to_bluetooth(target[0], 1)

    keyboard_override_hot_key = 't'
    keyboard_override = False
    while True:
        # Toggle for keyboard override. If you want to control from the hub directly
        if keyboard.is_pressed(keyboard_override_hot_key):
            # Switch toggle and wait until key is not pressed
            keyboard_override = not keyboard_override
            print("Toggled keyboard override: ", "on" if keyboard_override else "off")
            while keyboard.is_pressed(keyboard_override_hot_key):
                pass

        # Read from different control sources
        command_flags = 0x00
        source_string = 'Controller'
        try:
            # Raises index error if a controller is not found
            command_flags = read_controller_commands()
        except IndexError:
            # Read keyboard commands since we couldn't find a controller
            source_string = 'Database'
            command_flags, shard_iterator =\
                read_database_commands(client, shard_iterator, previous_command_flags)
            if keyboard_override:
                source_string = 'Keyboard'
                command_flags = read_keyboard_commands()

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
            """
            Bit Positions
            76543210
            0: Y pressed
            1: B pressed
            2: A pressed
            3: X pressed
            4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
            6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
            """
            print('Sending {0:#010b} from {1}'.format(command_flags, source_string))
            for i, target in enumerate(targets):
                try:
                    if target[2] is None:
                        raise OSError('Socket does not exist')
                    target[2].send(command_flags.to_bytes(1, "little"))
                except OSError:
                    print('Disconnected from car {}, attempting to reconnect'.format(i + 1))
                    # TODO see if we can get this to not be a blocking call so that the other cars can keep driving
                    # "pauses the game" so to speak
                    target[2] = connect_to_bluetooth(target[0], 1)
            previous_command_flags = command_flags

            # Limit how fast we can send updates to once every 10th of a second
            # as not to overwhelm the receiver's message buffer
            # sleep(.1) TODO check if we should do something like this


    #except OSError:
    #

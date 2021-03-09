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

# TODO test if updates only happen on state change
# TODO test if boost bug is fixed
# TODO test if WASD bug is fixed
# TODO add controls to webpage
# TODO add score feedback to webpage
# TODO test if we can control the car with controller if plugged in
# TODO see if we can connect to HC-05's without passwords disabled, not vital
# TODO make boost always available, but you can't steer while it's active

# List of cars in the format [device name, MAC address, socket]
targets = [
    ['HC-05', None, None],
    ['HC-06', None, None]
]
"""
targets = [
    ['HC-05', '98:D3:32:11:0B:77', None],
    ['HC-06', '20:20:03:19:06:47', None]
]
"""

# Try reconnecting if it fails to connect or the connection is lost
previous_command_flags = 0x00

keyboard_override_hot_key = 't'
keyboard_override = False

# TODO this is temporary remove this when implementing the final version
swap_receiver_hot_key = 'r'
swap_receiver = False
#
while True:
    # Toggle for keyboard override. If you want to control from the hub directly
    if keyboard.is_pressed(keyboard_override_hot_key):
        # Switch toggle and wait until key is not pressed
        keyboard_override = not keyboard_override
        print("Toggled keyboard override: ", "on" if keyboard_override else "off")
        while keyboard.is_pressed(keyboard_override_hot_key):
            pass

    # TODO this is temporary remove this when implementing the final version
    if keyboard.is_pressed(swap_receiver_hot_key):
        # Switch toggle and wait until key is not pressed
        swap_receiver = not swap_receiver
        print("Swapped receiver to: ", "HC-06" if swap_receiver else "HC-05")
        while keyboard.is_pressed(swap_receiver_hot_key):
            pass
    #

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

    # TODO this is temporary remove this when implementing the final version
    command_flags |= 0b01 if swap_receiver else 0b00
    #

    # Send the data over bluetooth if the state has changed
    if command_flags != previous_command_flags:
        """
        Bit Positions
        76543210
        0-1: Car Number
        2: Unused currently
        3: Boost Enabled
        4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
        6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
        """

        print('Sending {0:#010b} from {1}'.format(command_flags, source_string))
        for target in targets:
            try:
                if target[2] is None:
                    raise OSError('Socket does not exist')
                target[2].send(command_flags.to_bytes(1, "little"))
            except OSError:
                print('Disconnected from {}, attempting to reconnect'.format(target[0]))
                try:
                    connect_to_bluetooth(target)
                except ConnectionError as e:
                    print(e)
        previous_command_flags = command_flags

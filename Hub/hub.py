
import datetime
import keyboard
from hub_common import connect_to_bluetooth, initialize_sqs_client, read_from_sqs,\
    initialize_dynamodb_client, push_to_database, read_keyboard_commands, initialize_ports

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
# Initialize the client for streaming user commands from SQS
sqs_client = initialize_sqs_client()

# Initialize the client for sending the score back to users
dynamodb_client = initialize_dynamodb_client()

# TODO test if updates only happen on state change
# TODO test if boost bug is fixed
# TODO test if WASD bug is fixed
# TODO make boost always available, but you can't steer while it's active
# TODO make the match only start when all 4 players have joined
# TODO check that the timer works

# List of cars in the format [device name, MAC address, socket, player_name, previous_command_flags]
targets = [
    ['HC-06', '20:20:03:19:06:58', None, None, 0x00],
    ['HC-06', '20:20:03:19:31:96', None, None, 0x00]
]

# Car PCB 1: 20:20:03:19:06:58
# Car PCB 2: 20:20:03:19:31:96
# TODO update the command flags scheme to allow customization
# Try reconnecting if it fails to connect or the connection is lost
previous_command_flags = 0x00

keyboard_override_hot_key = 't'
keyboard_override = False

# Score keeping setup
ports = initialize_ports()
score_red, score_blue = 0, 0
set_score_hot_key = 'p'


# Timing
game_time = 20  # Minutes
time_between_updates = datetime.timedelta(seconds=1)
previous_update_time = datetime.datetime.now()
end_time = previous_update_time + datetime.timedelta(minutes=game_time)


def reset(client):
    # Get the global variables instead of making new local ones
    global score_red, score_blue, end_time

    # Reset the score
    score_red, score_blue = 0, 0

    # Remove players from the cars
    for target in targets:
        target[3] = None

    # Reset the timer
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=game_time)

    # Push everything to the database
    push_to_database(dynamodb_client, score_red, score_blue, end_time - datetime.datetime.now(), targets)


while True:
    # Check if a goal is trying to send us a score
    for port in ports:
        if port.in_waiting:
            line = port.readline().decode('utf-8').strip()
            for team in ['RED', 'BLUE']:
                if line == 'GOAL ' + team:
                    globals()['score_' + team.lower()] += 1
                    print(line, '\nRED:', score_red, '\nBLUE:', score_blue)

    # Update database once a second for timer and car ownership
    if previous_update_time + time_between_updates < datetime.datetime.now():
        previous_update_time = datetime.datetime.now()
        push_to_database(dynamodb_client, score_red, score_blue,
                         end_time - previous_update_time, targets)

    # TODO make an automated version of this
    if keyboard.is_pressed(set_score_hot_key):
        # Switch toggle and wait until key is not pressed
        print("Resetting Score")
        score_red, score_blue = input('New Red Score: '), input('New Blue Score: ')
        push_to_database(dynamodb_client, score_red, score_blue, end_time - datetime.datetime.now(), targets)
        while keyboard.is_pressed(set_score_hot_key):
            pass

    # Toggle for keyboard override. If you want to control from the hub directly
    if keyboard.is_pressed(keyboard_override_hot_key):
        # Switch toggle and wait until key is not pressed
        keyboard_override = not keyboard_override
        print("Toggled keyboard override: ", "on" if keyboard_override else "off")
        while keyboard.is_pressed(keyboard_override_hot_key):
            pass

    # Read from different control sources
    command_flags = 0x00

    # Read keyboard commands
    if keyboard_override:
        source_string = 'Keyboard'
        # Keyboard command only ever controls car 1
        command_flags = read_keyboard_commands()
    else:
        source_string = 'SQS'
        command_flags, start_time = read_from_sqs(sqs_client, targets)

    # Send the data over bluetooth if the state for the designated car has changed
    if command_flags is not None and command_flags != targets[command_flags & 0b11][4]:
        """
        Bit Positions
        76543210
        0-1: Car Number
        2: Unused currently
        3: Boost Enabled
        4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
        6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
        """
        # print('Sending {0:#010b} from {1}'.format(command_flags, source_string))

        for target in targets:
            try:
                if target[2] is None:
                    raise OSError('Socket does not exist')
                print('Sending {0:#010b} from {1}'.format(command_flags, source_string))
                target[2].send(command_flags.to_bytes(1, "little"))
            except OSError:
                print('Disconnected from {}, attempting to reconnect'.format(target[0]))
                try:
                    connect_to_bluetooth(target)
                except ConnectionError as e:
                    print(e)

        targets[command_flags & 0b11][4] = command_flags

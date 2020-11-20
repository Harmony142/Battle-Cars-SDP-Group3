
import bluetooth
from time import sleep
import keyboard
from inputs import devices
import boto3
import csv
import json

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


def read_keyboard_commands():
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
    cmd_flags = 0x00
    if keyboard.is_pressed('s'):
        cmd_flags |= 1 << 4
    if keyboard.is_pressed('w'):
        cmd_flags |= 1 << 5
    if keyboard.is_pressed('a'):
        cmd_flags |= 1 << 6
    if keyboard.is_pressed('d'):
        cmd_flags |= 1 << 7

    if keyboard.is_pressed('shift'):
        cmd_flags |= 0b1111

    return cmd_flags


def read_controller_commands():
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
    cmd_flags = 0x00

    # Try to find a controller if plugged in
    events = devices.gamepads[0].read()
    for event in events:
        # Ignore sync messages, no interesting information
        if event.ev_type == 'Sync':
            continue

        # Interpret buttons
        if event.code == 'BTN_NORTH':
            cmd_flags |= event.state << 0
        elif event.code == 'BTN_EAST':
            cmd_flags |= event.state << 1
        elif event.code == 'BTN_SOUTH':
            cmd_flags |= event.state << 2
        elif event.code == 'BTN_WEST':
            cmd_flags |= event.state << 3

        # Interpret d-pad
        elif event.code == 'ABS_HAT0Y':
            event.state = 2 if event.state < 0 else event.state
            cmd_flags |= event.state << 4
        elif event.code == 'ABS_HAT0X':
            event.state = 2 if event.state < 0 else event.state
            cmd_flags |= event.state << 6

        # Interpret left joystick
        elif event.code == 'ABS_Y':
            if event.state > 4000:
                cmd_flags |= 1 << 5
            elif event.state < -4000:
                cmd_flags |= 1 << 4
        elif event.code == 'ABS_X':
            if event.state > 4000:
                cmd_flags |= 1 << 7
            elif event.state < -4000:
                cmd_flags |= 1 << 6

    return cmd_flags


def read_database_commands(cl, it):
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
    response = cl.get_records(
        ShardIterator=it
        # Limit=1
    )
    # pp.pprint(response['Records'])
    if 'NextShardIterator' in response.keys():
        it = response['NextShardIterator']

    if 'Records' in response.keys() and len(response['Records']) > 0:
        keys_pressed = json.loads(response['Records'][0]['dynamodb']['NewImage']['description']['S'])

        cmd_flags = 0x00

        if keys_pressed['KeyS']:
            cmd_flags |= 1 << 4
        if keys_pressed['KeyW']:
            cmd_flags |= 1 << 5
        if keys_pressed['KeyA']:
            cmd_flags |= 1 << 6
        if keys_pressed['KeyD']:
            cmd_flags |= 1 << 7

        if keys_pressed['ShiftLeft']:
            cmd_flags |= 0b1111
    else:
        cmd_flags = previous_command_flags

    return cmd_flags, it


# Variables for connecting to the database for streaming commands from the web page
# TODO make this robust it just connects once when you launch hub.py
table_name = 'Todo-fkgtez5rpfcoferxahyyjer5i4-dev'
credentials_csv_file_name = 'dynamodb-stream-readonly-creds.csv'

with open(credentials_csv_file_name, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    credentials = next(reader)

# Connect to AWS DynamoDB API
client = boto3.client(
    service_name='dynamodbstreams',
    region_name='us-east-2',
    aws_access_key_id=credentials['Access key ID'],
    aws_secret_access_key=credentials['Secret access key'])

# Find the correct stream ARN
print('Attempting to connect to table: ', table_name)
response = client.list_streams(
    TableName=table_name
)
stream_arn = None
for stream in response['Streams']:
    if stream['TableName'] == table_name:
        stream_arn = stream['StreamArn']
        break
if stream_arn is None:
    raise ValueError('Table name {} not found in current account or no streams available'.format(table_name))
print('Found stream: ', stream_arn)

# Get the latest shard
response = client.describe_stream(
    StreamArn=stream_arn
)
shard_id = response['StreamDescription']['Shards'][2]['ShardId']

# Get the first shard iterator of the latest shard
response = client.get_shard_iterator(
    StreamArn=stream_arn,
    ShardId=shard_id,
    ShardIteratorType='LATEST',
)
# pp.pprint(response['ShardIterator'])
shard_iterator = response['ShardIterator']
print('Shard iterator: ', shard_iterator)


# TODO test if updates only happen on state change
# TODO test if boost bug is fixed
# TODO test if WASD bug is fixed
# TODO add controls to webpage
# TODO add score feedback to webpage
# TODO test if we can control the car with controller if plugged in
# TODO investigate multithreading/REST interfaces to allow streaming commands to multiple cars
# TODO see if we can connect to HC-05's without passwords disabled, not vital

# Pair HC-05 with PC first
target_name = "HC-05"
target_address = None

# Variables for controlling boost logic.
# TODO tweak these until they are reasonable, like a couple seconds of boost then a longer recharge
# TODO probably should re-implement this using time so we can precisely say x seconds of boost
# TODO maybe change it to an all or nothing thing, ie can only boost when tank full, goes until empty
# TODO add boost tank feedback to webpage
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
            port = 0
            max_port = 3
            for port in range(port, max_port + 1):
                print("Checking Port ", port)
                try:
                    sock.connect((target_address, port))
                    break
                except Exception as e:  # TODO figure out what type of exception sock raises
                    pass

            # Retry connection if we failed to connect
            if port > max_port:
                raise OSError('Failed to connect')

            print('Connected to {} at {}:{}'.format(target_name, target_address, port))

            keyboard_override_hot_key = 't'
            keyboard_override = False
            while True:
                # Toggle for keyboard override. If you want to control from the hub directly
                if keyboard.is_pressed(keyboard_override_hot_key):
                    # Switch toggle and wait until key is not pressed
                    keyboard_override = not keyboard_override
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
                    command_flags, shard_iterator = read_database_commands(client, shard_iterator)
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
                    sock.send(command_flags.to_bytes(1, "little"))
                    previous_command_flags = command_flags

                    # Limit how fast we can send updates to once every 10th of a second
                    # as not to overwhelm the receiver's message buffer
                    # sleep(.1) TODO check if we should do something like this

        else:
            print("Failed to find target bluetooth device nearby")
    except OSError:
        print('Disconnected from bluetooth receiver, attempting to reconnect')

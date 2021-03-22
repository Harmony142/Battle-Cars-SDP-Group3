
import datetime
import sys
import glob
import serial
import bluetooth
import keyboard
from inputs import devices
import json
import boto3
import csv
import pprint
pp = pprint.PrettyPrinter(indent=4)


def initialize_sqs_client():
    # Variables for connecting to the sqs queue holding user commands
    credentials_csv_file_name = 'sqs-read-delete-creds.csv'

    with open(credentials_csv_file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        credentials = next(reader)

    # Connect to AWS SQS
    client = boto3.client(
        service_name='sqs',
        region_name='us-east-2',
        aws_access_key_id=credentials['Access key ID'],
        aws_secret_access_key=credentials['Secret access key'])
    return client


def read_from_sqs(client):
    queue_url = 'https://sqs.us-east-2.amazonaws.com/614103748137/user-commands.fifo'

    response = client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=1
    )

    if 'Messages' in response.keys():
        payload = json.loads(response['Messages'][0]['Body'])

        current_time = datetime.datetime.now().timestamp() * 1000
        print('Website command to retrieval:', current_time - payload['StartTime'], 'ms')

        """
        Bit Positions
        76543210
        0-1: Car Number
        2: Unused currently
        3: Boost Enabled
        4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
        6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
        """
        cmd_flags = 0x00
        if bool(payload['KeyS']):
            cmd_flags |= 1 << 4
        if bool(payload['KeyW']):
            cmd_flags |= 1 << 5
        if bool(payload['KeyA']):
            cmd_flags |= 1 << 6
        if bool(payload['KeyD']):
            cmd_flags |= 1 << 7

        if bool(payload['ShiftLeft']):
            cmd_flags |= 1 << 3

        return cmd_flags


def initialize_ports():
    """ Lists serial port names
        adapted from https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-py

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(11)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    available_ports = []
    for port in ports:
        try:
            s = serial.Serial(port=port, baudrate=115200, timeout=1)
            available_ports.append(s)
        except (OSError, serial.SerialException):
            pass

    return available_ports


def connect_to_bluetooth(target):
    """
    Connects to a target bluetooth device via MAC address if available or by searching for device name

    :param target:  list with structure [device name, MAC address, socket]
    :raises ValueError: if target structure is invalid or useless, requires user intervention
    :raises ConnectionError: if we fail to connect to the target, should not require user intervention
    """

    # Check that input is useful
    if target[0] is None and target[1] is None:
        raise ValueError('No connection information')

    # Check input class of device name
    if target[0] is not None and target[0].__class__ is not str:
        raise ValueError('Target must be string or None')

    # Check input class of MAC address
    if target[1] is not None and target[1].__class__ is not str:
        raise ValueError('MAC address must be string or None')

    # Check if the target fits the format of a MAC address
    if target[1] is not None:
        check = target[1].split(':')
        if len(check) != 6 or not all(len(key) == 2 for key in check):
            raise ValueError('Invalid MAC address')

    # Search for bluetooth device if MAC address is not provided
    if target[1] is None:
        # Scan for nearby devices
        print('Scanning for nearby devices...')
        nearby_devices = bluetooth.discover_devices()

        # Try and find our bluetooth module
        print('Searching for our bluetooth module...')
        for bluetooth_device_address in nearby_devices:
            print(bluetooth.lookup_name(bluetooth_device_address))
            if bluetooth.lookup_name(bluetooth_device_address) == target[0]:
                target[1] = bluetooth_device_address
                break

        # Check we found our target
        if target[1] is None:
            raise ConnectionError('Failed to find target bluetooth device nearby')

        print('Found target bluetooth device', target[0], 'with address', target[1])

    port = 1
    print('Attempting to connect on port', port)
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    try:
        sock.connect((target[1], port))
    except OSError as e:
        # OSError when failing to connect, skip and go to next port unless we've run out of ports in the range
        raise ConnectionError('Failed to connect')

    print('Connected to {} at {}:{}'.format(target[0], target[1], port))
    target[2] = sock


def read_keyboard_commands():
    """
    Bit Positions
    76543210
    0-1: Car Number
    2: Unused currently
    3: Boost Enabled
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
        cmd_flags |= 1 << 3

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


'''
def read_database_commands(cl, it, previous_command_flags):
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
        print(keys_pressed)
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
'''


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


'''
# Variables for connecting to the sqs queue holding user commands
credentials_csv_file_name = 'sqs-read-delete-creds.csv'

with open(credentials_csv_file_name, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    credentials = next(reader)
    
credentials['Access key ID']
credentials['Secret access key']
'''


def initialize_sqs_client(access_key_id, secret_access_key):
    # Connect to AWS SQS
    return boto3.client(
        service_name='sqs',
        region_name='us-east-2',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key)


def read_from_sqs(sqs_client):
    queue_url = 'https://sqs.us-east-2.amazonaws.com/614103748137/user-commands.fifo'

    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=1
    )

    try:
        payload = json.loads(response['Messages'][0]['Body'])
        player_name = payload['PlayerName']

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

        return cmd_flags, payload['StartTime'], player_name
    except KeyError:
        pass
    except IndexError:
        pass

    return None, None, None


def initialize_dynamodb_client():
    # credentials_csv_file_name = 'dynamodb-update-only-creds.csv'
    #
    # with open(credentials_csv_file_name, newline='') as csvfile:
    #     reader = csv.DictReader(csvfile)
    #     credentials = next(reader)

    # Connect to AWS DynamoDB
    return boto3.client(
        service_name='dynamodb',
        region_name='us-east-2',
        aws_access_key_id='AKIAY563PRYUZJ2KYM52',
        aws_secret_access_key='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')


def push_game_state_to_database(dynamodb_client, score_red, score_blue, time_left):
    table_name = 'BattleCarsScore'

    attribute_updates = {
        'score_red': {
            'Value': {
                'N': str(score_red)
            }
        },
        'score_blue': {
            'Value': {
                'N': str(score_blue)
            }
        },
        'time_left': {
            'Value': {
                'S': str.join(':', str(time_left).split('.')[0].split(':')[1:])
            }
        }
    }

    dynamodb_client.update_item(
        TableName=table_name,
        Key={
            'id': {
                'N': '1'
            }
        },
        AttributeUpdates=attribute_updates
    )


def push_player_name_to_database(dynamodb_client, car_number, player_name):
    table_name = 'BattleCarsScore'

    attribute_updates = {
        'car_{}'.format(car_number): {
            'Value': {
                'S': player_name if player_name is not None else ''
            }
        }
    }

    dynamodb_client.update_item(
        TableName=table_name,
        Key={
            'id': {
                'N': '1'
            }
        },
        AttributeUpdates=attribute_updates
    )


def initialize_ports():
    """
    Opens non-bluetooth serial ports
    adapted from https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-py

    To find bluetooth COM ports, open settings then go to bluetooth and select "More Bluetooth Options".
    Inside "More Bluetooth Options", click on "COM Ports" and put the lower number in each pair (outgoing)

    :raises EnvironmentError:
        On unsupported or unknown platforms
    :returns:
        A list of the serial ports available on the system
    """
    bluetooth_com_ports = [3, 7]
    if sys.platform.startswith('win'):
        ports = set(['COM%s' % (i + 1) for i in range(11)]) - \
                set(['COM{}'.format(i + j) for i in range(0, 2) for j in bluetooth_com_ports])
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
            print(port)
            available_ports.append(s)
        except (OSError, serial.SerialException) as e:
            # print(e)
            pass
    return available_ports


def connect_to_bluetooth(mac_address):
    """
    Connects to a target bluetooth device via MAC address if available or by searching for device name

    :param mac_address:  MAC address of the target device. Can be found using get_mac_addresses.py
    :raises ValueError: if target structure is invalid or useless, requires user intervention
    :raises ConnectionError: if we fail to connect to the target, should not require user intervention
    """
    # Check input class of MAC address
    if mac_address.__class__ is not str:
        raise ValueError('MAC address must be string')

    # Check if the target fits the format of a MAC address
    check = mac_address.split(':')
    if len(check) != 6 or not all(len(key) == 2 for key in check):
        raise ValueError('Invalid MAC address')

    port = 1
    print('Attempting to connect on port', port)
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    try:
        sock.connect((mac_address, port))
    except OSError as e:
        # OSError when failing to connect, skip and go to next port unless we've run out of ports in the range
        raise ConnectionError('Failed to connect')

    print('Connected to {}:{}'.format(mac_address, port))
    return sock


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

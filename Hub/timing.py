
import keyboard
from hub_common import connect_to_bluetooth, initialize_sqs_client, read_from_sqs,\
    read_keyboard_commands, read_controller_commands, initialize_ports
import datetime

# Initialize the client for streaming user commands from SQS
sqs_client = initialize_sqs_client()

# List of cars in the format [device name, MAC address, socket]
targets = [
    # ['HC-05', None, None],
    ['HC-06', '20:20:03:19:06:58', None]
]

#20:20:03:19:06:58
# TODO update the command flags scheme to allow customization
# Try reconnecting if it fails to connect or the connection is lost
previous_command_flags = 0x00

# Score keeping setup
ports = initialize_ports()
score_blue, score_red = 0, 0

while True:
    # Read from different control sources
    command_flags = 0x00
    source_string = 'Controller'
    try:
        # Raises index error if a controller is not found
        command_flags = read_controller_commands()
    except IndexError:
        # Read keyboard commands since we couldn't find a controller
        source_string = 'SQS'
        command_flags, start_time = read_from_sqs(sqs_client)
        sqs_read_time = datetime.datetime.now().timestamp() * 1000

    # Send the data over bluetooth if the state has changed
    if command_flags is not None and command_flags != previous_command_flags:
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

                # Wait until PCB responds
                message_received = None
                while message_received is None:
                    for port in ports:
                        if port.in_waiting:
                            line = port.readline().decode('utf-8').strip()
                            if line == 'Message Received':
                                message_received = line

                current_time = datetime.datetime.now().timestamp() * 1000
                print('End to end time:', current_time - start_time, 'ms')

            except OSError:
                print('Disconnected from {}, attempting to reconnect'.format(target[0]))
                try:
                    connect_to_bluetooth(target)
                except ConnectionError as e:
                    print(e)
        previous_command_flags = command_flags
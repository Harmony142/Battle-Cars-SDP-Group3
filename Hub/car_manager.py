
import time
from hub_common import initialize_sqs_client, initialize_dynamodb_client, read_from_sqs, \
    push_player_name_to_database, connect_to_bluetooth


def car_manager(car_number, mac_address, sqs_access_key, sqs_secret_key):
    # Connect to SQS for streaming commands and DynamoDB for pushing player names back to the web page
    # sqs_client = initialize_sqs_client(sqs_access_key, sqs_secret_key)
    dynamodb_client = initialize_dynamodb_client()

    # Representation of a car in the format [device name, MAC address, socket, player_name, previous_command_flags]
    bluetooth_socket = None
    active_player_name = None
    previous_command_flags = 0x00
    car_index = car_number - 1

    while 1:
        """
        # Read from SQS
        command_flags, start_time, command_player_name = read_from_sqs(sqs_client)
        
        if active_player_name is None:
            # Claim a car and update the database
            active_player_name = command_player_name
            push_player_name_to_database(dynamodb_client, car_number, active_player_name)
            
        # Append which car this is targeting
        command_flags |= car_index
    
        # Send the data over bluetooth if the state for the designated car has changed
        # Ignore commands coming from players who do not own this car once it is claimed
        """
        command_flags = 1 << 5
        command_flags |= car_index

        # if command_flags is not None and command_flags != previous_command_flags \
        #         and command_player_name == active_player_name:
        if 1:
            """
            Bit Positions
            76543210
            0-1: Car Number
            2: Unused currently
            3: Boost Enabled
            4-5: Forwards/Backwards - 00-Nothing, 01-Backwards, 10-Forwards, 11-Nothing
            6-7: Left/Right - 00-Nothing, 01-Right, 10-Left, 11-Nothing
            """
            try:
                if bluetooth_socket is None:
                    raise OSError('Socket does not exist')
                print('Sending {0:#010b} to {1}'.format(command_flags, car_number))
                bluetooth_socket.send(command_flags.to_bytes(1, "little"))
            except OSError:
                print('Disconnected from car {}, attempting to reconnect'.format(car_number))
                try:
                    bluetooth_socket = connect_to_bluetooth(mac_address)
                except ConnectionError as e:
                    print(e)

            time.sleep(2)
            previous_command_flags = command_flags

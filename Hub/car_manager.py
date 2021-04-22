
from hub_common import initialize_sqs_client, initialize_dynamodb_client, read_from_sqs, \
    push_player_name_to_database, connect_to_bluetooth, pattern_map


def car_manager(car_number, mac_address):
    car_number = int(car_number)

    # Connect to SQS for streaming commands and DynamoDB for pushing player names back to the web page
    sqs_client = initialize_sqs_client()
    dynamodb_client = initialize_dynamodb_client()

    # Representation of a car in the format [device name, MAC address, socket, player_name, previous_command_flags]
    bluetooth_socket = None
    active_player_name = None
    previous_command_flags = None
    current_customization_data = {'Pattern': pattern_map['Rainbow'], 'Red': 50, 'Green': 50, 'Blue': 50}
    car_index = car_number - 1

    # Clear the player name in the DynamoDB table
    push_player_name_to_database(dynamodb_client, car_number, active_player_name)

    while 1:
        # Read from SQS
        command_flags, command_player_name, customization_data = read_from_sqs(sqs_client, car_number)
        
        if command_player_name is not None and active_player_name is None:
            # Claim a car and update the database
            active_player_name = command_player_name
            print(active_player_name, 'connected to Car', car_number)
            push_player_name_to_database(dynamodb_client, car_number, active_player_name)
    
        # Send the data over bluetooth if the state for the designated car has changed
        # Ignore commands coming from players who do not own this car once it is claimed
        if command_flags is not None and command_player_name == active_player_name \
                and (previous_command_flags is None or command_flags != previous_command_flags
                     or current_customization_data != customization_data):
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
                    print('First connection for Car {}, attempting to connect'.format(car_number))
                    bluetooth_socket = connect_to_bluetooth(mac_address)

                print('Sending {0:#010b} to Car {1}'.format(command_flags, car_number))

                # Always send command_flags
                bluetooth_socket.send(command_flags.to_bytes(1, "little"))

                # Send customization data if present
                if customization_data is not None:
                    print('Sending Customization Data ({Pattern}, {Red}, {Green}, {Blue}) to Car'.format(
                        **customization_data), car_number)
                    bluetooth_socket.send(customization_data['Pattern'].to_bytes(1, "little"))
                    bluetooth_socket.send(customization_data['Red'].to_bytes(1, "little"))
                    bluetooth_socket.send(customization_data['Green'].to_bytes(1, "little"))
                    bluetooth_socket.send(customization_data['Blue'].to_bytes(1, "little"))
                    current_customization_data = customization_data

            except OSError:
                print('Disconnected from car {}, attempting to reconnect'.format(car_number))
                try:
                    bluetooth_socket = connect_to_bluetooth(mac_address)
                except ConnectionError as e:
                    print(e)

            previous_command_flags = command_flags

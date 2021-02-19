
import keyboard
from inputs import devices
import json

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
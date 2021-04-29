
import multiprocessing
import datetime
import keyboard
import logging
from serial import SerialException
from hub_common import initialize_dynamodb_client, push_game_state_to_database, initialize_ports
from car_manager import car_manager

# Set the logging level
logging.basicConfig(format='[%(asctime)s][%(filename)s][%(levelname)s]: %(message)s', level=logging.INFO)

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

# Car PCB 1: 20:20:03:19:06:58
# Car PCB 2: 98:D3:32:11:0B:77
# Car PCB 3: 20:20:03:19:31:96
# Car PCB 4: 20:20:03:19:10:31

if __name__ == '__main__':
    # MAC addressed of each car in car number order (ie first in list is car 1)
    mac_addresses = [
        '20:20:03:19:06:58',
        '98:D3:32:11:0B:77',
        '20:20:03:19:31:96',
        '20:20:03:19:10:31'
    ]

    # Initialize the client for sending the score and timer to the players
    dynamodb_client = initialize_dynamodb_client()

    # Score keeping setup
    score_red, score_blue = 0, 0
    set_state_hot_key = 'q'
    reset_car_hot_key = 'w'

    winner = ''
    overtime = False

    # Timing
    game_time = datetime.timedelta(minutes=30)  # Set to 30 minutes, will manually start the game with 2 min left
    overtime_duration = datetime.timedelta(seconds=30)  # minutes=1)  # Shorter matches for demo day
    time_before_reset = datetime.timedelta(seconds=7)
    time_between_updates = datetime.timedelta(seconds=1)
    previous_update_time = datetime.datetime.now()
    end_time = previous_update_time + game_time

    car_managers = [None] * len(mac_addresses)


    def reset_car_manager(car_index=None):
        global car_managers
        car_indices = [car_index] if car_index is not None else range(len(mac_addresses))

        # Restart the car managers
        for car_index in car_indices:
            if car_managers[car_index] is not None:
                car_managers[car_index].terminate()
            car_managers[car_index] = multiprocessing.Process(target=car_manager,
                                                              kwargs={'car_number': str(car_index + 1),
                                                                      'mac_address': mac_addresses[car_index]},
                                                              daemon=True)
            car_managers[car_index].start()


    def reset(client):
        # Get the global variables instead of making new local ones
        global score_red, score_blue, end_time, winner, overtime

        # Reset the game state
        score_red, score_blue = 0, 0
        end_time = datetime.datetime.now() + game_time
        winner = ''
        overtime = False
        reset_car_manager()

        # Push everything to the database
        push_game_state_to_database(client, score_red, score_blue, end_time - datetime.datetime.now(), winner, overtime)


    # Initialize State
    reset(dynamodb_client)

    # Catch SerialException in case a goal gets unplugged
    try:
        ports = initialize_ports()

        while True:
            # Check if a goal is trying to send us a score
            for port in ports:
                if port.in_waiting:
                    line = port.readline().decode('utf-8').strip()
                    for team in ['RED', 'BLUE']:
                        if line == 'GOAL ' + team:
                            globals()['score_' + team.lower()] += 1
                            logging.info('{}\nRED: {}\nBLUE: {}'.format(line, score_red, score_blue))

            # Update database once a second for timer and car ownership
            if previous_update_time + time_between_updates < datetime.datetime.now():
                previous_update_time = datetime.datetime.now()

                # End the game immediately if a goal is scored during overtime
                if overtime and score_red != score_blue:
                    end_time = previous_update_time

                # Check for special game states
                if (end_time - previous_update_time).total_seconds() <= 0:
                    if winner != '':
                        # Reset the game now that the time before reset is over
                        reset(dynamodb_client)

                    elif overtime:
                        # Overtime is over! Draw if scores are still the same
                        # Wait before resetting so the web page can render the victory
                        winner = 'Red Team' if score_red > score_blue else 'Blue Team' \
                            if score_blue > score_red else 'Draw'
                        end_time += time_before_reset

                    else:
                        # Normal game time is over! Check if we need to go to overtime, otherwise decide our winner
                        if score_red == score_blue:
                            # Extend the match for sudden death in overtime
                            overtime = True
                            end_time += overtime_duration
                        else:
                            # Wait before resetting so the web page can render the victory
                            winner = 'Red Team' if score_red > score_blue else 'Blue Team'
                            end_time += time_before_reset

                push_game_state_to_database(dynamodb_client, score_red, score_blue,
                                            end_time - previous_update_time, winner, overtime)

            # Manual control for setting the game state
            if keyboard.is_pressed(set_state_hot_key):
                # Switch toggle and wait until key is not pressed
                try:
                    try:
                        red_score = int(input('New Red Score [non neg int]: '))
                    except ValueError:
                        raise ValueError('Red Score must be a number')
                    if red_score < 0:
                        raise ValueError('Red Score must be a non-negative integer')

                    try:
                        blue_score = int(input('New Blue Score [non-neg int]: '))
                    except ValueError:
                        raise ValueError('Blue Score must be a number')
                    if blue_score < 0:
                        raise ValueError('Blue Score must be a non-negative integer')

                    time_left = input('Time Left [min:non-neg sec]: ').split(':')
                    try:
                        minutes, seconds = [int(value) for value in time_left]
                    except (ValueError, TypeError):
                        raise ValueError('Time Left must be in format "minutes:non-negative seconds')

                    sudden_death = input('Overtime [Y, N]: ')
                    if sudden_death not in ['Y', 'N']:
                        raise ValueError('Overtime must be Y or N')
                    sudden_death = sudden_death == 'Y'

                    win = input('Winner [N, R, B, D]: ')
                    if win not in ['N', 'R', 'B', 'D']:
                        raise ValueError('Winner must be N(one), R(ed), B(lue), or D(raw)')
                    win = 'Red Team' if win == 'R' else 'Blue Team' if win == 'B' else 'Draw' if win == 'D' else ''

                    # All values are valid at this point
                    logging.info('Setting game state')
                    score_red = red_score
                    score_blue = blue_score
                    end_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes, seconds=seconds)
                    overtime = sudden_death
                    winner = win

                except ValueError as e:
                    logging.warning(str(e))
                    logging.warning('Cancelling setting game state')

            # Manual control for resetting cars
            if keyboard.is_pressed(reset_car_hot_key):
                # Switch toggle and wait until key is not pressed
                values = [str(i) for i in range(1, len(mac_addresses) + 1)]
                values.append('all')
                reset_car = input('Reset car {}: '.format(values))
                if reset_car in values:
                    logging.warning('Resetting Cars')
                    reset_car_manager(int(reset_car) - 1 if reset_car.isnumeric() else None)
                else:
                    logging.warning('ValueError: Value mus be in {}'.format(values))
                    logging.warning('Cancelling resetting a car')
    except SerialException:
        logging.warning('SerialException: active serial connection was unplugged')
        logging.warning('RED: {}\nBLUE: {}\nTIME LEFT: {}'.format(
            score_red, score_blue, end_time - datetime.datetime.now()))

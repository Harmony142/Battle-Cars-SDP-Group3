
import multiprocessing
import datetime
import keyboard
from hub_common import initialize_dynamodb_client, push_game_state_to_database, initialize_ports
from car_manager import car_manager

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
# Car PCB 2: 20:20:03:19:31:96

if __name__ == '__main__':
    # Parameters for car managers, needs MAC Address and (access key ID, secret access key) for respective SQS queue
    mac_addresses = [
        # '20:20:03:19:06:58',
        # '20:20:03:19:31:96',
        '98:D3:32:11:0B:77',
        # '20:20:03:19:10:31'
    ]

    # Initialize the client for sending the score and timer to the players
    dynamodb_client = initialize_dynamodb_client()

    # TODO test if updates only happen on state change
    # TODO test if boost bug is fixed
    # TODO test if WASD bug is fixed
    # TODO make boost always available, but you can't steer while it's active
    # TODO make the match only start when all 4 players have joined
    # TODO check that the timer works
    # TODO update the command flags scheme to allow customization

    # Score keeping setup
    ports = initialize_ports()
    score_red, score_blue = 0, 0
    set_state_hot_key = 'q'
    reset_car_hot_key = 'w'

    winner = ''
    overtime = False

    # Timing
    game_time = datetime.timedelta(minutes=5)
    overtime_duration = datetime.timedelta(minutes=1)
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


    reset(dynamodb_client)

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
                    winner = 'Red Team' if score_red > score_blue else 'Blue Team' if score_blue > score_red else 'Draw'
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
            print('Setting Game State')
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
                print('Setting game state')
                score_red = red_score
                score_blue = blue_score
                end_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes, seconds=seconds)
                overtime = sudden_death
                winner = win

            except ValueError as e:
                print(e)
                print('Cancelling setting game state')

        # Manual control for resetting cars
        if keyboard.is_pressed(reset_car_hot_key):
            # Switch toggle and wait until key is not pressed
            values = [str(i) for i in range(1, len(mac_addresses) + 1)]
            values.append('all')
            reset = input('Reset car {}: '.format(values))
            if reset in values:
                print('Resetting Cars')
                reset_car_manager(int(reset) - 1 if reset.isnumeric() else None)
            else:
                print('ValueError: Value mus be in {}'.format(values))
                print('Cancelling resetting a car')


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
        '20:20:03:19:06:58',
        # '20:20:03:19:31:96',
        # '20:20:03:19:06:47',
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
    set_score_hot_key = 'p'

    # Timing
    game_time = 20  # Minutes
    time_between_updates = datetime.timedelta(seconds=1)
    previous_update_time = datetime.datetime.now()
    end_time = previous_update_time + datetime.timedelta(minutes=game_time)

    car_managers = []


    def reset(client):
        # Get the global variables instead of making new local ones
        global score_red, score_blue, end_time, car_managers

        # Reset the score
        score_red, score_blue = 0, 0

        # Restart the car managers
        for process in car_managers:
            process.kill()

        car_managers = []
        for i, mac_address in enumerate(mac_addresses):
            car_managers.append(multiprocessing.Process(target=car_manager,
                                                        kwargs={'car_number': str(i + 1), 'mac_address': mac_address},
                                                        daemon=True))
            car_managers[-1].start()

        # Reset the timer
        end_time = datetime.datetime.now() + datetime.timedelta(minutes=game_time)

        # Push everything to the database
        push_game_state_to_database(client, score_red, score_blue, end_time - datetime.datetime.now())


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
            push_game_state_to_database(dynamodb_client, score_red, score_blue, end_time - previous_update_time)

        # TODO make an automated version of this
        if keyboard.is_pressed(set_score_hot_key):
            # Switch toggle and wait until key is not pressed
            print("Resetting Score")
            score_red, score_blue = input('New Red Score: '), input('New Blue Score: ')
            while keyboard.is_pressed(set_score_hot_key):
                pass

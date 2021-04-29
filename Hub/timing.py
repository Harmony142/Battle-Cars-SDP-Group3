
# TODO timing stuff: calculate n using stats, loop over a range of values for message_rate, graph confidence intervals
# TODO                for each message_rate, one line for using SQS and one for just in system

import uuid
import numpy
import pandas
from scipy import stats
import json
import multiprocessing
import datetime
import time
import boto3
import os
import sys
import logging
from hub_common import initialize_ports, connect_to_bluetooth, interpret_command_payload
from car_manager import car_manager

# Set the logging level
logging.basicConfig(format='[%(asctime)s][%(filename)s][%(levelname)s]: %(message)s', level=logging.INFO)

# Number of commands to send to each car
n = 10  # 100?

# Z score for 95% confidence interval
z_score = 1.96

# Variables for intervals
starting_delay = 1000
ending_delay = 100
number_of_delays = 1  # 20
message_delays = numpy.linspace(start=starting_delay, stop=ending_delay, num=number_of_delays)

# MAC addresses of the connected cars
mac_addresses = [
    '20:20:03:19:06:58',
    '98:D3:32:11:0B:77',
    '20:20:03:19:31:96',
    '20:20:03:19:10:31'
]

# Lists for maintaining car indices, numbers, and names
car_indices = numpy.arange(len(mac_addresses))
car_numbers = car_indices + 1
car_names = ['Car {}'.format(car_number) for car_number in car_numbers]

# Name of the folder where timing data will be stored
timing_data_folder = 'TimingData'
start_times_file_path = os.path.join(timing_data_folder, 'StartTimes{}.csv')
response_times_file_path = os.path.join(timing_data_folder, 'ResponseTimes.csv')
sample_means_file_path = os.path.join(timing_data_folder, 'SampleMeans.csv')
standard_errors_file_path = os.path.join(timing_data_folder, 'StandardErrors.csv')
graph_file_path = os.path.join(timing_data_folder, 'ResponseTimes.jpg')

# Create our client for sending SQS commands to mock the website
sqs_send_client = boto3.client(
    service_name='sqs',
    region_name='us-east-2',
    aws_access_key_id='AKIAY563PRYUWD457KGQ',
    aws_secret_access_key='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'
)


# Function for sending SQS commands to a car's SQS queue
def send_to_sqs(car_number_, payload):
    message_id = str(uuid.uuid4())

    sqs_send_client.send_message(
        QueueUrl='https://sqs.us-east-2.amazonaws.com/614103748137/car-commands-{}.fifo'.format(car_number_),
        MessageBody=json.dumps(payload),
        DelaySeconds=0,
        MessageDeduplicationId=message_id,
        MessageGroupId=message_id
    )


# Used for testing without the cars
def mock_bluetooth_messenger(delay_, car_index_, mac_address_):
    # Time interval between commands
    message_rate = datetime.timedelta(milliseconds=int(delay_))

    # Table for measuring response times from the cars
    start_times_ = pandas.DataFrame(index=numpy.arange(n), columns=[car_names[car_index_]], dtype='datetime64')

    # Keep looping until all responses have been received
    messages_sent = 0

    # Send messages to our car at regular intervals
    while messages_sent < n:
        start_times_.at[messages_sent, car_names[car_index_]] = datetime.datetime.now() + message_rate * messages_sent
        messages_sent += 1

    # Record our results
    start_times_.to_csv(start_times_file_path.format(car_index_), index=False)
    sys.exit(0)


# Subprocess for sending periodic messages to an individual car
def bluetooth_messenger(delay_, car_index_, mac_address_):
    # Time interval between commands
    # message_rate = datetime.timedelta(milliseconds=int(delay_))

    # Table for measuring response times from the cars
    start_times_ = pandas.DataFrame(index=numpy.arange(n), columns=[car_names[car_index_]], dtype='datetime64')

    # Connect to the cars
    bluetooth_socket = None
    while bluetooth_socket is None:
        try:
            bluetooth_socket = connect_to_bluetooth(mac_address_)
        except ConnectionError:
            pass

    # Keep looping until all responses have been received
    messages_sent = 0
    next_message_time = datetime.datetime.now()

    # Previously sent command for each car
    command_payload_ = {
        'KeyW': False,
        'KeyA': False,
        'KeyS': False,
        'KeyD': False,
        'ShiftLeft': False
    }

    # Send messages to our car at regular intervals
    while messages_sent < n:
        # Send messages to each car's SQS queue if the time interval has passed
        time.sleep(delay_ / 1000)
        # if datetime.datetime.now() > next_message_time:
        # Send messages
        logging.info('Sending message', messages_sent)

        # Record the start time
        start_times_.at[messages_sent, car_names[car_index_]] = datetime.datetime.now()

        # Flip the command so the hub doesn't de-dupe it
        command_payload_['KeyW'] = not command_payload_['KeyW']
        bluetooth_socket.send(interpret_command_payload(command_payload_).to_bytes(1, "little"))

        # Wait until it's time to send another message
        # next_message_time = datetime.datetime.now() + message_rate
        messages_sent += 1

    # Record our results
    time.sleep(3)
    start_times_.to_csv(start_times_file_path.format(car_index_), index=False)
    sys.exit(0)


# Subprocess for sending messages to the cars via bluetooth
def solo_bluetooth_messenger(delay_, *mac_addresses_):
    # Time interval between commands
    # message_rate = datetime.timedelta(milliseconds=int(delay_))

    # Table for measuring response times from the cars
    start_times_ = pandas.DataFrame(index=numpy.arange(n), columns=car_names, dtype='datetime64')

    # Connect to the cars
    bluetooth_sockets_ = []
    for mac_address_ in mac_addresses_:
        bluetooth_socket = None
        while bluetooth_socket is None:
            try:
                bluetooth_socket = connect_to_bluetooth(mac_address_)
            except ConnectionError:
                pass
        bluetooth_sockets_.append(bluetooth_socket)

    # Keep looping until all responses have been received
    messages_sent = 0
    # next_message_time = datetime.datetime.now()

    # Previously sent command for each car
    command_payload_ = {
        'KeyW': False,
        'KeyA': False,
        'KeyS': False,
        'KeyD': False,
        'ShiftLeft': False
    }

    # Send messages to each car at regular intervals
    while messages_sent < n:
        # Send messages to each car's SQS queue if the time interval has passed
        # if datetime.datetime.now() > next_message_time:
        # Send messages
        logging.info('Sending message', messages_sent)
        time.sleep(delay_ / 1000)
        # Flip the command so the hub doesn't de-dupe it
        command_payload_['KeyW'] = not command_payload_['KeyW']
        for index_, socket_ in enumerate(bluetooth_sockets_):
            # Record the start time
            start_times_.at[messages_sent, car_names[index_]] = datetime.datetime.now()

            # Send to car TODO test if we should only call this once
            socket_.send(interpret_command_payload(command_payload_).to_bytes(1, "little"))

        # Wait until it's time to send another message
        # next_message_time = datetime.datetime.now() + message_rate
        messages_sent += 1

    # Record our results
    time.sleep(3)
    start_times_.to_csv(start_times_file_path.format('E2E'), index=False)
    sys.exit(0)


# Used for testing without the cars
def mock_sqs_messenger(delay_):
    # Time interval between commands
    message_rate = datetime.timedelta(milliseconds=int(delay_))

    # Table for measuring response times from the cars
    start_times_ = pandas.DataFrame(index=numpy.arange(n), columns=car_names, dtype='datetime64')

    # Keep looping until all responses have been received
    messages_sent = 0

    # Send messages to each car at regular intervals
    while messages_sent < n:
        # Send messages
        for index in car_indices:
            # Record the start time
            start_times_.at[messages_sent, car_names[index]] = datetime.datetime.now() + message_rate * messages_sent
        messages_sent += 1

    # Record our results
    start_times_.to_csv(start_times_file_path.format('E2E'), index=False)
    sys.exit(0)


# Subprocess for sending messages to the cars via SQS
def sqs_messenger(delay_):
    # Time interval between commands
    # message_rate = datetime.timedelta(milliseconds=int(delay_))

    # Table for measuring response times from the cars
    start_times_ = pandas.DataFrame(index=numpy.arange(n), columns=car_names, dtype='datetime64')

    # Keep looping until all responses have been received
    messages_sent = 0
    # next_message_time = datetime.datetime.now()

    # Previously sent command for each car
    command_payloads_ = [{
        'PlayerName': car_names[index],
        'KeyW': False,
        'KeyA': False,
        'KeyS': False,
        'KeyD': False,
        'ShiftLeft': False
    } for index in car_indices]

    # Send messages to each car at regular intervals
    while messages_sent < n:
        # Send messages to each car's SQS queue if the time interval has passed
        # if datetime.datetime.now() > next_message_time:
        # Send messages
        logging.info('Sending message', messages_sent)

        # Give the other processes time to wake up and respond
        time.sleep(delay_ / 1000)
        for index in car_indices:
            # Record the start time
            start_times_.at[messages_sent, car_names[index]] = datetime.datetime.now()

            # Flip the command so the hub doesn't de-dupe it
            command_payloads_[index]['KeyW'] = not command_payloads_[index]['KeyW']
            send_to_sqs(car_numbers[index], command_payloads_[index])

        # Wait until it's time to send another message
        # next_message_time = datetime.datetime.now() + message_rate
        messages_sent += 1

    # Record our results
    time.sleep(3)
    start_times_.to_csv(start_times_file_path.format('E2E'), index=False)
    sys.exit(0)


if __name__ == '__main__':
    # Record when the script started running
    timing_script_start_time = datetime.datetime.now()

    # Create the folder in the local directory if it doesn't already exist
    if not os.path.exists(timing_data_folder):
        os.makedirs(timing_data_folder)

    # Setup the ports so we can listen for serial responses from cars
    ports = initialize_ports()

    # Create our range of message_delays
    sample_means = numpy.zeros([2, number_of_delays])
    standard_errors = numpy.zeros([2, number_of_delays])

    # Get data for all message delays
    for x in numpy.arange(2):
        for i, message_delay in enumerate(message_delays):
            # Check if we're doing end-to-end or in-system delays
            messengers = []
            if x == 0:
                # Setup Car Infrastructure
                logging.info('Setting up car managers')
                car_managers = []
                for car_index, mac_address in enumerate(mac_addresses):
                    # Create subprocess for relaying commands to the cars from SQS
                    car_managers.append(multiprocessing.Process(target=car_manager,
                                                                kwargs={'car_number': car_numbers[car_index],
                                                                        'mac_address': mac_address},
                                                                daemon=True))
                    car_managers[-1].start()
                
                # Connect each of the cars using a customization command
                for car_index in car_indices:
                    send_to_sqs(car_numbers[car_index], {
                        'PlayerName': car_names[car_index],
                        'Pattern': 'Solid',
                        'Red': 255 if car_index in [0, 3] else 0,
                        'Green': 255 if car_index in [1, 3] else 0,
                        'Blue': 255 if car_index in [2, 3] else 0
                    })

                # Give the car managers time to connect to the cars
                time.sleep(5)

                # Create the subprocess for sending messages to the cars
                messengers = [multiprocessing.Process(target=mock_sqs_messenger,
                                                      kwargs={'delay_': message_delay},
                                                      daemon=True)]
                messengers[0].start()
            else:
                car_managers = []
                messengers = []
                for car_index, mac_address in enumerate(mac_addresses):
                    # Create the subprocess for sending messages to the cars
                    messengers.append(multiprocessing.Process(target=mock_bluetooth_messenger,
                                                              kwargs={'delay_': message_delay,
                                                                      'car_index_': car_index,
                                                                      'mac_address_': mac_address},
                                                              daemon=True))
                    messengers[-1].start()

            # Tables for measuring response times from the cars
            response_times = pandas.DataFrame(index=numpy.arange(n), columns=car_names, dtype='datetime64')
            response_indices = numpy.zeros(shape=len(mac_addresses), dtype='int')

            # For mock tests only
            offset = datetime.timedelta(seconds=8)
            delta = datetime.timedelta(milliseconds=message_delay)
            for car_index in car_indices:
                for j in numpy.arange(n):
                    response_times.at[j, car_names[car_index]] = \
                        datetime.datetime.now() + offset + delta * j

            """
            while response_times.tail(1).isna().any(None):
                # See if a car is reporting back to us
                for port in ports:
                    if port.in_waiting:
                        # Check if a car is responding to a message
                        line = port.readline().decode('utf-8').strip()
                        if line.startswith('Message Received by Car '):
                            logging.info(line)
                            # Strip the car index from the message
                            car_index = int(line.split()[-1])

                            # Record the response time
                            response_times.at[
                                response_indices[car_index], car_names[car_index]] = datetime.datetime.now()

                            # Update how many responses we've received from this car
                            response_indices[car_index] += 1
            """
            # Save and reload the data because I couldn't figure out how to force the types to lineup otherwise
            response_times.to_csv(response_times_file_path, index=False)
            response_times = pandas.read_csv(response_times_file_path, parse_dates=car_names)

            # Cleanup messengers
            for messenger in messengers:
                messenger.join()

            # Read the results and calculate the time differences
            if x == 0:
                start_times = pandas.read_csv(start_times_file_path.format('E2E'), parse_dates=car_names)
            else:
                start_times = pandas.concat([pandas.read_csv(start_times_file_path.format(index),
                                                             parse_dates=[car_names[index]]) for index in car_indices],
                                            axis=1)

            # Statistical analysis of results
            # Adapted from https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data
            delays = (response_times - start_times).values / numpy.timedelta64(1, 's') * 1e3
            N = n * len(mac_addresses)
            # sample_mean = delays.sum() / N
            sample_means[x][i] = delays.mean(axis=None)
            # standard_error_of_the_mean = numpy.sqrt((((delays - sample_mean) ** 2).sum() / (N - 1)) / N)
            standard_errors[x][i] = stats.sem(a=delays, axis=None)
            logging.info('{} Message Delay: {}\nSample Mean: {}\nStandard Error: {}'
                  .format('E2E' if x == 0 else 'BT', message_delay, sample_means[x][i], standard_errors[x][i]))

            # Cleanup sockets
            for process in car_managers:
                process.terminate()

    # Write our results
    numpy.savetxt(fname=sample_means_file_path, X=sample_means, delimiter=',')
    numpy.savetxt(fname=standard_errors_file_path, X=standard_errors, delimiter=',')
    logging.info('Total Script Running Time: {}'.format(datetime.datetime.now() - timing_script_start_time))

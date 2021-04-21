
# TODO game stuff: Win Screen, Overtime, 5 min games, automatic reset, manual reset for car 1, 2, 3, 4, or all,
# TODO             manual reset for team scores and timer

# TODO timing stuff: calculate n using stats, loop over a range of values for message_rate, graph confidence intervals
# TODO                for each message_rate, one line for using SQS and one for just in system

# TODO testing stuff: make sure the HC-05 works (DO FIRST), try out testing script, test game stuff

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
from hub_common import initialize_ports
from car_manager import car_manager

# Number of commands to send to each car
n = 10

# Confidence value for intervals
confidence = .95

# MAC addresses of the connected cars
mac_addresses = [
    '20:20:03:19:06:58',
    '20:20:03:19:31:96',
    '20:20:03:19:06:47',
    '20:20:03:19:10:31'
]

# Lists for maintaining car indices, numbers, and names
car_indices = numpy.arange(len(mac_addresses))
car_numbers = car_indices + 1
car_names = ['Car {}'.format(car_number) for car_number in car_numbers]

# Name of the folder where timing data will be stored
timing_data_folder = 'TimingData'
start_times_file_path = os.path.join(timing_data_folder, 'StartTimes.csv')
response_times_file_path = os.path.join(timing_data_folder, 'ResponseTimes.csv')
delays_file_path = os.path.join(timing_data_folder, 'Delays.csv')
statistics_file_path = os.path.join(timing_data_folder, 'Statistics.csv')

# Create our client for sending SQS commands to mock the website
sqs_send_client = boto3.client(
    service_name='sqs',
    region_name='us-east-2',
    aws_access_key_id='AKIAY563PRYUWD457KGQ',
    aws_secret_access_key='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'
)


# Function for sending SQS commands to a car's SQS queue
def send_to_sqs(number, payload):
    message_id = str(uuid.uuid4())

    sqs_send_client.send_message(
        QueueUrl='https://sqs.us-east-2.amazonaws.com/614103748137/car-commands-{}.fifo'.format(number),
        MessageBody=json.dumps(payload),
        DelaySeconds=0,
        MessageDeduplicationId=message_id,
        MessageGroupId=message_id
    )


# Subprocess for reading responses from cars
def response_manager():
    # Setup the ports so we can listen for serial responses from cars
    ports = initialize_ports()

    # Tables for measuring response times from the cars
    response_times = pandas.DataFrame(index=numpy.arange(n), columns=car_names, dtype='float')
    response_indices = numpy.zeros(len(mac_addresses))

    while response_times.tail(1).isna().any(None):
        # See if a car is reporting back to us
        for port in ports:
            if port.in_waiting:
                # Check if a car is responding to a message
                line = port.readline().decode('utf-8').strip()
                if line.startswith('Message Received by Car '):
                    # Strip the car index from the message
                    car_index_ = line.split()[-1]

                    # Record the response time
                    response_times.at[response_indices[car_index_], car_names[car_index_]] = datetime.datetime.now()

                    # Update how many responses we've received from this car
                    response_indices[car_index_] += 1

    # Write the response times to a file and exit so the main process can continue
    response_times.to_csv(response_times_file_path)


if __name__ == '__main__':
    # Record when the script started running
    timing_script_start_time = datetime.datetime.now()

    # Create the folder in the local directory if it doesn't already exist
    if not os.path.exists(timing_data_folder):
        os.makedirs(timing_data_folder)

    # Setup Car Infrastructure
    print('Setting up car managers')
    car_managers = []
    for i, mac_address in enumerate(mac_addresses):
        # Create subprocess for relaying commands to the cars from SQS
        car_managers.append(multiprocessing.Process(target=car_manager,
                                                    kwargs={'car_number': car_numbers[i], 'mac_address': mac_address},
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

    # Give the hub a couple seconds to connect all the cars
    time.sleep(4)

    # Create our range of message_delays
    message_delays = numpy.linspace(start=1000, stop=50, num=1)

    # Get data for all message delays
    for message_delay in message_delays:
        # Create the subprocess for reading responses from the cars
        print('Setting up response manager')
        response_manager_process = multiprocessing.Process(target=response_manager, daemon=True)
        response_manager_process.start()

        # Time interval between commands
        message_rate = datetime.timedelta(milliseconds=1000)

        # Table for measuring response times from the cars
        start_times = pandas.DataFrame(index=numpy.arange(n), columns=car_names, dtype='datetime64')

        # Keep looping until all responses have been received
        messages_sent = 0
        next_message_time = datetime.datetime.now()

        # Previously sent command for each car
        command_payloads = [{
            'PlayerName': car_names[car_index],
            'KeyW': False,
            'KeyA': False,
            'KeyS': False,
            'KeyD': False,
            'ShiftLeft': False
        } for car_index in car_indices]

        # Send messages to each car at regular intervals
        while messages_sent < n:
            # Send messages to each car's SQS queue if the time interval has passed
            if datetime.datetime.now() > next_message_time:
                # Send messages
                print('Sending message', messages_sent)
                for car_index in car_indices:
                    # Record the start time
                    start_times.at[messages_sent, car_names[car_index]] = datetime.datetime.now()

                    # Flip the command so the hub doesn't de-dupe it
                    command_payloads[car_index]['KeyW'] = not command_payloads[car_index]['KeyW']
                    send_to_sqs(car_numbers[car_index], command_payloads[car_index])

                # Wait until it's time to send another message
                next_message_time = datetime.datetime.now() + message_rate
                messages_sent += 1

        # Write our results and wait until the response manager is done processing responses
        start_times.to_csv(start_times_file_path)
        print('Waiting for response manager to finish')
        response_manager_process.join()

        # Read the results and calculate the time differences
        print('Calculating differences')
        response_times_ = pandas.read_csv(response_times_file_path)
        delays = response_times_ - start_times
        delays.to_csv(delays_file_path)

        # Statistical analysis of results
        # Adapted from https://stackoverflow.com/questions/15033511/compute-a-confidence-interval-from-sample-data
        sample_mean = delays.mean(axis=None)
        standard_error_of_the_mean = stats.sem(a=delays, axis=None)
        interval = stats.t.interval(confidence, n - 1, loc=sample_mean, scale=standard_error_of_the_mean)

        print(sample_mean)
        print(sample_mean + 1.96 * standard_error_of_the_mean / sample_mean)
        print(interval)

    print('Total Script Running Time:', datetime.datetime.now() - timing_script_start_time)
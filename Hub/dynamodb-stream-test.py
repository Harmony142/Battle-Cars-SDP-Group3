
# TODO website bugs: always only one character true, doesnt restrict to wasd
# API Docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodbstreams.html
import boto3
import csv
import time
import pprint
pp = pprint.PrettyPrinter(indent=4)

table_name = 'Todo-fkgtez5rpfcoferxahyyjer5i4-dev'
credentials_csv_file_name = 'dynamodb-stream-readonly-creds.csv'

with open(credentials_csv_file_name, newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    credentials = next(reader)

# Connect to AWS DynamoDB API
client = boto3.client(
    service_name='dynamodbstreams',
    region_name='us-east-2',
    aws_access_key_id=credentials['Access key ID'],
    aws_secret_access_key=credentials['Secret access key'])

# Find the correct stream ARN
response = client.list_streams(
    TableName=table_name
)
pp.pprint(response['Streams'])
stream_arn = None
for stream in response['Streams']:
    if stream['TableName'] == table_name:
        stream_arn = stream['StreamArn']
        break
if stream_arn is None:
    raise ValueError('Table name {} not found in current account'.format(table_name))
pp.pprint(stream_arn)

# Get the latest shard
response = client.describe_stream(
    StreamArn=stream_arn
)
pp.pprint(response['StreamDescription']['Shards'])
shard_id = response['StreamDescription']['Shards'][0]['ShardId']

# Get the first shard iterator of the latest shard
response = client.get_shard_iterator(
    StreamArn=stream_arn,
    ShardId=shard_id,
    ShardIteratorType='LATEST',
)
pp.pprint(response['ShardIterator'])
shard_iterator = response['ShardIterator']

while True:
    response = client.get_records(
        ShardIterator=shard_iterator
        # Limit=1
    )
    time.sleep(1)
    if 'NextShardIterator' in response.keys():
        pp.pprint(response['Records'])
        pp.pprint(response['NextShardIterator'])
        shard_iterator = response['NextShardIterator']

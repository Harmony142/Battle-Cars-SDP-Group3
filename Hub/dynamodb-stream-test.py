
# TODO website bugs: always only one character true, doesnt restrict to wasd
# API Docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodbstreams.html
import pprint
import json
from hub_common import connect_to_database
pp = pprint.PrettyPrinter(indent=4)

client, shard_iterator = connect_to_database()

while True:
    response = client.get_records(
        ShardIterator=shard_iterator
        # Limit=1
    )

    if 'Records' in response.keys():
        if len(response['Records']) > 0:
            keys_pressed = json.loads(response['Records'][0]['dynamodb']['NewImage']['description']['S'])
            pp.pprint(keys_pressed)

    if 'NextShardIterator' in response.keys():
        shard_iterator = response['NextShardIterator']

import boto3
import json
import os
import uuid

print('Loading function')
iot = boto3.client('iot-data')

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': str(err) if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def handler(event, context):
    try:
        print("Received event: " + json.dumps(event, indent=2))
        request = json.loads(event['body'])
        cmd = {}
        id = str(uuid.uuid4())
        cmd['id'] = id
        cmd['cmd'] = request['cmd']
        iot.publish(
            topic=request['topic'],
            qos=1,
            payload=json.dumps(cmd)
        )
        return respond(None, id)
    except Exception as e:
        return respond(e)
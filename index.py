import boto3
import json
import os

print('Loading function')
iot = boto3.client('iot-data')

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }

def handler(event, context):
    try:
        print("Received event: " + json.dumps(event, indent=2))
        request = json.loads(event['body'])
        topic = request['topic']
        cmd = request['cmd']
        iot.publish(
            topic=topic,
            qos=1,
            payload=cmd
        )
        return respond(None, "success")
    except Exception as e:
        return respond(e)
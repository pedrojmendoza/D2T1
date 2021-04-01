# D2T1

This is a simple demo ilustrating how to connect a REST API with a device via AWS IoT Core. 

The API accepts a command that will be "forwarded" to a device using MQTT PUBLISH and the device will process the cmd and send the response back to IoT Core on a different topic.

Finally, IoT Core will process the response from the device using a rule associated to the response (uplink) topic and store the message on an S3 bucket.

## Pre-conditions

1) Install AWS CLI as detailed in https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html (the rest of the instructions here assume MacOS being used)

2) Create an IAM User with admin rights and make sure to create programmatic access credentials (access and secret keys) as detailed in https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_console

3) Create an AWS profile using the programmatic credentials (access key and secret key) as detailed in https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html#cli-configure-quickstart-config (the rest of the instructions here assume you will be using us-east-1 region)

4) Create an S3 bucket for the transformed/packaged artifacts as detailed in https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html

## Deploy the cloud-side artifacts

1) Deploy the infrastructure required for the REST API (make sure to adjust the bucket with your own bucket's name created above)...

<code>
aws cloudformation package \
--template-file api.template.yaml \
--s3-bucket <YOUR_S3_BUCKET_NAME> \
--output-template-file api.template.packaged.yaml \
&& aws cloudformation deploy \
--template-file api.template.packaged.yaml \
--stack-name D2T1 \
--capabilities CAPABILITY_IAM
</code>

2) Deploy the infrastructure required for the IoT Core rule (and destination S3 bucket) ...

<code>
aws cloudformation deploy \
--template-file iot.template.yaml \
--stack-name D2T1-IoT \
--capabilities CAPABILITY_IAM
</code>

## Create a new simulated client/device

1) Create a new thing and its private key and certificate in AWS IoT Core. You can use https://docs.aws.amazon.com/iot/latest/developerguide/iot-moisture-create-thing.html as reference

2) Adjust the IoT policy associate to your device's certificate to allow the publish/subscribe operations on the relevant topics. You can use the below policy if you use the default values in the script (make sure to replace with your AWS Account ID)

<code>
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iot:Publish"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:<YOUR_AWS_ACCOUNT_ID>:topic/d2t1/uplink"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Receive"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:<YOUR_AWS_ACCOUNT_ID>:topic/d2t1/cmds"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Subscribe"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:<YOUR_AWS_ACCOUNT_ID>:topicfilter/d2t1/cmds"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "iot:Connect"
      ],
      "Resource": [
        "arn:aws:iot:us-east-1:<YOUR_AWS_ACCOUNT_ID>:client/d2t1"
      ]
    }
  ]
}
</code>

3) Download Amazon Root CA ...

<code>
curl https://www.amazontrust.com/repository/AmazonRootCA1.pem > root-CA.crt
</code>

4) Install AWS IoT Device SDK for Python v1 as detailed in https://github.com/aws/aws-iot-device-sdk-python ...

<code>
pip install AWSIoTPythonSDK
</code>

5) Retrieve your AWS IoT Core ATS endpoint ...

<code>
IOT_ENDPOINT=`aws iot describe-endpoint --endpoint-type iot:Data-ATS --output text`
</code>

6) Run (endlessly) simulated device (adjust credentials files based on your settings) ...

<code>
python basicPubSub.py -e $IOT_ENDPOINT -r root-CA.crt -c d2t1.cert.pem -k d2t1.private.key
</code>

## Test

1) Obtain the endpoint of the REST API ...

<code>
API_ENDPOINT=`aws cloudformation describe-stacks --stack-name D2T1 --query 'Stacks[0].Outputs[0].OutputValue' --output text`
</code>

2) Send an HTTP POST to the REST API endpoint ...

<code>
curl -d '{"topic":"d2t1/cmds", "cmd":"send_files"}' -H "Content-Type: application/json" -X POST $API_ENDPOINT
</code>

3) Check S3 bucket objects ...

3.1) Obtain the S3 bucket name ...

<code>
BUCKET=`aws cloudformation describe-stacks --stack-name D2T1-IoT --query 'Stacks[0].Outputs[0].OutputValue' --output text`
</code>

3.2) List objects (based on the epoch of the message as received from the device by IoT Core) in S3 bucket

<code>
aws s3api list-objects --bucket $BUCKET --query 'Contents[].Key'
</code>

3.3) Get object from S3 bucket ...

<code>
aws s3api get-object --bucket $BUCKET --key <YOUR_KEY> <YOUR_OUTPUT_FILENAME>.json
</code>

3.4) Less your file ...

<code>
less <YOUR_OUTPUT_FILENAME>.json
</code>

## Potential improvements

1) Use Shadow service for sending commands as detailed in https://docs.aws.amazon.com/iot/latest/developerguide/iot-device-shadows.html

2) Include a CI/CD deployment pipeline for the cloud-side infra

3) Add unit testing for the lambda's code
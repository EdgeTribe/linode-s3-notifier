import boto3
import os
from botocore.client import Config
from datetime import datetime, timezone
import time
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse
import threading

# Populate vars from environment

#host = os.environ['OPENSEARCH_HOST']
#port = os.environ['OPENSEARCH_PORT']

bucket_name = os.environ['BUCKET_NAME']
region = os.environ['LINODE_REGION']
access_key = os.environ['ACCESS_KEY']
secret_key = os.environ['SECRET_KEY']

sqs_access_key = os.environ['AWS_ACCESS_KEY']
sqs_secret_key = os.environ['AWS_SECRET_KEY']
sqs_region = os.environ['AWS_REGION']
queue_url = os.environ['QUEUE_URL']
# The following is necessary for the boto client to know what to authenticate against
parsed_queue_url = urlparse(queue_url)
queue_endpoint_url = urlunparse((parsed_queue_url.scheme, parsed_queue_url.netloc, '', '', '', ''))

s3_client = boto3.client(
    's3',
    region_name=region,
    endpoint_url=f'https://{region}.linodeobjects.com',  # Linode S3 endpoint
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    config=Config(s3={'addressing_style': 'path'})  # Use path-style addressing
)

sqs_client = boto3.client(
    'sqs',
    region_name=region,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    endpoint_url=queue_endpoint_url
)

# Global error handler
def global_error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"An error occurred in {func.__name__}: {e}")
            # You can add more error handling logic here if needed
    return wrapper

def main():
    # Connect to OpenSearch
    #client = connect_to_opensearch(host, port, username, password, verify_ssl)
    print('Process start...')
    print('DEBUG: '+ queue_endpoint_url)

    while True:
        now = datetime.now()
        if now.second % 30 == 00:  # Check if the current minute ends in 0 or 5
            # Get the last 5 minutes of stuff
            current_time = datetime.now()
            end_time_obj = current_time
            end_time = current_time.strftime("%Y-%m-%dT%H:%M:%S")
            start_time_obj = current_time - timedelta(seconds=30)
            start_time = start_time_obj.strftime("%Y-%m-%dT%H:%M:%S")
            start_time_obj_naive = start_time_obj.replace(tzinfo=None)
            end_time_obj_naive = end_time_obj.replace(tzinfo=None)
            print('Interval: ' + str(start_time) + '-' + str(end_time))

            now = datetime.now()
            if now.second % 30 == 00: #If it for some miracle it takes less than a minute to execute and it's still 0 or 5, we don't want to loop this thing
                time.sleep(3)
            else:
                time.sleep(1)

            file_list = list_files_in_s3_bucket_by_modified_date(bucket_name, s3_client, start_time_obj_naive, end_time_obj_naive)
            #file_list = list_files_in_s3_bucket(bucket_name, region, access_key, secret_key)
            for file in file_list:
                print(file)

            print('Posting messages in new thread...')
            threading.Thread(target=send_messages_to_queue(queue_url, bucket_name, file_list, sqs_client))


            
            print('Main thread waiting for next run...')
            if now.second % 30 == 00:
                time.sleep(3)

        else:
            #print('Patiently waiting...')
            time.sleep(1)


def list_files_in_s3_bucket_by_modified_date(bucket_name, s3_client, start_time, end_time):
  
    # Strip time zone information from start_time and end_time to make them naive
    start_time_naive = start_time.replace(tzinfo=None)
    end_time_naive = end_time.replace(tzinfo=None)

    # Initialize variables for pagination
    continuation_token = None
    filtered_files = []

    # Paginate through all files (objects) in the bucket
    while True:
        if continuation_token:
            response = s3_client.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token)
        else:
            response = s3_client.list_objects_v2(Bucket=bucket_name)

        # Check if there are any objects
        if 'Contents' not in response:
            break

        # Filter objects based on LastModified time (strip timezone info from LastModified as well)
        for obj in response['Contents']:
            last_modified_naive = obj['LastModified'].replace(tzinfo=None)
            if start_time_naive <= last_modified_naive <= end_time_naive:
                filtered_files.append(obj['Key'])

        # Check if more objects are available for pagination
        if response.get('IsTruncated'):  # If True, there are more objects to fetch
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    return filtered_files

# Function to send a message mimicking an S3 event notification
def send_s3_event_message_to_sqs(queue_url, bucket_name, file_name, sqs_client):
    # Construct the message body similar to S3 event notification
    message_body = {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "et-lsn-linode:s3",
                "awsRegion": region,
                "eventTime": datetime.now(timezone.utc).isoformat(),
                "eventName": "ObjectCreated:Put",
                "userIdentity": {
                    "principalId": "LINODE:EXAMPLE"
                },
                "requestParameters": {
                    "sourceIPAddress": "192.0.2.1"
                },
                "responseElements": {
                    "x-amz-request-id": "C3D13FE58DE4C810",
                    "x-amz-id-2": "FMyUVURIbFmyLKC6SkjoRLyJXMfB+blfdkDlVCEcVZ2aC6V1z+b1Q"
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": bucket_name,
                        "ownerIdentity": {
                            "principalId": "LINODE"
                        },
                        "arn": f"arn:aws:s3:::{bucket_name}"
                    },
                    "object": {
                        "key": file_name,
                        "size": 1024,  # You can set the actual size if needed
                        "eTag": "9b2cf535f27731c974343645a3985328",
                        "sequencer": "0055AED6DCD90281E5"
                    }
                }
            }
        ]
    }

    # Send the message to SQS
    print ('DEBUG: Posting message to ' + queue_url)
    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=str(message_body)  # Convert to string before sending
    )

    return response

def send_messages_to_queue(queue_url, bucket_name, file_list, sqs_client):
    for file in file_list:
        response = send_s3_event_message_to_sqs(queue_url, bucket_name, file, sqs_client)
        print(response)

    


if __name__ == "__main__":
    main()
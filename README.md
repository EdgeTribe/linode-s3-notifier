# S3 to SQS Event Notification Script

This Python script periodically checks for newly modified files in a Linode S3 bucket and sends corresponding S3 event notifications to an AWS SQS queue. It uses the Boto3 library to interact with both the S3 and SQS services and leverages multi-threading to send messages asynchronously.

## Table of Contents
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [Functions](#functions)
- [Error Handling](#error-handling)
- [License](#license)

## Docker Run

You can run it straight from docker like:

   ```bash
   docker run --env-file=env.file edgetribe/linode-s3-notifier:latest
   ```

## Installation

1. Clone the repository or copy the script to your local environment.

2. Install the required dependencies using `pip`:

   ```bash
   pip install boto3
   ```

3. Ensure you have Python 3 installed.

## Environment Variables

The script uses several environment variables for configuration. Set them as follows:

| Variable           | Description                                            |
|--------------------|--------------------------------------------------------|
| `BUCKET_NAME`      | The name of your Linode S3 bucket.                     |
| `LINODE_REGION`    | The region where your Linode S3 bucket is hosted.      |
| `ACCESS_KEY`       | Your Linode S3 access key.                             |
| `SECRET_KEY`       | Your Linode S3 secret key.                             |
| `AWS_ACCESS_KEY`   | Your AWS SQS access key.                               |
| `AWS_SECRET_KEY`   | Your AWS SQS secret key.                               |
| `AWS_REGION`       | The AWS region where your SQS queue is hosted.         |
| `QUEUE_URL`        | The URL of your AWS SQS queue.                         |

Make sure you have configured these variables in your environment:

### Example for Linux/macOS:

```bash
export BUCKET_NAME=my-linode-bucket
export LINODE_REGION=us-east
export ACCESS_KEY=my-linode-access-key
export SECRET_KEY=my-linode-secret-key
export AWS_ACCESS_KEY=my-aws-access-key
export AWS_SECRET_KEY=my-aws-secret-key
export AWS_REGION=us-west-2
export QUEUE_URL=https://sqs.us-west-2.amazonaws.com/123456789012/my-queue
```

### Example for Windows (PowerShell):

```powershell
$env:BUCKET_NAME="my-linode-bucket"
$env:LINODE_REGION="us-east"
$env:ACCESS_KEY="my-linode-access-key"
$env:SECRET_KEY="my-linode-secret-key"
$env:AWS_ACCESS_KEY="my-aws-access-key"
$env:AWS_SECRET_KEY="my-aws-secret-key"
$env:AWS_REGION="us-west-2"
$env:QUEUE_URL="https://sqs.us-west-2.amazonaws.com/123456789012/my-queue"
```

## Usage

To run the script, execute the following command:

```bash
python script.py
```

The script continuously monitors the S3 bucket and posts new or modified file event notifications to the specified SQS queue every 30 seconds.

## Functions

### `list_files_in_s3_bucket_by_modified_date(bucket_name, s3_client, start_time, end_time)`
Fetches a list of files from the specified S3 bucket that have been modified within a given time range.

- `bucket_name`: Name of the S3 bucket.
- `s3_client`: Boto3 S3 client instance.
- `start_time`: Start of the time range.
- `end_time`: End of the time range.

Returns a list of files that meet the criteria.

### `send_s3_event_message_to_sqs(queue_url, bucket_name, file_name, sqs_client)`
Constructs and sends a message to SQS mimicking an S3 event notification for the given file.

- `queue_url`: SQS queue URL.
- `bucket_name`: Name of the S3 bucket.
- `file_name`: Name of the file for which to send the event notification.
- `sqs_client`: Boto3 SQS client instance.

### `send_messages_to_queue(queue_url, bucket_name, file_list, sqs_client)`
Sends S3 event messages for a list of files to the specified SQS queue in a separate thread.

- `queue_url`: SQS queue URL.
- `bucket_name`: Name of the S3 bucket.
- `file_list`: List of files for which to send the event notifications.
- `sqs_client`: Boto3 SQS client instance.

## Error Handling

The script uses a global error handler decorator `@global_error_handler` to catch and print any exceptions that occur during the execution of the wrapped functions. This ensures that the script doesn't crash due to unhandled exceptions.

## License

This project is licensed under the GNU General Public License v3
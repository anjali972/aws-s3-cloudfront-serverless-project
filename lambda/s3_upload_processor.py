import urllib.parse
import boto3

s3 = boto3.client("s3")

PROCESSED_BUCKET = "anjali-uploads-2026-unique31"


def lambda_handler(event, context):
    for record in event.get("Records", []):
        source_bucket = record["s3"]["bucket"]["name"]

        # Decode the object key from the S3 event
        key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        size = record["s3"]["object"].get("size", 0)

        print(
            f"Processing {key} ({size} bytes) "
            f"from {source_bucket}"
        )

        # Copy the uploaded object to the destination bucket
        s3.copy_object(
            Bucket=PROCESSED_BUCKET,
            Key=key,
            CopySource={
                "Bucket": source_bucket,
                "Key": key
            }
        )

        print(
            f"Successfully copied {key} "
            f"to {PROCESSED_BUCKET}"
        )

    return {
        "status": "ok"
    }
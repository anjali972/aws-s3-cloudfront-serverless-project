# AWS S3, CloudFront, and Serverless File Processing Project

A hands-on AWS project demonstrating secure static website delivery, S3 object versioning and lifecycle management, temporary object access, event-driven file processing with Lambda, IAM least privilege, and CloudWatch logging.

## Project Overview

This repository documents three separate AWS exercises:

1. **Secure static website hosting** — a private S3 bucket serves as the origin for CloudFront. CloudFront uses Origin Access Control (OAC) to retrieve objects securely and deliver the website over HTTPS.
2. **Event-driven file processing** — an S3 object-created event invokes a Python Lambda function. The function copies the uploaded object from a source bucket to a destination bucket and writes execution messages to CloudWatch Logs.
3. **S3 data protection and access practice** — a separate bucket demonstrates object versioning, delete markers, lifecycle rules, and pre-signed URLs.

> These are separate demonstrations. The versioning bucket is not the website bucket and is not part of the Lambda upload-processing path.

## Architecture

### 1. Static website delivery

```text
Website visitor
      |
      | HTTPS request
      v
Amazon CloudFront
Distribution: E1SYTYS303HUG7
      |
      | Origin Access Control (OAC)
      | authenticated origin request
      v
Private S3 website bucket
anjali-website-hosting
      |
      +-- Stores index.html and website assets
      +-- Block Public Access enabled
      +-- Bucket policy allows CloudFront distribution access
```

**Expected security test:** direct access through the S3 website endpoint returns `403 Forbidden`, while the CloudFront domain serves the website. The S3 bucket policy shown in the project grants `s3:GetObject` to the CloudFront service principal, restricted to the project's distribution ARN. Do not add a public-read policy if the intention is to keep the bucket private.

### 2. Event-driven file processing

```text
File upload
    |
    v
Source S3 bucket
anjali-uploads-2026-unique
    |
    | ObjectCreated event notification
    v
AWS Lambda: s3-upload-processor
    |                    \
    |                     +--> CloudWatch Logs
    |                          execution messages/errors
    |
    | Copies the object
    v
Destination S3 bucket
anjali-uploads-2026-unique-31
```

The Lambda execution role is `s3-upload-processor-role-`. Its permissions include the AWS-managed `AWSLambdaBasicExecutionRole` policy for logging and a custom inline policy named `S3_Upload_Processor_Access` (as shown in the console screenshot). The custom policy should grant only the permissions needed to read source objects and write destination objects.

### 3. Versioning and lifecycle demonstration

```text
Separate S3 bucket
anjali-versioning-demo-2026-unique
      |
      +-- Object version history and delete markers
      +-- Recovery of an earlier object version
      +-- Lifecycle rules for storage transitions/cleanup
      +-- Pre-signed URL exercise for temporary access
```

A pre-signed URL is a temporary bearer credential. Never commit a complete pre-signed URL to this repository, include it in screenshots, or publish it in a post.

## AWS Resources

| Component | Resource name / identifier | Purpose |
|---|---|---|
| Website bucket | `anjali-website-hosting` | Stores static website files; private CloudFront origin |
| CloudFront distribution | `E1SYTYS303HUG7` | HTTPS delivery and caching for the website |
| Versioning demo bucket | `anjali-versioning-demo-2026-unique` | Version history, delete markers, lifecycle, pre-signed URL practice |
| Lambda source bucket | `anjali-uploads-2026-unique` | Receives uploaded files and emits object-created events |
| Lambda function | `s3-upload-processor` | Copies uploaded objects to the destination bucket |
| Lambda destination bucket | `anjali-uploads-2026-unique-31` | Stores copies created by Lambda |
| Lambda execution role | `s3-upload-processor-role-` | Provides runtime permissions to Lambda |
| Lambda log group | `/aws/lambda/s3-upload-processor` | Stores function execution logs in CloudWatch Logs |

Resource names and IDs are account-specific. Verify them in the AWS Console before reusing this README in another environment. Consider whether you want to publish infrastructure identifiers in a public repository.

## Lambda Function (`lambda_function.py`)

The Lambda console screenshot shows the source file named **`lambda_function.py`**. In the Lambda console, the handler should therefore normally be set to `lambda_function.lambda_handler` for this file name and function name.

```python
import urllib.parse
import boto3

s3 = boto3.client("s3")
PROCESSED_BUCKET = "anjali-uploads-2026-unique-31"


def lambda_handler(event, context):
    for record in event.get("Records", []):
        source_bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        size = record["s3"]["object"].get("size", 0)

        print(f"Processing {key} ({size} bytes) from {source_bucket}")

        s3.copy_object(
            Bucket=PROCESSED_BUCKET,
            Key=key,
            CopySource={"Bucket": source_bucket, "Key": key},
        )

        print(f"Successfully copied {key} to {PROCESSED_BUCKET}")

    return {"status": "ok"}
```

### What the code does

1. Imports `boto3`, the AWS SDK for Python, and `urllib.parse` for decoding object keys from S3 event records.
2. Reads the source bucket and uploaded object key from each event record.
3. Calls S3 `copy_object` to copy that object into the destination bucket, preserving the key name.
4. Writes progress messages that can be inspected in CloudWatch Logs.
5. Returns a simple success response after processing the records.

**Important:** the source bucket and destination bucket must be different. The Lambda execution role needs `s3:GetObject` for source objects and `s3:PutObject` for destination objects, plus CloudWatch Logs permissions. The S3 event notification must target this Lambda function and use object-created events.

## Verification and Test Results

The screenshots captured during the project demonstrate these checks:

- [x] CloudFront distribution is enabled.
- [x] CloudFront invalidation for `/*` completed.
- [x] Website loads through the CloudFront domain.
- [x] Direct S3 website endpoint access returns `403 Forbidden` while public access is blocked.
- [x] S3 object-created event invokes the Lambda function.
- [x] CloudWatch Logs show `Processing final-test.txt` and `Successfully copied final-test.txt`.
- [x] The destination bucket contains the copied object.
- [x] The versioning demonstration shows multiple versions of `notes.txt`.
- [x] IAM role includes basic Lambda logging permissions and a custom S3 access policy.

## Security Notes

- Keep S3 Block Public Access enabled for the private website origin.
- Use CloudFront OAC with a bucket policy scoped to the intended distribution.
- Follow least privilege: restrict Lambda's S3 permissions to the required bucket/object ARNs.
- Never commit AWS access keys, secret keys, session tokens, account credentials, or full pre-signed URLs.
- Avoid uploading sensitive data to test buckets.
- Use CloudWatch Logs to troubleshoot execution failures; do not log secrets or sensitive file contents.

## Cost and Cleanup

CloudFront, AWS WAF, S3 storage and requests, Lambda invocations, and CloudWatch Logs can incur charges. The CloudFront distribution was created with security protection/WAF options enabled, so review the distribution's security configuration and current pricing before leaving it running. Check AWS Billing and Cost Management for actual charges; console estimates are not a bill guarantee.

When finished, remove resources only after checking dependencies. For example, disable or delete the CloudFront distribution before deleting an origin bucket that it still uses. Preserve any objects or versions you want to keep before cleaning up the versioning bucket.

## Suggested Repository Layout

```text
.
├── README.md
├── lambda/
│   └── lambda_function.py
├── website/
│   ├── index.html
│   ├── styles.css
│   └── assets/
└── screenshots/
    ├── cloudfront-distribution.png
    ├── cloudfront-invalidation.png
    ├── private-bucket-policy.png
    ├── s3-direct-access-denied.png
    ├── s3-static-website.png
    ├── lambda-function.png
    ├── lambda-cloudwatch-logs.png
    ├── iam-lambda-policy.png
    ├── s3-destination-bucket.png
    └── s3-versioning.png
```

The layout above is a suggested organization; adjust the paths to match the actual files in your repository.

## Skills Demonstrated

- Amazon S3 object storage, bucket policies, Block Public Access, versioning, lifecycle configuration, and pre-signed URLs
- Amazon CloudFront distribution setup, caching invalidation, and Origin Access Control
- AWS Lambda with Python and `boto3`
- S3 event notifications and event-driven serverless design
- IAM execution roles and least-privilege permissions
- CloudWatch Logs for troubleshooting and verification

---

**Project note:** This is a learning project. Before describing it as production-ready, add operational safeguards such as error handling and retry strategy, idempotency considerations, alerts, lifecycle/cost validation, and tests for large objects and unusual object keys.
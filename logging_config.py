import logging
import os
import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(message)s"
)

log = logging.getLogger("toolkit")

REGION = os.environ.get("AWS_REGION", "us-east-1")

log.info("Using region: %s", REGION)

s3 = boto3.client("s3", region_name=REGION)

log.info("S3 client created")

response = s3.list_buckets()

log.info("Found %d bucket(s)", len(response["Buckets"]))

for bucket in response["Buckets"]:
    log.info("Bucket: %s", bucket["Name"])
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"

s3 = boto3.client("s3", region_name=REGION)

bucket_name = "this-bucket-does-not-exist-ghaya-123456789"

try:
    response = s3.list_objects_v2(Bucket=bucket_name)
    print(response)

except ClientError as e:
    code = e.response["Error"]["Code"]

    if code == "NoSuchBucket":
        print("That bucket does not exist.")
    else:
        raise
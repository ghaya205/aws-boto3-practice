import boto3

REGION = "us-east-1"
BUCKET = "ghaya-aws-lab-111968427620"

s3 = boto3.client("s3", region_name=REGION)

paginator = s3.get_paginator("list_objects_v2")

for page in paginator.paginate(Bucket=BUCKET):
    for obj in page.get("Contents", []):
        print(obj["Key"])
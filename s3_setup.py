import boto3

REGION = "us-east-1"
BUCKET = "ghaya-aws-lab-111968427620"

s3 = boto3.client("s3", region_name=REGION)

s3.put_object(
    Bucket=BUCKET,
    Key="file1.txt",
    Body=b"Hello AWS"
)

s3.put_object(
    Bucket=BUCKET,
    Key="file2.txt",
    Body=b"AWS Learner Lab"
)

print("Files uploaded.")
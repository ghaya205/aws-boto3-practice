import boto3

# AWS account
sts = boto3.client("sts", region_name="us-east-1")
identity = sts.get_caller_identity()
account = identity["Account"]

print("AWS Account ID:", account)

# Learner Lab role
role_arn = f"arn:aws:iam::{account}:role/LabRole"
print("Lambda Role ARN:", role_arn)

# Lambda client
lambda_client = boto3.client("lambda", region_name="us-east-1")

# Lambda name
name = "my-first-lambda"

# Read ZIP
with open("lambda_function.zip", "rb") as f:
    package_bytes = f.read()

# Create Lambda
response = lambda_client.create_function(
    FunctionName=name,
    Runtime="python3.13",
    Role=role_arn,
    Handler="lambda_function.lambda_handler",
    Code={"ZipFile": package_bytes},
)

print("Lambda created!")
print("Function ARN:", response["FunctionArn"])
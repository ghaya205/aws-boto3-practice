import boto3

REGION = "us-east-1"

ec2 = boto3.client("ec2", region_name=REGION)

response = ec2.run_instances(
    ImageId="ami-0b5358cc8c5df0b02",
    InstanceType="t3.micro",
    MinCount=1,
    MaxCount=1,
    KeyName="vockey"
)

instance_id = response["Instances"][0]["InstanceId"]

print("Instance launched:", instance_id)

# Waiter
ec2.get_waiter("instance_running").wait(
    InstanceIds=[instance_id],
    WaiterConfig={"Delay": 15, "MaxAttempts": 40},
)

print("Instance is now running!")
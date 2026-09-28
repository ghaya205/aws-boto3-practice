import boto3

ec2 = boto3.client("ec2", region_name="us-east-1")

response = ec2.describe_images(
    Owners=["amazon"],
    Filters=[
        {
            "Name": "name",
            "Values": ["al2023-ami-2023*-x86_64"]
        },
        {
            "Name": "state",
            "Values": ["available"]
        }
    ]
)

images = sorted(
    response["Images"],
    key=lambda x: x["CreationDate"],
    reverse=True
)

for image in images[:5]:
    print(image["ImageId"], image["Name"])
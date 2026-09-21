import boto3

def show_identity():
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()

    print("WHO AM I?")
    print(f"Account ID : {identity['Account']}")
    print(f"User ID    : {identity['UserId']}")
    print(f"ARN        : {identity['Arn']}")

def show_region():
    session = boto3.session.Session()

    print("CURRENT REGION")
    print(f"Region  : {session.region_name}")
    print(f"Profile : {session.profile_name}")

def list_buckets_with_client():
    s3 = boto3.client("s3")
    response = s3.list_buckets()
 
    for bucket in response["Buckets"]:
        created = bucket["CreationDate"].strftime("%Y-%m-%d %H:%M")
        print(f"  {bucket['Name']:<45} created {created}")

def list_buckets_with_resource():
    s3 = boto3.resource("s3")
    for bucket in s3.buckets.all():
        print(f"  {bucket.name}")
def list_instances():
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances()
 
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}
            print(f"  {instance['InstanceId']}  "
                  f"{instance['InstanceType']:<12} "
                  f"{instance['State']['Name']:<12} "
                  f"{tags.get('Name', '(no name)')}")

def list_regions():
    ec2 = boto3.client("ec2")

    names = sorted(
        r["RegionName"]
        for r in ec2.describe_regions()["Regions"]
    )

    print("AVAILABLE AWS REGIONS")

    for i in range(0, len(names), 4):
        print("  " + "".join(f"{n:<20}" for n in names[i:i + 4]))

    print(f"Total: {len(names)} regions")


from botocore.exceptions import ClientError, NoCredentialsError

def main():
    try:
        show_identity()
        print('================================')
        show_region()
        print('================================')
        list_buckets_with_client()
        print('================================')
        list_buckets_with_resource()
        print('================================')
        list_instances()
        print('================================')
        list_regions()

    except NoCredentialsError:
        print("[ERROR] No credentials found. Check ~/.aws/credentials")

    except ClientError as e:
        code = e.response["Error"]["Code"]
        message = e.response["Error"]["Message"]

        print(f"[AWS ERROR] {code}: {message}")

        if code in ("ExpiredToken", "ExpiredTokenException"):
            print("Your session token expired. Restart the lab.")


if __name__ == "__main__":
    main()
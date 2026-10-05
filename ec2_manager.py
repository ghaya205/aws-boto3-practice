import boto3
from botocore.exceptions import ClientError, WaiterError


INSTANCE_TYPE = "t3.micro"
KEY_NAME = "vockey"
TAG_KEY = "CreatedBy"
TAG_VALUE = "boto3-lab"
WAITER_CONFIG = {"Delay": 15, "MaxAttempts": 40}

ec2 = boto3.client("ec2")
ssm = boto3.client("ssm")


def print_menu():
    print("=" * 41)
    print("EC2 MANAGER")
    print("=" * 41)
    print("1. List Instances      5. Reboot Instance")
    print("2. Launch Instance     6. Describe Instance")
    print("3. Start Instance      7. Add Tags")
    print("4. Stop Instance       8. Terminate Instance")
    print("9. CLEAN UP all lab instances")
    print("0. Exit")
    print("=" * 41)


def tags_to_dict(instance):
    return {t["Key"]: t["Value"] for t in instance.get("Tags", [])}


def get_instances():
    paginator = ec2.get_paginator("describe_instances")
    rows = []
    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                if inst["State"]["Name"] != "terminated":
                    rows.append(inst)
    return rows


def list_instances():
    rows = get_instances()
    if not rows:
        print("No instances found.")
        return
    print(f"{'INSTANCE ID':<21} {'TYPE':<12} {'STATE':<12} {'PUBLIC IP':<16} NAME")
    for inst in rows:
        tags = tags_to_dict(inst)
        print(f"{inst['InstanceId']:<21} "
              f"{inst['InstanceType']:<12} "
              f"{inst['State']['Name']:<12} "
              f"{inst.get('PublicIpAddress', '-'):<16} "
              f"{tags.get('Name', '(no name)')}")
    print(f"{len(rows)} instance(s).")


def get_latest_amazon_linux_ami():
    parameter = ("/aws/service/ami-amazon-linux-latest/"
                 "al2023-ami-kernel-default-x86_64")
    response = ssm.get_parameter(Name=parameter)
    return response["Parameter"]["Value"]


def ask_instance_id(prompt="Instance ID: "):
    return input(prompt).strip()


def wait_for(waiter_name, instance_ids, message, success):
    try:
        print(message)
        waiter = ec2.get_waiter(waiter_name)
        waiter.wait(InstanceIds=instance_ids, WaiterConfig=WAITER_CONFIG)
        print(success)
        return True
    except WaiterError:
        print("Timed out. Check the Console.")
        return False


def launch_instance():
    name = input("Name tag for the instance: ").strip() or "boto3-instance"
    ami_id = get_latest_amazon_linux_ami()
    print(f"Using latest Amazon Linux 2023 AMI: {ami_id}")

    response = ec2.run_instances(
        ImageId=ami_id,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        KeyName=KEY_NAME,
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Name", "Value": name},
                {"Key": TAG_KEY, "Value": TAG_VALUE},
            ],
        }],
    )
    instance = response["Instances"][0]
    instance_id = instance["InstanceId"]
    print(f"Launched {instance_id}, state = {instance['State']['Name']}")

    wait_for("instance_running", [instance_id],
             "Waiting for the instance to reach 'running' ...",
             "Instance is running.")

    detail = ec2.describe_instances(InstanceIds=[instance_id])
    running = detail["Reservations"][0]["Instances"][0]
    print("Public IP:", running.get("PublicIpAddress", "not assigned"))


def start_instance():
    instance_id = ask_instance_id()
    response = ec2.start_instances(InstanceIds=[instance_id])
    change = response["StartingInstances"][0]
    print(change["PreviousState"]["Name"], "->", change["CurrentState"]["Name"])
    wait_for("instance_running", [instance_id],
             "Waiting for the instance to reach 'running' ...",
             "Instance is running.")


def stop_instance():
    instance_id = ask_instance_id()
    response = ec2.stop_instances(InstanceIds=[instance_id])
    change = response["StoppingInstances"][0]
    print(change["PreviousState"]["Name"], "->", change["CurrentState"]["Name"])
    wait_for("instance_stopped", [instance_id],
             "Waiting for the instance to reach 'stopped' ...",
             "Instance is stopped.")


def reboot_instance():
    instance_id = ask_instance_id()
    ec2.reboot_instances(InstanceIds=[instance_id])
    print(f"Reboot requested for {instance_id}. The instance stays in the running state.")


def describe_instance():
    instance_id = ask_instance_id()
    response = ec2.describe_instances(InstanceIds=[instance_id])
    inst = response["Reservations"][0]["Instances"][0]
    tags = tags_to_dict(inst)
    groups = ", ".join(
        f"{g['GroupName']} ({g['GroupId']})" for g in inst.get("SecurityGroups", [])
    ) or "-"

    print(f"Instance ID      : {inst['InstanceId']}")
    print(f"Name             : {tags.get('Name', '(no name)')}")
    print(f"State            : {inst['State']['Name']}")
    print(f"Type             : {inst['InstanceType']}")
    print(f"AMI              : {inst['ImageId']}")
    print(f"Availability Zone: {inst['Placement']['AvailabilityZone']}")
    print(f"Public IP        : {inst.get('PublicIpAddress', '-')}")
    print(f"Private IP       : {inst.get('PrivateIpAddress', '-')}")
    print(f"Key Pair         : {inst.get('KeyName', '-')}")
    print(f"Launch Time      : {inst['LaunchTime']}")
    print(f"Security Groups  : {groups}")
    print("Tags:")
    if tags:
        for key, value in tags.items():
            print(f"  {key} = {value}")
    else:
        print("  (none)")


def add_tags():
    instance_id = ask_instance_id()
    key = input("Tag key: ").strip()
    value = input("Tag value: ").strip()
    if not key:
        print("Tag key cannot be empty.")
        return
    ec2.create_tags(
        Resources=[instance_id],
        Tags=[{"Key": key, "Value": value}],
    )
    print(f"Tag {key}={value} set on {instance_id}.")


def terminate_instance():
    instance_id = ask_instance_id()
    if input(f"Type YES to terminate {instance_id}: ").strip() != "YES":
        print("Cancelled.")
        return
    response = ec2.terminate_instances(InstanceIds=[instance_id])
    change = response["TerminatingInstances"][0]
    print(change["PreviousState"]["Name"], "->", change["CurrentState"]["Name"])
    wait_for("instance_terminated", [instance_id],
             "Waiting for the instance to terminate ...",
             "Instance is terminated.")


def cleanup():
    response = ec2.describe_instances(Filters=[
        {"Name": f"tag:{TAG_KEY}", "Values": [TAG_VALUE]},
        {"Name": "instance-state-name",
         "Values": ["pending", "running", "stopping", "stopped"]},
    ])
    ids = [inst["InstanceId"]
           for res in response["Reservations"]
           for inst in res["Instances"]]

    if not ids:
        print("No lab instances to clean up.")
        return

    print("These instances will be terminated:")
    for instance_id in ids:
        print(instance_id)

    if input("Type YES to confirm: ").strip() != "YES":
        print("Cancelled.")
        return

    ec2.terminate_instances(InstanceIds=ids)
    if wait_for("instance_terminated", ids,
                "Waiting for all instances to terminate ...",
                f"Terminated {len(ids)} instance(s)."):
        return


ACTIONS = {
    "1": list_instances,
    "2": launch_instance,
    "3": start_instance,
    "4": stop_instance,
    "5": reboot_instance,
    "6": describe_instance,
    "7": add_tags,
    "8": terminate_instance,
    "9": cleanup,
}


def main():
    while True:
        print_menu()
        choice = input("Choose an option: ").strip()
        if choice == "0":
            print("Goodbye.")
            break
        action = ACTIONS.get(choice)
        if action is None:
            print("Invalid option.")
            continue
        try:
            action()
        except ClientError as error:
            code = error.response["Error"]["Code"]
            message = error.response["Error"]["Message"]
            print(f"AWS error [{code}]: {message}")
        except Exception as error:
            print(f"Unexpected error: {error}")
        print()


if __name__ == "__main__":
    main()
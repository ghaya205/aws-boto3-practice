import sys
import os
import boto3
from botocore.exceptions import ClientError
from boto3.exceptions import S3UploadFailedError
from logging_config import REGION


MENU = """
=========================================
            S3 MANAGER
=========================================
  1. Create Bucket
  2. List Buckets
  3. Upload File
  4. List Files
  5. Download File
  6. Delete File
  7. Generate Presigned URL
  8. Delete Bucket
  9. Backup Local Folder
  0. Exit
=========================================
"""

s3 = boto3.client("s3")


def create_bucket():
    name = input("New bucket name: ").strip()
    try:
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=name)
        else:
            s3.create_bucket(
                Bucket=name,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        print(f"Created bucket '{name}'")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "BucketAlreadyExists":
            print("That name is taken by another AWS account.")
        elif code == "BucketAlreadyOwnedByYou":
            print("You already own that bucket.")
        else:
            print(f"[AWS ERROR] {code}")


def list_buckets():
    try:
        response = s3.list_buckets()
    except ClientError as e:
        print(f"[AWS ERROR] {e.response['Error']['Code']}")
        return

    buckets = response.get("Buckets", [])
    if not buckets:
        print("(no buckets)")
        return

    for b in buckets:
        print(f"{b['Name']:<50} {b['CreationDate']:%Y-%m-%d %H:%M}")
    print(f"\n{len(buckets)} bucket(s)")

def upload_file():
    path   = input("Local file path: ").strip()
    bucket = input("Target bucket: ").strip()

    if not os.path.isfile(path):
        print(f"File not found: {path}")
        return

    default_key = os.path.basename(path)
    key = input(f"Object key [{default_key}]: ").strip() or default_key

    s3.upload_file(path, bucket, key)
    print(f"Uploaded {path} -> s3://{bucket}/{key}")


def list_objects():
    bucket = input("Bucket name: ").strip()
    prefix = input("Prefix filter (Enter for all): ").strip()

    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

    total_objects = 0
    total_bytes = 0

    print(f"\n{'KEY':<50} {'SIZE':>12}  MODIFIED")
    print("-" * 78)

    for page in pages:
        for obj in page.get("Contents", []):
            total_objects += 1
            total_bytes += obj["Size"]
            print(f"{obj['Key']:<50} {obj['Size']:>12,}  "
                  f"{obj['LastModified']:%Y-%m-%d %H:%M}")

    if total_objects == 0:
        print("(bucket is empty)")
        return

    print(f"\n{total_objects} object(s), "
          f"{total_bytes / 1024 / 1024:.2f} MB total")


def download_file():
    bucket = input("Bucket name: ").strip()
    key    = input("Object key: ").strip()
    dest   = input("Save as: ").strip() or os.path.basename(key)

    try:
        s3.download_file(bucket, key, dest)
        print(f"Downloaded -> {dest}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            print("That object does not exist.")
        else:
            raise


def delete_file():
    bucket = input("Bucket name: ").strip()
    key    = input("Object key: ").strip()

    try:
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"Deleted s3://{bucket}/{key}")
    except ClientError as e:
        print(f"[AWS ERROR] {e.response['Error']['Code']}")





def generate_presigned_url():
    bucket  = input("Bucket name: ").strip()
    key     = input("Object key: ").strip()
    raw     = input("Valid for how many seconds? [3600]: ").strip()
    expires = int(raw) if raw.isdigit() else 3600

    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )
    print(f"\nValid for {expires} seconds:\n{url}\n")


def delete_bucket():
    name = input("Bucket to delete: ").strip()
    confirm = input(f"Type the bucket name again to confirm: ").strip()

    if confirm != name:
        print("Names do not match. Nothing was deleted.")
        return

    try:
        s3.delete_bucket(Bucket=name)
        print(f"Deleted bucket '{name}'")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "BucketNotEmpty":
            print("Bucket is not empty. Delete every object first (option 6), then try again.")
        elif code == "NoSuchBucket":
            print("That bucket does not exist. Check the name and the region.")
        else:
            print(f"[AWS ERROR] {code}")


def backup_local_folder():
    folder = input("Local folder to back up: ").strip()
    bucket = input("Target bucket: ").strip()
    prefix = input("Key prefix [backup/]: ").strip() or "backup/"

    if not os.path.isdir(folder):
        print(f"Folder not found: {folder}")
        return

    if not prefix.endswith("/"):
        prefix += "/"

    success = 0
    failed = 0

    for root, dirs, files in os.walk(folder):
        for filename in files:
            local_path = os.path.join(root, filename)

            relative = os.path.relpath(local_path, folder)
            key = prefix + relative.replace(os.sep, "/")

            try:
                s3.upload_file(local_path, bucket, key)
                print(f"Uploaded {local_path} -> s3://{bucket}/{key}")
                success += 1
            except (ClientError, S3UploadFailedError) as e:
                print(f"Failed {local_path}: {e}")
                failed += 1

    print(f"\nBackup finished: {success} uploaded, {failed} failed")


ACTIONS = {
    "1": create_bucket,
    "2": list_buckets,
    "3": upload_file,
    "4": list_objects,
    "5": download_file,
    "6": delete_file,
    "7": generate_presigned_url,
    "8": delete_bucket,
    "9": backup_local_folder,
}


def main():
    while True:
        print(MENU)

        choice = input("Choose an option: ").strip()

        if choice == "0":
            sys.exit(0)

        action = ACTIONS.get(choice)

        if action:
            action()
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
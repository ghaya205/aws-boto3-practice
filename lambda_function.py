#name = "my-first-lambda"
#def lambda_handler(event, context):
   # return {
        #"statusCode": 200,
        #"body": "Hello from AWS Lambda!"
    #}
import json


def lambda_handler(event, context):
    name = event.get("name", "world")
    return {
        "statusCode": 200,
        "body": json.dumps({"message": f"Hello, {name}, from Lambda!"}),
    }

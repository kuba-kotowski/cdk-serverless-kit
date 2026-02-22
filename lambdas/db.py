import os
import boto3


TABLE_NAME = os.environ["DYNAMODB_TABLE"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def put_item(item: dict):
    table.put_item(Item=item)


def get_item(key: dict):
    response = table.get_item(Key=key)
    return response.get("Item", {})
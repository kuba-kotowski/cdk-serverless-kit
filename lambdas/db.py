import os
import boto3

dynamodb = boto3.resource("dynamodb")

table_name = os.getenv("DYNAMODB_TABLE")
table = dynamodb.Table(table_name)


def put_item(item: dict):
    table.put_item(Item=item)


def get_item(key: dict):
    response = table.get_item(Key=key)
    return response.get("Item", {})
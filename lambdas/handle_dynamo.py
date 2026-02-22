import json

from utils import create_response
from db import put_item, get_item


id = "123"

item = {
    "id": id,
    "name": "Test Item"
}


def post(event, context):

    put_item(item)

    return create_response(201, {"message": "Test Item created successfully"})


def get(event, context):

    item = get_item({"id": id})

    return create_response(200, item)
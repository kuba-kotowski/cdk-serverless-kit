from utils import create_response


def handler(event, context):
    return create_response(200, {"message": "Hello from CDK Serverless Kit"})
import boto3

secret_client = boto3.client('secretsmanager')

api_key_secret_name = 'my-api-key'
api_key = secret_client.get_secret_value(SecretId=api_key_secret_name)['SecretString']


def handler(event, context):
    """
    Simple example of a Lambda Authorizer that checks for a Bearer token in the Authorization header.
    """

    headers = event.get("headers", {})
    auth_header = headers.get("authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return {"isAuthorized": False}

    token = auth_header.split(" ")[1]

    # Validate JWT here
    if token and token == api_key:
        return {
            "isAuthorized": True,
            "context": {
                "role": "internal"
            }
        }
    
    return {"isAuthorized": False}
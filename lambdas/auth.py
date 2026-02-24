import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


secret_client = boto3.client('secretsmanager')

secret_id = os.getenv('SECRET_ID')
secret_key = os.getenv('SECRET_KEY')

if not secret_id or not secret_key:
    raise ValueError("SECRET_ID and SECRET_KEY environment variables must be set")


_cached_api_key = None

def _get_api_key():
    global _cached_api_key
    if _cached_api_key is None:
        try:
            secret = secret_client.get_secret_value(SecretId=secret_id)
            secret_json = json.loads(secret["SecretString"])
            _cached_api_key = secret_json.get(secret_key)
            if not _cached_api_key:
                logger.warning(f"Secret key '{secret_key}' not found in secret '{secret_id}'")
        except Exception as e:
            logger.exception("Failed to retrieve secret")
            return None
    return _cached_api_key


def handler(event, context):
    """
    Simple example of a Lambda Authorizer that checks for a Bearer token in the Authorization header.
    """

    headers = event.get("headers", {})
    auth_header = headers.get("authorization") or headers.get("Authorization")

    try:
        scheme, token = auth_header.split(" ")
        if scheme.lower() != "bearer":
            return {"isAuthorized": False}
    except ValueError:
        return {"isAuthorized": False}

    # Validate token here:
    # For demonstration, we simply compare the token to a value stored in Secrets Manager.
    api_key = _get_api_key()
    if not api_key:
        logger.error("API key not available for authorization")
        return {"isAuthorized": False}

    if token and token == api_key:
        logger.info("Authorization successful")
        return {
            "isAuthorized": True,
            "context": {
                "role": "internal"
            }
        }
    else:
        logger.warning("Unauthorized access attempt")
        return {"isAuthorized": False}
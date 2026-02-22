from typing import Dict, Any
import json


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }

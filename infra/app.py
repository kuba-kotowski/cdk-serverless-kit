import aws_cdk as cdk
from stack import ServerlessStack

app = cdk.App()

ServerlessStack(
    app,
    "ServerlessStack",  # This will be overridden with dynamic name
)

app.synth()
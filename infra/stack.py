import os
import yaml
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_lambda as _lambda,
    aws_apigatewayv2 as apigateway2,
    aws_apigatewayv2_integrations as integrations,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class ServerlessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        config = self.load_config("config.yaml")
        self.project_name = config["project_name"]
        self.env_name = config.get("env_name", "main")
        
        # Use dynamic stack name
        stack_name = f"{self.project_name}-{self.env_name}-stack"
        super().__init__(scope, stack_name, **kwargs)

        # Optional DynamoDB
        table = None
        if config.get("dynamodb"):
            table = self.create_dynamodb_table()

        # Optional API Gateway
        if config.get("api_gateway"):
            api = self.create_api_gateway()
            routes = self.load_config("routes.yaml")["routes"]

            self.create_from_routes(routes, table, api)
        else:
            self.create_lambdas_standalone(table)

    def create_lambdas_standalone(self, table):
        for py_file in self.get_lambda_files():
            module_name = py_file.replace('.py', '')
            self.create_lambda(f"{self.project_name}-{self.env_name}-{module_name}", f"{module_name}.handler", table)

    def create_from_routes(self, routes, table, api):
        for route in routes:
            method = route.get("method", "GET")
            path = route["path"]
            handler = route["handler"]
            
            fn = self.create_lambda(f"{self.project_name}-{self.env_name}-{method}-{path.replace('/', '')}", handler, table)
            
            api.add_routes(
                path=path,
                methods=[getattr(apigateway2.HttpMethod, method)],
                integration=integrations.HttpLambdaIntegration(f"{method}-{path}-integration", fn)
            )

    def create_lambda(self, function_id, handler, table):
        fn = _lambda.Function(
            self,
            function_id,
            function_name=function_id,
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler=handler,
            code=_lambda.Code.from_asset("lambdas"),
            timeout=Duration.seconds(10)
        )
        
        if table:
            table.grant_read_write_data(fn)
            fn.add_environment("DYNAMODB_TABLE", table.table_name)
        
        return fn

    def get_lambda_files(self):
        return [f for f in os.listdir("lambdas") if f.endswith(".py") and not f.startswith("__")]

    def create_dynamodb_table(self):
        table_id = f"{self.project_name}-{self.env_name}-Table"
        table = dynamodb.Table(
            self,
            table_id,
            table_name=table_id,
            partition_key={"name": "id", "type": dynamodb.AttributeType.STRING},
            removal_policy=RemovalPolicy.DESTROY,
        )

        return table
    
    def create_api_gateway(self):
        api_id = f"{self.project_name}-HttpApi" # env_name will be included as stage, under the same API
        api = apigateway2.HttpApi(
            self, 
            api_id, 
            api_name=api_id,
            create_default_stage=False
        )
        api.add_stage(
            f"{self.env_name}",
            auto_deploy=True
        )

        return api

    def load_config(self, path="config.yaml"):
        with open(path) as f:
            return yaml.safe_load(f)
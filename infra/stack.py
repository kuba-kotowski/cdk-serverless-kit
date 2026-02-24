import os
import yaml
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_lambda as _lambda,
    aws_cognito as cognito,
    aws_secretsmanager as secretsmanager,
    aws_apigatewayv2 as apigateway2,
    aws_apigatewayv2_integrations as integrations,
    aws_apigatewayv2_authorizers as authorizers,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
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
            
            authorizer = None
            if config.get("auth"):
                if config["auth"] == "lambda":
                    self.secret_key = config.get("secret_key", "api_key")
                    
                    secret = self.create_secret_api_key()
                    authorizer = self.create_lambda_authorizer("auth.handler", table, secret)
                
                elif config["auth"] == "cognito":
                    authorizer = self.create_jwt_authorizer()

            routes = self.load_config("routes.yaml")["routes"]

            self.create_from_routes(routes, table, api, authorizer)
        else:
            self.create_lambdas_standalone(table)

    def create_lambdas_standalone(self, table):
        for py_file in self.get_lambda_files():
            module_name = py_file.replace('.py', '')
            self.create_lambda(f"{self.project_name}-{self.env_name}-{module_name}", f"{module_name}.handler", table)

    def create_from_routes(self, routes, table, api, authorizer):
        for route in routes:
            # Validate required fields
            if "path" not in route or "handler" not in route:
                raise ValueError(f"Route missing required 'path' or 'handler': {route}")
            
            method = route.get("method", "GET")
            path = route["path"]
            handler = route["handler"]
            
            safe_path = path.replace('/', '-').replace('{', '').replace('}', '').strip('-')
            function_id = f"{self.project_name}-{self.env_name}-{method}-{safe_path}"
            
            fn = self.create_lambda(function_id, handler, table)
            
            integration_id = f"{method}-{safe_path}-integration"
            
            kwargs = {"authorizer": authorizer} if route.get("auth") else {}
            api.add_routes(
                path=path,
                methods=[getattr(apigateway2.HttpMethod, method)],
                integration=integrations.HttpLambdaIntegration(integration_id, fn),
                **kwargs
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
            create_default_stage=False,
            cors_preflight=apigateway2.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[
                    apigateway2.CorsHttpMethod.GET,
                    apigateway2.CorsHttpMethod.POST,
                    apigateway2.CorsHttpMethod.PUT,
                    apigateway2.CorsHttpMethod.PATCH,
                    apigateway2.CorsHttpMethod.DELETE,
                    apigateway2.CorsHttpMethod.OPTIONS
                ],
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Amz-Date",
                    "X-Api-Key",
                    "X-Amz-Security-Token"
                ],
                max_age=Duration.days(1)
            )
        )
        
        api.add_stage(
            f"{self.env_name}",
            auto_deploy=True
        )

        return api

    def create_secret_api_key(self):
        secret_id = f"{self.project_name}-{self.env_name}-ApiKey"
        secret = secretsmanager.Secret(
            self,
            secret_id,
            secret_name=secret_id,
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=f'{{"{self.secret_key}": ""}}',
                generate_string_key=self.secret_key
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        return secret

    def create_lambda_authorizer(self, auth_handler, table, secret):
        authorizer_id = f"{self.project_name}-{self.env_name}-LambdaAuthorizer"
        fn = self.create_lambda(f"{authorizer_id}", auth_handler, table)
        
        # Grant Secrets Manager permissions to authorizer if secrets manager is used in the handler
        if secret:
            fn.add_to_role_policy(
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["secretsmanager:GetSecretValue"],
                    resources=[f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{secret.secret_name}-*"]
                )
            )
            fn.add_environment("SECRET_ID", secret.secret_name)
            fn.add_environment("SECRET_KEY", self.secret_key)

        authorizer = authorizers.HttpLambdaAuthorizer(
            authorizer_id,
            handler=fn,
            identity_source=["$request.header.Authorization"],
            response_types=[authorizers.HttpLambdaResponseType.SIMPLE]
        )

        return authorizer

    def create_jwt_authorizer(self):
        user_pool, user_pool_client = self.create_cognito_user_pool()

        authorizer_id = f"{self.project_name}-{self.env_name}-JWTAuthorizer"
        authorizer = authorizers.HttpJwtAuthorizer(
            authorizer_id,
            jwt_issuer=user_pool.user_pool_provider_url,
            jwt_audience=[user_pool_client.user_pool_client_id],
        )

        return authorizer

    def create_cognito_user_pool(self):
        user_pool_id = f"{self.project_name}-{self.env_name}-UserPool"
        user_pool = cognito.UserPool(
            self, 
            user_pool_id, 
            user_pool_name=user_pool_id,
            removal_policy=RemovalPolicy.DESTROY
        )

        user_pool_client_id = f"{self.project_name}-{self.env_name}-UserPoolClient"
        user_pool_client = cognito.UserPoolClient(
            self,
            user_pool_client_id,
            user_pool=user_pool
        )

        return user_pool, user_pool_client
    
    def load_config(self, path="config.yaml"):
        with open(path) as f:
            return yaml.safe_load(f)
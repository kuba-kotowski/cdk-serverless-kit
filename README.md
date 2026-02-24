# CDK Serverless Template

Bootstrap serverless projects with Lambda functions.

## Getting Started

1. **Copy this repository** for your new project

2. **Configure** `config.yaml`:
    ```yaml
    project_name: your-service-name
    region: eu-central-1
    env_name: dev
    api_gateway: true    # or false
    auth: null           # options: null, lambda, cognito
    secret_key: api_key  # optional for lambda authorizer, default is 'api_key'
    dynamodb: false      # or true
    ```

3. **Add your Lambda functions** to `lambdas/` folder
    - For standalone projects: Each `.py` file needs a `handler(event, context)` function
    - For API projects: Use any function names (specified in routes)

4. **For API projects**: Define routes in `routes.yaml`
    ```yaml
    routes:
    - path: /hello
        method: GET
        handler: hello.handler
        auth: true          # optional, requires authentication
    - path: /public
        method: GET
        handler: public.handler
        # auth: false by default
    ```

## Authentication

When `auth` is configured in `config.yaml`, you can protect routes by adding `auth: true`:

- **Lambda Authorizer** (`auth: lambda`):
  - Uses Bearer token validation with AWS Secrets Manager
  - Requires `auth.py` lambda function for token validation
  - Configure `secret_key` parameter (defaults to 'api_key')
  - Send requests with `Authorization: Bearer {your-token}` header

- **Cognito JWT** (`auth: cognito`):
  - Uses AWS Cognito User Pool for JWT token validation
  - Automatically creates User Pool and User Pool Client
  - Send requests with `Authorization: Bearer {jwt-token}` header

5. **Deploy** 

    **One-time account setup** (if not done before):
    ```bash
    npx cdk bootstrap {account-id}/{region} --profile your-aws-profile
    ```
    *Note: `your-aws-profile` refers to your AWS credentials profile in `.aws/config`*

    **GitHub Actions** (recommended):
    - Push to your repository branch
    - GitHub Actions handles deployment automatically

    **From local machine**:
    ```bash
    conda activate your-env # if using conda env

    pip install -r requirements

    npx cdk deploy --profile your-aws-profile
    ```

    **Deleting all resources**:
    ```bash
    conda activate your-env # if using conda env

    npx cdk destroy --profile your-aws-profile
    ```

## Important!

- If using **API Gateway**, include `routes.yaml` to create HTTP endpoints.
- If using **Authentication**, routes with `auth: true` will be protected by the configured authorizer.
- If using **DynamoDB**, from default it's creating one table with partition key - `id (string)`. 
- If using **multiple environments**, use `env_name` param - it creates separate AWS resources.
- Stack is named `{project_name}-{env_name}-stack`. Once set & deployed, don't change it unless you want your services to be recreated. 

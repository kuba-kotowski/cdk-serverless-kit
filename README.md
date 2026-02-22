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
    ```

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
- If using **DynamoDB**, from default it's creating one table with partition key - `id (string)`. 
- If using **multiple environments**, use `env_name` param - it creates separate AWS resources.
- Stack is named `{project_name}-{env_name}-stack`. Once set & deployed, don't change it unless you want your services to be recreated. 

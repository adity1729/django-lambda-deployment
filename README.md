# Django Serverless Deployment on AWS Lambda

A complete guide to deploying Django applications to AWS Lambda using Docker containers, API Gateway, and automated CI/CD with GitHub Actions.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Manual Deployment](#manual-deployment)
- [GitHub Actions CI/CD](#github-actions-cicd)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

## 🚀 Prerequisites

- AWS CLI installed and configured
- Docker installed
- Python 3.9+ and Django project
- GitHub account (for CI/CD)
- AWS Account with appropriate permissions

## ⚡ Quick Start

### 1. Configure AWS CLI

```bash
aws configure
```

Enter your AWS Access Key ID, Secret Access Key, and preferred region.

### 2. Set Environment Variables

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION="us-east-1"  # Change to your preferred region
export ECR_REPO="django-serverless"
export LAMBDA_FUNCTION="django-serverless"
export IAM_ROLE="lambda-django-role"
```

### 3. Run Setup Script

```bash
chmod +x deploy.sh
./deploy.sh
```

## 📦 Manual Deployment

### Step 1: Create ECR Repository

```bash
aws ecr create-repository \
    --repository-name $ECR_REPO \
    --region $AWS_REGION
```

### Step 2: Build and Push Docker Image

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
    docker login --username AWS --password-stdin \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build Docker image for AMD64 architecture (important for Lambda compatibility)
docker buildx build --platform linux/amd64 -t $ECR_REPO:latest .

# Tag the image
docker tag $ECR_REPO:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
```

> **Note:** If Docker push fails, it might have cached the wrong repository name. Use the full URI directly instead of variables.

### Step 3: Create IAM Role for Lambda

```bash
# Create trust policy file
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create the IAM role
aws iam create-role \
    --role-name $IAM_ROLE \
    --assume-role-policy-document file://trust-policy.json

# Attach necessary policies
aws iam attach-role-policy \
    --role-name $IAM_ROLE \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

aws iam attach-role-policy \
    --role-name $IAM_ROLE \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Get the role ARN (save this for next step)
export ROLE_ARN=$(aws iam get-role --role-name $IAM_ROLE --query Role.Arn --output text)
echo "Role ARN: $ROLE_ARN"
```

### Step 4: Create Lambda Function

```bash
# Set image URI
export IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest"

# Wait for role to propagate (important!)
sleep 10

# Create Lambda function
aws lambda create-function \
    --function-name $LAMBDA_FUNCTION \
    --region $AWS_REGION \
    --package-type Image \
    --code ImageUri=$IMAGE_URI \
    --role $ROLE_ARN \
    --timeout 30 \
    --memory-size 512 \
    --environment Variables="{DJANGO_SETTINGS_MODULE=config.settings}"
```

> **Important Notes:**
> - If you get a `ValidationException` error, verify your `ROLE_ARN` is set correctly
> - Ensure your ECR image region matches your Lambda function region
> - Make sure your Django `ALLOWED_HOSTS` includes the API Gateway domain or use `["*"]` for testing

### Step 5: Create API Gateway

```bash
# Create HTTP API
aws apigatewayv2 create-api \
    --name django-api \
    --protocol-type HTTP \
    --target arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:$LAMBDA_FUNCTION \
    --region $AWS_REGION

# Grant API Gateway permission to invoke Lambda
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --region $AWS_REGION

# Get the API endpoint
export API_ENDPOINT=$(aws apigatewayv2 get-apis \
    --region $AWS_REGION \
    --query "Items[?Name=='django-api'].ApiEndpoint" \
    --output text)

echo "🎉 Deployment Complete!"
echo "API Endpoint: $API_ENDPOINT"
```

### Step 6: Test Your Deployment

```bash
curl $API_ENDPOINT/api/hello/
```

## 🔄 GitHub Actions CI/CD

### 1. Add Secrets to GitHub Repository

Go to: **Repository Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

| Secret Name | Value | Description |
|------------|-------|-------------|
| `AWS_ACCOUNT_ID` | Your AWS Account ID | Get from `aws sts get-caller-identity` |
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key | IAM user access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Key | IAM user secret key |
| `AWS_REGION` | `us-east-1` | Your deployment region |
| `DJANGO_SECRET_KEY` | Your Django secret | Django SECRET_KEY setting |

### 2. Create Deployment Workflow

Create `.github/workflows/deploy.yml` in your repository with the workflow configuration (see artifact above).

### 3. Configure Variables in Workflow

Update these variables in the workflow file if needed:

```yaml
env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: django-serverless
  LAMBDA_FUNCTION: django-serverless
```

### 4. Push and Deploy

```bash
git add .
git commit -m "Add deployment workflow"
git push origin main
```

The GitHub Action will automatically:
1. Build your Docker image for AMD64
2. Push to Amazon ECR
3. Update Lambda function
4. Display the API endpoint

## 🔧 Updating Your Lambda Function

When you make changes to your Django code:

```bash
# Rebuild for AMD64 architecture
docker buildx build --platform linux/amd64 -t $ECR_REPO:latest .

# Tag and push
docker tag $ECR_REPO:latest \
    $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Update Lambda function
aws lambda update-function-code \
    --function-name $LAMBDA_FUNCTION \
    --image-uri $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest \
    --region $AWS_REGION

# Check update status
aws lambda get-function \
    --function-name $LAMBDA_FUNCTION \
    --region $AWS_REGION \
    --query 'Configuration.LastUpdateStatus' \
    --output text
```

## 🐛 Troubleshooting

### Internal Server Error (500)

This is commonly caused by architecture mismatch between your local machine and Lambda.

**Solution:** Always build for AMD64 architecture:

```bash
docker buildx build --platform linux/amd64 -t $ECR_REPO:latest .
```

If you're on an M1/M2 Mac, you're building ARM64 by default, but Lambda expects AMD64.

### ValidationException: Invalid Role ARN

**Problem:** The IAM role ARN format is incorrect or the role doesn't exist.

**Solution:**
```bash
# Verify role exists
aws iam get-role --role-name $IAM_ROLE

# Set ROLE_ARN explicitly
export ROLE_ARN="arn:aws:iam::$AWS_ACCOUNT_ID:role/$IAM_ROLE"
```

### Region Mismatch Error

**Problem:** ECR image and Lambda function are in different regions.

**Solution:** Ensure both are in the same region:
```bash
# Check ECR region
aws ecr describe-repositories --repository-name $ECR_REPO --region $AWS_REGION

# Always specify --region flag when creating Lambda
```

### Permission Denied: ResourceConflictException

**Problem:** API Gateway permission already exists.

**Solution:**
```bash
# Remove existing permission
aws lambda remove-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id apigateway-invoke \
    --region $AWS_REGION

# Add it again
aws lambda add-permission \
    --function-name $LAMBDA_FUNCTION \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --region $AWS_REGION
```

### Django ALLOWED_HOSTS Error

**Problem:** Django rejects requests from API Gateway.

**Solution:** Add API Gateway domain to `ALLOWED_HOSTS` in `settings.py`:

```python
# For development/testing
ALLOWED_HOSTS = ["*"]

# For production (recommended)
ALLOWED_HOSTS = [
    "your-api-id.execute-api.us-east-1.amazonaws.com",
    "localhost",
    "127.0.0.1"
]
```

## 📁 Project Structure

```
django-serverless/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── your_django_project/
│   ├── settings.py            # Django settings
│   ├── urls.py
│   └── ...
├── Dockerfile                 # Container definition
├── requirements.txt           # Python dependencies
├── trust-policy.json         # IAM role trust policy
├── deploy.sh                 # Deployment script
└── README.md                 # This file
```

## 📚 Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Amazon ECR Documentation](https://docs.aws.amazon.com/ecr/)
- [API Gateway Documentation](https://docs.aws.amazon.com/apigateway/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)

## 📝 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `AWS_ACCOUNT_ID` | Your AWS account identifier | `123456789012` |
| `AWS_REGION` | AWS region for deployment | `us-east-1` |
| `ECR_REPO` | ECR repository name | `django-serverless` |
| `LAMBDA_FUNCTION` | Lambda function name | `django-serverless` |
| `IAM_ROLE` | IAM role name for Lambda | `lambda-django-role` |
| `ROLE_ARN` | Full ARN of IAM role | `arn:aws:iam::123456789012:role/...` |
| `IMAGE_URI` | Full ECR image URI | `123456789012.dkr.ecr.us-east-1...` |
| `API_ENDPOINT` | API Gateway endpoint URL | `https://abc123.execute-api...` |

## 🔒 Security Best Practices

1. **Never commit AWS credentials** to your repository
2. Use **IAM roles** with least privilege principle
3. Set specific **ALLOWED_HOSTS** in production
4. Use **environment variables** for sensitive configuration
5. Enable **CloudWatch logs** for monitoring
6. Implement **API Gateway authentication** for production APIs
7. Use **AWS Secrets Manager** for sensitive data

## 📄 License

MIT License - Feel free to use this in your projects!

---

**Need help?** Open an issue or check the troubleshooting section above.

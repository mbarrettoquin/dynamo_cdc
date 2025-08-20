@echo off
REM Deploy script for DynamoDB CDC Latency Testing Framework (Windows)

echo 🚀 Deploying DynamoDB CDC Latency Testing Framework...

REM Check if AWS CLI is configured
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ AWS CLI is not configured. Please run 'aws configure' first.
    exit /b 1
)

REM Check if CDK is installed
cdk --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ AWS CDK is not installed. Installing...
    npm install -g aws-cdk
)

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Navigate to CDK directory
cd cdk

REM Bootstrap CDK (only needed once per account/region)
echo 🏗️ Bootstrapping CDK...
cdk bootstrap

REM Deploy the stack
echo 🚀 Deploying infrastructure...
cdk deploy --require-approval never

if %errorlevel% equ 0 (
    echo ✅ Deployment successful!
    echo.
    echo 📊 To monitor latency metrics:
    echo aws logs tail /aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader* --follow
    echo.
    echo 📈 To query latency data ^(CloudWatch Insights^):
    echo aws logs start-query --log-group-name /aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader* --start-time ^(Get-Date^).AddHours^(-1^).ToUniversalTime^(^).ToString^("yyyy-MM-ddTHH:mm:ssZ"^) --end-time ^(Get-Date^).ToUniversalTime^(^).ToString^("yyyy-MM-ddTHH:mm:ssZ"^) --query-string "fields @timestamp, latency_ms | filter ispresent^(latency_ms^) | sort @timestamp desc"
) else (
    echo ❌ Deployment failed. Check the error messages above.
    exit /b 1
)

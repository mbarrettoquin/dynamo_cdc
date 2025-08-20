#!/bin/bash

# Deploy script for DynamoDB CDC Latency Testing Framework

echo "🚀 Deploying DynamoDB CDC Latency Testing Framework..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    echo "❌ AWS CDK is not installed. Installing..."
    npm install -g aws-cdk
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Navigate to CDK directory
cd cdk

# Bootstrap CDK (only needed once per account/region)
echo "🏗️ Bootstrapping CDK..."
cdk bootstrap

# Deploy the stack
echo "🚀 Deploying infrastructure..."
cdk deploy --require-approval never

if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "📊 To monitor latency metrics:"
    echo "aws logs tail /aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader* --follow"
    echo ""
    echo "📈 To query latency data (CloudWatch Insights):"
    echo "aws logs start-query --log-group-name /aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader* --start-time \$(date -d '1 hour ago' +%s) --end-time \$(date +%s) --query-string 'fields @timestamp, latency_ms | filter ispresent(latency_ms) | sort @timestamp desc'"
else
    echo "❌ Deployment failed. Check the error messages above."
    exit 1
fi

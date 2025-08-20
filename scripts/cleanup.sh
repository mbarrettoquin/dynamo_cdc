#!/bin/bash

# Cleanup script for DynamoDB CDC Latency Testing Framework

echo "🧹 Cleaning up DynamoDB CDC Latency Testing Framework..."

# Navigate to CDK directory
cd cdk

# Destroy the stack
echo "🗑️ Destroying infrastructure..."
cdk destroy --force

if [ $? -eq 0 ]; then
    echo "✅ Cleanup successful! All resources have been removed."
else
    echo "❌ Cleanup failed. Check the error messages above."
    echo "You may need to manually remove some resources from the AWS Console."
    exit 1
fi

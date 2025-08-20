@echo off
REM Cleanup script for DynamoDB CDC Latency Testing Framework (Windows)

echo 🧹 Cleaning up DynamoDB CDC Latency Testing Framework...

REM Navigate to CDK directory
cd cdk

REM Destroy the stack
echo 🗑️ Destroying infrastructure...
cdk destroy --force

if %errorlevel% equ 0 (
    echo ✅ Cleanup successful! All resources have been removed.
) else (
    echo ❌ Cleanup failed. Check the error messages above.
    echo You may need to manually remove some resources from the AWS Console.
    exit /b 1
)

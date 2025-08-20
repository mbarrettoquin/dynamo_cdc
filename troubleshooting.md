# DynamoDB CDC Latency Testing Framework - Troubleshooting Guide

## Common Issues and Solutions

### 1. DynamoDB Table Not Found

**Error**: `Table not found` or `ResourceNotFoundException`

**Solution**: 
- Verify your DynamoDB table name in `cdk/cdk_stack.py`
- Ensure the table exists in the same AWS region as your deployment
- Check that streams are enabled on the table

```bash
# Check if table exists
aws dynamodb describe-table --table-name FOS_DocStore_Compare_POC-dev-dynamodb

# Enable streams if not already enabled
aws dynamodb update-table \
    --table-name FOS_DocStore_Compare_POC-dev-dynamodb \
    --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES
```

### 2. No Latency Metrics in Logs

**Symptoms**: Writer Lambda runs but no latency data appears in Reader Lambda logs

**Troubleshooting**:

1. **Check if streams are enabled**:
   ```bash
   aws dynamodb describe-table --table-name FOS_DocStore_Compare_POC-dev-dynamodb --query 'Table.StreamSpecification'
   ```

2. **Verify test records are being written**:
   ```bash
   aws logs tail /aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyWriter* --follow
   ```

3. **Check Reader Lambda is receiving events**:
   ```bash
   aws logs tail /aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader* --follow
   ```

4. **Verify event source mapping exists**:
   ```bash
   aws lambda list-event-source-mappings --function-name DynamoCdcLatencyStack-DynamoCdcLatencyReader*
   ```

### 3. CDK Bootstrap Error

**Error**: `Need to perform AWS CDK bootstrap`

**Solution**:
```bash
cd cdk
cdk bootstrap
```

If this fails, check your AWS credentials and region configuration.

### 4. Permission Errors

**Error**: `AccessDenied` or `UnauthorizedOperation`

**Solution**:
- Ensure your AWS credentials have sufficient permissions
- Required permissions include:
  - DynamoDB: PutItem, DescribeTable, DescribeStream, GetRecords, GetShardIterator, ListStreams
  - Lambda: CreateFunction, UpdateFunction, CreateEventSourceMapping
  - IAM: CreateRole, AttachRolePolicy
  - CloudFormation: CreateStack, UpdateStack, DescribeStacks
  - EventBridge: CreateRule, PutTargets

### 5. Lambda Function Timeout

**Error**: `Task timed out after X seconds`

**Solution**:
- Increase timeout in `cdk_stack.py` (currently set to 30-60 seconds)
- Check for any infinite loops or hanging operations in Lambda code

### 6. High Latency Values

**Issue**: Consistently high latency measurements (>5000ms)

**Investigation**:

1. **Check DynamoDB throttling**:
   ```bash
   aws cloudwatch get-metric-statistics \
       --namespace AWS/DynamoDB \
       --metric-name ReadThrottledEvents \
       --dimensions Name=TableName,Value=FOS_DocStore_Compare_POC-dev-dynamodb \
       --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
       --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
       --period 300 \
       --statistics Sum
   ```

2. **Monitor Lambda cold starts**:
   - Check Lambda duration metrics in CloudWatch
   - Consider provisioned concurrency for consistent performance

3. **Verify stream shard iterator age**:
   ```bash
   aws cloudwatch get-metric-statistics \
       --namespace AWS/DynamoDB \
       --metric-name IteratorAgeMilliseconds \
       --dimensions Name=TableName,Value=FOS_DocStore_Compare_POC-dev-dynamodb \
       --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
       --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
       --period 300 \
       --statistics Average
   ```

### 7. No Test Records Found in Stream

**Issue**: Reader Lambda processes events but doesn't find test records

**Debug Steps**:

1. **Check test record format in Writer Lambda logs**
2. **Verify filtering logic in Reader Lambda**
3. **Examine actual stream record structure**:

Add this debug code to `reader.py`:
```python
logger.info(f"DEBUG - Full record: {json.dumps(record, default=str)}")
```

### 8. Deployment Fails

**Error**: Various CloudFormation errors during `cdk deploy`

**Solutions**:

1. **Check existing resources**:
   ```bash
   aws cloudformation describe-stacks --stack-name DynamoCdcLatencyStack
   ```

2. **Clean up and retry**:
   ```bash
   cdk destroy --force
   cdk deploy
   ```

3. **Check CloudFormation events**:
   ```bash
   aws cloudformation describe-stack-events --stack-name DynamoCdcLatencyStack
   ```

### 9. Monitoring and Debugging Commands

**View Lambda function details**:
```bash
aws lambda get-function --function-name DynamoCdcLatencyStack-DynamoCdcLatencyWriter*
aws lambda get-function --function-name DynamoCdcLatencyStack-DynamoCdcLatencyReader*
```

**Check EventBridge rule**:
```bash
aws events list-rules --name-prefix DynamoCdcLatencyStack
```

**Monitor Lambda invocations**:
```bash
aws cloudwatch get-metric-statistics \
    --namespace AWS/Lambda \
    --metric-name Invocations \
    --dimensions Name=FunctionName,Value=DynamoCdcLatencyStack-DynamoCdcLatencyWriter* \
    --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
    --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
    --period 300 \
    --statistics Sum
```

### 10. Manual Testing

**Manually trigger Writer Lambda**:
```bash
aws lambda invoke \
    --function-name DynamoCdcLatencyStack-DynamoCdcLatencyWriter* \
    --payload '{}' \
    /tmp/output.json
```

**Query DynamoDB for test records**:
```bash
aws dynamodb scan \
    --table-name FOS_DocStore_Compare_POC-dev-dynamodb \
    --filter-expression "test_type = :tt" \
    --expression-attribute-values '{":tt":{"S":"cdc_latency_measurement"}}' \
    --limit 5
```

## Getting Help

If you continue to experience issues:

1. Check AWS service health: https://status.aws.amazon.com/
2. Review CloudWatch logs for detailed error messages
3. Validate your AWS account limits and quotas
4. Test with a smaller, simpler DynamoDB table first

## Performance Optimization

For production-like testing:

1. **Use provisioned capacity** instead of on-demand for consistent performance
2. **Enable point-in-time recovery** to avoid impacting performance
3. **Monitor DynamoDB metrics** (consumed capacity, throttling)
4. **Consider VPC endpoints** to reduce network latency
5. **Use Lambda provisioned concurrency** to eliminate cold starts

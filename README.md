# DynamoDB CDC Latency Testing Framework

This framework measures the latency of DynamoDB Change Data Capture (CDC) stream updates by writing test records and measuring the time between write and stream processing.

## Architecture

```
EventBridge (Scheduler) → Lambda (Writer) → DynamoDB Table → DynamoDB Stream → Lambda (Reader) → CloudWatch Logs
```

## Components

- **Writer Lambda**: Periodically writes test records with timestamps to DynamoDB
- **Reader Lambda**: Processes DynamoDB stream events and calculates latency
- **EventBridge Rule**: Triggers the writer every 1 minute
- **CloudWatch Logs**: Stores latency measurements for analysis

## Prerequisites

- AWS CLI configured with appropriate permissions
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- Python 3.9+ installed
- Existing DynamoDB table: `FOS_DocStore_Compare_POC-dev-dynamodb` with streams enabled

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your DynamoDB table name:**
   Edit `cdk/cdk_stack.py` and update the `DYNAMODB_TABLE_NAME` variable if needed.

3. **Deploy the infrastructure:**
   ```bash
   cd cdk
   cdk bootstrap
   cdk deploy
   ```

4. **Monitor latency:**
   ```bash
   # View real-time logs
   aws logs tail /aws/lambda/dynamo-cdc-latency-reader --follow
   
   # Query latency metrics (CloudWatch Insights)
   aws logs start-query --log-group-name /aws/lambda/dynamo-cdc-latency-reader --start-time $(date -d '1 hour ago' +%s) --end-time $(date +%s) --query-string 'fields @timestamp, latency_ms | filter ispresent(latency_ms) | sort @timestamp desc'
   ```

5. **Clean up:**
   ```bash
   cd cdk
   cdk destroy
   ```

## Latency Metrics

The framework logs structured JSON with the following fields:
- `test_id`: Unique identifier for each test record
- `write_timestamp`: When the record was written to DynamoDB
- `stream_timestamp`: When the stream event was processed
- `latency_ms`: Calculated latency in milliseconds
- `event_name`: DynamoDB stream event type (INSERT/MODIFY/REMOVE)

## Customization

- **Update Frequency**: Modify the `rate(30 seconds)` schedule in `cdk_stack.py`
- **Test Data Size**: Adjust the payload in `lambda/writer.py`
- **Monitoring**: Add CloudWatch alarms or custom metrics as needed

## Troubleshooting

- Ensure your DynamoDB table has streams enabled with "NEW_AND_OLD_IMAGES" view type
- Check Lambda function logs in CloudWatch for any errors
- Verify IAM permissions are correctly applied

## Cost Considerations

This test framework incurs minimal costs:
- Lambda invocations (writer runs every 1 minute)
- DynamoDB writes (small test records)
- CloudWatch Logs storage
- Estimated cost: < $5/month for continuous testing

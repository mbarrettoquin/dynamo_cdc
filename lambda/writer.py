import json
import boto3
import os
import uuid
from datetime import datetime, timezone
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Lambda function that writes test records to DynamoDB with timestamps
    for CDC latency measurement.
    """
    
    table_name = os.environ['DYNAMODB_TABLE_NAME']
    table = dynamodb.Table(table_name)
    
    try:
        # Generate unique test record
        test_id = str(uuid.uuid4())
        current_timestamp = datetime.now(timezone.utc)
        
        # Create test item with timestamp
        test_item = {
            'id': f"latency-test-{test_id}",
            'test_id': test_id,
            'test_timestamp': current_timestamp.isoformat(),
            'timestamp_epoch_ms': int(current_timestamp.timestamp() * 1000),
            'test_type': 'cdc_latency_measurement',
            'test_data': {
                'description': 'Test record for measuring DynamoDB CDC stream latency',
                'created_by': 'dynamo-cdc-latency-writer',
                'sequence': int(current_timestamp.timestamp())
            }
        }
        
        # Write to DynamoDB
        response = table.put_item(Item=test_item)
        
        logger.info(f"Successfully wrote test record: {test_id} at {current_timestamp.isoformat()}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Test record created successfully',
                'test_id': test_id,
                'timestamp': current_timestamp.isoformat(),
                'table_name': table_name
            })
        }
        
    except Exception as e:
        logger.error(f"Error writing test record: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to write test record',
                'details': str(e)
            })
        }

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function that processes DynamoDB stream events and calculates
    CDC latency for test records.
    """
    
    try:
        # Process each record in the stream event
        for record in event['Records']:
            process_stream_record(record)
            
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed stream records')
        }
        
    except Exception as e:
        logger.error(f"Error processing stream records: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing stream records: {str(e)}')
        }

def process_stream_record(record: Dict[str, Any]):
    """
    Process a single DynamoDB stream record and calculate latency
    for test records.
    """
    
    try:
        event_name = record['eventName']
        
        # Only process INSERT and MODIFY events
        if event_name not in ['INSERT', 'MODIFY']:
            return
            
        # Extract the DynamoDB image
        dynamodb_record = record.get('dynamodb', {})
        new_image = dynamodb_record.get('NewImage', {})
        
        # Check if this is a test record
        test_type = new_image.get('test_type', {}).get('S', '')
        if test_type != 'cdc_latency_measurement':
            return
            
        # Extract test information
        test_id = new_image.get('test_id', {}).get('S', 'unknown')
        test_timestamp_str = new_image.get('test_timestamp', {}).get('S', '')
        
        if not test_timestamp_str:
            logger.warning(f"No test_timestamp found for test_id: {test_id}")
            return
            
        # Calculate latency
        stream_timestamp = datetime.now(timezone.utc)
        test_timestamp = datetime.fromisoformat(test_timestamp_str.replace('Z', '+00:00'))
        
        latency_ms = (stream_timestamp - test_timestamp).total_seconds() * 1000
        
        # Log structured latency data for analysis
        latency_data = {
            'test_id': test_id,
            'event_name': event_name,
            'write_timestamp': test_timestamp.isoformat(),
            'stream_timestamp': stream_timestamp.isoformat(),
            'latency_ms': round(latency_ms, 2),
            'approximate_creation_date_time': dynamodb_record.get('ApproximateCreationDateTime', 0)
        }
        
        # Log as structured JSON for easy parsing
        logger.info(f"LATENCY_METRIC: {json.dumps(latency_data)}")
        
        # Also log a human-readable summary
        logger.info(f"CDC Latency - Test ID: {test_id}, Latency: {latency_ms:.2f}ms, Event: {event_name}")
        
    except Exception as e:
        logger.error(f"Error processing individual stream record: {str(e)}")
        logger.error(f"Record content: {json.dumps(record, default=str)}")

def extract_dynamodb_value(attr_value: Dict[str, Any]) -> Any:
    """
    Extract the actual value from a DynamoDB attribute value structure.
    """
    if 'S' in attr_value:
        return attr_value['S']
    elif 'N' in attr_value:
        return float(attr_value['N'])
    elif 'B' in attr_value:
        return attr_value['B']
    elif 'SS' in attr_value:
        return attr_value['SS']
    elif 'NS' in attr_value:
        return [float(n) for n in attr_value['NS']]
    elif 'BS' in attr_value:
        return attr_value['BS']
    elif 'M' in attr_value:
        return {k: extract_dynamodb_value(v) for k, v in attr_value['M'].items()}
    elif 'L' in attr_value:
        return [extract_dynamodb_value(item) for item in attr_value['L']]
    elif 'NULL' in attr_value:
        return None
    elif 'BOOL' in attr_value:
        return attr_value['BOOL']
    else:
        return attr_value

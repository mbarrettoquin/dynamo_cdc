# DynamoDB CDC Latency Analysis Queries

This file contains useful CloudWatch Insights queries for analyzing the latency data collected by the framework.

## Prerequisites

Replace `LOG_GROUP_NAME` with your actual log group name:
```
/aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader*
```

## Basic Latency Query

```sql
fields @timestamp, latency_ms, test_id, event_name
| filter ispresent(latency_ms)
| sort @timestamp desc
| limit 100
```

## Average Latency Over Time (5-minute intervals)

```sql
fields @timestamp, latency_ms
| filter ispresent(latency_ms)
| stats avg(latency_ms) as avg_latency_ms by bin(5m)
| sort @timestamp
```

## Latency Statistics Summary

```sql
fields latency_ms
| filter ispresent(latency_ms)
| stats count(*) as total_measurements, 
        avg(latency_ms) as avg_latency, 
        min(latency_ms) as min_latency, 
        max(latency_ms) as max_latency,
        pct(latency_ms, 50) as p50_latency,
        pct(latency_ms, 90) as p90_latency,
        pct(latency_ms, 95) as p95_latency,
        pct(latency_ms, 99) as p99_latency
```

## High Latency Events (>1000ms)

```sql
fields @timestamp, latency_ms, test_id, event_name
| filter latency_ms > 1000
| sort latency_ms desc
```

## Latency by Event Type

```sql
fields latency_ms, event_name
| filter ispresent(latency_ms)
| stats count(*) as count, avg(latency_ms) as avg_latency by event_name
| sort avg_latency desc
```

## Recent Latency Trend (Last Hour)

```sql
fields @timestamp, latency_ms
| filter ispresent(latency_ms) and @timestamp > datefloor(@timestamp, 1h)
| stats avg(latency_ms) as avg_latency by bin(1m)
| sort @timestamp
```

## Error Analysis

```sql
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
```

## AWS CLI Commands

### Start a CloudWatch Insights Query

```bash
# Replace LOG_GROUP_NAME with your actual log group
aws logs start-query \
    --log-group-name "/aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader*" \
    --start-time $(date -d '1 hour ago' +%s) \
    --end-time $(date +%s) \
    --query-string 'fields @timestamp, latency_ms | filter ispresent(latency_ms) | stats avg(latency_ms) as avg_latency by bin(5m) | sort @timestamp'
```

### Get Query Results

```bash
# Replace QUERY_ID with the ID returned from start-query
aws logs get-query-results --query-id YOUR_QUERY_ID
```

### Tail Live Logs

```bash
aws logs tail /aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader* --follow
```

## PowerShell Commands (Windows)

### Start a CloudWatch Insights Query

```powershell
$startTime = [DateTimeOffset]::Now.AddHours(-1).ToUnixTimeSeconds()
$endTime = [DateTimeOffset]::Now.ToUnixTimeSeconds()

aws logs start-query `
    --log-group-name "/aws/lambda/DynamoCdcLatencyStack-DynamoCdcLatencyReader*" `
    --start-time $startTime `
    --end-time $endTime `
    --query-string "fields @timestamp, latency_ms | filter ispresent(latency_ms) | stats avg(latency_ms) as avg_latency by bin(5m) | sort @timestamp"
```

## Custom Metrics Dashboard

You can create a CloudWatch Dashboard with the following widgets:

1. **Average Latency Over Time**: Line chart showing trends
2. **Latency Distribution**: Histogram of latency values
3. **P99 Latency**: High percentile tracking for SLA monitoring
4. **Error Rate**: Count of processing errors
5. **Throughput**: Number of CDC events processed per minute

## Alerting Recommendations

Set up CloudWatch Alarms for:
- Average latency > 500ms (or your threshold)
- P99 latency > 2000ms 
- Error rate > 5%
- No data received for > 5 minutes (indicates system issues)

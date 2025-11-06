# Assumptions and Design Decisions

## Assumptions Made

1. **ClickHouse Connection**
   - ClickHouse is accessible from the execution environment
   - Using native protocol (port 9000) - can be changed to HTTP (8123) if needed
   - Credentials provided via environment variables

2. **Call Status Filtering**
   - Only counting calls with status 'Answered'
   - This can be easily modified in the query if all calls should be included
   - Rationale: Answered calls are most relevant for agent performance metrics

3. **Date Handling**
   - Defaults to processing yesterday's data (typical for daily exports)
   - Can be overridden via TARGET_DATE environment variable
   - Uses UTC timezone (can be adjusted if needed)

4. **S3 Structure**
   - Files stored in: `s3://bucket/agent_metrics/YYYY-MM-DD/agent_metrics_YYYY-MM-DD.csv`
   - This allows easy date-based organization and querying
   - One file per day as specified

5. **CSV Format**
   - Includes: agent_id, avg_call_length_sec, p90_call_length_sec, total_calls, date
   - Rounding to 2 decimal places for readability
   - UTF-8 encoding

6. **Error Handling**
   - Logs errors but doesn't retry (can be added for production)
   - Fails fast on connection errors
   - Cleans up local CSV files after upload

7. **GitHub Actions**
   - Runs daily at 2 AM UTC (adjustable via cron)
   - Requires secrets to be configured in GitHub repository
   - Can be manually triggered via workflow_dispatch

## Potential Improvements for Production

1. **Retry Logic**: Add retry mechanism for transient failures
2. **Monitoring**: Add metrics/alerts for failed exports
3. **Validation**: Validate data before uploading (e.g., check for nulls, negative values)
4. **Backfill**: Add capability to backfill historical data
5. **Incremental Processing**: Handle partial day data if needed
6. **Compression**: Compress CSV files before upload to save storage
7. **Partitioning**: Consider partitioning by agent_id if dataset is very large
8. **Data Quality Checks**: Validate that metrics are within expected ranges

## Questions to Clarify

1. Should all call statuses be included, or only 'Answered'?
2. What timezone should be used for date calculations?
3. Should the script handle cases where no data exists for a date?
4. Are there any data quality requirements (e.g., minimum number of calls per agent)?
5. Should the script send notifications on failure?


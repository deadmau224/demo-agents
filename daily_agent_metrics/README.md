# Daily Agent Metrics Export

This project exports daily agent call metrics from ClickHouse to AWS S3.
Calculates for each agent:
- Average call length
- 90th percentile call length

## Requirements

- Calculate for each agent:
  - Average call length
  - 90th percentile call length
- Export results as CSV (one file per day)
- Query data from ClickHouse database (falls back to mock data if unavailable)
- Upload to AWS S3 bucket (optional - falls back to local file if S3 unavailable)
- Run daily via GitHub Actions

## ClickHouse Setup

### 1. Set Up ClickHouse Database

You have several options:

#### Option A: ClickHouse Cloud (Recommended)

1. Sign up at https://clickhouse.com/cloud
2. Create a service
3. Get connection details from the dashboard

#### Option B: Docker (For Local Testing)

```bash
docker run -d \
  --name clickhouse-server \
  -p 8123:8123 \
  -p 9000:9000 \
  clickhouse/clickhouse-server
```

Default credentials:
- Host: `localhost`
- Port: `9000` (native) or `8123` (HTTP)
- Username: `default`
- Password: (empty)

#### Option C: Existing ClickHouse Instance

Use your existing ClickHouse connection details.

### 2. Create Database Schema

Run these SQL commands in your ClickHouse database:

```sql
CREATE DATABASE IF NOT EXISTS default;

CREATE TABLE IF NOT EXISTS conversations (
    agent_id String,
    call_start DateTime,
    call_duration_sec Float32,
    call_status String
) ENGINE = MergeTree()
ORDER BY (call_start, agent_id);
```

### 3. Insert Sample Data (For Testing)

```sql
INSERT INTO conversations VALUES
('agent_001', '2025-11-06 10:00:00', 342.5, 'Answered'),
('agent_001', '2025-11-06 11:15:00', 512.3, 'Answered'),
('agent_002', '2025-11-06 09:30:00', 298.7, 'Answered'),
('agent_002', '2025-11-06 14:20:00', 445.2, 'Answered'),
('agent_003', '2025-11-06 12:00:00', 567.8, 'Answered');
```

### 4. Store ClickHouse Credentials in GitHub Secrets

1. Go to your repository: https://github.com/deadmau224/demo-agents/settings/secrets/actions
2. Click **"New repository secret"** for each:
   - Name: `CLICKHOUSE_HOST`, Value: `ybdjbqn5cv.us-east-1.aws.clickhouse.cloud` (or your host)
   - Name: `CLICKHOUSE_PORT`, Value: `8443` (or your port)
   - Name: `CLICKHOUSE_DATABASE`, Value: `default` (or your database name)
   - Name: `CLICKHOUSE_USER`, Value: `default` (or your username)
   - Name: `CLICKHOUSE_PASSWORD`, Value: (your password)

**Note:** The script will automatically fall back to mock data if ClickHouse credentials are not provided or connection fails.

## AWS Setup

### 1. Create AWS Account

If you don't have an AWS account:
1. Go to https://aws.amazon.com and click "Create an AWS Account"
2. Follow the signup process (requires credit card, but free tier available)
3. Free tier includes 5GB S3 storage for 12 months
4. Complete account verification

### 2. Create S3 Bucket

1. Open AWS Console → Navigate to **S3** service
2. Click **"Create bucket"**
3. Configure bucket settings:
   - **Bucket name**: `daily-agent-metrics-deadmau224` (must be globally unique - change as needed)
   - **AWS Region**: `us-east-1 (N. Virginia)` (or your preferred region)
   - **Block all public access**: **Enabled** (recommended for security)
   - **Default encryption**: Enable (SSE-S3 is fine)
   - **Bucket Versioning**: Disabled (can enable later if needed)
4. Click **"Create bucket"**

### 3. Create IAM User for GitHub Actions

1. Go to **IAM** → **Users** → Click **"Create user"**
2. User name: `github-actions-agent-metrics`
3. Select **"Programmatic access"** only (no console access needed)
4. Click **"Next"**
5. Set permissions:
   - Select **"Attach policies directly"**
   - Search and select: `AmazonS3FullAccess` (or create a custom policy with only PutObject permissions for this specific bucket)
6. Click **"Next"** → Review → **"Create user"**
7. **IMPORTANT**: Copy the **Access Key ID** and **Secret Access Key** immediately (shown only once)
   - Save these credentials securely - you won't be able to see the secret key again

### 4. Store Credentials in GitHub Secrets

1. Go to your repository: https://github.com/deadmau224/demo-agents/settings/secrets/actions
2. Click **"New repository secret"** for each:
   - Name: `AWS_ACCESS_KEY_ID`, Value: (paste your Access Key ID)
   - Name: `AWS_SECRET_ACCESS_KEY`, Value: (paste your Secret Access Key)
   - Name: `AWS_REGION`, Value: `us-east-1` (or your bucket region)
   - Name: `S3_BUCKET`, Value: `daily-agent-metrics-deadmau224` (or your bucket name)

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional - for local testing):

**ClickHouse (optional - will use mock data if not set):**
```bash
export CLICKHOUSE_HOST=ybdjbqn5cv.us-east-1.aws.clickhouse.cloud
export CLICKHOUSE_PORT=8443
export CLICKHOUSE_DATABASE=default
export CLICKHOUSE_USER=default
export CLICKHOUSE_PASSWORD=your_password
```

**AWS S3 (optional - will save locally if not set):**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
export S3_BUCKET=your_bucket_name
```

3. Run locally:
```bash
python export_agent_metrics.py
```

### Optional Environment Variables

- `TARGET_DATE`: Override target date (format: `YYYY-MM-DD`, defaults to yesterday)
- `OUTPUT_DIR`: Specify output directory for CSV files (defaults to current directory)

## Project Structure

```
daily_agent_metrics/
├── export_agent_metrics.py  # Main script
├── requirements.txt          # Python dependencies
├── .github/
│   └── workflows/
│       └── daily_export.yml  # GitHub Actions workflow
├── README.md
└── ASSUMPTIONS.md
```

## GitHub Actions

The workflow runs daily at 2 AM UTC and can also be manually triggered:

1. **Scheduled runs**: Automatically runs every day at 2 AM UTC
2. **Manual runs**: Go to Actions → Daily Agent Metrics Export → Run workflow
   - You can optionally specify a target date (YYYY-MM-DD format)

The generated CSV files are:
- Uploaded to S3 bucket at path: `agent_metrics/YYYY-MM-DD/agent_metrics_YYYY-MM-DD.csv`
- Also uploaded as GitHub Actions artifacts (retained for 30 days) as backup

## Testing

### Local Testing

1. **Test with ClickHouse and AWS credentials:**
```bash
export CLICKHOUSE_HOST=ybdjbqn5cv.us-east-1.aws.clickhouse.cloud
export CLICKHOUSE_PORT=8443
export CLICKHOUSE_DATABASE=default
export CLICKHOUSE_USER=default
export CLICKHOUSE_PASSWORD=your_password
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
export S3_BUCKET=your_bucket_name
python export_agent_metrics.py
```

2. **Test with ClickHouse only (no S3):**
```bash
export CLICKHOUSE_HOST=ybdjbqn5cv.us-east-1.aws.clickhouse.cloud
export CLICKHOUSE_PORT=8443
export CLICKHOUSE_DATABASE=default
export CLICKHOUSE_USER=default
export CLICKHOUSE_PASSWORD=your_password
python export_agent_metrics.py
# Should query ClickHouse and save CSV locally
```

3. **Test without ClickHouse (mock data):**
```bash
# Don't set ClickHouse environment variables
python export_agent_metrics.py
# Should use mock data and save CSV locally
```

4. **Test with custom date:**
```bash
export TARGET_DATE=2024-01-15
export CLICKHOUSE_HOST=ybdjbqn5cv.us-east-1.aws.clickhouse.cloud
export CLICKHOUSE_PORT=8443
export CLICKHOUSE_DATABASE=default
export CLICKHOUSE_USER=default
export CLICKHOUSE_PASSWORD=your_password
python export_agent_metrics.py
```

### GitHub Actions Testing

1. **Manually trigger workflow:**
   - Go to Actions tab → Daily Agent Metrics Export → Run workflow
   - Optionally specify a target date
   - Click "Run workflow"

2. **Verify S3 upload:**
   - Check workflow logs for "Successfully uploaded to s3://..." message
   - Go to AWS S3 Console → Your bucket → `agent_metrics/` folder
   - Verify CSV file exists for the date

3. **Verify artifact backup:**
   - In workflow run, check "Artifacts" section
   - Download and verify CSV file

## CSV Format

The generated CSV includes:
- `agent_id`: Agent identifier
- `avg_call_length_sec`: Average call length in seconds
- `p90_call_length_sec`: 90th percentile call length in seconds
- `total_calls`: Total number of calls for the agent
- `date`: Date of the metrics (YYYY-MM-DD)

## Example Output

```csv
agent_id,avg_call_length_sec,p90_call_length_sec,total_calls,date
agent_001,342.15,512.30,45,2024-01-15
agent_002,298.67,445.20,32,2024-01-15
...
```

## Current Implementation

- **Data Source**: Queries ClickHouse database (falls back to mock data if unavailable)
- **Output**: CSV files uploaded to S3 and saved as GitHub Actions artifacts
- **ClickHouse**: Optional - script falls back to mock data if credentials missing or connection fails
- **S3 Upload**: Optional - script continues to work even if S3 credentials are missing

## Troubleshooting

### ClickHouse Connection Fails

- **Error: "Failed to initialize ClickHouse client"**
  - Verify ClickHouse credentials are correct in GitHub secrets
  - Check that ClickHouse service is running and accessible
  - Verify host and port are correct (port 8443 for HTTPS, 8123 for HTTP)
  - Script will automatically fall back to mock data if connection fails

- **Error: "Table 'conversations' does not exist"**
  - Create the table using the SQL schema provided in the ClickHouse Setup section
  - Verify you're using the correct database name

- **Error: "Connection timeout" or "Cannot connect"**
  - Check that ClickHouse host is accessible from GitHub Actions (public IP/domain)
  - Verify firewall rules allow connections from GitHub Actions IPs
  - For ClickHouse Cloud, ensure your service allows external connections

- **No data returned from query**
  - Verify data exists in the `conversations` table for the target date
  - Check that `call_status = 'Answered'` matches your data
  - Verify date format in `call_start` column matches expected format

- **Using mock data instead of ClickHouse**
  - This is normal if ClickHouse credentials are not set
  - Check logs for "will use mock data" messages
  - Verify all ClickHouse secrets are set in GitHub repository

### S3 Upload Fails

- **Error: "S3 bucket does not exist"**
  - Verify bucket name in `S3_BUCKET` secret matches your actual bucket name
  - Check bucket region matches `AWS_REGION` secret

- **Error: "Access denied"**
  - Verify IAM user has `AmazonS3FullAccess` policy (or appropriate S3 permissions)
  - Check Access Key ID and Secret Access Key are correct in GitHub secrets

- **Error: "AWS credentials not found"**
  - Script will fall back to local file generation
  - Check GitHub secrets are set correctly if running in GitHub Actions
  - Check environment variables are set if running locally

### Local Testing Issues

- **Module not found: boto3**
  - Run: `pip install -r requirements.txt`

- **CSV file not generated**
  - Check script output for error messages
  - Verify Python version is 3.11 or compatible

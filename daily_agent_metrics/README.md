# Daily Agent Metrics Export

This project exports daily agent call metrics (using mock data) to AWS S3.
Calculates for each agent:
- Average call length
- 90th percentile call length

## Requirements

- Calculate for each agent:
  - Average call length
  - 90th percentile call length
- Export results as CSV (one file per day)
- Upload to AWS S3 bucket (optional - falls back to local file if S3 unavailable)
- Run daily via GitHub Actions

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

1. **Test with AWS credentials:**
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
export S3_BUCKET=your_bucket_name
python export_agent_metrics.py
```

2. **Test without AWS credentials (S3 disabled):**
```bash
# Don't set AWS environment variables
python export_agent_metrics.py
# Should generate CSV locally and skip S3 upload
```

3. **Test with custom date:**
```bash
export TARGET_DATE=2024-01-15
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

- **Data Source**: Uses mock/simulated data (no ClickHouse connection required yet)
- **Output**: CSV files uploaded to S3 and saved as GitHub Actions artifacts
- **S3 Upload**: Optional - script continues to work even if S3 credentials are missing
- **Future**: ClickHouse integration will be added later

## Troubleshooting

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

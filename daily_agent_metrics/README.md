# Daily Agent Metrics Export

This project exports daily agent call metrics using mock data (ClickHouse and AWS S3 integration to be added later).

## Requirements

- Calculate for each agent:
  - Average call length
  - 90th percentile call length
- Export results as CSV (one file per day)
- Run daily via GitHub Actions

## Setup

1. Install dependencies (none required - uses Python standard library):
```bash
# No installation needed!
```

2. Run locally:
```bash
python export_agent_metrics.py
```

3. Optional environment variables:
```bash
export TARGET_DATE=2024-01-15  # Override target date (defaults to yesterday)
export OUTPUT_DIR=./output     # Specify output directory (defaults to current directory)
```

## Project Structure

```
daily_agent_metrics/
├── export_agent_metrics.py  # Main script
├── requirements.txt          # Python dependencies (currently empty)
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

The generated CSV files are uploaded as artifacts and retained for 30 days.

## Current Implementation

- **Data Source**: Uses mock/simulated data (no ClickHouse connection required)
- **Output**: CSV files saved locally and uploaded as GitHub Actions artifacts
- **Future**: ClickHouse and AWS S3 integration will be added later

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

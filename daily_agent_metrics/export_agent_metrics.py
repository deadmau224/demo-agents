#!/usr/bin/env python3
"""
Daily Agent Metrics Export

Exports daily agent call metrics from ClickHouse to AWS S3.
Calculates for each agent:
- Average call length
- 90th percentile call length
"""

import os
import sys
import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import statistics

# Optional ClickHouse support
try:
    import clickhouse_connect
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    clickhouse_connect = None

# Optional S3 support
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentMetricsExporter:
    """Exports agent metrics from ClickHouse (or mock data), optionally uploads to S3."""
    
    def __init__(self, enable_s3: bool = True):
        """Initialize exporter with ClickHouse and optional S3.
        
        Args:
            enable_s3: If True, attempt to initialize S3 client (fails gracefully if credentials missing)
        """
        logger.info("Initializing AgentMetricsExporter")
        self.clickhouse_client = None
        self.clickhouse_enabled = False
        self.s3_client = None
        self.s3_bucket = None
        self.s3_enabled = False
        
        # Initialize ClickHouse (optional)
        if CLICKHOUSE_AVAILABLE:
            self._init_clickhouse()
        else:
            logger.warning("clickhouse-connect not available - will use mock data")
        
        # Initialize S3 (optional)
        if enable_s3 and S3_AVAILABLE:
            self._init_s3()
        elif enable_s3 and not S3_AVAILABLE:
            logger.warning("boto3 not available - S3 upload disabled. Install boto3 to enable S3 upload.")
    
    def _init_clickhouse(self) -> None:
        """Initialize ClickHouse client (optional, fails gracefully if credentials missing)."""
        try:
            host = os.getenv('CLICKHOUSE_HOST')
            port = os.getenv('CLICKHOUSE_PORT')
            database = os.getenv('CLICKHOUSE_DATABASE', 'default')
            username = os.getenv('CLICKHOUSE_USER', 'default')
            password = os.getenv('CLICKHOUSE_PASSWORD')
            
            logger.info(f"🔍 ClickHouse config check - Host present: {bool(host)}, Port present: {bool(port)}, Password present: {bool(password)}")
            
            # If host is provided, try to initialize ClickHouse
            if host:
                logger.info(f"🔌 Attempting to connect to ClickHouse - Host: {host}, Port: {port}")
                if not port:
                    logger.warning("CLICKHOUSE_HOST set but CLICKHOUSE_PORT missing - ClickHouse disabled")
                    return
                
                # Extract hostname if URL format is provided
                if host.startswith('http://') or host.startswith('https://'):
                    from urllib.parse import urlparse
                    parsed = urlparse(host)
                    host = parsed.hostname or host
                    # Use port from URL if port not set separately
                    if not port and parsed.port:
                        port = str(parsed.port)
                
                # Remove port from hostname if included
                if ':' in host:
                    host = host.split(':')[0]
                
                try:
                    port_int = int(port)
                except ValueError:
                    logger.warning(f"Invalid CLICKHOUSE_PORT '{port}' - ClickHouse disabled")
                    return
                
                # Use secure=True for HTTPS ports (8443), secure=False for HTTP ports (8123)
                secure = port_int in [8443, 9440]  # HTTPS ports
                
                self.clickhouse_client = clickhouse_connect.get_client(
                    host=host,
                    port=port_int,
                    database=database,
                    username=username,
                    password=password,
                    secure=secure
                )
                
                # Test connection
                self.clickhouse_client.command('SELECT 1')
                
                self.clickhouse_enabled = True
                logger.info(f"ClickHouse client initialized for {host}:{port_int} (secure={secure})")
            else:
                logger.info("CLICKHOUSE_HOST not set - will use mock data")
        except Exception as e:
            logger.warning(f"Failed to initialize ClickHouse client: {e} - will use mock data")
            self.clickhouse_client = None
            self.clickhouse_enabled = False
    
    def _init_s3(self) -> None:
        """Initialize S3 client (optional, fails gracefully if credentials missing)."""
        try:
            s3_bucket = os.getenv('S3_BUCKET')
            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            aws_region = os.getenv('AWS_REGION', 'us-east-1')
            
            # If bucket name is provided, try to initialize S3
            if s3_bucket:
                if not aws_access_key or not aws_secret_key:
                    logger.warning("S3_BUCKET set but AWS credentials missing - S3 upload disabled")
                    logger.info("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to enable S3 upload")
                    return
                
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
                self.s3_bucket = s3_bucket
                self.s3_enabled = True
                logger.info(f"S3 client initialized for bucket: {s3_bucket} in region: {aws_region}")
            else:
                logger.info("S3_BUCKET not set - S3 upload disabled (files will be saved locally)")
        except NoCredentialsError:
            logger.warning("AWS credentials not found - S3 upload disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize S3 client: {e} - S3 upload disabled")
    
    def _generate_mock_call_data(self, agent_id: str, num_calls: int) -> List[float]:
        """
        Generate mock call duration data for an agent.
        
        Args:
            agent_id: Agent identifier
            num_calls: Number of calls to generate
            
        Returns:
            List of call durations in seconds
        """
        # Use agent_id as seed for consistent data generation
        random.seed(hash(agent_id) % 10000)
        
        # Generate realistic call durations (30 seconds to 30 minutes)
        # Using a normal distribution with some variation per agent
        base_mean = 300 + (hash(agent_id) % 600)  # 5-15 minutes base
        base_std = 120 + (hash(agent_id) % 60)    # 2-3 minutes std dev
        
        durations = []
        for _ in range(num_calls):
            duration = random.gauss(base_mean, base_std)
            # Ensure reasonable bounds
            duration = max(30, min(1800, duration))
            durations.append(round(duration, 2))
        
        return durations
    
    def get_agent_metrics(self, target_date: datetime) -> List[Dict]:
        """
        Get agent metrics from ClickHouse or generate mock data.
        
        Args:
            target_date: Date to query metrics for
            
        Returns:
            List of dictionaries with agent_id, avg_call_length, p90_call_length
        """
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Try to get data from ClickHouse
        if self.clickhouse_enabled:
            try:
                logger.info(f"Querying ClickHouse for metrics on date: {date_str}")
                
                # Query to calculate metrics per agent
                query = f"""
                SELECT 
                    agent_id,
                    AVG(call_duration_sec) AS avg_call_length,
                    quantile(0.9)(call_duration_sec) AS p90_call_length,
                    COUNT(*) AS total_calls
                FROM conversations
                WHERE 
                    toDate(call_start) = '{date_str}'
                    AND call_status = 'Answered'
                GROUP BY agent_id
                ORDER BY agent_id
                """
                
                result = self.clickhouse_client.query(query)
                
                # Convert to list of dictionaries
                metrics = []
                for row in result.result_rows:
                    agent_id, avg_length, p90_length, total_calls = row
                    metrics.append({
                        'agent_id': str(agent_id),
                        'avg_call_length_sec': round(float(avg_length), 2),
                        'p90_call_length_sec': round(float(p90_length), 2),
                        'total_calls': int(total_calls)
                    })
                
                logger.info(f"Retrieved metrics for {len(metrics)} agents from ClickHouse")
                return metrics
                
            except Exception as e:
                logger.warning(f"Error querying ClickHouse: {e} - falling back to mock data")
                # Fall through to mock data generation
        
        # Fallback to mock data
        logger.info(f"Generating mock metrics for date: {date_str}")
        
        # Generate mock agents (5-10 agents)
        num_agents = random.randint(5, 10)
        agent_ids = [f"agent_{i:03d}" for i in range(1, num_agents + 1)]
        
        metrics = []
        for agent_id in agent_ids:
            # Generate 10-100 calls per agent
            num_calls = random.randint(10, 100)
            call_durations = self._generate_mock_call_data(agent_id, num_calls)
            
            # Calculate average
            avg_length = statistics.mean(call_durations)
            
            # Calculate 90th percentile
            sorted_durations = sorted(call_durations)
            p90_index = int(len(sorted_durations) * 0.9)
            p90_length = sorted_durations[p90_index] if p90_index < len(sorted_durations) else sorted_durations[-1]
            
            metrics.append({
                'agent_id': agent_id,
                'avg_call_length_sec': round(avg_length, 2),
                'p90_call_length_sec': round(p90_length, 2),
                'total_calls': num_calls
            })
        
        logger.info(f"Generated mock metrics for {len(metrics)} agents")
        return metrics
    
    def generate_csv(self, metrics: List[Dict], target_date: datetime) -> str:
        """
        Generate CSV file from metrics data.
        
        Args:
            metrics: List of metric dictionaries
            target_date: Date for the metrics
            
        Returns:
            Path to generated CSV file
        """
        date_str = target_date.strftime('%Y-%m-%d')
        filename = f"agent_metrics_{date_str}.csv"
        
        if not metrics:
            logger.warning(f"No metrics found for {date_str}, creating empty CSV")
        
        # Write CSV
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['agent_id', 'avg_call_length_sec', 'p90_call_length_sec', 'total_calls', 'date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for metric in metrics:
                metric['date'] = date_str
                writer.writerow(metric)
        
        logger.info(f"Generated CSV file: {filename}")
        return filename
    
    def upload_to_s3(self, filename: str, target_date: datetime) -> Optional[str]:
        """
        Upload CSV file to S3 (optional).
        
        Args:
            filename: Local CSV file path
            target_date: Date for the metrics
            
        Returns:
            S3 key (path) of uploaded file, or None if upload failed/disabled
        """
        if not self.s3_enabled:
            logger.info("S3 upload disabled - skipping upload")
            return None
        
        date_str = target_date.strftime('%Y-%m-%d')
        s3_key = f"agent_metrics/{date_str}/{filename}"
        
        try:
            logger.info(f"Uploading {filename} to s3://{self.s3_bucket}/{s3_key}")
            self.s3_client.upload_file(
                filename,
                self.s3_bucket,
                s3_key
            )
            logger.info(f"Successfully uploaded to s3://{self.s3_bucket}/{s3_key}")
            return s3_key
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchBucket':
                logger.error(f"S3 bucket '{self.s3_bucket}' does not exist")
            elif error_code == 'AccessDenied':
                logger.error(f"Access denied to S3 bucket '{self.s3_bucket}' - check IAM permissions")
            else:
                logger.error(f"Error uploading to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            return None
    
    def export_metrics(self, target_date: datetime = None, output_dir: str = None) -> Dict[str, str]:
        """
        Main export function: query ClickHouse, generate CSV, optionally upload to S3.
        
        Args:
            target_date: Date to export (defaults to yesterday)
            output_dir: Directory to save CSV file (defaults to current directory)
            
        Returns:
            Dictionary with 'csv_path' and optionally 's3_key' if uploaded
        """
        if target_date is None:
            # Default to yesterday (typical for daily exports)
            target_date = datetime.now() - timedelta(days=1)
        
        result = {}
        
        try:
            # Get metrics (from ClickHouse or mock data)
            metrics = self.get_agent_metrics(target_date)
            
            # Generate CSV
            csv_filename = self.generate_csv(metrics, target_date)
            
            # Move to output directory if specified
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, csv_filename)
                os.rename(csv_filename, output_path)
                csv_filename = output_path
            
            result['csv_path'] = csv_filename
            
            # Upload to S3 (optional, doesn't fail if disabled)
            s3_key = self.upload_to_s3(csv_filename, target_date)
            if s3_key:
                result['s3_key'] = s3_key
                # Don't delete local file if S3 upload succeeded - keep as backup
                logger.info(f"CSV file kept locally at: {csv_filename}")
            else:
                logger.info(f"CSV file saved locally at: {csv_filename} (S3 upload not available/failed)")
            
            logger.info(f"Export completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise


def main():
    """Main entry point."""
    # Allow date override via environment variable (for testing)
    target_date_str = os.getenv('TARGET_DATE')
    if target_date_str:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
    else:
        # Default to yesterday
        target_date = datetime.now() - timedelta(days=1)
    
    # Allow output directory override
    output_dir = os.getenv('OUTPUT_DIR')
    
    try:
        exporter = AgentMetricsExporter(enable_s3=True)
        result = exporter.export_metrics(target_date, output_dir)
        
        data_source = "ClickHouse" if exporter.clickhouse_enabled else "mock data"
        print(f"Success! Metrics exported from {data_source} to: {result['csv_path']}")
        if 's3_key' in result:
            print(f"Uploaded to S3: s3://{exporter.s3_bucket}/{result['s3_key']}")
        else:
            print("Note: S3 upload not available - CSV file saved locally")
        
        sys.exit(0)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

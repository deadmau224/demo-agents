#!/usr/bin/env python3
"""
Daily Agent Metrics Export

Exports daily agent call metrics (using mock data for now).
Calculates for each agent:
- Average call length
- 90th percentile call length
"""

import os
import sys
import csv
import random
from datetime import datetime, timedelta
from typing import List, Dict
import logging
import statistics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentMetricsExporter:
    """Exports agent metrics using mock data."""
    
    def __init__(self):
        """Initialize exporter with mock data generation."""
        logger.info("Initializing AgentMetricsExporter with mock data")
    
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
        Generate mock agent metrics for a specific date.
        
        Args:
            target_date: Date to generate metrics for
            
        Returns:
            List of dictionaries with agent_id, avg_call_length, p90_call_length
        """
        date_str = target_date.strftime('%Y-%m-%d')
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
        
        logger.info(f"Generated metrics for {len(metrics)} agents")
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
    
    def export_metrics(self, target_date: datetime = None, output_dir: str = None) -> str:
        """
        Main export function: generate metrics, create CSV.
        
        Args:
            target_date: Date to export (defaults to yesterday)
            output_dir: Directory to save CSV file (defaults to current directory)
            
        Returns:
            Path to generated CSV file
        """
        if target_date is None:
            # Default to yesterday (typical for daily exports)
            target_date = datetime.now() - timedelta(days=1)
        
        try:
            # Generate metrics
            metrics = self.get_agent_metrics(target_date)
            
            # Generate CSV
            csv_filename = self.generate_csv(metrics, target_date)
            
            # Move to output directory if specified
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, csv_filename)
                os.rename(csv_filename, output_path)
                csv_filename = output_path
            
            logger.info(f"Export completed successfully: {csv_filename}")
            return csv_filename
            
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
        exporter = AgentMetricsExporter()
        csv_path = exporter.export_metrics(target_date, output_dir)
        print(f"Success! Metrics exported to: {csv_path}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

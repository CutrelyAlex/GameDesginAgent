"""
CSV writer for saving query results to local files.
"""

import csv
from pathlib import Path
from datetime import datetime
from typing import List

from src.aggregator.schemas import QueryResult


class CSVWriter:
    """
    Write query results to CSV files following the specification schema.
    
    Schema: keyword, provider, title, url, snippet, summary, timestamp, request_id
    
    If the target file exists, creates a new file with ISO timestamp suffix.
    """
    
    FIELDNAMES = [
        "keyword",
        "provider", 
        "title",
        "url",
        "snippet",
        "summary",
        "timestamp",
        "request_id"
    ]
    
    def __init__(self, output_dir: str = "data/results"):
        """
        Initialize CSV writer.
        
        Args:
            output_dir: Directory to save CSV files (default: data/results)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_output_path(self, base_filename: str) -> Path:
        """
        Get output path, adding timestamp suffix if file exists.
        
        Args:
            base_filename: Base filename (e.g., "results.csv")
            
        Returns:
            Path object with unique filename
        """
        base_path = self.output_dir / base_filename
        
        if not base_path.exists():
            return base_path
        
        # File exists, add ISO timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        stem = base_path.stem
        suffix = base_path.suffix
        new_filename = f"{stem}_{timestamp}{suffix}"
        
        return self.output_dir / new_filename
    
    def write_results(
        self,
        results: List[QueryResult],
        filename: str = "results.csv"
    ) -> Path:
        """
        Write query results to CSV file.
        
        Args:
            results: List of QueryResult objects to write
            filename: Base filename (default: results.csv)
            
        Returns:
            Path to the created CSV file
        """
        output_path = self._get_output_path(filename)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.FIELDNAMES)
            writer.writeheader()
            
            for result in results:
                row = {
                    "keyword": result.keyword,
                    "provider": result.provider,
                    "title": result.title,
                    "url": str(result.url),
                    "snippet": result.snippet,
                    "summary": result.summary or "",
                    "timestamp": result.timestamp.isoformat(),
                    "request_id": result.request_id
                }
                writer.writerow(row)
        
        return output_path

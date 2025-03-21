"""
Utility functions for the structured data extraction pipeline.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extraction_pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("extraction_pipeline")

def setup_directories(base_dir: str, subdirs: List[str]) -> None:
    """
    Set up the directory structure for the project.
    
    Args:
        base_dir: Base directory path
        subdirs: List of subdirectories to create
    """
    os.makedirs(base_dir, exist_ok=True)
    
    for subdir in subdirs:
        os.makedirs(os.path.join(base_dir, subdir), exist_ok=True)
    
    logger.info(f"Directory structure set up at {base_dir}")

def save_extraction_result(data: Dict[str, Any], 
                           doc_id: str, 
                           doc_type: str, 
                           output_dir: str,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Save extraction results to a JSON file.
    
    Args:
        data: Extracted data
        doc_id: Document identifier
        doc_type: Document type
        output_dir: Output directory
        metadata: Additional metadata to include
        
    Returns:
        Path to the saved file
    """
    # Create type-specific subdirectory if it doesn't exist
    type_dir = os.path.join(output_dir, doc_type)
    os.makedirs(type_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{doc_type}_{doc_id}_{timestamp}.json"
    filepath = os.path.join(type_dir, filename)
    
    # Prepare full output with metadata
    output = {
        "document_id": doc_id,
        "document_type": doc_type,
        "extraction_time": datetime.now().isoformat(),
        "extracted_data": data
    }
    
    if metadata:
        output["metadata"] = metadata
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Extraction result saved to {filepath}")
    return filepath

def load_extraction_result(filepath: str) -> Dict[str, Any]:
    """
    Load a previously saved extraction result.
    
    Args:
        filepath: Path to the extraction result JSON file
        
    Returns:
        Loaded data as a dictionary
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_confidence_report(confidence_scores: Dict[str, Any]) -> str:
    """
    Format confidence scores into a readable report.
    
    Args:
        confidence_scores: Dictionary of confidence scores
        
    Returns:
        Formatted report as a string
    """
    report = ["# Extraction Confidence Report", ""]
    
    # Overall scores
    report.append(f"## Overall Confidence: {confidence_scores['overall_confidence']:.2f}")
    report.append(f"Completeness Score: {confidence_scores['overall_completeness']:.2f}")
    report.append("")
    
    # Field scores
    report.append("## Field-level Confidence Scores")
    
    field_scores = confidence_scores.get('field_scores', {})
    for field, score in sorted(field_scores.items(), key=lambda x: x[1], reverse=True):
        report.append(f"- {field}: {score:.2f}")
    
    return "\n".join(report)

class Timer:
    """Simple timer for measuring execution time"""
    
    def __init__(self, description="Operation"):
        self.description = description
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"{self.description} completed in {duration:.2f} seconds")
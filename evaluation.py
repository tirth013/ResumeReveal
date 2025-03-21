"""
Evaluation metrics and logging for the extraction pipeline.
Measures extraction accuracy and performance.
"""

import json
import os
import logging
from typing import Dict, Any, List, Tuple, Optional, Union, Set
from datetime import datetime

# Set up logging
logger = logging.getLogger("extraction_pipeline.evaluation")

class ExtractionEvaluator:
    """
    Evaluates extraction results against ground truth data.
    """
    
    def __init__(self, log_directory: str = "evaluation_logs"):
        """
        Initialize the evaluator.
        
        Args:
            log_directory: Directory to store evaluation logs
        """
        self.log_dir = log_directory
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create log file for evaluations
        self.log_file = os.path.join(self.log_dir, f"evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    def evaluate_extraction(self, 
                           extracted_data: Dict[str, Any], 
                           ground_truth: Dict[str, Any],
                           doc_id: str,
                           doc_type: str) -> Dict[str, Any]:
        """
        Evaluate an extraction result against ground truth.
        
        Args:
            extracted_data: The data extracted from the document
            ground_truth: The known correct data (ground truth)
            doc_id: Document identifier
            doc_type: Document type
            
        Returns:
            Dictionary of evaluation metrics
        """
        # Initialize metrics
        metrics = {
            "document_id": doc_id,
            "document_type": doc_type,
            "timestamp": datetime.now().isoformat(),
            "overall_accuracy": 0.0,
            "field_metrics": {},
            "field_errors": []
        }
        
        # Flatten both dictionaries for comparison
        extracted_flat = self._flatten_dict(extracted_data)
        ground_truth_flat = self._flatten_dict(ground_truth)
        
        # Get all unique keys
        all_keys = set(extracted_flat.keys()) | set(ground_truth_flat.keys())
        
        # Calculate field-level metrics
        correct = 0
        total = len(all_keys)
        
        for key in all_keys:
            extracted_value = extracted_flat.get(key)
            ground_truth_value = ground_truth_flat.get(key)
            
            # Check if the values match
            if key in extracted_flat and key in ground_truth_flat:
                # Compare values
                if isinstance(ground_truth_value, (list, dict)) and isinstance(extracted_value, (list, dict)):
                    # For complex types, use string comparison
                    is_match = json.dumps(extracted_value, sort_keys=True) == json.dumps(ground_truth_value, sort_keys=True)
                else:
                    # For simple types, use direct comparison
                    is_match = extracted_value == ground_truth_value
                
                field_score = 1.0 if is_match else 0.0
                
                if is_match:
                    correct += 1
                else:
                    metrics["field_errors"].append({
                        "field": key,
                        "extracted": extracted_value,
                        "ground_truth": ground_truth_value
                    })
            
            # Missing field in extraction
            elif key in ground_truth_flat and key not in extracted_flat:
                field_score = 0.0
                metrics["field_errors"].append({
                    "field": key,
                    "error": "missing_field",
                    "ground_truth": ground_truth_value
                })
            
            # Extra field in extraction
            elif key in extracted_flat and key not in ground_truth_flat:
                field_score = 0.0
                metrics["field_errors"].append({
                    "field": key,
                    "error": "extra_field",
                    "extracted": extracted_value
                })
            
            else:
                field_score = 0.0
            
            # Add to field metrics
            metrics["field_metrics"][key] = field_score
        
        # Calculate overall accuracy
        metrics["overall_accuracy"] = correct / total if total > 0 else 0.0
        
        # Log evaluation results
        self._log_evaluation(metrics)
        
        return metrics
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """
        Flatten a nested dictionary.
        
        Args:
            d: The dictionary to flatten
            parent_key: Key prefix for nested items
            sep: Separator between keys
            
        Returns:
            Flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(self._flatten_dict(item, f"{new_key}[{i}]", sep).items())
                    else:
                        items.append((f"{new_key}[{i}]", item))
            else:
                items.append((new_key, v))
                
        return dict(items)
    
    def _log_evaluation(self, metrics: Dict[str, Any]) -> None:
        """
        Log evaluation metrics to file.
        
        Args:
            metrics: Evaluation metrics to log
        """
        # Read existing logs if they exist
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = {"evaluations": []}
        else:
            logs = {"evaluations": []}
        
        # Add new evaluation
        logs["evaluations"].append(metrics)
        logs["last_updated"] = datetime.now().isoformat()
        
        # Write updated logs
        with open(self.log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        
        logger.info(f"Evaluation logged for document {metrics['document_id']} with accuracy {metrics['overall_accuracy']:.2f}")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of all evaluations.
        
        Returns:
            Summary report dictionary
        """
        if not os.path.exists(self.log_file):
            return {"error": "No evaluations have been logged yet"}
        
        with open(self.log_file, 'r') as f:
            logs = json.load(f)
        
        evaluations = logs.get("evaluations", [])
        
        if not evaluations:
            return {"error": "No evaluations have been logged yet"}
        
        # Calculate overall statistics
        total_docs = len(evaluations)
        avg_accuracy = sum(eval_data["overall_accuracy"] for eval_data in evaluations) / total_docs
        
        # Group by document type
        doc_types = {}
        for eval_data in evaluations:
            doc_type = eval_data["document_type"]
            if doc_type not in doc_types:
                doc_types[doc_type] = []
            
            doc_types[doc_type].append(eval_data)
        
        # Calculate per-type statistics
        type_stats = {}
        for doc_type, evals in doc_types.items():
            type_count = len(evals)
            type_avg_accuracy = sum(e["overall_accuracy"] for e in evals) / type_count
            
            # Find common errors
            error_fields = {}
            for e in evals:
                for error in e.get("field_errors", []):
                    field = error.get("field", "unknown")
                    if field not in error_fields:
                        error_fields[field] = 0
                    error_fields[field] += 1
            
            # Sort error fields by frequency
            common_errors = sorted(
                [{"field": k, "count": v} for k, v in error_fields.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:5]  # Top 5 errors
            
            type_stats[doc_type] = {
                "count": type_count,
                "average_accuracy": type_avg_accuracy,
                "common_errors": common_errors
            }
        
        # Create summary report
        summary = {
            "total_documents": total_docs,
            "average_accuracy": avg_accuracy,
            "document_types": type_stats,
            "generated_at": datetime.now().isoformat()
        }
        
        return summary
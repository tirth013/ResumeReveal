"""
Structured Data Extraction Pipeline for Resumes
Command-line interface for resume processing and extraction.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import project components
from document_loaders import extract_text_from_pdf, extract_text_from_docx
from DocumentCollector import DocumentCollector
from parsers import get_parser
from utils import save_extraction_result, load_extraction_result, Timer, setup_directories, logger
from evaluation import ExtractionEvaluator

def process_document(file_path: str, output_dir: str = "output", llm_provider: str = "groq") -> Dict[str, Any]:
    """
    Process a single resume document and extract structured data.
    
    Args:
        file_path: Path to the resume document file
        output_dir: Output directory for results
        llm_provider: LLM provider to use
        
    Returns:
        Extracted data as a dictionary
    """
    logger.info(f"Processing resume: {file_path}")
    
    # Extract text based on file extension
    file_ext = os.path.splitext(file_path)[1].lower()
    with Timer(f"Text extraction from {file_ext}"):
        if file_ext == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            text = extract_text_from_docx(file_path)
        elif file_ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    # Get parser for resume document type
    parser = get_parser("resume", llm_provider=llm_provider)
    with Timer(f"Data extraction with {llm_provider}"):
        extracted_data = parser.parse(text)
    
    # Save extraction result
    doc_id = os.path.basename(file_path).split('.')[0]
    output_path = save_extraction_result(
        data=extracted_data,
        doc_id=doc_id,
        doc_type="resume",
        output_dir=output_dir
    )
    
    logger.info(f"Results saved to: {output_path}")
    return extracted_data

def batch_process(doc_dir: str, output_dir: str = "output", llm_provider: str = "groq") -> List[Dict[str, Any]]:
    """
    Process multiple resume documents from a directory.
    
    Args:
        doc_dir: Directory containing resume documents
        output_dir: Output directory for results
        llm_provider: LLM provider to use
        
    Returns:
        List of extracted data dictionaries
    """
    logger.info(f"Batch processing documents from: {doc_dir}")
    
    # Collect documents
    collector = DocumentCollector(doc_dir)
    file_paths = collector.get_resume_files()
    
    if not file_paths:
        logger.warning(f"No resume documents found in: {doc_dir}")
        return []
    
    logger.info(f"Found {len(file_paths)} resume documents")
    
    # Process each document
    results = []
    for i, file_path in enumerate(file_paths):
        logger.info(f"Processing document {i+1}/{len(file_paths)}: {file_path}")
        
        try:
            result = process_document(file_path, output_dir, llm_provider)
            results.append(result)
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {str(e)}")
    
    logger.info(f"Batch processing complete. Processed {len(results)}/{len(file_paths)} documents")
    return results

def compare_extractions(file_path: str, llm_providers: List[str] = ["groq", "openai"]) -> Dict[str, Dict[str, Any]]:
    """
    Compare extraction results from different LLM providers.
    
    Args:
        file_path: Path to the resume document
        llm_providers: List of LLM providers to compare
        
    Returns:
        Dictionary mapping provider names to extraction results
    """
    results = {}
    
    for provider in llm_providers:
        logger.info(f"Processing with {provider}...")
        try:
            result = process_document(file_path, llm_provider=provider)
            results[provider] = result
        except Exception as e:
            logger.error(f"Error with provider {provider}: {str(e)}")
            results[provider] = {"error": str(e)}
    
    return results

def main():
    """Main entry point for the CLI."""
    
    # Set up the argument parser
    parser = argparse.ArgumentParser(description="Resume Data Extraction Pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Process a single document
    process_parser = subparsers.add_parser("process", help="Process a single resume document")
    process_parser.add_argument("file", help="Path to the resume document")
    process_parser.add_argument("--output", "-o", default="output", help="Output directory")
    process_parser.add_argument("--llm", default="groq", choices=["groq", "openai"], 
                              help="LLM provider to use")
    
    # Process multiple documents in a directory
    batch_parser = subparsers.add_parser("batch", help="Process multiple resume documents")
    batch_parser.add_argument("directory", help="Directory containing resume documents")
    batch_parser.add_argument("--output", "-o", default="output", help="Output directory")
    batch_parser.add_argument("--llm", default="groq", choices=["groq", "openai"], 
                            help="LLM provider to use")
    
    # Compare different LLM providers
    compare_parser = subparsers.add_parser("compare", help="Compare different LLM providers")
    compare_parser.add_argument("file", help="Path to the resume document")
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Create output directories
    setup_directories("output", ["resume"])
    
    # Execute the command
    if args.command == "process":
        process_document(args.file, args.output, args.llm)
    elif args.command == "batch":
        batch_process(args.directory, args.output, args.llm)
    elif args.command == "compare":
        results = compare_extractions(args.file)
        print("Comparison Results:")
        for provider, result in results.items():
            print(f"\n--- {provider.upper()} ---")
            print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
import os
import shutil
import json
import csv
import hashlib
import random
from datetime import datetime
import pathlib

class DocumentCollector:
    def __init__(self,base_directory):
        """
        Initialize the resume collection system.
        
        Args:
            base_directory: Root directory for storing all resumes and metadata
        """
        self.base_dir = base_directory

        self.doc_types = ["resumes"]
        
        # Create directories for resume storage
        os.makedirs(os.path.join(self.base_dir, "resumes"), exist_ok=True)
        
        # Initialize metadata storage
        self.metadata_file = os.path.join(self.base_dir,"metadata.json")
        if not os.path.exists(self.metadata_file):
            self._initialize_metadata()
        

    def _initialize_metadata(self):
        """Create initial empty metadata structure."""
        metadata = {
            "documents": {},
            "stats": {"resumes": 0},
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.metadata_file,'w') as f:
            json.dump(metadata,f,indent=2)
    
    def add_document(self, file_path, doc_type="resume", metadata=None):
        """
        Add a resume to the collection.

        Args:
            file_path: Path to the resume file
            doc_type: Always "resume" (kept for backward compatibility)
            metadata: Additional metadata about the resume
            
        Returns:
            document_id: Unique ID for the added resume
        """
        # Ensure doc_type is always "resume"
        doc_type = "resume"
        
        # Generate unique document ID and create proper filename
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1]
        document_id = self._generate_document_id(file_path)
        new_filename = f"resume_{document_id}{file_ext}"

        # Copy file to appropriate directory
        target_dir = os.path.join(self.base_dir, "resumes")
        target_path = os.path.join(target_dir, new_filename)
        shutil.copy2(file_path, target_path)
        
        # Update metadata
        self._update_metadata(document_id, doc_type, target_path, metadata)
        
        return document_id

    def _generate_document_id(self, file_path):
        """Generate a unique ID for a resume based on content and timestamp"""
        timestamp = datetime.now().isoformat()
        
        # Get file hash to help with uniqueness
        with open(file_path, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            
        return f"{file_hash}_{int(datetime.now().timestamp())}"
    
    def _update_metadata(self, document_id, doc_type, file_path, custom_metadata=None):
        """Update the metadata file with information about the new resume"""
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Add document entry
        metadata["documents"][document_id] = {
            "doc_type": doc_type,
            "file_path": file_path,
            "added_date": datetime.now().isoformat(),
            "metadata": custom_metadata or {}
        }
        
        # Update statistics
        metadata["stats"]["resumes"] += 1
        metadata["last_updated"] = datetime.now().isoformat()
        
        # Save updated metadata
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def add_ground_truth(self, document_id, ground_truth_data):
        """
        Add ground truth data for a resume.
        
        Args:
            document_id: ID of the resume
            ground_truth_data: Ground truth data (dict)
        """
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
            
        if document_id not in metadata["documents"]:
            raise ValueError(f"Resume {document_id} not found in collection")
            
        # Add ground truth to document metadata
        metadata["documents"][document_id]["ground_truth"] = ground_truth_data
        metadata["last_updated"] = datetime.now().isoformat()
        
        # Save updated metadata
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    def export_ground_truth_csv(self, output_path):
        """
        Export ground truth data to CSV.
        
        Args:
            output_path: Path to save the CSV file
        """
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
            
        # Get all documents
        documents = metadata["documents"]
            
        # Filter documents with ground truth
        documents_with_gt = {k: v for k, v in documents.items() if "ground_truth" in v}
        
        if not documents_with_gt:
            print("No resumes with ground truth data found")
            return
            
        # CSV structure for resumes
        headers = ["document_id", "name", "email", "phone", "skills", "education", "experience", "summary"]
        
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for doc_id, doc_data in documents_with_gt.items():
                gt = doc_data["ground_truth"]
                row = [
                    doc_id,
                    gt.get("name", ""),
                    gt.get("email", ""),
                    gt.get("phone", ""),
                    "|".join(gt.get("skills", [])),
                    json.dumps(gt.get("education", [])),
                    json.dumps(gt.get("experience", [])),
                    gt.get("summary", "")
                ]
                writer.writerow(row)
                
        print(f"Ground truth data exported to {output_path}")

    def get_document_catalog(self):
        """
        Get a catalog of all resumes in the collection.
            
        Returns:
            dict: Resume catalog
        """
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
        
        return metadata["documents"]

    def get_statistics(self):
        """
        Get statistics about the resume collection.
        
        Returns:
            dict: Collection statistics
        """
        with open(self.metadata_file, 'r') as f:
            metadata = json.load(f)
            
        stats = metadata["stats"]
        
        # Add total count (same as resumes count in this case)
        stats["total"] = stats["resumes"]
        
        return stats

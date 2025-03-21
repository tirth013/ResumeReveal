"""
Document parser for extracting structured data from resumes.
"""

import json
from typing import Dict, Any, List, Optional, Union
from schemas import SCHEMAS
from llm_config import get_llm, create_extraction_prompt
from utils import logger

class DocumentParser:
    """Base parser class for extracting structured data from documents."""
    
    def __init__(self, doc_type: str, llm_provider: str = "groq"):
        """
        Initialize the document parser.
        
        Args:
            doc_type: Type of document to parse
            llm_provider: LLM provider to use
        """
        self.doc_type = doc_type
        self.schema = SCHEMAS.get(doc_type)
        if not self.schema:
            raise ValueError(f"Unknown document type: {doc_type}")
            
        self.llm = get_llm(provider=llm_provider)
        logger.info(f"Initialized {doc_type} parser with {llm_provider} LLM")
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse document text and extract structured data.
        
        Args:
            text: Document text content
            
        Returns:
            Structured data extracted from the document
        """
        prompt = create_extraction_prompt(self.doc_type, text)
        extraction_result = self.llm.invoke(prompt)
        extracted_data = self._process_extraction(extraction_result)
        
        return extracted_data
    
    def _process_extraction(self, extraction_result: Any) -> Dict[str, Any]:
        """
        Process extraction result from LLM.
        
        Args:
            extraction_result: Raw extraction from LLM
            
        Returns:
            Processed structured data
        """
        try:
            if hasattr(extraction_result, 'content'):
                content = extraction_result.content
            else:
                content = str(extraction_result)
                
            json_str = ""
            
            if "```json" in content and "```" in content.split("```json")[1]:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content and "```" in content.split("```")[1]:
                json_str = content.split("```")[1].split("```")[0].strip()
            elif "{" in content and "}" in content:
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                if start_idx >= 0 and end_idx > 0:
                    json_str = content[start_idx:end_idx].strip()
            else:
                json_str = content.strip()
                
            extracted_data = json.loads(json_str)
            
            if self.doc_type == "resume":
                if "skills" in extracted_data and extracted_data["skills"] is None:
                    extracted_data["skills"] = []
                if "education" in extracted_data and extracted_data["education"] is None:
                    extracted_data["education"] = []
                if "experience" in extracted_data and extracted_data["experience"] is None:
                    extracted_data["experience"] = []
            
            if self.schema:
                validated_data = self.schema(**extracted_data)
                return validated_data.model_dump()
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error processing extraction result: {str(e)}")
            
            try:
                content = str(extraction_result.content) if hasattr(extraction_result, 'content') else str(extraction_result)
                
                if "```" in content:
                    code_blocks = content.split("```")
                    for i in range(1, len(code_blocks), 2):
                        block = code_blocks[i]
                        if block.startswith("json"):
                            block = block[4:].strip()
                        else:
                            block = block.strip()
                            
                        try:
                            data = json.loads(block)
                            logger.info("Successfully extracted JSON from code block")
                            
                            if self.doc_type == "resume":
                                if "skills" in data and data["skills"] is None:
                                    data["skills"] = []
                                if "education" in data and data["education"] is None:
                                    data["education"] = []
                                if "experience" in data and data["experience"] is None:
                                    data["experience"] = []
                            
                            if self.schema:
                                validated_data = self.schema(**data)
                                return validated_data.model_dump()
                            return data
                        except json.JSONDecodeError:
                            continue
                
                start_idx = content.find("{")
                end_idx = content.rfind("}") + 1
                if start_idx >= 0 and end_idx > 0:
                    json_str = content[start_idx:end_idx]
                    try:
                        data = json.loads(json_str)
                        logger.info("Successfully extracted JSON using brace matching")
                        
                        if self.doc_type == "resume":
                            if "skills" in data and data["skills"] is None:
                                data["skills"] = []
                            if "education" in data and data["education"] is None:
                                data["education"] = []
                            if "experience" in data and data["experience"] is None:
                                data["experience"] = []
                        
                        if self.schema:
                            validated_data = self.schema(**data)
                            return validated_data.model_dump()
                        return data
                    except:
                        pass
                        
                return {"error": str(e), "raw_result": str(extraction_result)}
            except Exception as nested_error:
                logger.error(f"Failed all JSON extraction attempts: {str(nested_error)}")
                return {"error": str(e), "raw_result": str(extraction_result)}

class ResumeParser(DocumentParser):
    """Parser for resume documents."""
    
    def __init__(self, llm_provider: str = "groq"):
        super().__init__(doc_type="resume", llm_provider=llm_provider)
        
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse resume document."""
        return super().parse(text)
    
    def _process_extraction(self, extraction_result: Any) -> Dict[str, Any]:
        """
        Override to preprocess education data before validation.
        """
        try:
            extracted_data = super()._process_extraction(extraction_result)
            
            if "error" in extracted_data:
                return extracted_data
                
            if "education" in extracted_data and extracted_data["education"]:
                self._preprocess_education_data(extracted_data)
                
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error in resume data preprocessing: {str(e)}")
            return {"error": str(e), "raw_result": str(extraction_result)}
    
    def _preprocess_education_data(self, data: Dict[str, Any]) -> None:
        """
        Preprocess education data to handle different graduation year formats.
        
        Args:
            data: Extracted data dictionary to preprocess in-place
        """
        if not data.get("education"):
            return
            
        for edu in data["education"]:
            if "graduation_year" in edu and edu["graduation_year"]:
                if isinstance(edu["graduation_year"], str) and not edu["graduation_year"].isdigit():
                    continue
                    
                try:
                    edu["graduation_year"] = int(edu["graduation_year"])
                except (ValueError, TypeError):
                    pass

def get_parser(doc_type: str, llm_provider: str = "groq") -> DocumentParser:
    """
    Get the appropriate parser for a document type.
    
    Args:
        doc_type: Type of document (must be "resume")
        llm_provider: LLM provider to use
        
    Returns:
        Parser instance for the specified document type
    """
    if doc_type != "resume":
        raise ValueError("Only resume document type is supported")
        
    return ResumeParser(llm_provider=llm_provider)

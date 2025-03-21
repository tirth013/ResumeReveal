"""
LLM configuration and prompting utilities.
Configure LLM providers and implement structured prompting for resume extraction.
"""

import os
import json
from typing import Dict, List, Any, Optional
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks.manager import CallbackManager
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# LLM Provider configurations
LLM_PROVIDERS = {
    "groq": {
        "model_name": "llama3-70b-8192",  # You can also use "mixtral-8x7b-32768" or other Groq models
        "temperature": 0.1,
        "max_tokens": 4000
    }
}

def get_llm(provider="groq", streaming=False):
    """
    Initialize and return an LLM model instance.
    
    Args:
        provider: LLM provider name
        streaming: Whether to enable streaming output
        
    Returns:
        Configured LLM instance
    """
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()]) if streaming else None
    
    if provider == "groq":
        return ChatGroq(
            model_name=LLM_PROVIDERS["groq"]["model_name"],
            temperature=LLM_PROVIDERS["groq"]["temperature"],
            max_tokens=LLM_PROVIDERS["groq"]["max_tokens"],
            streaming=streaming,
            callback_manager=callback_manager
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

# Extraction prompts for resume extraction
EXTRACTION_PROMPTS = {
    "resume": {
        "system": """You are an expert data extraction assistant specialized in extracting structured information from resumes.
Your task is to extract key information from the resume text and format it according to the specified schema.
The output should be valid JSON with the following structure:
{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number",
  "skills": ["Skill 1", "Skill 2", ...],
  "education": [
    {"degree": "Degree Name", "institution": "Institution Name", "graduation_year": "YYYY or YYYY-YYYY"},
    ...
  ],
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "start_date": "Start Date",
      "end_date": "End Date or Present",
      "description": "Job Description"
    },
    ...
  ],
  "summary": "Professional summary"
}
Ensure all data is properly formatted and accurate. Extract as much information as possible from the provided text.
Only include fields that are present in the resume. If a field is missing, omit it or use null.
For graduation_year, you can use a single year (e.g., 2022) or a range (e.g., "2018-2022") when appropriate.
Respond with only valid JSON.""",
        "human": """Extract structured data from the following resume text. Output should be only valid JSON.

Resume text:
{text}

JSON Output:"""
    }
}

def create_extraction_prompt(doc_type: str, text: str) -> List[Dict[str, str]]:
    """
    Create a prompt for extracting structured data from resume text.
    
    Args:
        doc_type: Type of document to extract data from (should be "resume")
        text: Resume text content
        
    Returns:
        List of prompt messages for LLM
    """
    if doc_type not in EXTRACTION_PROMPTS:
        raise ValueError(f"No extraction prompt available for document type: {doc_type}")
    
    prompt_template = EXTRACTION_PROMPTS[doc_type]
    
    # Create messages
    system_message = SystemMessage(content=prompt_template["system"])
    human_message = HumanMessage(content=prompt_template["human"].format(text=text))
    
    return [system_message, human_message]

def get_schema_json(doc_type: str) -> str:
    """
    Get JSON schema for a document type.
    
    Args:
        doc_type: Document type (should be "resume")
        
    Returns:
        JSON schema as a string
    """
    from schemas import SCHEMAS
    
    schema_class = SCHEMAS.get(doc_type)
    if not schema_class:
        raise ValueError(f"No schema available for document type: {doc_type}")
    
    schema_json = schema_class.schema_json(indent=2)
    return schema_json

# System prompt for resume extraction
SYSTEM_PROMPT = """You are an expert document analyzer specializing in extracting structured information from resumes. 
Your task is to carefully read the provided resume and extract the requested information in a structured JSON format.
Be precise, extract only what is explicitly stated in the document, and format your response according to the specified schema.
If information is not present, use null for optional fields or an empty list for list fields."""

# Resume extraction prompt
RESUME_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
    Extract the following information from this resume:
    - Full name
    - Contact information (email, phone, address, LinkedIn)
    - Skills (as a list)
    - Education history (degree, institution, graduation year, GPA if available)
    - Work experience (company, title, dates, description)
    - Summary or objective statement
    - Certifications
    - Languages
    
    The resume text is:
    
    {document_text}
    
    Respond with ONLY a JSON object that follows this exact schema:
    {schema}
    """)
])

# Prompt templates for different extraction tasks
SYSTEM_PROMPT_OTHER = """You are an expert document analyzer specializing in extracting structured information from unstructured text. 
Your task is to carefully read the provided document and extract the requested information in a structured JSON format.
Be precise, extract only what is explicitly stated in the document, and format your response according to the specified schema.
If information is not present, use null for optional fields or an empty list for list fields."""

# Document type detection prompt
DOCUMENT_TYPE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT_OTHER),
    ("human", """
    Analyze the following document text and determine if it is a resume.
    Respond with either "resume" or "unknown".
    
    Document text:
    
    {document_text}
    
    Respond with ONLY a single word: "resume" or "unknown".
    """)
])

# Prompt selector based on document type
PROMPT_REGISTRY = {
    "resume": RESUME_EXTRACTION_PROMPT
}

def get_prompt_for_doc_type(doc_type):
    """Get the appropriate prompt template for a document type"""
    if doc_type not in PROMPT_REGISTRY:
        raise ValueError(f"Unknown document type: {doc_type}")
    return PROMPT_REGISTRY[doc_type]

async def extract_data(document_text, doc_type, schema, provider="groq"):
    """
    Extract structured data from document text using LLM.
    
    Args:
        document_text: Text content of the document
        doc_type: Type of document (resume, invoice, contract)
        schema: JSON schema for the expected output
        provider: LLM provider to use
        
    Returns:
        Extracted data as a dictionary
    """
    llm = get_llm(provider)
    prompt = get_prompt_for_doc_type(doc_type)
    
    # Format the prompt with document text and schema
    formatted_prompt = prompt.format_messages(
        document_text=document_text,
        schema=json.dumps(schema.schema(), indent=2)
    )
    
    # Get response from LLM
    response = await llm.ainvoke(formatted_prompt)
    
    # Extract the JSON part from the response
    response_text = response.content
    
    try:
        # Parse the response as JSON
        return json.loads(response_text)
    except json.JSONDecodeError:
        # If we can't parse as JSON, try to extract JSON from the text
        try:
            # Look for JSON portion
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > 0:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            else:
                raise ValueError("Could not extract valid JSON from LLM response")
        except Exception as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")

async def detect_doc_type_with_llm(document_text, provider="groq"):
    """
    Detect document type using LLM.
    
    Args:
        document_text: Text content of the document
        provider: LLM provider to use
        
    Returns:
        Detected document type as a string ("resume" or "unknown")
    """
    llm = get_llm(provider)
    
    # Format the prompt with document text
    formatted_prompt = DOCUMENT_TYPE_PROMPT.format_messages(
        document_text=document_text
    )
    
    # Get response from LLM
    response = await llm.ainvoke(formatted_prompt)
    
    # Clean and normalize the response
    doc_type = response.content.strip().lower()
    
    # Validate the response
    valid_types = ["resume", "unknown"]
    
    if doc_type in valid_types:
        return doc_type
    else:
        # If invalid response, fallback to keyword-based detection
        from document_loaders import detect_document_type
        return detect_document_type(document_text)
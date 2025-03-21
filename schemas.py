from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field

# Resume schema
class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[Union[int, str]] = None
    
class Experience(BaseModel):
    company: str
    title: str
    start_date: str
    end_date: Optional[str] = None
    description: Optional[str] = None
    
class ResumeSchema(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    summary: Optional[str] = None

# Schema registry
SCHEMAS = {
    "resume": ResumeSchema
}
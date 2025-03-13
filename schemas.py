from pydantic import BaseModel, validator, HttpUrl
from typing import Optional

class ScrapedElement(BaseModel):
    content: str
    source_url: HttpUrl
    element_type: str
    css_classes: Optional[list[str]] = None
    parent_element: Optional[str] = None
    
    @validator('content')
    def content_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Empty content found')
        return v.strip()

class ScrapedData(BaseModel):
    elements: list[ScrapedElement]
    page_title: str
    scraped_url: HttpUrl
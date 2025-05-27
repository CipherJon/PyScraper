from pydantic import BaseModel, Field, HttpUrl, ValidationError
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from dateutil.parser import isoparse

def parse_datetime_fields(data: Any, datetime_fields: set[str] = {'timestamp', 'created_at', 'updated_at'}) -> Any:
    """Parse datetime fields in the data structure.
    
    Args:
        data: The data structure to parse
        datetime_fields: Set of field names that should be parsed as datetimes
        
    Returns:
        The data structure with datetime fields parsed
    """
    def parse_value(value: Any, current_key: str = None) -> Any:
        """Parse a single value, checking if it should be treated as a datetime.
        
        Args:
            value: The value to parse
            current_key: The key/field name of the current value
            
        Returns:
            The parsed value
        """
        if isinstance(value, str) and current_key in datetime_fields:
            try:
                return isoparse(value)
            except ValueError:
                return value
        elif isinstance(value, dict):
            return {k: parse_value(v, k) for k, v in value.items()}
        elif isinstance(value, list):
            return [parse_value(item, current_key) for item in value]
        return value
    
    return parse_value(data)

class ScrapedElement(BaseModel):
    """Model for a single scraped element."""
    content: str = Field(..., description="The text content of the element")
    source_url: str = Field(..., description="URL where the element was scraped from")
    element_type: str = Field(..., description="HTML tag type or element type")
    css_classes: Optional[List[str]] = Field(None, description="CSS classes applied to the element")
    parent_element: Optional[str] = Field(None, description="Parent element tag name")
    css_selector: Optional[str] = Field(None, description="CSS selector used to find the element")
    xpath_selector: Optional[str] = Field(None, description="XPath selector used to find the element")
    attributes: Optional[Dict[str, str]] = Field(default_factory=dict, description="HTML attributes of the element")
    position: Optional[Dict[str, int]] = Field(None, description="Position information (line, column) if available")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the element was scraped")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the element")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert the element to a dictionary."""
        return {
            'content': self.content,
            'source_url': self.source_url,
            'element_type': self.element_type,
            'css_classes': self.css_classes,
            'parent_element': self.parent_element,
            'css_selector': self.css_selector,
            'xpath_selector': self.xpath_selector,
            'attributes': self.attributes,
            'position': self.position,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    def to_json(self, **kwargs) -> str:
        """Convert the element to a JSON string.
        
        Args:
            **kwargs: Additional arguments to pass to Pydantic's json method
            
        Returns:
            str: JSON string representation of the element
        """
        return self.json(**kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> 'ScrapedElement':
        """Create a ScrapedElement instance from a JSON string.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            ScrapedElement: New instance created from JSON
            
        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            data = json.loads(json_str)
            # Parse datetime fields
            data = parse_datetime_fields(data)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
        except ValidationError as e:
            raise ValueError(f"Invalid data: {str(e)}")

class ScrapedData(BaseModel):
    """Model for scraped data from a page."""
    elements: List[ScrapedElement] = Field(default_factory=list, description="List of scraped elements")
    page_title: str = Field("", description="Title of the scraped page")
    scraped_url: str = Field(..., description="URL that was scraped")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the scrape")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the data was scraped")
    status: str = Field("success", description="Status of the scraping operation")
    error: Optional[str] = Field(None, description="Error message if scraping failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert the data to a dictionary."""
        return {
            'elements': [elem.to_dict() for elem in self.elements],
            'page_title': self.page_title,
            'scraped_url': self.scraped_url,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status,
            'error': self.error
        }

    def to_json(self, **kwargs) -> str:
        """Convert the data to a JSON string.
        
        Args:
            **kwargs: Additional arguments to pass to Pydantic's json method
            
        Returns:
            str: JSON string representation of the data
        """
        return self.json(**kwargs)

    @classmethod
    def from_json(cls, json_str: str) -> 'ScrapedData':
        """Create a ScrapedData instance from a JSON string.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            ScrapedData: New instance created from JSON
            
        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            data = json.loads(json_str)
            # Parse datetime fields
            data = parse_datetime_fields(data)
            return cls(**data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")
        except ValidationError as e:
            raise ValueError(f"Invalid data: {str(e)}")
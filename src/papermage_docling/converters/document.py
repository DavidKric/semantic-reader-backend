from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field


class Box(BaseModel):
    """Represents a bounding box with coordinates."""
    x0: float
    y0: float
    x1: float
    y1: float
    page: int = 0


class Span(BaseModel):
    """Represents a span of text with bounding box."""
    text: str = ""
    box: Optional[Box] = None
    start: int = 0
    end: int = 0


class Entity(BaseModel):
    """Represents a document entity with spans and boxes."""
    id: str = ""
    box: Optional[Box] = None
    spans: List[Span] = Field(default_factory=list)
    boxes: List[Box] = Field(default_factory=list)
    text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TableEntity(Entity):
    """Represents a table in the document."""
    rows: List[List[str]] = Field(default_factory=list)
    columns: List[str] = Field(default_factory=list)
    caption: str = ""


class FigureEntity(Entity):
    """Represents a figure in the document."""
    caption: str = ""


class Page(BaseModel):
    """Represents a page in the document."""
    number: int
    width: float = 0
    height: float = 0
    rotation: float = 0
    words: List[Span] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)


class Document(BaseModel):
    """
    A document representation based on PaperMage's document structure.
    
    This is used as a converter to translate between Docling's native data structures
    and PaperMage's expected format. Compatible with DoclingParse v4.
    """
    id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    pages: List[Page] = Field(default_factory=list)
    full_text: str = ""
    entities: Dict[str, List[Entity]] = Field(default_factory=dict)
    symbols: str = ""  # Backward compatibility field
    
    def to_json(self) -> Dict[str, Any]:
        """Convert the document to a JSON-serializable dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Document":
        """Create a Document from a JSON dictionary."""
        return cls.model_validate(data)
    
    def get_entity_layer(self, layer_name: str) -> List[Entity]:
        """Get a specific entity layer by name."""
        return self.entities.get(layer_name, [])
    
    def add_entity_layer(self, layer_name: str, entities: List[Entity]) -> None:
        """Add or replace an entity layer."""
        self.entities[layer_name] = entities 
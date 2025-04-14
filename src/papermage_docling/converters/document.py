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
    """Represents a span of text in the document."""
    start: int
    end: int


class Entity(BaseModel):
    """Represents a document entity with spans and boxes."""
    spans: List[Span]
    boxes: List[Box]
    text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """
    A document representation based on PaperMage's document structure.
    
    This is used as a converter to translate between Docling's native data structures
    and PaperMage's expected format.
    """
    symbols: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    entities: Dict[str, List[Entity]] = Field(default_factory=dict)
    
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
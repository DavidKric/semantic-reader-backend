from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type


class BasePredictor(ABC):
    """
    Abstract base class for all analysis predictors (Docling, custom, plugin, etc.).
    Provides plugin metadata and registration mechanism.
    """
    # Registry for all predictors
    _registry: Dict[str, Type['BasePredictor']] = {}

    name: str = "base"
    description: str = "Base predictor interface."

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'name') and cls.name != "base":
            BasePredictor._registry[cls.name] = cls

    @classmethod
    def get_predictor(cls, name: str) -> Optional[Type['BasePredictor']]:
        return cls._registry.get(name)

    @classmethod
    def list_predictors(cls) -> List[str]:
        return list(cls._registry.keys())

    @abstractmethod
    def analyze(self, document_path: str, **kwargs) -> Any:
        """
        Run analysis on the given document.
        Args:
            document_path: Path to the document file
            kwargs: Additional analysis options
        Returns:
            Analysis result (type depends on predictor)
        """
        pass

    @classmethod
    def plugin_metadata(cls) -> Dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description,
        }

# Example usage for plugin authors:
# class MyCustomPredictor(BasePredictor):
#     name = "my_custom"
#     description = "My custom analysis predictor."
#     def analyze(self, document_path: str, **kwargs):
#         # Custom analysis logic
#         return {} 
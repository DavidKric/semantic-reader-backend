import pytest
from unittest.mock import MagicMock, patch

from app.services.analysis_service import AnalysisService

class DummyPredictor:
    def __init__(self):
        self.called_with = None
    def analyze(self, document_path, **kwargs):
        self.called_with = (document_path, kwargs)
        return {"result": f"analyzed {document_path}"}

def test_plugin_registration_and_usage(monkeypatch):
    """Test that custom predictors (plugins) can be registered and used by AnalysisService."""
    service = AnalysisService()
    # Inject dummy predictors as plugins
    service.figure_predictor = DummyPredictor()
    service.table_predictor = DummyPredictor()
    service.layout_predictor = DummyPredictor()
    service.structure_predictor = DummyPredictor()
    service.language_predictor = DummyPredictor()

    # Test each analysis method
    result = service.analyze_figures("doc1.pdf", opt=1)
    assert result["result"] == "analyzed doc1.pdf"
    assert service.figure_predictor.called_with[0] == "doc1.pdf"
    assert service.figure_predictor.called_with[1]["opt"] == 1

    result = service.analyze_tables("doc2.pdf", foo="bar")
    assert result["result"] == "analyzed doc2.pdf"
    assert service.table_predictor.called_with[0] == "doc2.pdf"
    assert service.table_predictor.called_with[1]["foo"] == "bar"

    result = service.analyze_layout("doc3.pdf")
    assert result["result"] == "analyzed doc3.pdf"
    result = service.analyze_structure("doc4.pdf")
    assert result["result"] == "analyzed doc4.pdf"
    result = service.analyze_language("doc5.pdf")
    assert result["result"] == "analyzed doc5.pdf"

def test_missing_predictor_raises():
    """Test that missing predictors raise the correct RuntimeError."""
    service = AnalysisService()
    service.figure_predictor = None
    service.table_predictor = None
    service.layout_predictor = None
    service.structure_predictor = None
    service.language_predictor = None

    with pytest.raises(RuntimeError):
        service.analyze_figures("doc.pdf")
    with pytest.raises(RuntimeError):
        service.analyze_tables("doc.pdf")
    with pytest.raises(RuntimeError):
        service.analyze_layout("doc.pdf")
    with pytest.raises(RuntimeError):
        service.analyze_structure("doc.pdf")
    with pytest.raises(RuntimeError):
        service.analyze_language("doc.pdf")

def test_plugin_extensibility(monkeypatch):
    """Test that new plugin types can be added dynamically to AnalysisService."""
    service = AnalysisService()
    # Add a new custom plugin
    class CustomPredictor:
        def analyze(self, document_path, **kwargs):
            return {"custom": document_path}
    service.custom_predictor = CustomPredictor()
    # Simulate a new analysis method
    def analyze_custom(self, document_path, **kwargs):
        if not hasattr(self, "custom_predictor"):
            raise RuntimeError("Custom analysis is not available")
        return self.custom_predictor.analyze(document_path, **kwargs)
    # Attach the method
    import types
    service.analyze_custom = types.MethodType(analyze_custom, service)
    # Test the new plugin
    result = service.analyze_custom("doc6.pdf", x=42)
    assert result["custom"] == "doc6.pdf" 
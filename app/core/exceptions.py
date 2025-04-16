class DocumentProcessingError(Exception):
    """Exception raised when document processing fails."""
    pass

class InvalidDocumentError(Exception):
    """Exception raised when a document is invalid."""
    pass

class EmptyDocumentError(Exception):
    """Exception raised when a document is empty."""
    pass

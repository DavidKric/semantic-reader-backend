"""
Base pipeline implementation for document processing.

This module provides the base classes for building document processing
pipelines using DoclingDocument as the core data structure.
"""

import time
import logging
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable, TypeVar, Generic

# Import the DoclingDocument from docling_core
try:
    from docling_core.types import DoclingDocument
except ImportError:
    logging.warning("docling_core not found. Document pipeline will not be available.")
    # Define a stub class for type hints only
    class DoclingDocument:
        pass

logger = logging.getLogger(__name__)

# Type variable for document processor input/output
T = TypeVar('T', bound=DoclingDocument)


class DocumentProcessor(Generic[T]):
    """
    Base class for document processors that work with DoclingDocument.
    
    This class defines the interface for document processors, which are
    responsible for performing specific operations on a document.
    """
    
    def __init__(self, name: str):
        """
        Initialize the document processor.
        
        Args:
            name: Name of the processor for identification and logging
        """
        self.name = name
        logger.info(f"Initialized DocumentProcessor: {name}")
    
    @abstractmethod
    def process(self, doc: T, **kwargs) -> T:
        """
        Process a document and return the updated document.
        
        Args:
            doc: The document to process
            **kwargs: Additional processing options
            
        Returns:
            The processed document
        """
        pass


class PipelineStep:
    """
    A step in a document processing pipeline.
    
    This class represents a single step in a pipeline, which consists of
    a document processor, a condition for execution, and error handling options.
    """
    
    def __init__(
        self, 
        processor: DocumentProcessor,
        condition: Optional[Callable[[DoclingDocument], bool]] = None,
        error_handler: Optional[Callable[[DoclingDocument, Exception], DoclingDocument]] = None,
        retries: int = 0,
        retry_delay: float = 1.0
    ):
        """
        Initialize a pipeline step.
        
        Args:
            processor: The document processor to use for this step
            condition: Optional condition function to determine if this step should execute
            error_handler: Optional function to handle errors during processing
            retries: Number of retries for failed operations
            retry_delay: Delay between retries in seconds
        """
        self.processor = processor
        self.condition = condition
        self.error_handler = error_handler
        self.retries = retries
        self.retry_delay = retry_delay
        self.stats = {
            "executions": 0,
            "successes": 0,
            "failures": 0,
            "retries": 0,
            "skips": 0,
            "total_time": 0.0
        }
        
        logger.info(f"Initialized PipelineStep with processor: {processor.name}")
    
    def should_execute(self, doc: DoclingDocument) -> bool:
        """
        Determine if this step should execute for a document.
        
        Args:
            doc: The document to check
            
        Returns:
            True if the step should execute, False otherwise
        """
        if self.condition is None:
            return True
        
        try:
            return self.condition(doc)
        except Exception as e:
            logger.warning(f"Error evaluating condition for {self.processor.name}: {e}")
            return False
    
    def execute(self, doc: DoclingDocument, **kwargs) -> DoclingDocument:
        """
        Execute this step on a document.
        
        Args:
            doc: The document to process
            **kwargs: Additional processing options
            
        Returns:
            The processed document
        """
        # Check if we should skip this step
        if not self.should_execute(doc):
            logger.info(f"Skipping step {self.processor.name} (condition not met)")
            self.stats["skips"] += 1
            return doc
        
        # Execute the processor with retries
        retries_left = self.retries
        start_time = time.time()
        self.stats["executions"] += 1
        
        while True:
            try:
                result = self.processor.process(doc, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                
                self.stats["successes"] += 1
                self.stats["total_time"] += execution_time
                
                logger.info(f"Step {self.processor.name} executed successfully in {execution_time:.2f}s")
                return result
            
            except Exception as e:
                if retries_left > 0:
                    retries_left -= 1
                    self.stats["retries"] += 1
                    logger.warning(f"Error in step {self.processor.name}, retrying ({retries_left} retries left): {e}")
                    time.sleep(self.retry_delay)
                else:
                    self.stats["failures"] += 1
                    execution_time = time.time() - start_time
                    self.stats["total_time"] += execution_time
                    
                    logger.error(f"Error in step {self.processor.name} after {self.retries} retries: {e}")
                    
                    # Use error handler if available
                    if self.error_handler is not None:
                        try:
                            logger.info(f"Using error handler for step {self.processor.name}")
                            return self.error_handler(doc, e)
                        except Exception as handler_error:
                            logger.error(f"Error handler for step {self.processor.name} failed: {handler_error}")
                    
                    # Re-raise the exception if no error handler
                    raise


class Pipeline:
    """
    A document processing pipeline using DoclingDocument.
    
    This class represents a complete document processing pipeline, which
    consists of a sequence of processing steps that are executed in order.
    """
    
    def __init__(self, name: str = "DoclingPipeline"):
        """
        Initialize a document processing pipeline.
        
        Args:
            name: Name of the pipeline for identification and logging
        """
        self.name = name
        self.steps = []
        self.step_names = set()
        self.metadata = {
            "id": str(uuid.uuid4()),
            "created": time.time(),
            "name": name
        }
        
        logger.info(f"Initialized Pipeline: {name}")
    
    def add_step(
        self, 
        processor: DocumentProcessor,
        name: Optional[str] = None,
        condition: Optional[Callable[[DoclingDocument], bool]] = None,
        error_handler: Optional[Callable[[DoclingDocument, Exception], DoclingDocument]] = None,
        retries: int = 0,
        retry_delay: float = 1.0
    ) -> "Pipeline":
        """
        Add a processing step to the pipeline.
        
        Args:
            processor: The document processor to add
            name: Optional custom name for this step (defaults to processor.name)
            condition: Optional condition function to determine if this step should execute
            error_handler: Optional function to handle errors during processing
            retries: Number of retries for failed operations
            retry_delay: Delay between retries in seconds
            
        Returns:
            The pipeline instance for method chaining
        """
        step_name = name or processor.name
        
        # Ensure step names are unique
        if step_name in self.step_names:
            step_name = f"{step_name}_{len(self.steps)}"
        
        # Create and add the step
        step = PipelineStep(
            processor=processor,
            condition=condition,
            error_handler=error_handler,
            retries=retries,
            retry_delay=retry_delay
        )
        
        self.steps.append((step_name, step))
        self.step_names.add(step_name)
        
        logger.info(f"Added step '{step_name}' to pipeline '{self.name}'")
        return self
    
    def process(self, doc: DoclingDocument, **kwargs) -> DoclingDocument:
        """
        Process a document through the pipeline.
        
        Args:
            doc: The document to process
            **kwargs: Additional processing options
            
        Returns:
            The processed document
        """
        if not self.steps:
            logger.warning(f"Pipeline '{self.name}' has no steps defined")
            return doc
        
        logger.info(f"Starting pipeline '{self.name}' with {len(self.steps)} steps")
        start_time = time.time()
        current_doc = doc
        
        try:
            # Process each step in order
            for step_name, step in self.steps:
                logger.info(f"Executing step '{step_name}'")
                current_doc = step.execute(current_doc, **kwargs)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            logger.info(f"Pipeline '{self.name}' completed in {execution_time:.2f}s")
            return current_doc
        
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Pipeline '{self.name}' failed after {execution_time:.2f}s: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get pipeline statistics.
        
        Returns:
            Dictionary of pipeline statistics
        """
        stats = {
            "name": self.name,
            "steps": len(self.steps),
            "steps_stats": {}
        }
        
        # Collect stats from each step
        for step_name, step in self.steps:
            stats["steps_stats"][step_name] = step.stats.copy()
            if step.stats["executions"] > 0:
                stats["steps_stats"][step_name]["avg_time"] = (
                    step.stats["total_time"] / step.stats["executions"]
                )
        
        return stats 
"""
Tests for JSON schema validation.

These tests verify that the document processing output matches the expected
JSON schema, ensuring compatibility with downstream systems.
"""

import os
import json
import pytest
import jsonschema
from pathlib import Path

# Import test utilities
from ..conftest import TEST_DATA_DIR, TEST_EXPECTED_DIR

# Define JSON schema for document output
# This should match the expected output structure
DOCUMENT_SCHEMA = {
    "type": "object",
    "required": ["pages"],
    "properties": {
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["width", "height", "blocks"],
                "properties": {
                    "width": {"type": "number"},
                    "height": {"type": "number"},
                    "blocks": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["x0", "y0", "x1", "y1", "text"],
                            "properties": {
                                "x0": {"type": "number"},
                                "y0": {"type": "number"},
                                "x1": {"type": "number"},
                                "y1": {"type": "number"},
                                "text": {"type": "string"}
                            }
                        }
                    },
                    "tables": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["rows", "cols", "cells"],
                            "properties": {
                                "rows": {"type": "integer"},
                                "cols": {"type": "integer"},
                                "x0": {"type": "number"},
                                "y0": {"type": "number"},
                                "x1": {"type": "number"},
                                "y1": {"type": "number"},
                                "cells": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "required": ["row", "col", "text"],
                                        "properties": {
                                            "row": {"type": "integer"},
                                            "col": {"type": "integer"},
                                            "text": {"type": "string"},
                                            "x0": {"type": "number"},
                                            "y0": {"type": "number"},
                                            "x1": {"type": "number"},
                                            "y1": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "figures": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["x0", "y0", "x1", "y1"],
                            "properties": {
                                "x0": {"type": "number"},
                                "y0": {"type": "number"},
                                "x1": {"type": "number"},
                                "y1": {"type": "number"},
                                "caption": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string"},
                "pages": {"type": "integer"}
            }
        }
    }
}

def test_schema_validation():
    """
    Test that all expected outputs conform to the JSON schema.
    """
    # Find all expected output JSON files
    expected_files = list(TEST_EXPECTED_DIR.glob("*.json"))
    
    if not expected_files:
        pytest.skip("No expected output files found")
    
    for json_file in expected_files:
        # Load the expected JSON output
        with open(json_file, "r") as f:
            expected_output = json.load(f)
        
        # Validate against the schema
        try:
            jsonschema.validate(instance=expected_output, schema=DOCUMENT_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(f"Schema validation failed for {json_file.name}: {e}")

def test_missing_required_fields():
    """
    Test that the schema validation correctly identifies missing required fields.
    """
    # Create a document with missing required fields
    invalid_document = {
        "pages": [
            {
                # Missing width and height
                "blocks": []
            }
        ]
    }
    
    # Validate against the schema - should fail
    with pytest.raises(jsonschema.exceptions.ValidationError) as excinfo:
        jsonschema.validate(instance=invalid_document, schema=DOCUMENT_SCHEMA)
    
    # Check that the error message identifies the missing fields
    error_message = str(excinfo.value)
    assert "width" in error_message or "height" in error_message, \
        "Validation error should mention missing required fields"

def test_invalid_field_types():
    """
    Test that the schema validation correctly identifies invalid field types.
    """
    # Create a document with invalid field types
    invalid_document = {
        "pages": [
            {
                "width": "100",  # Should be a number, not a string
                "height": 200,
                "blocks": [
                    {
                        "x0": 0,
                        "y0": 0,
                        "x1": 100,
                        "y1": 20,
                        "text": 123  # Should be a string, not a number
                    }
                ]
            }
        ]
    }
    
    # Validate against the schema - should fail
    with pytest.raises(jsonschema.exceptions.ValidationError) as excinfo:
        jsonschema.validate(instance=invalid_document, schema=DOCUMENT_SCHEMA)
    
    # Check that the error message identifies the invalid type
    error_message = str(excinfo.value)
    assert "type" in error_message, \
        "Validation error should mention invalid type"

def test_additional_fields():
    """
    Test that the schema validation allows additional fields not specified in the schema.
    """
    # Create a document with additional fields
    valid_document = {
        "pages": [
            {
                "width": 100,
                "height": 200,
                "blocks": [
                    {
                        "x0": 0,
                        "y0": 0,
                        "x1": 100,
                        "y1": 20,
                        "text": "Sample text",
                        "additional_field": "This is allowed"  # Additional field
                    }
                ],
                "another_field": 123  # Additional field
            }
        ],
        "extra_section": {  # Additional top-level section
            "some_data": "This is allowed"
        }
    }
    
    # Validate against the schema - should pass
    try:
        jsonschema.validate(instance=valid_document, schema=DOCUMENT_SCHEMA)
    except jsonschema.exceptions.ValidationError as e:
        pytest.fail(f"Schema validation should allow additional fields: {e}")

def test_sample_conversion_output(expected_outputs):
    """
    Test that actual sample conversion outputs conform to the JSON schema.
    
    Args:
        expected_outputs: Fixture providing expected outputs
    """
    # Skip if no expected outputs
    if not expected_outputs:
        pytest.skip("No expected outputs available")
    
    for sample_name, expected_output in expected_outputs.items():
        # Validate against the schema
        try:
            jsonschema.validate(instance=expected_output, schema=DOCUMENT_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(f"Schema validation failed for {sample_name}: {e}")
        
        print(f"✓ {sample_name} conforms to the schema")

#!/usr/bin/env python3
"""
Example script demonstrating the CoreRecipe usage.

This script shows how to use the CoreRecipe API for document processing,
which provides a similar interface to PaperMage's CoreRecipe.
"""

import os
import sys
import json
from pprint import pprint

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the CoreRecipe
from papermage_docling import CoreRecipe


def main():
    """Run the CoreRecipe example."""
    print("CoreRecipe Example")
    print("=================")
    
    # Example PDF path
    pdf_path = "examples/sample.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"\nExample PDF file not found: {pdf_path}")
        print("Please provide a sample PDF file to process.")
        return
    
    print(f"\nProcessing {pdf_path} with CoreRecipe...")
    
    try:
        # Method 1: Using run() method (most flexible)
        recipe = CoreRecipe(
            enable_ocr=False,
            detect_tables=True,
            detect_figures=True
        )
        result = recipe.run(pdf_path)
        
        print("\nMethod 1: Using run() - Success!")
        
        # Method 2: Using from_pdf() method (PaperMage compatibility)
        print("\nProcessing with from_pdf() method...")
        result2 = recipe.from_pdf(pdf_path)
        
        print("\nMethod 2: Using from_pdf() - Success!")
        
        # Method 3: Default recipe with minimal configuration
        print("\nProcessing with default recipe...")
        default_recipe = CoreRecipe.default()
        result3 = default_recipe.run(pdf_path)
        
        print("\nMethod 3: Using default recipe - Success!")
        
        # Display document structure
        print("\nDocument Structure:")
        if hasattr(result, 'metadata'):
            print(f"Metadata: {result.metadata}")
        
        if hasattr(result, 'get_entity_layer'):
            print("\nEntity Layers:")
            for layer_name in ['paragraphs', 'tables', 'figures']:
                entities = result.get_entity_layer(layer_name)
                print(f"- {layer_name}: {len(entities)} entities")
        
        # Save result to JSON file for inspection
        output_path = "examples/recipe_output.json"
        with open(output_path, 'w') as f:
            # Convert to JSON-serializable format if needed
            if hasattr(result, 'to_json'):
                json.dump(result.to_json(), f, indent=2)
            elif hasattr(result, '__dict__'):
                json.dump(result.__dict__, f, indent=2)
            else:
                json.dump(str(result), f, indent=2)
        
        print(f"\nProcessing result saved to {output_path}")
    
    except Exception as e:
        print(f"Error during processing: {str(e)}")


if __name__ == "__main__":
    main() 
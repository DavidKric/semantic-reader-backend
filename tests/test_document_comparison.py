"""
Test document visualization and comparison with pytest integration.

This test module runs the document comparison script and integrates its
visualization outputs with pytest-html reporting.
"""

import pytest
import os
import shutil
import subprocess
import json
from pathlib import Path
import sys
import logging

# Import our document comparison script
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from document_comparison import find_sample_files, generate_visualizations, extract_metadata, collect_document_stats

# Import optional dependencies for report integration
try:
    from papermage_docling.visualizers.report_generator import generate_document_report
    REPORT_AVAILABLE = True
except ImportError:
    REPORT_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test output directory (will be cleaned up after tests)
TEST_OUTPUT_DIR = Path("test_results") / "visualizations"


@pytest.fixture(scope="module")
def output_dir():
    """Create and clean up the test output directory."""
    # Create output directory if it doesn't exist
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    
    yield TEST_OUTPUT_DIR
    
    # Comment out to keep the visualization outputs for inspection
    # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)


def get_test_files(sample_type="simple", max_files=1):
    """Get test PDF files for testing."""
    try:
        files = find_sample_files(sample_type)
        return files[:max_files]  # Limit to specified number of files
    except (FileNotFoundError, ValueError) as e:
        pytest.skip(f"Could not find test files: {e}")
        return []


def extract_document_data(pdf_file):
    """Extract raw JSON data from a document."""
    try:
        # Use papermage-docling services instead of direct docling access
        from papermage_docling.converter import PaperMageDoclingConverter
        
        # Initialize converter with the file
        converter = PaperMageDoclingConverter()
        try:
            papermage_doc = converter.convert_document(pdf_file)
            
            # Extract data from the papermage document
            raw_data = {
                "filename": pdf_file,
                "pages": []
            }
            
            # Extract page data
            for i, page in enumerate(papermage_doc.pages):
                page_data = {
                    "page_number": i + 1,
                    "word_count": len(page.blocks) if hasattr(page, "blocks") else 0,
                    "line_count": len([b for b in page.blocks if hasattr(b, "lines")]) if hasattr(page, "blocks") else 0,
                }
                
                # Add text blocks data
                if hasattr(page, "blocks") and page.blocks:
                    blocks = []
                    for block in page.blocks[:30]:  # Limit to first 30 blocks
                        block_data = {
                            "text": block.text if hasattr(block, "text") else "",
                            "type": block.type if hasattr(block, "type") else "unknown",
                            "bbox": block.bbox if hasattr(block, "bbox") else [0, 0, 0, 0],
                        }
                        blocks.append(block_data)
                    page_data["blocks"] = blocks
                
                raw_data["pages"].append(page_data)
            
            return raw_data
        except Exception as e:
            logger.warning(f"PaperMage conversion failed: {e}, falling back to direct docling access")
            # Fall back to direct docling access
            from docling_core.types.doc.page import TextCellUnit
            from docling_parse.pdf_parser import DoclingPdfParser
            
            # Parse the document
            parser = DoclingPdfParser(loglevel="error")
            pdf_doc = parser.load(path_or_stream=pdf_file, lazy=True)
            
            # Extract all text from all pages
            raw_data = {
                "filename": pdf_file,
                "pages": []
            }
            
            for page_no in range(1, pdf_doc.number_of_pages() + 1):
                try:
                    pdf_page = pdf_doc.get_page(page_no=page_no)
                    
                    # Extract basic page data
                    page_data = {
                        "page_number": page_no,
                        "word_count": 0,
                        "line_count": 0,
                    }
                    
                    # Extract text
                    words = []
                    lines = []
                    try:
                        # Try to get words and lines if available
                        for word in pdf_page.iterate_cells(unit_type=TextCellUnit.WORD):
                            words.append({
                                "text": word.text,
                                "bbox": [0, 0, 0, 0]  # Default bbox to avoid attribute errors
                            })
                        
                        for line in pdf_page.iterate_cells(unit_type=TextCellUnit.LINE):
                            lines.append({
                                "text": line.text,
                                "bbox": [0, 0, 0, 0]  # Default bbox to avoid attribute errors
                            })
                    except Exception as e:
                        logger.warning(f"Failed to extract cells for page {page_no}: {e}")
                    
                    page_data["word_count"] = len(words)
                    page_data["line_count"] = len(lines)
                    
                    if words:
                        page_data["words"] = words[:30]  # Limit to first 30 words
                    if lines:
                        page_data["lines"] = lines[:10]  # Limit to first 10 lines
                    
                    raw_data["pages"].append(page_data)
                except Exception as e:
                    logger.warning(f"Failed to process page {page_no}: {e}")
                    # Add an empty page
                    raw_data["pages"].append({
                        "page_number": page_no,
                        "word_count": 0,
                        "line_count": 0,
                        "error": str(e)
                    })
            
            return raw_data
    except Exception as e:
        logger.warning(f"Failed to extract raw data using any method: {e}")
        # Create minimal data structure
        return {
            "error": str(e),
            "filename": pdf_file,
            "pages": [{
                "page_number": 1,
                "word_count": 0,
                "line_count": 0,
                "error": "Failed to extract data"
            }]
        }


@pytest.mark.parametrize("sample_type", ["simple", pytest.param("tables", marks=pytest.mark.xfail)])
def test_document_visualization(sample_type, output_dir, request):
    """
    Test document visualization with different sample types.
    
    Args:
        sample_type: Type of sample to process ("simple", "tables", etc.)
        output_dir: Directory to save visualizations (from fixture)
        request: pytest request object for report integration
    """
    # Get test files
    test_files = get_test_files(sample_type)
    assert len(test_files) > 0, f"No test files found for {sample_type}"
    
    for pdf_file in test_files:
        logger.info(f"Testing visualization for {pdf_file}")
        
        # Create a subdirectory for this file
        file_output_dir = output_dir / Path(pdf_file).stem
        os.makedirs(file_output_dir, exist_ok=True)
        
        # Extract raw JSON data before visualization
        raw_data = extract_document_data(pdf_file)
        
        # Save raw data as JSON file
        raw_data_path = file_output_dir / f"{Path(pdf_file).stem}_raw_data.json"
        with open(raw_data_path, 'w') as f:
            json.dump(raw_data, f, indent=2)
        
        # Also save raw data as text file for better report display
        raw_text_path = file_output_dir / f"{Path(pdf_file).stem}_raw_data.txt"
        with open(raw_text_path, 'w') as f:
            f.write(f"Document: {pdf_file}\n\n")
            f.write(f"Pages: {len(raw_data['pages'])}\n\n")
            for page in raw_data['pages']:
                f.write(f"Page {page['page_number']}:\n")
                f.write(f"  Words: {page.get('word_count', 0)}\n")
                f.write(f"  Lines: {page.get('line_count', 0)}\n")
                if 'words' in page:
                    f.write("\n  Sample Words:\n")
                    for word in page['words'][:10]:  # Show top 10 words
                        f.write(f"    {word['text']} {word['bbox']}\n")
                if 'lines' in page:
                    f.write("\n  Sample Lines:\n")
                    for line in page['lines'][:5]:  # Show top 5 lines
                        f.write(f"    {line['text']}\n")
                f.write("\n")
        
        # Generate visualizations
        visualizations = generate_visualizations(pdf_file, file_output_dir)
        
        # Verify visualizations were created
        assert visualizations, f"No visualizations generated for {pdf_file}"
        assert "char" in visualizations, "Character level visualizations not generated"
        assert "word" in visualizations, "Word level visualizations not generated"
        assert "line" in visualizations, "Line level visualizations not generated"
        
        # Generate and attach report if available
        if REPORT_AVAILABLE:
            try:
                # Extract metadata and stats
                metadata = extract_metadata(pdf_file)
                document_stats = collect_document_stats(str(file_output_dir), pdf_file)
                
                # Add raw data to document stats for display in the report
                document_stats["raw_data"] = {
                    "file_path": str(raw_data_path),
                    "word_count": sum(page.get("word_count", 0) for page in raw_data["pages"]),
                    "line_count": sum(page.get("line_count", 0) for page in raw_data["pages"]),
                    "page_count": len(raw_data["pages"]),
                    "pages": raw_data["pages"]  # Include full page data for display
                }
                
                # Generate HTML report
                report_path = str(file_output_dir / f"{Path(pdf_file).stem}_report.html")
                
                # Add raw data to the report context
                report_context = {
                    "raw_data": raw_data,
                    "json_preview": json.dumps(raw_data, indent=2)[:2000] + "\n...",  # Truncate long output
                    "raw_text_content": open(raw_text_path, 'r').read()  # Include text version
                }
                
                report_path = generate_document_report(
                    output_path=report_path,
                    title=f"Document Analysis: {Path(pdf_file).stem}",
                    filename=Path(pdf_file).name,
                    visualizations=visualizations,
                    metadata=metadata,
                    document_stats=document_stats,
                    additional_context=report_context  # Pass raw data to report template
                )
                
                logger.info(f"Generated report: {report_path}")
                
                # Attach to pytest-html report if available 
                try:
                    from pytest_html import extras
                    
                    if hasattr(request, "node") and hasattr(request.node, "user_properties"):
                        # Add a direct link to the visualization report
                        report_rel_path = os.path.relpath(report_path, os.getcwd())
                        
                        # Make the link more prominent with HTML styling
                        styled_link = f"""
                        <div style="margin: 10px 0; padding: 10px; background-color: #f0f0f0; border-radius: 5px;">
                            <h3>Visualization Report</h3>
                            <p>View detailed visualizations for {os.path.basename(pdf_file)}:</p>
                            <a href="{report_rel_path}" target="_blank" style="display: inline-block; padding: 8px 15px; 
                                background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; 
                                font-weight: bold;">Open Report</a>
                            <p style="margin-top: 10px; font-size: 12px; color: #666;">
                                Raw data: <a href="{os.path.relpath(raw_text_path, os.getcwd())}" target="_blank">Text Data</a> | 
                                <a href="{os.path.relpath(raw_data_path, os.getcwd())}" target="_blank">JSON Data</a>
                            </p>
                        </div>
                        """
                        
                        # Add the styled link to the report with proper filename in the ID to avoid collisions
                        request.node.user_properties.append(
                            (f"extra_{Path(pdf_file).stem}", extras.html(styled_link))
                        )
                        
                        # Add a preview of the raw data
                        raw_data_preview = f"""
                        <div style="margin: 10px 0; padding: 10px; background-color: #f0f0f0; border-radius: 5px;">
                            <h3>Raw Document Data Preview - {os.path.basename(pdf_file)}</h3>
                            <pre style="max-height: 300px; overflow: auto; background-color: #f8f8f8; 
                                padding: 10px; border: 1px solid #ddd; border-radius: 4px;">
                            {open(raw_text_path, 'r').read()[:1000]}
                            ...
                            </pre>
                        </div>
                        """
                        
                        # Add the raw data preview to the report
                        request.node.user_properties.append(
                            (f"extra_raw_{Path(pdf_file).stem}", extras.html(raw_data_preview))
                        )
                        
                        # Add some representative images to the report
                        for viz_type, pages in visualizations.items():
                            if not pages:
                                continue
                            # Get the first page's visualization for each type
                            first_page = min(pages.keys())
                            img_path = pages[first_page]
                            try:
                                request.node.user_properties.append(
                                    (f"extra_img_{Path(pdf_file).stem}_{viz_type}", extras.image(
                                        img_path, 
                                        name=f"{viz_type.capitalize()} - {Path(pdf_file).stem} - Page {first_page}"
                                    ))
                                )
                            except Exception as e:
                                logger.warning(f"Failed to attach image {img_path}: {e}")
                except ImportError:
                    logger.warning("pytest-html not available, skipping report integration")
            except Exception as e:
                logger.warning(f"Failed to generate report: {e}")
                logger.exception("Details:")


def test_docling_visualize_script(output_dir):
    """
    Test the docling_visualize.py script by executing it as a subprocess.
    
    Args:
        output_dir: Directory to save visualizations (from fixture)
    """
    # Get a test file
    test_files = get_test_files(sample_type="simple")
    if not test_files:
        pytest.skip("No test files found")
    
    pdf_file = test_files[0]
    
    # Create subdirectory for script output
    script_output_dir = output_dir / "docling_visualize_output"
    os.makedirs(script_output_dir, exist_ok=True)
    
    # Get the absolute path to the script
    script_path = Path(__file__).parent / "scripts" / "docling_visualize.py"
    
    # Make the script executable if it's not already
    if not os.access(script_path, os.X_OK):
        script_path.chmod(script_path.stat().st_mode | 0o111)
    
    # Run the script as a subprocess
    try:
        # Build the command
        command = [
            sys.executable,
            str(script_path),
            "--pdf", pdf_file,
            "--output-dir", str(script_output_dir),
            "--category", "all"
        ]
        
        logger.info(f"Running command: {' '.join(command)}")
        
        # Execute the command
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Log the output
        logger.info(f"Command output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Command stderr:\n{result.stderr}")
        
        # Verify outputs were created
        output_files = list(script_output_dir.glob("*.png"))
        assert output_files, "No visualization files were generated"
        
        # Check for specific visualization types
        assert list(script_output_dir.glob("*.char.png")), "No character visualizations generated"
        assert list(script_output_dir.glob("*.word.png")), "No word visualizations generated"
        assert list(script_output_dir.glob("*.line.png")), "No line visualizations generated"
        
        logger.info(f"Generated {len(output_files)} visualization files")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Script execution failed: {e}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        pytest.fail(f"docling_visualize.py script execution failed with exit code {e.returncode}")
    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Error executing script: {e}")
        pytest.fail(f"Error executing script: {e}") 
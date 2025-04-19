"""
Visualization module for document processing reports.

This module provides functions for generating visualizations of document
components (layout, text blocks, tables, figures) for inclusion in HTML reports.
"""

import base64
import io
from typing import Any, Dict, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np


def create_layout_visualization(page: Dict[str, Any], 
                                dpi: int = 100, 
                                figsize: Optional[Tuple[float, float]] = None) -> str:
    """
    Create a visualization of the document page layout.
    
    Args:
        page: Page data containing text blocks, tables, and figures
        dpi: DPI for the generated image
        figsize: Figure size (width, height) in inches
        
    Returns:
        Base64-encoded image data string for HTML embedding
    """
    # Get page dimensions
    width = page.get("width", 612)  # Default to 8.5x11 at 72dpi
    height = page.get("height", 792)
    
    # Calculate aspect ratio and figure size
    aspect_ratio = height / width
    if figsize is None:
        # Default to a reasonably sized figure
        fig_width = 8
        fig_height = fig_width * aspect_ratio
        figsize = (fig_width, fig_height)
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    
    # Set axis limits to match page dimensions
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.invert_yaxis()  # Invert y-axis to match PDF coordinates (origin at top-left)
    
    # Draw page boundary
    ax.add_patch(patches.Rectangle((0, 0), width, height, 
                               fill=False, edgecolor='black', linewidth=1))
    
    # Get the elements to visualize
    text_blocks = page.get("text_blocks", page.get("blocks", []))
    tables = page.get("tables", [])
    figures = page.get("figures", [])
    
    # Draw text blocks
    for i, block in enumerate(text_blocks):
        x0 = block.get("x0", 0)
        y0 = block.get("y0", 0)
        x1 = block.get("x1", x0 + 10)
        y1 = block.get("y1", y0 + 10)
        
        # Draw text block with blue color
        ax.add_patch(patches.Rectangle((x0, y0), x1-x0, y1-y0,
                                   fill=True, alpha=0.3, 
                                   edgecolor='blue', facecolor='lightblue', 
                                   linewidth=1))
        
        # Add block identifier
        ax.text(x0 + (x1-x0)/2, y0 + (y1-y0)/2, f"T{i+1}",
               horizontalalignment='center', verticalalignment='center',
               fontsize=8, color='blue')
    
    # Draw tables
    for i, table in enumerate(tables):
        x0 = table.get("x0", 0)
        y0 = table.get("y0", 0)
        x1 = table.get("x1", x0 + 10)
        y1 = table.get("y1", y0 + 10)
        
        # Draw table with green color
        ax.add_patch(patches.Rectangle((x0, y0), x1-x0, y1-y0,
                                   fill=True, alpha=0.3, 
                                   edgecolor='green', facecolor='lightgreen', 
                                   linewidth=1))
        
        # Add table identifier
        table_label = f"Table {i+1}"
        if "rows" in table and "cols" in table:
            table_label += f" ({table['rows']}x{table['cols']})"
        
        ax.text(x0 + (x1-x0)/2, y0 + (y1-y0)/2, table_label,
               horizontalalignment='center', verticalalignment='center',
               fontsize=8, color='green')
    
    # Draw figures
    for i, figure in enumerate(figures):
        x0 = figure.get("x0", 0)
        y0 = figure.get("y0", 0)
        x1 = figure.get("x1", x0 + 10)
        y1 = figure.get("y1", y0 + 10)
        
        # Draw figure with red color
        ax.add_patch(patches.Rectangle((x0, y0), x1-x0, y1-y0,
                                   fill=True, alpha=0.3, 
                                   edgecolor='red', facecolor='pink', 
                                   linewidth=1))
        
        # Add figure identifier
        figure_label = f"Fig {i+1}"
        figure_type = figure.get("type", figure.get("image_type", ""))
        if figure_type:
            figure_label += f" ({figure_type})"
        
        ax.text(x0 + (x1-x0)/2, y0 + (y1-y0)/2, figure_label,
               horizontalalignment='center', verticalalignment='center',
               fontsize=8, color='red')
    
    # Add legend
    if text_blocks:
        text_patch = patches.Patch(color='lightblue', alpha=0.3, label='Text Blocks')
        ax.add_artist(plt.legend(handles=[text_patch], loc='upper right'))
    
    if tables:
        table_patch = patches.Patch(color='lightgreen', alpha=0.3, label='Tables')
        ax.add_artist(plt.legend(handles=[table_patch], loc='upper left'))
    
    if figures:
        figure_patch = patches.Patch(color='pink', alpha=0.3, label='Figures')
        ax.add_artist(plt.legend(handles=[figure_patch], loc='lower right'))
    
    # Remove axis ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Convert plot to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Encode image to base64
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{img_data}"


def create_text_visualization(page: Dict[str, Any], dpi: int = 100) -> str:
    """
    Create a visualization of the text blocks with reading order.
    
    Args:
        page: Page data containing text blocks
        dpi: DPI for the generated image
        
    Returns:
        Base64-encoded image data string for HTML embedding
    """
    # Get page dimensions
    width = page.get("width", 612)  # Default to 8.5x11 at 72dpi
    height = page.get("height", 792)
    
    # Calculate aspect ratio and figure size
    aspect_ratio = height / width
    fig_width = 8
    fig_height = fig_width * aspect_ratio
    
    # Create figure
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    
    # Set axis limits to match page dimensions
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.invert_yaxis()  # Invert y-axis to match PDF coordinates (origin at top-left)
    
    # Draw page boundary
    ax.add_patch(patches.Rectangle((0, 0), width, height, 
                               fill=False, edgecolor='black', linewidth=1))
    
    # Get the text blocks
    text_blocks = page.get("text_blocks", page.get("blocks", []))
    
    # Draw text blocks with reading order
    for i, block in enumerate(text_blocks):
        x0 = block.get("x0", 0)
        y0 = block.get("y0", 0)
        x1 = block.get("x1", x0 + 10)
        y1 = block.get("y1", y0 + 10)
        
        # Draw text block with blue color
        ax.add_patch(patches.Rectangle((x0, y0), x1-x0, y1-y0,
                                   fill=True, alpha=0.2, 
                                   edgecolor='blue', facecolor='lightblue', 
                                   linewidth=1))
        
        # Add block number (reading order)
        ax.text(x0 + (x1-x0)/2, y0 + (y1-y0)/2, f"{i+1}",
               horizontalalignment='center', verticalalignment='center',
               fontsize=10, weight='bold', color='blue')
        
        # Add small sample of text
        if "text" in block and block["text"]:
            text_sample = block["text"][:20] + "..." if len(block["text"]) > 20 else block["text"]
            ax.text(x0, y1 + 5, text_sample,
                   horizontalalignment='left', verticalalignment='bottom',
                   fontsize=6, color='black')
    
    # If there are more than 1 block, draw arrows between blocks to show reading order
    if len(text_blocks) > 1:
        for i in range(len(text_blocks) - 1):
            start_block = text_blocks[i]
            end_block = text_blocks[i + 1]
            
            # Get center points of blocks
            start_x = start_block.get("x0", 0) + (start_block.get("x1", 0) - start_block.get("x0", 0)) / 2
            start_y = start_block.get("y0", 0) + (start_block.get("y1", 0) - start_block.get("y0", 0)) / 2
            end_x = end_block.get("x0", 0) + (end_block.get("x1", 0) - end_block.get("x0", 0)) / 2
            end_y = end_block.get("y0", 0) + (end_block.get("y1", 0) - end_block.get("y0", 0)) / 2
            
            # Draw arrow
            ax.annotate("", 
                       xy=(end_x, end_y), 
                       xytext=(start_x, start_y),
                       arrowprops=dict(arrowstyle="->", color="blue", alpha=0.6))
    
    # Remove axis ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Add title
    ax.set_title("Text Blocks and Reading Order", fontsize=12)
    
    # Convert plot to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Encode image to base64
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{img_data}"


def create_table_visualization(table: Dict[str, Any], dpi: int = 100) -> str:
    """
    Create a visualization of a table with its cells.
    
    Args:
        table: Table data containing cells
        dpi: DPI for the generated image
        
    Returns:
        Base64-encoded image data string for HTML embedding
    """
    # Get table dimensions
    x0 = table.get("x0", 0)
    y0 = table.get("y0", 0)
    x1 = table.get("x1", 500)
    y1 = table.get("y1", 300)
    width = x1 - x0
    height = y1 - y0
    
    # Get rows and columns
    rows = table.get("rows", 0)
    cols = table.get("cols", 0)
    cells = table.get("cells", [])
    
    # Skip if no rows or columns
    if rows <= 0 or cols <= 0:
        # Create a simple figure with a message
        fig, ax = plt.subplots(figsize=(6, 3), dpi=dpi)
        ax.text(0.5, 0.5, "No table data available",
               horizontalalignment='center', verticalalignment='center',
               fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_axis_off()
        
        # Convert plot to image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        
        # Encode image to base64
        img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return f"data:image/png;base64,{img_data}"
    
    # Create figure with aspect ratio matching the table
    aspect_ratio = height / width
    fig_width = 10
    fig_height = max(3, fig_width * aspect_ratio)  # Ensure minimum height
    
    # Create figure
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    
    # Set axis limits to match table dimensions with some padding
    padding = 50  # Add padding around the table
    ax.set_xlim(x0 - padding, x1 + padding)
    ax.set_ylim(y1 + padding, y0 - padding)  # Invert y-axis to match PDF coordinates
    
    # Draw table boundary
    ax.add_patch(patches.Rectangle((x0, y0), width, height, 
                               fill=False, edgecolor='green', linewidth=2))
    
    # Color scheme for cells
    colors = plt.cm.Pastel1(np.linspace(0, 1, 9))
    
    # Draw cells
    for cell in cells:
        row = cell.get("row", 0)
        col = cell.get("col", 0)
        cell_x0 = cell.get("x0", x0)
        cell_y0 = cell.get("y0", y0)
        cell_x1 = cell.get("x1", cell_x0 + width/cols)
        cell_y1 = cell.get("y1", cell_y0 + height/rows)
        cell_text = cell.get("text", "")
        
        # Color index for the cell
        color_idx = (row + col) % len(colors)
        
        # Draw cell
        ax.add_patch(patches.Rectangle((cell_x0, cell_y0), cell_x1-cell_x0, cell_y1-cell_y0,
                                    fill=True, alpha=0.3, 
                                    edgecolor='black', facecolor=colors[color_idx], 
                                    linewidth=1))
        
        # Add row/col indices
        ax.text(cell_x0 + 5, cell_y0 + 5, f"R{row},C{col}",
               horizontalalignment='left', verticalalignment='top',
               fontsize=8, color='black')
        
        # Add text sample if it fits
        if cell_text:
            text_sample = cell_text[:10] + "..." if len(cell_text) > 10 else cell_text
            ax.text(cell_x0 + (cell_x1-cell_x0)/2, cell_y0 + (cell_y1-cell_y0)/2, text_sample,
                   horizontalalignment='center', verticalalignment='center',
                   fontsize=8, color='black')
    
    # Add title
    ax.set_title(f"Table ({rows}x{cols})", fontsize=12)
    
    # Remove axis ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Convert plot to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Encode image to base64
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{img_data}"


def create_figure_visualization(figure: Dict[str, Any], dpi: int = 100) -> str:
    """
    Create a visualization of a figure with its caption.
    
    Args:
        figure: Figure data
        dpi: DPI for the generated image
        
    Returns:
        Base64-encoded image data string for HTML embedding
    """
    # Get figure dimensions and type
    x0 = figure.get("x0", 0)
    y0 = figure.get("y0", 0)
    x1 = figure.get("x1", x0 + 200)
    y1 = figure.get("y1", y0 + 200)
    width = x1 - x0
    height = y1 - y0
    
    figure_type = figure.get("type", figure.get("image_type", "Unknown"))
    
    # Get caption if available
    caption = ""
    if "caption" in figure:
        if isinstance(figure["caption"], dict) and "text" in figure["caption"]:
            caption = figure["caption"]["text"]
        elif isinstance(figure["caption"], str):
            caption = figure["caption"]
    
    # Create figure with aspect ratio matching the figure
    aspect_ratio = height / width
    fig_width = 8
    fig_height = fig_width * aspect_ratio
    
    # Create figure
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    
    # Set axis limits to match figure dimensions with some padding
    padding = 50  # Add padding around the figure
    ax.set_xlim(x0 - padding, x1 + padding)
    ax.set_ylim(y1 + padding, y0 - padding)  # Invert y-axis to match PDF coordinates
    
    # Draw figure boundary
    ax.add_patch(patches.Rectangle((x0, y0), width, height, 
                               fill=True, alpha=0.2, 
                               edgecolor='red', facecolor='pink', 
                               linewidth=2))
    
    # Add figure type
    ax.text(x0 + width/2, y0 + height/2, f"Figure\n({figure_type})",
           horizontalalignment='center', verticalalignment='center',
           fontsize=12, color='red')
    
    # Add caption if available
    if caption:
        # Try to locate caption coordinates
        caption_coords = None
        if isinstance(figure.get("caption"), dict):
            caption_x0 = figure["caption"].get("x0")
            caption_y0 = figure["caption"].get("y0")
            caption_x1 = figure["caption"].get("x1")
            caption_y1 = figure["caption"].get("y1")
            
            if all(v is not None for v in [caption_x0, caption_y0, caption_x1, caption_y1]):
                caption_coords = (caption_x0, caption_y0, caption_x1, caption_y1)
        
        if caption_coords:
            # Draw caption boundary
            caption_x0, caption_y0, caption_x1, caption_y1 = caption_coords
            caption_width = caption_x1 - caption_x0
            caption_height = caption_y1 - caption_y0
            
            ax.add_patch(patches.Rectangle((caption_x0, caption_y0), caption_width, caption_height,
                                       fill=True, alpha=0.2, 
                                       edgecolor='green', facecolor='lightgreen', 
                                       linewidth=1))
            
            # Add caption text
            if len(caption) > 50:
                caption = caption[:47] + "..."
            
            ax.text(caption_x0 + caption_width/2, caption_y0 + caption_height/2, f"Caption: {caption}",
                   horizontalalignment='center', verticalalignment='center',
                   fontsize=8, color='green', wrap=True)
            
            # Draw arrow from figure to caption
            ax.annotate("", 
                       xy=(caption_x0 + caption_width/2, caption_y0 + caption_height/2), 
                       xytext=(x0 + width/2, y1),
                       arrowprops=dict(arrowstyle="->", color="green", alpha=0.6))
        else:
            # Just add caption text below the figure
            if len(caption) > 50:
                caption = caption[:47] + "..."
                
            ax.text(x0 + width/2, y1 + 20, f"Caption: {caption}",
                   horizontalalignment='center', verticalalignment='bottom',
                   fontsize=10, color='green')
    
    # Add title
    ax.set_title(f"Figure ({figure_type})", fontsize=12)
    
    # Remove axis ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Convert plot to image
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    
    # Encode image to base64
    img_data = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    
    return f"data:image/png;base64,{img_data}" 
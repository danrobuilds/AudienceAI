import base64
import uuid
import tempfile
import os
from typing import Dict, Any
import mermaid as md

def create_diagram(mermaid_code: str) -> Dict[str, Any]:
    """
    Create a diagram using local mermaid-py library.
    
    Args:
        mermaid_code: Complete, valid Mermaid diagram code
    
    Returns:
        Dictionary with base64_data, filename, size, and diagram_type
    """
    try:
        # Clean up the mermaid code
        clean_code = mermaid_code.strip()
        
        # Convert escape sequences to actual characters
        clean_code = clean_code.replace('\\n', '\n').replace('\\t', '\t')
        
        print(f"Processing Mermaid code: {clean_code[:200]}...")
        
        # Detect diagram type from the code
        diagram_type = _detect_diagram_type(clean_code)
        print(f"Detected diagram type: {diagram_type}")
        
        # Clean up the code based on diagram type
        clean_code = _clean_mermaid_code(clean_code, diagram_type)
        
        # Validate the code before processing
        if not _validate_mermaid_code(clean_code, diagram_type):
            return {"error": "Invalid Mermaid code structure"}
        
        print(f"Cleaned code:\n{clean_code}")
        
        # Generate image using local mermaid-py library
        image_data = _generate_mermaid_image_local(clean_code)
        
        if not image_data:
            return {"error": "Failed to generate diagram image"}
        
        # Validate image data
        if len(image_data) < 100:  # PNG files should be at least 100 bytes
            return {"error": "Generated image is too small, likely corrupted"}
        
        # Encode as base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # Get file size
        file_size = len(image_data)
        size_str = f"{file_size // 1024}KB" if file_size > 1024 else f"{file_size}B"
        
        filename = f"{diagram_type}_diagram_{str(uuid.uuid4())[:8]}.png"
        print(f"Successfully created diagram: {filename} ({size_str})") 

        return {
            "base64_data": base64_data,
            "filename": filename,
            "size": size_str,
            "diagram_type": diagram_type,
            "success": True
        }
    except Exception as e:
        print(f"Exception in create_diagram: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {"error": f"Failed to create diagram: {str(e)}"}

def _detect_diagram_type(mermaid_code: str) -> str:
    """Detect the diagram type from Mermaid code."""
    code_lower = mermaid_code.lower().strip()
    
    if code_lower.startswith('flowchart') or code_lower.startswith('graph'):
        return 'flowchart'
    elif code_lower.startswith('sequencediagram'):
        return 'sequence'
    elif code_lower.startswith('pie'):
        return 'pie'
    elif code_lower.startswith('mindmap'):
        return 'mindmap'
    elif code_lower.startswith('timeline'):
        return 'timeline'
    elif code_lower.startswith('gantt'):
        return 'gantt'
    elif code_lower.startswith('classdiagram'):
        return 'class'
    else:
        return 'diagram'

def _validate_mermaid_code(mermaid_code: str, diagram_type: str) -> bool:
    """Validate Mermaid code structure."""
    if not mermaid_code.strip():
        return False
    
    lines = mermaid_code.strip().split('\n')
    if not lines:
        return False
    
    # Basic validation based on diagram type
    if diagram_type == 'class':
        # Class diagrams should have class definitions
        has_class_content = any('class ' in line for line in lines)
        return has_class_content
    elif diagram_type == 'flowchart':
        # Flowcharts should have node connections
        has_connections = any('-->' in line or '->' in line for line in lines)
        return has_connections or len(lines) > 1
    
    return True  # Default to valid for other diagram types

def _clean_mermaid_code(mermaid_code: str, diagram_type: str) -> str:
    """Clean up Mermaid code based on diagram type."""
    lines = mermaid_code.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.rstrip()  # Keep leading spaces but remove trailing spaces
        
        # Skip empty lines
        if not line.strip():
            continue
        
        # Handle different diagram types differently
        if diagram_type == 'class':
            # For class diagrams, preserve most syntax but clean up problematic elements
            stripped = line.strip().lower()
            
            # Skip only problematic style definitions that might cause issues
            if stripped.startswith('style ') and ('fill:' in stripped or 'stroke:' in stripped):
                continue
            
            # Keep class definitions and other important syntax
            cleaned_lines.append(line)
            
        elif diagram_type == 'mindmap':
            # For mindmap, clean up node definitions as before
            stripped = line.strip()
            if stripped.startswith('root((') and stripped.endswith('))'):
                # Clean up root node syntax - preserve indentation
                content = stripped[6:-2]  # Remove 'root((' and '))'
                indent = line[:len(line) - len(line.lstrip())]  # Preserve original indentation
                cleaned_lines.append(f"{indent}root({content})")
            elif stripped.startswith(':'):
                # Clean up leaf nodes with colons - preserve indentation
                content = stripped[1:]  # Remove leading colon
                indent = line[:len(line) - len(line.lstrip())]  # Preserve original indentation
                cleaned_lines.append(f"{indent}{content}")
            else:
                cleaned_lines.append(line)
        else:
            # For other diagram types, minimal cleaning
            stripped = line.strip().lower()
            
            # Only skip obviously problematic lines
            if stripped.startswith('style ') and ('fill:' in stripped or 'stroke:' in stripped):
                continue
                
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def _generate_mermaid_image_local(mermaid_code: str) -> bytes:
    """Generate diagram image using local mermaid-py library."""
    try:
        print("Generating diagram locally using mermaid-py...")
        
        # Create Mermaid diagram object
        diagram = md.Mermaid(mermaid_code)
        
        # Create a temporary file for the PNG output
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            # Generate PNG image to the temporary file
            # Note: mermaid-py doesn't support width, height, scale parameters
            diagram.to_png(temp_path)
            
            # Check if the file was created successfully
            if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                # Read the file content
                with open(temp_path, 'rb') as f:
                    png_data = f.read()
                
                print(f"Successfully generated diagram: {len(png_data)} bytes")
                return png_data
            else:
                print("Failed to generate PNG file")
                return None
                
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        print(f"Error generating diagram: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return None

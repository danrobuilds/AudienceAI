# MANUALLY CALL TO BATCH INGEST PDFS FROM DIRECTORY

import pdfplumber
import os
import io
import uuid
from datetime import datetime
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from services.supabase_service import supabase

# --- Constants ---
EMBEDDINGS_MODEL_NAME = "nomic-embed-text"
STORAGE_BUCKET = "files"
TENANT_ID = "2e916cd6-d890-4127-afe0-6e3dde85bddc"  # Dummy tenant ID for now

# --- Chunking Configuration ---
CHUNK_SIZE = 1000        # Characters per chunk
CHUNK_OVERLAP = 200      # Overlap between chunks to maintain context
MIN_CHUNK_SIZE = 20      # Much smaller minimum - only filter out truly empty/whitespace chunks

# --- Global Instances (Lazy Initialization) ---
embeddings_model_instance = None

def _initialize_embeddings():
    global embeddings_model_instance
    if embeddings_model_instance is None:
        try:
            print(f"[pdf_uploader DEBUG] Initializing OllamaEmbeddings model: {EMBEDDINGS_MODEL_NAME}")
            embeddings_model_instance = OllamaEmbeddings(model=EMBEDDINGS_MODEL_NAME)
            print("[pdf_uploader DEBUG] OllamaEmbeddings initialized.")
        except Exception as e:
            print(f"[pdf_uploader ERROR] Failed to initialize OllamaEmbeddings: {e}")
            raise ConnectionError(f"Failed to initialize OllamaEmbeddings for '{EMBEDDINGS_MODEL_NAME}': {e}. Ensure Ollama is running.")
    return embeddings_model_instance

def _upload_pdf_to_storage(pdf_bytes: bytes, filename: str, tenant_id: str = None) -> tuple[str | None, str | None]:
    """
    Upload PDF to Supabase storage bucket in a tenant-specific folder.
    
    Args:
        pdf_bytes (bytes): PDF file bytes
        filename (str): Original filename
        tenant_id (str, optional): Tenant ID for folder organization
        
    Returns:
        tuple[str | None, str | None]: (file_url, error_message)
    """
    try:
        # Use provided tenant_id or default
        current_tenant_id = tenant_id or TENANT_ID
        
        # Generate unique filename to avoid conflicts
        file_extension = os.path.splitext(filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create tenant-specific path
        tenant_folder_path = f"{current_tenant_id}/{unique_filename}"
        
        print(f"[pdf_uploader DEBUG] Uploading {filename} as {unique_filename} to bucket '{STORAGE_BUCKET}' in folder '{current_tenant_id}'")
        
        # Upload file to storage with tenant folder path
        response = supabase.storage.from_(STORAGE_BUCKET).upload(
            path=tenant_folder_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf"}
        )
        
        if hasattr(response, 'error') and response.error:
            return None, f"Storage upload error: {response.error}"
        
        # Get public URL with the full path
        file_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(tenant_folder_path)
        
        print(f"[pdf_uploader DEBUG] Successfully uploaded to: {file_url}")
        return file_url, None
        
    except Exception as e:
        print(f"[pdf_uploader ERROR] Failed to upload PDF to storage: {e}")
        return None, f"Failed to upload PDF to storage: {e}"

def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> tuple[str | None, str | None]:
    """Extracts text from PDF bytes. Returns (text, error_message)."""
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"  
            return (text.strip(), None) if text else (None, "No text found in PDF.")
    except Exception as e:
        return None, f"Error extracting text from PDF bytes: {e}"

def _chunk_text(text: str, source_filename: str) -> list[Document]:
    """
    Split text into chunks using RecursiveCharacterTextSplitter.
    
    Args:
        text (str): The full text to chunk
        source_filename (str): Original PDF filename for metadata
        
    Returns:
        list[Document]: List of Document objects with chunked text and metadata
    """
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Try to split on natural boundaries
    )
    
    # Split the text
    chunks = text_splitter.split_text(text)
    
    # Smart filtering: Keep chunks that are likely valuable even if short
    filtered_chunks = []
    for chunk in chunks:
        chunk_stripped = chunk.strip()
        
        # Skip truly empty chunks
        if not chunk_stripped:
            continue
            
        # Always keep chunks that might be valuable regardless of size
        is_valuable_short_chunk = (
            # Headers or titles (often short but important)
            chunk_stripped.isupper() or
            chunk_stripped.endswith(':') or
            chunk_stripped.startswith('#') or
            # Data points or metrics
            any(char.isdigit() for char in chunk_stripped) or
            # Bullet points or list items
            chunk_stripped.startswith('•') or chunk_stripped.startswith('-') or
            # URLs or references
            'http' in chunk_stripped.lower() or 'www.' in chunk_stripped.lower() or
            # Common important keywords
            any(keyword in chunk_stripped.lower() for keyword in [
                'summary', 'conclusion', 'key', 'important', 'critical', 
                'revenue', 'profit', 'growth', 'result', 'finding'
            ])
        )
        
        # Keep if above minimum size OR if it's a valuable short chunk
        if len(chunk_stripped) >= MIN_CHUNK_SIZE or is_valuable_short_chunk:
            filtered_chunks.append(chunk_stripped)
    
    chunks = filtered_chunks
    
    # Create Document objects with metadata
    documents = []
    for i, chunk in enumerate(chunks):
        doc = Document(
            page_content=chunk,
            metadata={
                "source_filename": source_filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "document_type": "pdf_chunk"
            }
        )
        documents.append(doc)
    
    return documents

def _generate_embeddings_for_chunks(chunks: list[Document]) -> list[list[float]]:
    """
    Generate embeddings for a list of document chunks.
    
    Args:
        chunks (list[Document]): List of document chunks
        
    Returns:
        list[list[float]]: List of embedding vectors
    """
    try:
        embeddings_model = _initialize_embeddings()
        
        # Extract text content from chunks
        texts = [chunk.page_content for chunk in chunks]
        
        print(f"[pdf_uploader DEBUG] Generating embeddings for {len(texts)} chunks")
        
        # Generate embeddings
        embeddings = embeddings_model.embed_documents(texts)
        
        print(f"[pdf_uploader DEBUG] Generated {len(embeddings)} embeddings")
        return embeddings
        
    except Exception as e:
        print(f"[pdf_uploader ERROR] Failed to generate embeddings: {e}")
        raise e

def _insert_chunks_to_database(chunks: list[Document], embeddings: list[list[float]], file_url: str, original_filename: str, tenant_id: str) -> tuple[bool, str]:
    """
    Insert chunks and their embeddings into the internal_documents table.
    
    Args:
        chunks (list[Document]): List of document chunks
        embeddings (list[list[float]]): List of embedding vectors
        file_url (str): URL of the uploaded PDF file
        original_filename (str): Original filename
        tenant_id (str): Tenant ID for the document
        
    Returns:
        tuple[bool, str]: (success, message)
    """
    try:
        print(f"[pdf_uploader DEBUG] Inserting {len(chunks)} chunks into database")
        
        # Prepare data for batch insert
        insert_data = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            row = {
                "tenant_id": tenant_id,
                "file_url": file_url,
                "file_name": original_filename,
                "content": chunk.page_content,
                "embedding": embedding,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "metadata": {
                    "chunk_size": len(chunk.page_content),
                    "document_type": "pdf_chunk",
                }
            }
            insert_data.append(row)
        
        # Insert all chunks in batch
        response = supabase.table("internal_documents").insert(insert_data).execute()
        
        if hasattr(response, 'error') and response.error:
            return False, f"Database insert error: {response.error}"
        
        print(f"[pdf_uploader DEBUG] Successfully inserted {len(insert_data)} chunks into database")
        return True, f"Successfully inserted {len(insert_data)} chunks into database"
        
    except Exception as e:
        print(f"[pdf_uploader ERROR] Failed to insert chunks into database: {e}")
        return False, f"Failed to insert chunks into database: {e}"

def _check_existing_document(filename: str) -> tuple[bool, int]:
    """
    Check if a document with the same filename already exists in the database.
    
    Args:
        filename (str): Original filename to check
        
    Returns:
        tuple[bool, int]: (exists, chunk_count)
    """
    try:
        response = supabase.table("internal_documents").select("id").eq("metadata->>source_filename", filename).execute()
        
        if hasattr(response, 'error') and response.error:
            print(f"[pdf_uploader WARNING] Error checking existing document: {response.error}")
            return False, 0
        
        chunk_count = len(response.data) if response.data else 0
        exists = chunk_count > 0
        
        print(f"[pdf_uploader DEBUG] Document '{filename}' {'exists' if exists else 'does not exist'} with {chunk_count} chunks")
        return exists, chunk_count
        
    except Exception as e:
        print(f"[pdf_uploader WARNING] Could not check for existing document {filename}: {e}")
        return False, 0

def process_and_add_pdf(pdf_bytes: bytes, original_filename: str, tenant_id: str = None) -> tuple[bool, str]:
    """
    Processes an uploaded PDF, extracts text, chunks it, generates embeddings,
    and stores everything in Supabase if the document doesn't already exist.
    
    Args:
        pdf_bytes (bytes): PDF file bytes
        original_filename (str): Original filename
        tenant_id (str, optional): Tenant ID, defaults to TENANT_ID constant
        
    Returns:
        tuple[bool, str]: (success, message)
    """
    # Use provided tenant_id or default
    current_tenant_id = tenant_id or TENANT_ID
    
    # Check if document already exists BEFORE uploading
    exists, existing_chunk_count = _check_existing_document(original_filename)
    if exists:
        return False, f"File '{original_filename}' already exists in the database with {existing_chunk_count} chunks."
    
    # Extract text from PDF first (before uploading to storage)
    text_content, extract_error = _extract_text_from_pdf_bytes(pdf_bytes)
    if extract_error:
        return False, extract_error
    if not text_content:
        return False, "No text content extracted from PDF, nothing to add."
    
    # Chunk the text
    print(f"[pdf_uploader DEBUG] Chunking text from '{original_filename}' (total length: {len(text_content)} chars)")
    chunked_documents = _chunk_text(text_content, original_filename)
    
    if not chunked_documents:
        return False, f"No valid chunks created from '{original_filename}' after text splitting."
    
    print(f"[pdf_uploader DEBUG] Created {len(chunked_documents)} chunks from '{original_filename}'")
    
    # Generate embeddings for all chunks
    try:
        embeddings = _generate_embeddings_for_chunks(chunked_documents)
    except Exception as e:
        return False, f"Failed to generate embeddings: {e}"
    
    # Upload PDF to storage (only after everything else is ready)
    file_url, upload_error = _upload_pdf_to_storage(pdf_bytes, original_filename, current_tenant_id)
    if upload_error:
        return False, upload_error
    
    # Insert chunks and embeddings into database
    success, message = _insert_chunks_to_database(chunked_documents, embeddings, file_url, original_filename, current_tenant_id)
    
    if success:
        return True, f"File '{original_filename}' processed and added to database as {len(chunked_documents)} chunks."
    else:
        return False, message

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.

    Args:
        pdf_path (str): The path to the PDF file.

    Returns:
        str: The extracted text from the PDF, or an error message if extraction fails.
    """
    if not os.path.exists(pdf_path):
        return "Error: PDF file not found."
    if not pdf_path.lower().endswith(".pdf"):
        return "Error: File is not a PDF."

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"  # Add a newline character after each page's text
            return text.strip() if text else "Error: No text found in PDF."
    except Exception as e:
        return f"Error extracting text: {e}"

# Legacy function for compatibility - no longer needed with Supabase
def _initialize_vector_store():
    """Legacy function for compatibility with batch upload script."""
    print("[pdf_uploader DEBUG] Supabase connection ready (no vector store initialization needed)")
    return True

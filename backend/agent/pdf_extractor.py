# MANUALLY CALL TO BATCH INGEST PDFS FROM DIRECTORY

import pdfplumber
import os
import io # For BytesIO
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Constants ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "..", "local_embeddings_db")
PDF_COLLECTION_NAME = "pdf_text_content"
EMBEDDINGS_MODEL_NAME = "nomic-embed-text"

# --- Chunking Configuration ---
CHUNK_SIZE = 1000        # Characters per chunk
CHUNK_OVERLAP = 200      # Overlap between chunks to maintain context
MIN_CHUNK_SIZE = 20      # Much smaller minimum - only filter out truly empty/whitespace chunks

# --- Global Instances (Lazy Initialization) ---
embeddings_model_instance = None
vector_store_instance = None

def _initialize_embeddings():
    global embeddings_model_instance
    if embeddings_model_instance is None:
        try:
            print(f"[pdf_extractor DEBUG] Initializing OllamaEmbeddings model: {EMBEDDINGS_MODEL_NAME}")
            embeddings_model_instance = OllamaEmbeddings(model=EMBEDDINGS_MODEL_NAME)
            print("[pdf_extractor DEBUG] OllamaEmbeddings initialized.")
        except Exception as e:
            print(f"[pdf_extractor ERROR] Failed to initialize OllamaEmbeddings: {e}")
            raise ConnectionError(f"Failed to initialize OllamaEmbeddings for '{EMBEDDINGS_MODEL_NAME}': {e}. Ensure Ollama is running.")
    return embeddings_model_instance

def _initialize_vector_store():
    global vector_store_instance
    if vector_store_instance is None:
        try:
            embeddings = _initialize_embeddings()
            print(f"[pdf_extractor DEBUG] Initializing Chroma vector store. Collection: '{PDF_COLLECTION_NAME}', DB Path: '{DB_PATH}'")
            if not os.path.exists(DB_PATH):
                 os.makedirs(DB_PATH)
                 print(f"[pdf_extractor INFO] Created Chroma DB directory: {DB_PATH}")

            vector_store_instance = Chroma(
                collection_name=PDF_COLLECTION_NAME,
                persist_directory=DB_PATH,
                embedding_function=embeddings
            )
            print("[pdf_extractor DEBUG] Chroma vector store initialized.")
        except Exception as e:
            print(f"[pdf_extractor ERROR] Failed to initialize Chroma vector store at '{DB_PATH}': {e}")
            raise ConnectionError(f"Failed to initialize Chroma vector store at '{DB_PATH}': {e}")
    return vector_store_instance

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

def process_and_add_pdf(pdf_bytes: bytes, original_filename: str) -> tuple[bool, str]:
    """
    Processes an uploaded PDF, extracts text, chunks it, and adds chunks to the Chroma vector store
    if documents with the same filename don't already exist.
    """
    try:
        vector_store = _initialize_vector_store()
    except ConnectionError as e:
        return False, str(e)

    # Sanitize filename for use as ID base
    name_part = original_filename.lower()
    if name_part.endswith(".pdf"):
        name_part = name_part[:-4]
    
    sanitized_name_part = "".join(c if c.isalnum() or c in ['_'] else '_' for c in name_part)
    sanitized_name_part = '_'.join(filter(None, sanitized_name_part.split('_'))) 

    # Check if any chunks from this PDF already exist
    base_doc_id = f"pdf_{sanitized_name_part}"
    
    try:
        print(f"[pdf_extractor DEBUG] Checking for existing documents with base ID: {base_doc_id}")
        # Check for existing chunks (they'll have IDs like pdf_filename_chunk_0, pdf_filename_chunk_1, etc.)
        collection = vector_store._collection
        existing_docs = collection.get(where={"source_filename": original_filename})
        
        if existing_docs and existing_docs.get('ids') and len(existing_docs['ids']) > 0:
            print(f"[pdf_extractor INFO] Found {len(existing_docs['ids'])} existing chunks for '{original_filename}'.")
            return False, f"File '{original_filename}' already exists in the database with {len(existing_docs['ids'])} chunks."
        print(f"[pdf_extractor DEBUG] No existing chunks found for '{original_filename}'. Proceeding to add.")
    except Exception as e:
        print(f"[pdf_extractor WARNING] Could not definitively check for existing chunks for {original_filename} due to: {e}. Proceeding with add attempt.")

    # Extract text from PDF
    text_content, error = _extract_text_from_pdf_bytes(pdf_bytes)
    if error:
        return False, error
    if not text_content: # Handles None or empty string from extraction
        return False, "No text content extracted from PDF, nothing to add."

    # Chunk the text
    print(f"[pdf_extractor DEBUG] Chunking text from '{original_filename}' (total length: {len(text_content)} chars)")
    chunked_documents = _chunk_text(text_content, original_filename)
    
    if not chunked_documents:
        return False, f"No valid chunks created from '{original_filename}' after text splitting."

    print(f"[pdf_extractor DEBUG] Created {len(chunked_documents)} chunks from '{original_filename}'")

    # Generate IDs for each chunk
    chunk_ids = []
    for i, doc in enumerate(chunked_documents):
        chunk_id = f"{base_doc_id}_chunk_{i}"
        chunk_ids.append(chunk_id)
        # Update metadata with the unique chunk ID
        doc.metadata["chunk_id"] = chunk_id

    try:
        print(f"[pdf_extractor DEBUG] Adding {len(chunked_documents)} chunks to vector store.")
        vector_store.add_documents(documents=chunked_documents, ids=chunk_ids)
        print(f"[pdf_extractor INFO] Successfully added {len(chunked_documents)} chunks from '{original_filename}' to database.")
    
        return True, f"File '{original_filename}' processed and added to database as {len(chunked_documents)} chunks."
    except Exception as e:
        print(f"[pdf_extractor ERROR] Error adding chunks from '{original_filename}': {e}")
        return False, f"Error adding document chunks for '{original_filename}' to vector store: {e}"

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

def batch_ingest_pdfs_from_directory(pdf_directory_path: str):
    """
    Process all PDF files in the given directory, chunk them, and add chunks to the vector database.
    
    Args:
        pdf_directory_path (str): Path to the directory containing PDF files
    """
    print(f"🚀 Starting PDF batch ingestion with chunking from: {pdf_directory_path}")
    print(f"📐 Chunk settings: {CHUNK_SIZE} chars/chunk, {CHUNK_OVERLAP} chars overlap, {MIN_CHUNK_SIZE} chars minimum")
    print("=" * 80)
    
    # Check if directory exists
    if not os.path.exists(pdf_directory_path):
        print(f"❌ Error: Directory '{pdf_directory_path}' does not exist.")
        return
    
    if not os.path.isdir(pdf_directory_path):
        print(f"❌ Error: '{pdf_directory_path}' is not a directory.")
        return
    
    # Initialize vector store first
    try:
        print("🔧 Initializing vector store...")
        vector_store = _initialize_vector_store()
        print("✅ Vector store initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        return
    
    # Find all PDF files
    pdf_files = []
    for file in os.listdir(pdf_directory_path):
        if file.lower().endswith('.pdf'):
            pdf_files.append(file)
    
    if not pdf_files:
        print(f"📄 No PDF files found in '{pdf_directory_path}'")
        return
    
    print(f"📚 Found {len(pdf_files)} PDF files to process:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    print()
    
    # Process each PDF file - enhanced tracking
    successful_count = 0
    skipped_count = 0
    failed_count = 0
    total_chunks_created = 0
    total_chunks_skipped = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        full_path = os.path.join(pdf_directory_path, pdf_file)
        print(f"📄 Processing [{i}/{len(pdf_files)}]: {pdf_file}")
        
        try:
            # Read PDF file as bytes
            with open(full_path, 'rb') as f:
                pdf_bytes = f.read()
            
            # Process and add to vector database (with chunking)
            success, message = process_and_add_pdf(pdf_bytes, pdf_file)
            
            if success:
                print(f"   ✅ SUCCESS: {message}")
                successful_count += 1
                # Extract chunk count from success message
                if "chunks" in message:
                    try:
                        chunk_count = int(message.split("as ")[1].split(" chunks")[0])
                        total_chunks_created += chunk_count
                    except:
                        pass  # If parsing fails, just continue
            else:
                if "already exists" in message:
                    print(f"   ⏭️  SKIPPED: {message}")
                    skipped_count += 1
                    # Extract chunk count from skip message for existing files
                    if "chunks" in message:
                        try:
                            chunk_count = int(message.split("with ")[1].split(" chunks")[0])
                            total_chunks_skipped += chunk_count
                        except:
                            pass
                else:
                    print(f"   ❌ FAILED: {message}")
                    failed_count += 1
                    
        except Exception as e:
            print(f"   ❌ ERROR: Failed to process {pdf_file}: {e}")
            failed_count += 1
        
        print()  # Add spacing between files
    
    # Enhanced summary with chunking statistics
    print("=" * 80)
    print("📊 BATCH INGESTION SUMMARY WITH CHUNKING")
    print(f"   📁 Total files processed: {len(pdf_files)}")
    print(f"   ✅ Successfully added: {successful_count} files")
    print(f"   ⏭️  Skipped (already exist): {skipped_count} files")
    print(f"   ❌ Failed: {failed_count} files")
    print("   " + "─" * 40)
    print(f"   🧩 Total chunks created: {total_chunks_created}")
    if total_chunks_skipped > 0:
        print(f"   📦 Total chunks skipped: {total_chunks_skipped}")
    print(f"   📈 Average chunks per successful file: {total_chunks_created / max(successful_count, 1):.1f}")
    print(f"   📐 Chunk configuration: {CHUNK_SIZE} chars, {CHUNK_OVERLAP} overlap")
    print("=" * 80)


if __name__ == '__main__':
    print("📁 PDF Extractor - Batch Processing Mode")
    print("=" * 50)
    
    # Interactive mode for batch processing
    print("\nBatch PDF Ingestion Options:")
    print("1. Use default directory (backend/pdfs)")
    print("2. Specify custom directory")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '3':
        print("👋 Exiting...")
        exit(0)
    elif choice == '1':
        # Default directory
        pdf_directory = os.path.join(SCRIPT_DIR, "..", "pdfs")
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)
            print(f"📁 Created default directory: {pdf_directory}")
        print(f"🎯 Using default directory: {pdf_directory}")
    elif choice == '2':
        # Custom directory
        pdf_directory = input("Enter PDF directory path: ").strip()
        if not pdf_directory:
            print("❌ No directory specified. Exiting...")
            exit(1)
        print(f"🎯 Using custom directory: {pdf_directory}")
    else:
        print("❌ Invalid choice. Exiting...")
        exit(1)
    
    # Confirm before proceeding
    confirmation = input(f"\nProceed with batch ingestion from '{pdf_directory}'? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("❌ Cancelled by user.")
        exit(0)
    
    # Start batch ingestion
    batch_ingest_pdfs_from_directory(pdf_directory)
    print("\n✨ Batch ingestion complete!")

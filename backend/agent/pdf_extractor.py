import pdfplumber
import os
import io # For BytesIO
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# --- Constants ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "..", "mcpserver", "local_embeddings_db")
PDF_COLLECTION_NAME = "pdf_text_content"
EMBEDDINGS_MODEL_NAME = "nomic-embed-text"

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

def process_and_add_pdf(pdf_bytes: bytes, original_filename: str) -> tuple[bool, str]:
    """
    Processes an uploaded PDF, extracts text, and adds it to the Chroma vector store
    if a document with the same filename doesn't already exist.
    """
    try:
        vector_store = _initialize_vector_store()
    except ConnectionError as e:
        return False, str(e)

    # Sanitize filename for use as ID
    name_part = original_filename.lower()
    if name_part.endswith(".pdf"):
        name_part = name_part[:-4]
    
    sanitized_name_part = "".join(c if c.isalnum() or c in ['_'] else '_' for c in name_part)
    sanitized_name_part = '_'.join(filter(None, sanitized_name_part.split('_'))) 

    doc_id = f"pdf_{sanitized_name_part}"

    try:
        print(f"[pdf_extractor DEBUG] Checking for existing document with ID: {doc_id}")
        existing_docs = vector_store.get(ids=[doc_id])
        if existing_docs and existing_docs.get('ids') and doc_id in existing_docs['ids']:
            print(f"[pdf_extractor INFO] Document ID '{doc_id}' already exists.")
            return False, f"File '{original_filename}' (ID: {doc_id}) already exists in the database."
        print(f"[pdf_extractor DEBUG] Document ID '{doc_id}' does not exist. Proceeding to add.")
    except Exception as e:
        print(f"[pdf_extractor WARNING] Could not definitively check for existing doc ID {doc_id} due to: {e}. Proceeding with add attempt.")

    text_content, error = _extract_text_from_pdf_bytes(pdf_bytes)
    if error:
        return False, error
    if not text_content: # Handles None or empty string from extraction
        return False, "No text content extracted from PDF, nothing to add."

    doc = Document(
        page_content=text_content,
        metadata={"source_filename": original_filename, "id": doc_id}
    )

    try:
        print(f"[pdf_extractor DEBUG] Adding document ID '{doc_id}' to vector store.")
        vector_store.add_documents(documents=[doc], ids=[doc_id])
        print(f"[pdf_extractor INFO] Document ID '{doc_id}' added successfully.")
    
        return True, f"File '{original_filename}' processed and added to database with ID '{doc_id}'."
    except Exception as e:
        print(f"[pdf_extractor ERROR] Error adding document ID '{doc_id}': {e}")
        return False, f"Error adding document for '{original_filename}' to vector store: {e}"

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


"""
if __name__ == '__main__':
    # Define the directory for PDFs, relative to this script file
    script_current_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjusted path: Go up one level from agent to backend, then to pdfs
    pdf_dir = os.path.join(script_current_dir, "..", "pdfs") # Assuming pdfs is at backend/pdfs

    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
        print(f"Created directory: {pdf_dir}")
    elif not os.path.isdir(pdf_dir):
        print(f"Error: '{pdf_dir}' exists but is not a directory. Please check the path.")
        exit(1)

    print("\n--- PDF to Vector DB Ingestion Script (Standalone) ---")
    
    # This part needs to use _initialize_vector_store() and then iterate
    # For each file, convert to bytes and call process_and_add_pdf
    # Or adapt process_and_add_pdf to also accept a file path for standalone use.

    # Example of how it might be adapted:
    try:
        vector_store = _initialize_vector_store() # Ensure DB and collection are ready
        print("Vector store initialized for standalone script.")
    except ConnectionError as e:
        print(f"Failed to initialize vector store for standalone script: {e}")
        exit(1)

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in '{pdf_dir}'.")
    else:
        print(f"Found {len(pdf_files)} PDF files in '{pdf_dir}'. Processing...")
        for pdf_file_name in pdf_files:
            full_pdf_path = os.path.join(pdf_dir, pdf_file_name)
            print(f"Processing (standalone): {pdf_file_name}...")
            try:
                with open(full_pdf_path, 'rb') as f:
                    pdf_bytes_content = f.read()
                success, message = process_and_add_pdf(pdf_bytes_content, pdf_file_name)
                if success:
                    print(f"  SUCCESS: {message}")
                else:
                    print(f"  FAILURE/SKIP: {message}")
            except Exception as e_file:
                print(f"  ERROR processing file {pdf_file_name}: {e_file}")

    print("\n--- PDF to Vector DB Ingestion Script Finished (Standalone) ---")
"""

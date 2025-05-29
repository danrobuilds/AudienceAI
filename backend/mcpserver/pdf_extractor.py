import pdfplumber
import os
# csv import will be removed as it's no longer used
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

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

if __name__ == '__main__':
    # Define the directory for PDFs, relative to this script file
    script_current_dir = os.path.dirname(os.path.abspath(__file__))
    # Adjusted path: Go up one level from mcpserver to backend, then to pdfs
    pdf_dir = os.path.join(script_current_dir, "..", "pdfs")

    if not os.path.exists(pdf_dir):
        os.makedirs(pdf_dir)
        print(f"Created directory: {pdf_dir}")
    elif not os.path.isdir(pdf_dir):
        print(f"Error: '{pdf_dir}' exists but is not a directory. Please check the path.")
        exit(1)

    print("\n--- PDF to Vector DB Ingestion Script ---")

    # --- Vector DB Setup ---
    # DB_LOCATION points to backend/mcpserver/local_embeddings_db
    # Adjusted path: Directly into local_embeddings_db from mcpserver
    db_path = os.path.join(script_current_dir, "local_embeddings_db")
    
    try:
        embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
    except Exception as e:
        print(f"Error initializing OllamaEmbeddings: {e}")
        print("Please ensure Ollama is running and the 'nomic-embed-text' model is available.")
        exit(1)
        
    pdf_collection_name = "pdf_text_content" 

    try:
        vector_store = Chroma(
            collection_name=pdf_collection_name,
            persist_directory=db_path,
            embedding_function=embeddings_model
        )
        print(f"Initialized vector store. Collection: '{pdf_collection_name}', DB Path: '{db_path}'")
    except Exception as e:
        print(f"Error initializing Chroma vector store: {e}")
        print(f"Please check the path '{db_path}' and permissions.")
        exit(1)

    # --- PDF Processing and Document Creation ---
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
    
    documents_to_add = []
    document_ids = []

    if not pdf_files:
        print(f"No PDF files found in '{pdf_dir}'.")
    else:
        print(f"Found {len(pdf_files)} PDF files in '{pdf_dir}'. Processing...")
        for pdf_file_name in pdf_files:
            full_pdf_path = os.path.join(pdf_dir, pdf_file_name)
            print(f"Processing: {pdf_file_name}...")
            text_content = extract_text_from_pdf(full_pdf_path)

            if text_content.startswith("Error:"):
                print(f"  Failed to extract text: {text_content}")
            else:
                doc = Document(
                    page_content=text_content,
                    metadata={"source_filename": pdf_file_name, "original_path": full_pdf_path}
                )
                documents_to_add.append(doc)
                # Sanitize filename for use as ID (lowercase, replace spaces)
                sanitized_filename = pdf_file_name.lower().replace(' ', '_')
                doc_id = f"pdf_{sanitized_filename}"
                document_ids.append(doc_id)
                print(f"  Successfully extracted text. Prepared document with ID: {doc_id}")

        # --- Add Documents to Vector Store (Upsert based on ID) ---
        if documents_to_add:
            print(f"\nAdding/updating {len(documents_to_add)} documents in vector store collection '{pdf_collection_name}'...")
            try:
                vector_store.add_documents(documents=documents_to_add, ids=document_ids)
                # Chroma with a persist_directory typically auto-persists on add/update.
                # If not, an explicit vector_store.persist() might be needed for some Chroma versions.
                print("Successfully added/updated documents to the vector store.")
            except Exception as e:
                print(f"Error adding documents to vector store: {e}")
        elif pdf_files: # If there were PDF files but none yielded valid documents
            print("No valid documents were extracted from the PDFs to add to the vector store.")
        # If no pdf_files, the earlier message "No PDF files found..." is sufficient.


    print("\n--- PDF to Vector DB Ingestion Script Finished ---")

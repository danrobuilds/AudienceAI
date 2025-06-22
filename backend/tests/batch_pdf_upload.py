#!/usr/bin/env python3
"""
Batch PDF Upload Utility

This script provides functionality to batch process PDF files from directories
and upload them to the vector database using the main pdf_uploader module.
"""

import os
import sys

# Add the parent directory to the path so we can import from infra
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from infra.pdf_uploader import process_and_add_pdf, _initialize_vector_store

def batch_ingest_pdfs_from_directory(pdf_directory_path: str):
    """
    Process all PDF files in the given directory, chunk them, and add chunks to the vector database.
    
    Args:
        pdf_directory_path (str): Path to the directory containing PDF files
    """
    print(f"🚀 Starting PDF batch ingestion with chunking from: {pdf_directory_path}")
    print(f"📐 Chunk settings: Using default settings from pdf_uploader module")
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
        print("🔧 Initializing Supabase connection...")
        vector_store = _initialize_vector_store()
        print("✅ Supabase connection initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase connection: {e}")
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
    print("=" * 80)


def main():
    """Interactive CLI for batch PDF processing."""
    print("📁 PDF Uploader - Batch Processing Mode (Supabase)")
    print("=" * 50)
    
    # Get the script directory for default paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)  # Go up one level from tests to backend
    
    # Interactive mode for batch processing
    print("\nBatch PDF Ingestion Options:")
    print("1. Use default directory (backend/pdfs)")
    print("2. Specify custom directory")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == '3':
        print("👋 Exiting...")
        return
    elif choice == '1':
        # Default directory
        pdf_directory = os.path.join(backend_dir, "pdfs")
        if not os.path.exists(pdf_directory):
            os.makedirs(pdf_directory)
            print(f"📁 Created default directory: {pdf_directory}")
        print(f"🎯 Using default directory: {pdf_directory}")
    elif choice == '2':
        # Custom directory
        pdf_directory = input("Enter PDF directory path: ").strip()
        if not pdf_directory:
            print("❌ No directory specified. Exiting...")
            return
        print(f"🎯 Using custom directory: {pdf_directory}")
    else:
        print("❌ Invalid choice. Exiting...")
        return
    
    # Confirm before proceeding
    confirmation = input(f"\nProceed with batch ingestion from '{pdf_directory}'? (y/N): ").strip().lower()
    if confirmation not in ['y', 'yes']:
        print("❌ Cancelled by user.")
        return
    
    # Start batch ingestion
    batch_ingest_pdfs_from_directory(pdf_directory)
    print("\n✨ Batch ingestion complete!")


if __name__ == '__main__':
    main() 
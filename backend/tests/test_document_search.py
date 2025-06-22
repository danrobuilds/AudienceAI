#!/usr/bin/env python3
"""
Test script for the document library search functionality.
This script allows you to:
1. Search the document library with custom queries
2. View all available documents in the collection
3. Test the search functionality outside of the MCP server
"""

import os
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../.env")

# Set up paths (same as server.py)
SERVER_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_LOCATION = os.path.join(SERVER_SCRIPT_DIR, "..", "local_embeddings_db")

def initialize_embeddings():
    """Initialize the embeddings model"""
    try:
        embeddings = OllamaEmbeddings(model="nomic-embed-text")
        print("✅ Successfully initialized OllamaEmbeddings")
        return embeddings
    except Exception as e:
        print(f"❌ Failed to initialize OllamaEmbeddings: {e}")
        print("Make sure Ollama is running and 'nomic-embed-text' model is available")
        return None

def get_vector_store(embeddings):
    """Get the vector store instance"""
    try:
        vector_store = Chroma(
            collection_name="pdf_text_content",
            persist_directory=DB_LOCATION,
            embedding_function=embeddings
        )
        print("✅ Successfully connected to vector store")
        return vector_store
    except Exception as e:
        print(f"❌ Failed to connect to vector store: {e}")
        return None

def search_documents(vector_store, query, k=5):
    """Search documents with a query"""
    try:
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        results = retriever.invoke(query)
        return results
    except Exception as e:
        print(f"❌ Error searching documents: {e}")
        return []

def show_all_documents(vector_store):
    """Show all documents in the collection"""
    try:
        # Get the collection to see how many documents we have
        collection = vector_store._collection
        count = collection.count()
        print(f"\n📚 Total documents in collection: {count}")
        
        if count == 0:
            print("No documents found in the collection.")
            return
            
        # Get all documents (limit to first 20 for readability)
        limit = min(20, count)
        results = collection.get(limit=limit, include=['documents', 'metadatas'])
        
        print(f"\n📄 Showing first {limit} documents:")
        print("=" * 80)
        
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            print(f"\nDocument {i+1}:")
            if metadata and metadata.get('source_filename'):
                print(f"  Source: {metadata['source_filename']}")
            print(f"  Content (first 200 chars): {doc[:200]}...")
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error retrieving all documents: {e}")

def interactive_search(vector_store):
    """Interactive search mode"""
    print("\n🔍 Interactive Search Mode")
    print("Type your search queries (or 'quit' to exit)")
    print("=" * 50)
    
    while True:
        query = input("\nEnter search query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
            
        if not query:
            continue
            
        print(f"\nSearching for: '{query}'")
        results = search_documents(vector_store, query)
        
        if not results:
            print("No relevant documents found.")
            continue
            
        print(f"\n📋 Found {len(results)} relevant documents:")
        print("=" * 60)
        
        for i, doc in enumerate(results):
            print(f"\nResult {i+1}:")
            if doc.metadata and doc.metadata.get('source_filename'):
                print(f"  📄 Source: {doc.metadata['source_filename']}")
            print(f"  📝 Content: {doc.page_content}")
            print("-" * 40)

def main():
    print("🚀 Document Library Test Script")
    print("=" * 50)
    
    # Initialize embeddings
    embeddings = initialize_embeddings()
    if not embeddings:
        return
    
    # Get vector store
    vector_store = get_vector_store(embeddings)
    if not vector_store:
        return
    
    # Show menu
    while True:
        print("\n📋 Choose an option:")
        print("1. Show all documents in collection")
        print("2. Interactive search mode")
        print("3. Quick test search")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            show_all_documents(vector_store)
        elif choice == '2':
            interactive_search(vector_store)
        elif choice == '3':
            # Quick test searches
            test_queries = [
                "artificial intelligence",
                "machine learning", 
                "data analysis",
                "marketing strategy"
            ]
            
            print("\n🧪 Running quick test searches...")
            for query in test_queries:
                print(f"\n🔍 Testing query: '{query}'")
                results = search_documents(vector_store, query, k=2)
                print(f"   Found {len(results)} results")
                if results:
                    for i, doc in enumerate(results[:1]):  # Show just the top result
                        source = doc.metadata.get('source_filename', 'Unknown') if doc.metadata else 'Unknown'
                        content_preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                        print(f"   Top result from {source}: {content_preview}")
        elif choice == '4':
            break
        else:
            print("Invalid choice. Please enter 1-4.")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main() 
import os
import pandas as pd
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


# Determine the absolute path to the directory where vector.py is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Assume influencers_data_filtered.csv is one level up from the agent directory (in backend)
CSV_PATH = os.path.join(SCRIPT_DIR, "..", "influencers_data_filtered.csv")
# Place the Chroma DB in the backend directory (one level up from agent)
DB_LOCATION = os.path.join(SCRIPT_DIR, "..", "local_embeddings_db")


df = pd.read_csv(CSV_PATH)

embeddings = OllamaEmbeddings(model="nomic-embed-text")

# This Chroma instance is primarily for the initial data loading.
# Querying will be handled by instances created directly in server.py tools.
initial_vector_store_setup = Chroma(
    collection_name = "viral_post_data",
    persist_directory=DB_LOCATION,
    embedding_function=embeddings
)

# Check if database exists and has documents for the viral_post_data collection
embeddings_db_exists = os.path.exists(DB_LOCATION)
collection_has_documents = False

if embeddings_db_exists:
    try:
        # Check count on the specific collection we are about to populate
        temp_store_check = Chroma(
            collection_name="viral_post_data", 
            persist_directory=DB_LOCATION,
            embedding_function=embeddings
        )
        collection_has_documents = temp_store_check._collection.count() > 0
    except Exception as e:
        print(f"Could not check document count for viral_post_data: {e}")
        collection_has_documents = False # Assume not populated if check fails

if not embeddings_db_exists or not collection_has_documents:
    print(f"Database at '{DB_LOCATION}' for collection 'viral_post_data' does not exist or is empty.")
    print("Proceeding with initial data population from CSV...")
    documents = []
    ids = []

    for i, row in df.iterrows():
        # Combine relevant content for embedding
        page_content_parts = []
        
        # Add headline if available
        if pd.notna(row["headline"]) and row["headline"]:
            page_content_parts.append(f"Headline: {row['headline']}")
        
        # Add location if available
        if pd.notna(row["location"]) and row["location"]:
            page_content_parts.append(f"Location: {row['location']}")
        
        # Add about section if available
        if pd.notna(row["about"]) and row["about"]:
            page_content_parts.append(f"About: {row['about']}")
        
        # Add main content if available
        if pd.notna(row["content"]) and row["content"]:
            page_content_parts.append(f"Content: {row['content']}")
        
        # Add hashtags if available
        if pd.notna(row["hashtags"]) and row["hashtags"]:
            page_content_parts.append(f"Hashtags: {row['hashtags']}")
        
        # Combine all parts
        page_content = "\n\n".join(page_content_parts)
        
        # Create metadata with engagement metrics
        metadata = {
            "source": row["name"] if pd.notna(row["name"]) else "Unknown",
            "views": row["views"] if pd.notna(row["views"]) else 0,
            "comments": row["comments"] if pd.notna(row["comments"]) else 0,
            "reactions": row["reactions"] if pd.notna(row["reactions"]) else 0,
            "followers": row["followers"] if pd.notna(row["followers"]) else 0,
            "time_spent": row["time_spent"] if pd.notna(row["time_spent"]) else "",
            "media_type": row["media_type"] if pd.notna(row["media_type"]) else ""
        }
        
        document = Document(
            page_content=page_content,
            metadata=metadata
        )
        documents.append(document)
        ids.append(str(i))
    
    print(f"Finished preparing all {len(documents)} documents")


if not embeddings_db_exists or not collection_has_documents:
    print(f"Creating embeddings for {len(documents)} documents...")
    print("This may take a few minutes...")
    
    # Add documents in batches to show progress
    batch_size = 50
    total_docs = len(documents)
    
    for i in range(0, total_docs, batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        print(f"Processing batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size} ({i+1}-{min(i+batch_size, total_docs)}/{total_docs})")
        
        initial_vector_store_setup.add_documents(documents=batch_docs, ids=batch_ids)
    
    print(f"Successfully added all {len(documents)} documents to vector store for 'viral_post_data'")




# Retrievers are no longer defined here; they are created on-demand in server.py tools.
# retriever = vector_store.as_retriever(
#     search_kwargs={"k": 10}
# )

# # --- Retriever for PDF Text Content ---
# # Use the same embedding function and DB location, but a different collection name
# pdf_collection_name = "pdf_text_content"
# 
# pdf_vector_store = Chroma(
#     collection_name=pdf_collection_name,
#     persist_directory=DB_LOCATION,
#     embedding_function=embeddings
# )
# 
# pdf_content_retriever = pdf_vector_store.as_retriever(
#     search_kwargs={"k": 5} # Retrieve top 5 relevant PDF chunks
# )


# input_prompt = input("prompt: ")

# result = retriever.invoke(input_prompt)

# print(f"Query: {input_prompt}")
# print(f"Number of results: {len(result)}")
# print("="*80)

# for i, doc in enumerate(result):
#     print(f"\nResult {i+1}:")
#     print("-" * 40)
#     print("FULL CONTENT:")
#     print(doc.page_content)
#     print("-" * 40)
#     print("METADATA:")
#     for key, value in doc.metadata.items():
#         print(f"  {key}: {value}")
#     print("="*80) 
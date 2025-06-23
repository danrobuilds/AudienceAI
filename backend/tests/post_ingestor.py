import os
import pandas as pd
from langchain_nomic import NomicEmbeddings
import sys

# Add the parent directory to the path to import services
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.supabase_service import supabase

# Determine the absolute path to the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# The CSV file is in the same directory as this script
CSV_PATH = os.path.join(SCRIPT_DIR, "influencers_data_filtered.csv")

# Load the CSV data
df = pd.read_csv(CSV_PATH)

# Initialize embeddings model with Nomic remote API
print("Initializing NomicEmbeddings with remote API...")
try:
    embeddings = NomicEmbeddings(
        model="nomic-embed-text-v1.5",
        inference_mode="remote",  # Use remote API
        dimensionality=768,  # Full dimensionality for best performance
        # The API key should be set as NOMIC_API_KEY environment variable
    )
    print("Successfully initialized NomicEmbeddings with remote API")
except Exception as e:
    print(f"CRITICAL: Failed to initialize NomicEmbeddings: {e}")
    print("Ensure NOMIC_API_KEY is set in your environment variables.")
    print("Get your API key from https://atlas.nomic.ai/")
    raise e

# Check if viral_content table already has data
print("Checking if viral_content table has existing data...")
try:
    existing_data = supabase.table('viral_content').select('id').limit(1).execute()
    table_has_data = len(existing_data.data) > 0
except Exception as e:
    print(f"Could not check existing data: {e}")
    table_has_data = False

if not table_has_data:
    print("Table is empty or doesn't exist. Proceeding with data upload...")
    
    # Process the CSV data
    posts_to_insert = []
    
    for i, row in df.iterrows():
        # Combine relevant content for embedding and storage
        content_parts = []
        
        # Add headline if available
        if pd.notna(row["headline"]) and row["headline"]:
            content_parts.append(f"Headline: {row['headline']}")
        
        # Add location if available
        if pd.notna(row["location"]) and row["location"]:
            content_parts.append(f"Location: {row['location']}")
        
        # Add about section if available
        if pd.notna(row["about"]) and row["about"]:
            content_parts.append(f"About: {row['about']}")
        
        # Add main content if available
        if pd.notna(row["content"]) and row["content"]:
            content_parts.append(f"Content: {row['content']}")
        
        # Add hashtags if available
        if pd.notna(row["hashtags"]) and row["hashtags"]:
            content_parts.append(f"Hashtags: {row['hashtags']}")
        
        # Combine all parts
        full_content = "\n\n".join(content_parts)
        
        # Calculate total interactions (views + comments + reactions)
        views = int(row["views"]) if pd.notna(row["views"]) else 0
        comments = int(row["comments"]) if pd.notna(row["comments"]) else 0
        reactions = int(row["reactions"]) if pd.notna(row["reactions"]) else 0
        total_interactions = views + comments + reactions
        
        # Generate embedding for the content
        print(f"Generating embedding for post {i+1}/{len(df)}...")
        embedding_vector = embeddings.embed_query(full_content)
        
        # Prepare post data for Supabase
        post_data = {
            "type": "linkedin",
            "content": full_content,
            "interactions": total_interactions,
            "embedding": embedding_vector,
            # Additional metadata as JSON
            "metadata": {
                "source": row["name"] if pd.notna(row["name"]) else "Unknown",
                "views": views,
                "comments": comments,
                "reactions": reactions,
                "followers": int(row["followers"]) if pd.notna(row["followers"]) else 0,
                "time_spent": row["time_spent"] if pd.notna(row["time_spent"]) else "",
                "media_type": row["media_type"] if pd.notna(row["media_type"]) else ""
            }
        }
        
        posts_to_insert.append(post_data)
    
    print(f"Finished preparing all {len(posts_to_insert)} posts")
    
    # Insert posts into Supabase in batches
    batch_size = 50
    total_posts = len(posts_to_insert)
    
    for i in range(0, total_posts, batch_size):
        batch_posts = posts_to_insert[i:i+batch_size]
        
        print(f"Uploading batch {i//batch_size + 1}/{(total_posts + batch_size - 1)//batch_size} ({i+1}-{min(i+batch_size, total_posts)}/{total_posts})")
        
        try:
            result = supabase.table('viral_content').insert(batch_posts).execute()
            print(f"Successfully uploaded batch of {len(batch_posts)} posts")
        except Exception as e:
            print(f"Error uploading batch: {e}")
            break
    
    print(f"Successfully uploaded all {len(posts_to_insert)} posts to Supabase viral_content table")

else:
    print("viral_content table already has data. Skipping upload.")
    print("Delete existing data if you want to re-upload.")




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
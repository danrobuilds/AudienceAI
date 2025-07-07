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

# Process the CSV data (always append posts)
print("Processing CSV data for upload...")
posts_to_insert = []

for i, row in df.iterrows():
    # Combine relevant content for embedding and storage
    content_parts = []
    
    # Add target audience if available
    if pd.notna(row["target_audience"]) and row["target_audience"]:
        content_parts.append(f"Target Audience: {row['target_audience']}")
    
    # Add main content if available
    if pd.notna(row["content"]) and row["content"]:
        content_parts.append(f"Content: {row['content']}")
    
    # Add metadata description if available
    if pd.notna(row["media_description"]) and row["media_description"]:
        content_parts.append(f"Media Description: {row['media_description']}")
    
    # Combine all parts
    full_content = "\n\n".join(content_parts)
    
    # Generate embedding for the content
    print(f"Generating embedding for post {i+1}/{len(df)}...")
    embedding_vector = embeddings.embed_query(full_content)
    
    # Prepare post data for Supabase
    post_data = {
        "type": "linkedin",
        "content": row["content"] if pd.notna(row["content"]) else "",
        "embedding": embedding_vector,
        "target_audience": row["target_audience"] if pd.notna(row["target_audience"]) else "",
        "media_description": row["media_description"] if pd.notna(row["media_description"]) else "",
        "content_url": row["content_url"] if pd.notna(row["content_url"]) else "",
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
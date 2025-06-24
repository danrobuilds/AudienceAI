import os
from dotenv import load_dotenv
from langchain_nomic import NomicEmbeddings

load_dotenv()

# Initialize embeddings model once
try:
    # Use Nomic's remote API instead of local Ollama
    shared_embeddings = NomicEmbeddings(
        model="nomic-embed-text-v1.5",
        inference_mode="remote",  # Use remote API
        dimensionality=768,  # Full dimensionality for best performance
        # The API key should be set as NOMIC_API_KEY environment variable
    )
    print("Successfully initialized NomicEmbeddings with remote API")
except Exception as e:
    print(f"CRITICAL: Failed to initialize NomicEmbeddings in embeddings_service.py: {e}")
    print("Ensure NOMIC_API_KEY is set in your environment variables.")
    print("Get your API key from https://atlas.nomic.ai/")
    # Depending on desired behavior, you might exit or disable tools that need embeddings
    shared_embeddings = None # Set to None so tools can check and fail gracefully 
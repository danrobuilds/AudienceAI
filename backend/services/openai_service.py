import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

def initialize_llm():
    """Initialize and return the LLM instance with proper configuration."""
    return ChatOpenAI(
        model="o3", 
        request_timeout=120.0, 
        
        model_kwargs={"response_format": {"type": "text"}}
    ) 
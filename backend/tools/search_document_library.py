import os
from services.embeddings_service import shared_embeddings
from services.supabase_service import supabase

# Search the internal PDF document library using Supabase vector similarity search.

def search_document_library(query: str, tenant_id: str = "") -> dict:
    

    print(f"Tool: Searching document library with query: '{query}' for tenant: '{tenant_id}'")
    
    if shared_embeddings is None:
        return {"error": "Embeddings model not available for document library search."}
    
    if supabase is None:
        return {"error": "Supabase client not available for document library search."}
    
    try:
        # Generate embedding for the query
        query_embedding = shared_embeddings.embed_query(query)
        
        # Use specific RPC function for document search with tenant filtering
        response = supabase.rpc(
            'search_internal_documents', 
            {
                'query_embedding': query_embedding,
                'match_count': 3,
                'input_tenant_id': tenant_id
            }
        ).execute()
        
        if not response.data:
            return {"error": "No relevant documents found in the library for this topic."}
        
        document_segments = []
        source_files = set()
        
        for i, doc in enumerate(response.data[:5]): 
            filename = doc.get('file_name', doc.get('source_filename', 'Unknown file'))
            document_id = doc.get('document_id')
            tenant_id = doc.get('tenant_id')
            similarity = doc.get('similarity', 0)
            content = doc.get('content', 'No content available')
            
            # Add to source files set
            source_files.add(filename)
            
            # Generate signed URL
            document_url = None
            url_error = None
            if document_id and tenant_id:
                try:
                    signed_url, error = generate_signed_url_for_document(
                        document_uuid=document_id,
                        tenant_id=tenant_id,
                        filename=filename,
                        expiry_seconds=3600
                    )
                    
                    if signed_url:
                        document_url = signed_url
                        print(f"Generated signed URL for {filename}")
                    else:
                        url_error = error
                        print(f"[WARNING] Failed to generate signed URL for {filename}: {error}")
                        
                except Exception as e:
                    url_error = f"Error generating URL: {str(e)}"
                    print(f"[WARNING] Could not generate signed URL for {filename}: {e}")
            else:
                url_error = "Missing document metadata"
            
            # Build document segment
            segment = {
                "segment_number": i + 1,
                "filename": filename,
                "similarity_score": similarity,
                "content": content,
                "document_url": document_url,
                "url_error": url_error if not document_url else None,
                "document_id": document_id,
                "tenant_id": tenant_id
            }
            
            document_segments.append(segment)
        
        return {
            "success": True,
            "query": query,
            "total_segments": len(document_segments),
            "source_files": sorted(list(source_files)),
            "document_segments": document_segments
        }

    except Exception as e:
        print(f"Error in search_document_library tool: {e}")
        return {"error": f"Error retrieving documents from library: {str(e)}"} 
    


def generate_signed_url_for_document(document_uuid: str, tenant_id: str, filename: str, expiry_seconds: int = 3600) -> tuple[str | None, str | None]:
    """ Generate a signed URL for a document using its UUID """

    try:
        # Construct storage path
        file_extension = os.path.splitext(filename)[1]
        storage_path = f"{tenant_id}/{document_uuid}{file_extension}"
        
        # Storage configuration for signed URL generation
        STORAGE_BUCKET = "files"
        
        response = supabase.storage.from_(STORAGE_BUCKET).create_signed_url(
            path=storage_path,
            expires_in=expiry_seconds
        )
        
        if hasattr(response, 'error') and response.error:
            return None, f"Failed to create signed URL: {response.error}"
        
        # Extract the signed URL from the response
        signed_url = response.get('signedURL') if hasattr(response, 'get') else response
        
        return signed_url, None
        
    except Exception as e:
        return None, f"Failed to generate signed URL: {e}"
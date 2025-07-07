from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import io
import uuid
from pydantic import BaseModel
from infra.pdf_uploader import process_and_add_pdf

router = APIRouter()

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    chunks_created: Optional[int] = None

class DocumentListResponse(BaseModel):
    documents: List[dict]
    total_count: int


@router.post("/upload-multiple", response_model=List[DocumentUploadResponse])
async def upload_multiple_documents(files: List[UploadFile] = File(...), tenant_id: str = Form(...)):
    """
    Upload and process multiple PDF documents.
    """

    try:
        uuid.UUID(tenant_id.strip())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant ID format. Must be a valid UUID."
        )
        
    
    if len(files) > 10:  # Limit batch uploads
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 10 files allowed per batch upload"
        )
    
    results = []
    
    for file in files:
        try:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                results.append(DocumentUploadResponse(
                    success=False,
                    message="Only PDF files are supported",
                    filename=file.filename
                ))
                continue
            
            # Read file content
            file_content = await file.read()
            
            # Validate file size
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            if len(file_content) > MAX_FILE_SIZE:
                results.append(DocumentUploadResponse(
                    success=False,
                    message="File size exceeds 10MB limit",
                    filename=file.filename
                ))
                continue
            
            if len(file_content) == 0:
                results.append(DocumentUploadResponse(
                    success=False,
                    message="Empty file",
                    filename=file.filename
                ))
                continue
            
            # Process the PDF with tenant_id
            success, message = process_and_add_pdf(file_content, file.filename, tenant_id.strip())
            
            chunks_created = None
            if success:
                try:
                    if "chunks" in message:
                        chunks_created = int(message.split("as ")[1].split(" chunks")[0])
                except:
                    pass
            
            results.append(DocumentUploadResponse(
                success=success,
                message=message,
                filename=file.filename,
                chunks_created=chunks_created
            ))
            
        except Exception as e:
            results.append(DocumentUploadResponse(
                success=False,
                message=f"Error processing file: {str(e)}",
                filename=file.filename
            ))
    
    return results


@router.delete("/delete/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the vector database.
    Note: This is a placeholder implementation. You may need to implement
    a proper document deletion function in the pdf_extractor module.
    """
    try:
        # TODO: Implement document deletion functionality in pdf_extractor
        return JSONResponse(
            content={"message": f"Document deletion not yet implemented for ID: {document_id}"},
            status_code=status.HTTP_501_NOT_IMPLEMENTED
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting document: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """
    Health check endpoint for the documents service.
    """
    try:
        # Test vector store initialization
        from infra.pdf_uploader import _initialize_vector_store
        _initialize_vector_store()
        return {"status": "healthy", "service": "internal_documents"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from services.supabase_service import supabase
import uuid
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class SignInRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID (UUID format)")
    
    @validator('tenant_id')
    def validate_tenant_id(cls, v):
        if not v or not v.strip():
            raise ValueError('Tenant ID is required')
        
        try:
            uuid.UUID(v.strip())
        except ValueError:
            raise ValueError('Tenant ID must be a valid UUID format')
        
        return v.strip()

class SignInResponse(BaseModel):
    success: bool
    message: str
    tenant_id: str

@router.post("/signin", response_model=SignInResponse)
async def signin(request: SignInRequest):
    """
    Authenticate user by validating tenant ID exists in the tenants table.
    """
    try:
        logger.info(f"Attempting signin for tenant_id: {request.tenant_id}")
        
        # Query the tenants table to check if the UUID exists
        response = supabase.table('tenants').select('id').eq('id', request.tenant_id).execute()
        
        if not response.data:
            logger.warning(f"Invalid tenant_id attempted: {request.tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid tenant ID. Please check your credentials."
            )
        
        logger.info(f"Successful signin for tenant_id: {request.tenant_id}")
        return SignInResponse(
            success=True,
            message="Successfully authenticated",
            tenant_id=request.tenant_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error during signin for tenant_id {request.tenant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )

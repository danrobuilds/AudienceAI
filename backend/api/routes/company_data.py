from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent.context import get_company_context
from services.supabase_service import supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/company_data", tags=["company_data"])

class CompanyDataUpdate(BaseModel):
    context_description: str = None
    target_audience: str = None
    market_need: str = None
    industry: str = None
    core_value_prop: str = None

@router.get("/data")
async def get_company_data(tenant_id: str = "dummy_tenant_id"):
    """Get company data from tenants table"""
    try:
        # Query the tenants table for company information
        response = supabase.table('tenants').select('context_description, target_audience, market_need, industry, core_value_prop').eq('id', tenant_id).execute()
        
        if response.data and len(response.data) > 0:
            company_data = response.data[0]
            return {
                "success": True,
                "data": {
                    "context_description": company_data.get('context_description', ''),
                    "target_audience": company_data.get('target_audience', ''),
                    "market_need": company_data.get('market_need', ''),
                    "industry": company_data.get('industry', ''),
                    "core_value_prop": company_data.get('core_value_prop', '')
                }
            }
        else:
            logger.warning(f"No tenant found with ID: {tenant_id}")
            return {
                "success": False,
                "error": "Company data not found"
            }
            
    except Exception as e:
        logger.error(f"Error fetching company data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch company data")

@router.post("/data")
async def update_company_data(data: CompanyDataUpdate, tenant_id: str = "dummy_tenant_id"):
    """Update company data in tenants table"""
    try:
        # Build update object with only non-None values
        update_data = {}
        if data.context_description is not None:
            update_data['context_description'] = data.context_description
        if data.target_audience is not None:
            update_data['target_audience'] = data.target_audience
        if data.market_need is not None:
            update_data['market_need'] = data.market_need
        if data.industry is not None:
            update_data['industry'] = data.industry
        if data.core_value_prop is not None:
            update_data['core_value_prop'] = data.core_value_prop

        if not update_data:
            return {
                "success": False,
                "error": "No data provided to update"
            }

        # Update the tenants table
        response = supabase.table('tenants').update(update_data).eq('id', tenant_id).execute()
        
        if response.data and len(response.data) > 0:
            return {
                "success": True,
                "message": "Company data updated successfully",
                "data": response.data[0]
            }
            
    except Exception as e:
        logger.error(f"Error updating company data: {e}")
        raise HTTPException(status_code=500, detail="Failed to update company data") 
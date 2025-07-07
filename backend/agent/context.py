import asyncio
from services.supabase_service import supabase
import logging

logger = logging.getLogger(__name__)

async def get_company_context(tenant_id: str = "dummy_tenant_id") -> str:
   
    try:
        # Query the tenants table for the context_description
        response = supabase.table('tenants').select('context_description').eq('id', tenant_id).execute()
        
        if response.data and len(response.data) > 0:
            return str(response.data[0].get('context_description', ''))
        else:
            logger.warning(f"No tenant found with ID")
            return ""
            
    except Exception as e:
        logger.error(f"Error fetching company context for tenant")
        return ""



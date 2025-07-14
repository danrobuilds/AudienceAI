import asyncio
from services.supabase_service import supabase
import logging

logger = logging.getLogger(__name__)

async def get_company_context(tenant_id: str = "dummy_tenant_id") -> str:
   
    try:
        # Query the tenants table for the context_description
        response = supabase.table('tenants').select('context_description, target_audience, market_need, industry, core_value_prop').eq('id', tenant_id).execute()
        
        if response.data and len(response.data) > 0:
            lines = []
            lines.append("Here is helpful context about the core value proposition of the company: ")
            lines.append(str(response.data[0].get('context_description', '')))
            lines.append("Target audience: " + str(response.data[0].get('target_audience', '')))
            lines.append("Market need: " + str(response.data[0].get('market_need', '')))
            lines.append("Industry: " + str(response.data[0].get('industry', '')))
            lines.append("Core value prop: " + str(response.data[0].get('core_value_prop', '')))
            return "\n".join(lines)
        else:
            logger.warning(f"No tenant found with ID")
            return ""
            
    except Exception as e:
        logger.error(f"Error fetching company context for tenant")
        return ""



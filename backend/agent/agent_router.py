import asyncio
import json
from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from services.openai_service import initialize_llm
from agent.agent_calling import AGENT_REGISTRY
from agent.context import get_company_context

def build_router_functions():
    """Build OpenAI function schema for agent routing"""
    return [{
        "name": "dispatch_agent",
        "description": "Select which specialized agent should handle the user's follow-up request to modify existing content.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "enum": list(AGENT_REGISTRY.keys()),
                    "description": "The agent to dispatch the request to"
                },
                "args": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                    "description": "Arguments to pass to the selected agent"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why this agent was chosen"
                }
            },
            "required": ["agent", "args", "reasoning"],
            "additionalProperties": False
        },
        "strict": True
    }]

async def route_followup_query(
    followup_query: str,
    existing_content: Dict[str, Any],
    modality: str,
    tenant_id: str,
    async_log_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Route a follow-up query to the appropriate agent(s) and update existing content.
    
    """
    
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[ROUTER] {message}")
    
    await _log(f"Routing follow-up query: {followup_query[:100]}...")
    
    try:
        # Initialize router LLM
        router_llm = initialize_llm()
        
        # Get company context
        company_context = await get_company_context(tenant_id)
        
        # Build router system message
        router_system_msg = f"""
        You are the routing brain of a marketing-content workflow handling follow-up requests.
        
        Available agents:
        - info: {AGENT_REGISTRY["info"]["description"]}
        - compose: {AGENT_REGISTRY["compose"]["description"]}
        - multimodal: {AGENT_REGISTRY["multimodal"]["description"]}
        
        Current content state:
        - Post content: {existing_content.get('post_content', 'Not generated')[:200]}...
        - Generated images: {len(existing_content.get('generated_images', []))} images
        - Modality: {modality}
        
        Company context: {company_context}
        
        Analyze the follow-up request and determine which agent should handle it.
        
        Examples:
        - "Make the post more engaging" -> compose (rewrite the post)
        - "Add more statistics" -> info (gather more information)
        - "Change the image to be more professional" -> multimodal (regenerate image)
        - "Rewrite with a different tone" -> compose (rewrite the post)
        - "Add more context about the industry" -> info (gather more information)
        
        Return ONLY the function call to dispatch_agent. Do not explain your reasoning beyond the reasoning field.
        """
        
        # Prepare messages
        messages = [
            SystemMessage(content=router_system_msg),
            HumanMessage(content=f"Follow-up request: {followup_query}")
        ]
        
        # Get router decision
        router_llm_with_tools = router_llm.bind_tools(build_router_functions(), tool_choice="auto")
        response = await router_llm_with_tools.ainvoke(messages)
        
        if not response.tool_calls:
            await _log("Router did not call any tools, treating as compose request")
            # Default to compose if no tool call
            return await _handle_compose_followup(
                followup_query, existing_content, modality, tenant_id, async_log_callback
            )
        
        # Extract routing decision
        tool_call = response.tool_calls[0]
        dispatch_args = tool_call["args"]
        
        selected_agent = dispatch_args["agent"]
        agent_args = dispatch_args["args"]
        reasoning = dispatch_args.get("reasoning", "No reasoning provided")
        
        await _log(f"Router selected agent '{selected_agent}': {reasoning}")
        
        # Route to appropriate handler
        if selected_agent == "info":
            return await _handle_info_followup(
                followup_query, existing_content, modality, tenant_id, async_log_callback, agent_args
            )
        elif selected_agent == "compose":
            return await _handle_compose_followup(
                followup_query, existing_content, modality, tenant_id, async_log_callback, agent_args
            )
        elif selected_agent == "multimodal":
            return await _handle_multimodal_followup(
                followup_query, existing_content, modality, tenant_id, async_log_callback, agent_args
            )
        else:
            await _log(f"Unknown agent: {selected_agent}, defaulting to compose")
            return await _handle_compose_followup(
                followup_query, existing_content, modality, tenant_id, async_log_callback
            )
            
    except Exception as e:
        await _log(f"Router error: {e}")
        # Fallback to compose agent for any errors
        return await _handle_compose_followup(
            followup_query, existing_content, modality, tenant_id, async_log_callback
        )

async def _handle_info_followup(
    followup_query: str,
    existing_content: Dict[str, Any],
    modality: str,
    tenant_id: str,
    async_log_callback: Optional[callable],
    agent_args: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Handle follow-up queries that need more information gathering"""
    
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[INFO_FOLLOWUP] {message}")
    
    await _log("Gathering additional information for follow-up...")
    
    # Get the info agent
    info_agent = AGENT_REGISTRY["info"]["entrypoint"]
    
    # Call info agent with correct signature
    gathered_info = await info_agent(
        user_prompt_text=followup_query,
        llm=initialize_llm(),
        async_log_callback=async_log_callback,
        company_context=await get_company_context(tenant_id),
        tenant_id=tenant_id
    )
    
    # Now call compose agent with the new information
    return await _handle_compose_followup(
        followup_query, existing_content, modality, tenant_id, async_log_callback, 
        {"gathered_info": gathered_info}
    )

async def _handle_compose_followup(
    followup_query: str,
    existing_content: Dict[str, Any],
    modality: str,
    tenant_id: str,
    async_log_callback: Optional[callable],
    agent_args: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Handle follow-up queries that need post content modification"""
    
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[COMPOSE_FOLLOWUP] {message}")
    
    await _log("Modifying post content based on follow-up...")
    
    # Get the compose agent
    compose_agent = AGENT_REGISTRY["compose"]["entrypoint"]
    
    # Call compose agent with correct signature
    updated_response = await compose_agent(
        user_prompt_text=f"Original request resulted in: {existing_content.get('post_content', '')}. Now modify it based on this follow-up: {followup_query}",
        gathered_info=agent_args.get("gathered_info", "No additional information gathered") if agent_args else "No additional information gathered",
        llm=initialize_llm(),
        async_log_callback=async_log_callback,
        company_context=await get_company_context(tenant_id),
        modality=modality,
        tenant_id=tenant_id
    )
    
    # Update existing content with new post content
    updated_content = existing_content.copy()
    updated_content["post_content"] = updated_response.get("post_content", updated_response)
    
    # Update image description if provided
    if isinstance(updated_response, dict) and "image_description" in updated_response:
        updated_content["image_description"] = updated_response["image_description"]
    
    return updated_content

async def _handle_multimodal_followup(
    followup_query: str,
    existing_content: Dict[str, Any],
    modality: str,
    tenant_id: str,
    async_log_callback: Optional[callable],
    agent_args: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Handle follow-up queries that need image/media modification"""
    
    async def _log(message):
        if async_log_callback:
            await asyncio.wait_for(async_log_callback(message), timeout=5.0)
        else:
            print(f"[MULTIMODAL_FOLLOWUP] {message}")
    
    await _log("Modifying visual content based on follow-up...")
    
    # Get the multimodal agent
    multimodal_agent = AGENT_REGISTRY["multimodal"]["entrypoint"]
    
    # Call multimodal agent with correct signature
    new_images = await multimodal_agent(
        post_content=existing_content.get("post_content", ""),
        modality=modality,
        llm=initialize_llm(),
        async_log_callback=async_log_callback,
        tenant_id=tenant_id,
        image_description=f"Based on this follow-up request: {followup_query}. Previous image description: {existing_content.get('image_description', 'No previous description')}"
    )
    
    # Update existing content with new images
    updated_content = existing_content.copy()
    updated_content["generated_images"] = new_images
    
    return updated_content

# agents.py
from typing import Callable, Dict, Any
from agent.agent_info_gatherer import gather_information
from agent.agent_post_creator import create_viral_post
from agent.agent_multimodal_creator import create_media_for_post

AgentSpec = Dict[str, Any]

AGENT_REGISTRY: Dict[str, AgentSpec] = {
    "info": {
        "description": "Gather facts, stats and context for the post",
        "entrypoint": gather_information,
        "args_schema": {
            "type": "object",
            "properties": {
                "user_prompt_text": {"type": "string"},
                "tenant_id": {"type": "string"}
            },
            "required": ["user_prompt_text", "tenant_id"]
        },
    },
    "compose": {
        "description": "Write or rewrite the social-media copy",
        "entrypoint": create_viral_post,
        "args_schema": {
            "type": "object",
            "properties": {
                "user_prompt_text": {"type": "string"},
                "gathered_info": {"type": "string"},
                "modality": {"type": "string"}
            },
            "required": ["user_prompt_text", "gathered_info", "modality"]
        },
    },
    "multimodal": {
        "description": "Generate or regenerate an image/diagram for the post",
        "entrypoint": create_media_for_post,
        "args_schema": {
            "type": "object",
            "properties": {
                "post_content": {"type": "string"},
                "image_description": {"type": "string"},
                "modality": {"type": "string"}
            },
            "required": ["post_content", "image_description", "modality"]
        },
    },
}
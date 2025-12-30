"""Example: Using the API to create and invoke agents"""

import httpx
import json
import asyncio
from typing import Dict, Any


BASE_URL = "http://localhost:8000"


async def create_agent(agent_config: Dict[str, Any]) -> str:
    """Create an agent via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/agents", json=agent_config)
        response.raise_for_status()
        return response.json()["agent_name"]


async def invoke_agent(agent_name: str, input_data: str) -> Dict[str, Any]:
    """Invoke an agent via API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/agents/{agent_name}/invoke",
            json={
                "input": {"input": input_data},
                "metadata": {"source": "api_example"}
            }
        )
        response.raise_for_status()
        return response.json()


async def stream_agent(agent_name: str, input_data: str):
    """Stream agent execution via API."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/agents/{agent_name}/stream",
            json={
                "input": {"input": input_data},
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(f"Stream event: {data}")


async def main():
    """Demonstrate API usage."""
    
    # Define agent configuration
    agent_config = {
        "name": "customer-support-bot",
        "description": "A customer support agent that helps with product queries",
        "llm_provider": "openai",
        "model": "gpt-3.5-turbo",
        "api_key_env": "OPENAI_API_KEY",
        "workflow_type": "sequential",
        "nodes": [
            {
                "name": "classify_intent",
                "type": "llm",
                "prompt": """Classify the customer's intent into one of these categories:
                - product_info: Questions about product features or specifications
                - pricing: Questions about pricing or discounts
                - technical_support: Technical issues or troubleshooting
                - order_status: Questions about order or delivery status
                - general: General inquiries
                
                Respond with only the category name."""
            },
            {
                "name": "generate_response",
                "type": "llm",
                "prompt": """You are a helpful customer support agent. 
                Based on the customer's query and the classified intent, provide a helpful and professional response.
                Be concise but thorough."""
            }
        ],
        "tools": ["web_search"],
        "enable_logging": True,
        "enable_metrics": True
    }
    
    print("API Usage Example")
    print("-" * 50)
    
    try:
        # Create the agent
        print("Creating agent...")
        agent_name = await create_agent(agent_config)
        print(f"Agent created: {agent_name}")
        print("-" * 50)
        
        # Test queries
        queries = [
            "What are the main features of your premium plan?",
            "I'm having trouble logging into my account",
            "When will my order #12345 be delivered?",
            "Do you offer student discounts?"
        ]
        
        for query in queries:
            print(f"\nQuery: {query}")
            result = await invoke_agent(agent_name, query)
            print(f"Response: {result.get('output', 'No response')}")
            print("-" * 50)
        
        # Demonstrate streaming
        print("\nStreaming example:")
        await stream_agent(agent_name, "Tell me about your refund policy")
        
    except httpx.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Make sure the API server is running before executing this
    print("Note: Make sure the API server is running (python -m src.main)")
    asyncio.run(main()) 
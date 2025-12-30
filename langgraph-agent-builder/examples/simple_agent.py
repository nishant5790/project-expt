"""Example: Simple Sequential Agent"""

import asyncio
import sys
sys.path.append("..")

from src import (
    AgentBuilder,
    AgentConfig,
    NodeConfig,
    NodeType,
    LLMProvider,
    WorkflowType
)


async def main():
    """Create and run a simple sequential agent."""
    
    # Define agent configuration
    config = AgentConfig(
        name="simple-assistant",
        description="A simple AI assistant that processes queries sequentially",
        llm_provider=LLMProvider.OPENAI,
        model="gpt-3.5-turbo",
        api_key_env="OPENAI_API_KEY",
        workflow_type=WorkflowType.SEQUENTIAL,
        nodes=[
            NodeConfig(
                name="understand_query",
                type=NodeType.LLM,
                prompt="You are a helpful assistant. Analyze the user's query and understand what they are asking for. Be concise."
            ),
            NodeConfig(
                name="generate_response",
                type=NodeType.LLM,
                prompt="Based on the previous analysis, provide a helpful and detailed response to the user's query."
            )
        ]
    )
    
    # Build the agent
    builder = AgentBuilder()
    agent = builder.build(config)
    
    # Test the agent
    print("Simple Sequential Agent Example")
    print("-" * 50)
    
    # Example 1: Simple question
    result = await agent.ainvoke({
        "input": "What is the capital of France?"
    })
    
    print(f"Query: What is the capital of France?")
    print(f"Response: {result['output']}")
    print("-" * 50)
    
    # Example 2: More complex query
    result = await agent.ainvoke({
        "input": "Explain the difference between machine learning and deep learning"
    })
    
    print(f"Query: Explain the difference between machine learning and deep learning")
    print(f"Response: {result['output']}")


if __name__ == "__main__":
    asyncio.run(main()) 
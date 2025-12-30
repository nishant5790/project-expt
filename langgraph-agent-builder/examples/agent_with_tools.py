"""Example: Agent with Tools and Conditional Logic"""

import asyncio
import sys
sys.path.append("..")

from src import (
    AgentBuilder,
    AgentConfig,
    NodeConfig,
    EdgeConfig,
    NodeType,
    LLMProvider,
    WorkflowType,
    ToolRegistry
)
from src.core.tools import calculator, database_query


async def main():
    """Create and run an agent with tools and conditional logic."""
    
    # Register custom tools
    tool_registry = ToolRegistry()
    tool_registry.register_tool("calculator", calculator)
    tool_registry.register_tool("database_query", database_query)
    
    # Define agent configuration
    config = AgentConfig(
        name="research-assistant",
        description="An AI assistant that can use tools to answer questions",
        llm_provider=LLMProvider.OPENAI,
        model="gpt-4",
        api_key_env="OPENAI_API_KEY",
        workflow_type=WorkflowType.CONDITIONAL,
        tools=["calculator", "database_query", "web_search"],
        nodes=[
            NodeConfig(
                name="analyze_query",
                type=NodeType.LLM,
                prompt="""Analyze the user's query and determine what type of information they need.
                Classify the query as one of: 'calculation', 'database', 'web_search', or 'general'.
                Respond with only the classification."""
            ),
            NodeConfig(
                name="route_query",
                type=NodeType.CONDITIONAL,
                condition="state['output'].strip().lower()",
                branches={
                    "calculation": "use_calculator",
                    "database": "query_database",
                    "web_search": "search_web",
                    "default": "direct_answer"
                }
            ),
            NodeConfig(
                name="use_calculator",
                type=NodeType.TOOL,
                tool="calculator",
                tool_config={
                    "expression": "$input"
                }
            ),
            NodeConfig(
                name="query_database",
                type=NodeType.TOOL,
                tool="database_query",
                tool_config={
                    "query": "$input"
                }
            ),
            NodeConfig(
                name="search_web",
                type=NodeType.TOOL,
                tool="web_search"
            ),
            NodeConfig(
                name="direct_answer",
                type=NodeType.LLM,
                prompt="Provide a direct answer to the user's query based on your knowledge."
            ),
            NodeConfig(
                name="format_response",
                type=NodeType.LLM,
                prompt="Format the previous results into a clear, helpful response for the user."
            )
        ],
        edges=[
            EdgeConfig(source="analyze_query", target="route_query"),
            EdgeConfig(source="use_calculator", target="format_response"),
            EdgeConfig(source="query_database", target="format_response"),
            EdgeConfig(source="search_web", target="format_response"),
            EdgeConfig(source="direct_answer", target="format_response"),
        ]
    )
    
    # Build the agent
    builder = AgentBuilder(tool_registry=tool_registry)
    agent = builder.build(config)
    
    # Test the agent
    print("Agent with Tools Example")
    print("-" * 50)
    
    # Example 1: Calculation
    result = await agent.ainvoke({
        "input": "What is 125 * 48 + 372?"
    })
    print(f"Query: What is 125 * 48 + 372?")
    print(f"Response: {result['output']}")
    print("-" * 50)
    
    # Example 2: General knowledge
    result = await agent.ainvoke({
        "input": "What is photosynthesis?"
    })
    print(f"Query: What is photosynthesis?")
    print(f"Response: {result['output']}")
    print("-" * 50)
    
    # Example 3: Database query (simulated)
    result = await agent.ainvoke({
        "input": "SELECT * FROM users WHERE age > 25"
    })
    print(f"Query: SELECT * FROM users WHERE age > 25")
    print(f"Response: {result['output']}")


if __name__ == "__main__":
    asyncio.run(main()) 
# LangGraph Agent Builder

A production-ready framework for dynamically building LangGraph agents through configuration. This system allows users to create sophisticated AI agents by simply providing agent specifications, without writing boilerplate code.

## Features

- **Dynamic Agent Creation**: Build LangGraph agents from configuration files or API requests
- **Production Ready**: Built-in error handling, logging, monitoring, and scaling capabilities
- **Flexible Architecture**: Support for various LLM providers, tools, and workflows
- **State Management**: Robust state persistence and recovery mechanisms
- **API First**: RESTful API for agent management and execution
- **Extensible**: Easy to add custom tools, nodes, and edge conditions
- **Monitoring**: Prometheus metrics and structured logging

## Quick Start

```python
from langgraph_agent_builder import AgentBuilder, AgentConfig

# Define agent configuration
config = AgentConfig(
    name="customer-support-agent",
    description="An agent for handling customer support queries",
    llm_provider="openai",
    model="gpt-4",
    tools=["web_search", "database_query"],
    workflow_type="sequential",
    nodes=[
        {
            "name": "analyze_query",
            "type": "llm",
            "prompt": "Analyze the customer query and determine the intent"
        },
        {
            "name": "fetch_info",
            "type": "tool",
            "tool": "database_query"
        },
        {
            "name": "generate_response",
            "type": "llm",
            "prompt": "Generate a helpful response based on the information"
        }
    ]
)

# Build and run the agent
builder = AgentBuilder()
agent = builder.build(config)
result = await agent.invoke({"query": "What is my order status?"})
```

## Installation

```bash
pip install langgraph-agent-builder
```

## Documentation

Full documentation is available at [docs/index.md](docs/index.md)

## License

MIT License 
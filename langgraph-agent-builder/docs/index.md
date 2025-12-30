# LangGraph Agent Builder Documentation

## Table of Contents
1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Examples](#examples)
8. [Production Deployment](#production-deployment)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

## Introduction

LangGraph Agent Builder is a production-ready framework for dynamically building AI agents using LangGraph. It allows users to create sophisticated agents by simply providing configuration, without writing boilerplate code.

### Key Features
- **Dynamic Agent Creation**: Build agents from JSON/YAML configuration
- **Multiple LLM Support**: OpenAI, Anthropic, Azure OpenAI, and more
- **Tool Integration**: Built-in and custom tools support
- **Workflow Types**: Sequential, parallel, conditional, and cyclic workflows
- **Production Ready**: Logging, metrics, error handling, and scaling
- **API First**: RESTful API with streaming support
- **State Management**: Persistent state with Redis support

## Architecture

The system is built with a modular architecture:

```
langgraph-agent-builder/
├── src/
│   ├── config/          # Configuration models
│   ├── core/            # Core components (LLM, tools, state)
│   ├── builders/        # Agent builder logic
│   ├── api/             # FastAPI server
│   └── utils/           # Logging, metrics, helpers
├── examples/            # Example configurations
└── tests/              # Test suite
```

### Core Components

1. **AgentBuilder**: Main class that orchestrates agent creation
2. **LLMFactory**: Creates LLM instances for different providers
3. **ToolRegistry**: Manages available tools
4. **NodeFactory**: Creates workflow nodes
5. **StateManager**: Handles agent state

## Installation

### Using pip

```bash
pip install langgraph-agent-builder
```

### From source

```bash
git clone https://github.com/yourusername/langgraph-agent-builder
cd langgraph-agent-builder
pip install -e .
```

### Using Docker

```bash
docker-compose up -d
```

## Quick Start

### 1. Set up environment variables

```bash
cp env.example .env
# Edit .env with your API keys
```

### 2. Create a simple agent

```python
from langgraph_agent_builder import AgentBuilder, AgentConfig, NodeConfig, NodeType, LLMProvider

# Define agent configuration
config = AgentConfig(
    name="my-assistant",
    description="A helpful AI assistant",
    llm_provider=LLMProvider.OPENAI,
    model="gpt-3.5-turbo",
    api_key_env="OPENAI_API_KEY",
    nodes=[
        NodeConfig(
            name="process",
            type=NodeType.LLM,
            prompt="You are a helpful assistant. Answer the user's question."
        )
    ]
)

# Build and use the agent
builder = AgentBuilder()
agent = builder.build(config)
result = await agent.ainvoke({"input": "What is the capital of France?"})
print(result["output"])
```

### 3. Using the API

Start the server:
```bash
python -m src.main
```

Create an agent via API:
```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d @agent_config.json
```

## Configuration

### Agent Configuration Schema

```json
{
  "name": "agent-name",
  "description": "Agent description",
  "llm_provider": "openai|anthropic|azure_openai",
  "model": "gpt-4",
  "api_key_env": "OPENAI_API_KEY",
  "workflow_type": "sequential|parallel|conditional|cyclic",
  "nodes": [
    {
      "name": "node-name",
      "type": "llm|tool|conditional|human_input",
      "prompt": "Prompt for LLM nodes",
      "tool": "tool-name for tool nodes",
      "condition": "Python expression for conditional nodes"
    }
  ],
  "tools": ["tool1", "tool2"],
  "edges": [
    {
      "source": "node1",
      "target": "node2",
      "condition": "Optional condition"
    }
  ]
}
```

### Node Types

1. **LLM Node**: Processes input using language models
2. **Tool Node**: Executes tools (search, database, custom)
3. **Conditional Node**: Routes based on conditions
4. **Human Input Node**: Waits for human input
5. **Custom Node**: User-defined logic

### Workflow Types

1. **Sequential**: Nodes execute one after another
2. **Parallel**: Nodes execute simultaneously
3. **Conditional**: Dynamic routing based on conditions
4. **Cyclic**: Supports loops with iteration limits
5. **Custom**: Define your own edge connections

## API Reference

### POST /agents
Create a new agent from configuration.

Request:
```json
{
  "name": "agent-name",
  "llm_provider": "openai",
  "model": "gpt-4",
  ...
}
```

### GET /agents
List all agents.

### GET /agents/{agent_name}
Get agent information.

### POST /agents/{agent_name}/invoke
Invoke an agent.

Request:
```json
{
  "input": {"input": "Your query"},
  "thread_id": "optional-thread-id",
  "config": {}
}
```

### POST /agents/{agent_name}/stream
Stream agent execution (Server-Sent Events).

### DELETE /agents/{agent_name}
Delete an agent.

### GET /metrics
Prometheus metrics endpoint.

### GET /health
Health check endpoint.

## Examples

### Customer Support Agent

```python
config = AgentConfig(
    name="support-bot",
    description="Customer support agent",
    llm_provider=LLMProvider.OPENAI,
    model="gpt-4",
    workflow_type=WorkflowType.CONDITIONAL,
    nodes=[
        NodeConfig(
            name="classify",
            type=NodeType.LLM,
            prompt="Classify the query: technical, billing, or general"
        ),
        NodeConfig(
            name="route",
            type=NodeType.CONDITIONAL,
            condition="state['output'].lower()",
            branches={
                "technical": "tech_support",
                "billing": "billing_support",
                "default": "general_support"
            }
        ),
        # ... more nodes
    ]
)
```

### Research Assistant with Tools

```python
config = AgentConfig(
    name="researcher",
    description="Research assistant with web search",
    llm_provider=LLMProvider.OPENAI,
    model="gpt-4",
    tools=["web_search", "calculator"],
    nodes=[
        NodeConfig(
            name="analyze",
            type=NodeType.LLM,
            prompt="Analyze what information is needed"
        ),
        NodeConfig(
            name="search",
            type=NodeType.TOOL,
            tool="web_search"
        ),
        NodeConfig(
            name="synthesize",
            type=NodeType.LLM,
            prompt="Synthesize the search results"
        )
    ]
)
```

## Production Deployment

### Docker Deployment

1. Build the image:
```bash
docker build -t langgraph-agent-builder .
```

2. Run with docker-compose:
```bash
docker-compose up -d
```

This starts:
- Agent Builder API
- Redis for state persistence
- Prometheus for metrics
- Grafana for visualization

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests.

### Environment Variables

Key environment variables:
- `OPENAI_API_KEY`: OpenAI API key
- `REDIS_HOST`: Redis hostname
- `API_PORT`: API server port
- `LOG_LEVEL`: Logging level
- `ENABLE_METRICS`: Enable Prometheus metrics

## Monitoring

### Metrics

The system exposes Prometheus metrics:
- `langgraph_agent_invocations_total`: Total invocations
- `langgraph_agent_successes_total`: Successful executions
- `langgraph_agent_errors_total`: Errors by type
- `langgraph_agent_execution_duration_seconds`: Execution time
- `langgraph_agent_active_agents`: Currently active agents

### Logging

Structured logging with JSON format:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "agent": "support-bot",
  "node": "classify",
  "message": "Executing LLM node"
}
```

### Grafana Dashboards

Import the provided Grafana dashboards from `grafana/` directory.

## Troubleshooting

### Common Issues

1. **LLM API Key Errors**
   - Verify environment variables are set
   - Check API key permissions

2. **Redis Connection Failed**
   - Ensure Redis is running
   - Check connection parameters

3. **Agent Creation Failed**
   - Validate configuration schema
   - Check node names are unique
   - Verify edges reference existing nodes

4. **Performance Issues**
   - Enable metrics to identify bottlenecks
   - Consider using Redis for state persistence
   - Scale horizontally with multiple API workers

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python -m src.main
```

### Support

- GitHub Issues: https://github.com/yourusername/langgraph-agent-builder/issues
- Documentation: https://docs.langgraph-agent-builder.com
- Discord: https://discord.gg/langgraph-builder 
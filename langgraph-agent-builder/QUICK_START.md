# Quick Start Guide

This guide helps you get the LangGraph Agent Builder running quickly, even without all dependencies installed.

## Option 1: Full Installation (Recommended)

```bash
# 1. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install the package with all dependencies
pip install -e .

# 3. Set up environment variables
cp env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, etc.)

# 4. Start the server
python -m src.main --host 0.0.0.0 --port 8000
```

## Option 2: Minimal Installation (Demo Mode)

If you encounter dependency issues, the system includes fallback implementations:

```bash
# 1. Install only basic Python requirements
pip install pydantic fastapi uvicorn pyyaml python-multipart

# 2. Set up environment
cp env.example .env

# 3. Start in demo mode (uses mock LLMs and tools)
python -m src.main --host 0.0.0.0 --port 8000
```

## Option 3: Docker (Easiest)

```bash
# 1. Set up environment
cp env.example .env
# Edit .env with your API keys

# 2. Run with Docker Compose
docker-compose up -d
```

## Verify Installation

1. **Health Check:**
```bash
curl http://localhost:8000/health
```

2. **List Available Tools:**
```bash
curl http://localhost:8000/tools
```

3. **Create Simple Agent:**
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-agent",
    "llm_provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key_env": "OPENAI_API_KEY",
    "nodes": [
      {
        "name": "respond",
        "type": "llm",
        "prompt": "You are a helpful assistant. Respond to the user."
      }
    ]
  }'
```

4. **Test Agent:**
```bash
curl -X POST "http://localhost:8000/agents/test-agent/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input": "Hello, how are you?"
    }
  }'
```

## Common Issues & Solutions

### 1. Import Errors
If you see LangChain/LangGraph import errors, the system will use fallback implementations. To get full functionality:

```bash
pip install langgraph langchain langchain-openai langchain-anthropic langchain-community
```

### 2. YAML Errors
If YAML support is missing:

```bash
pip install pyyaml
```

### 3. Prometheus Metrics Errors
If metrics don't work:

```bash
pip install prometheus-client
```

### 4. macOS Python Environment Issues
If you see "externally-managed-environment" errors:

```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Next Steps

1. **Check the API documentation:** Visit `http://localhost:8000/docs` for interactive API docs
2. **Try YAML configuration:** Upload a YAML file using the examples in `examples/config_examples/`
3. **Add custom tools:** Use the `/tools/custom` endpoint to register your own tools
4. **Monitor your agents:** Check metrics at `http://localhost:8000/metrics`

## Example Workflows

### Create Agent from YAML:
```bash
# Upload a YAML configuration
curl -X POST "http://localhost:8000/agents/from-yaml" \
  -F "file=@examples/config_examples/simple_agent.yaml"
```

### Register Custom Tool:
```bash
curl -X POST "http://localhost:8000/tools/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "greeter",
    "description": "Greet users",
    "function_code": "def greet(name: str) -> str:\n    return f\"Hello, {name}!\"",
    "parameters_schema": {
      "name": {"type": "string", "description": "Name to greet"}
    }
  }'
```

For more detailed information, see the full documentation in `docs/` or the comprehensive examples in `examples/`. 
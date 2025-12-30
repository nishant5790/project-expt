# LangGraph Agent Builder - Enhanced Features Summary

## 🎉 New Features Added

### 1. Custom Tools Support
- **Dynamic Tool Registration**: Add custom tools via API or configuration
- **Inline Code**: Define tools with Python code directly in configuration
- **Module Loading**: Reference external Python files for complex tools
- **Parameter Validation**: Automatic parameter validation with Pydantic schemas

### 2. YAML Configuration Support
- **File Upload**: Create agents by uploading YAML configuration files
- **Validation**: Validate YAML configurations before creating agents
- **Examples**: Pre-built YAML templates for common use cases

### 3. Enhanced API Endpoints
- Extended REST API with new endpoints for tools and configuration management
- Better error handling and validation
- Streaming support for real-time agent execution

## 🚀 Quick Start Guide

### Step 1: Start the Server
```bash
# Clone the repository
git clone <repo-url>
cd langgraph-agent-builder

# Install dependencies
pip install -e .

# Set up environment variables
cp env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, etc.)

# Start the server
python -m src.main --host 0.0.0.0 --port 8000
```

### Step 2: Register Custom Tools

#### Option A: Via API (Inline Code)
```bash
curl -X POST "http://localhost:8000/tools/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "email_validator",
    "description": "Validate email addresses",
    "function_code": "def validate_email(email: str) -> str:\n    import re\n    pattern = r\"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$\"\n    return \"valid\" if re.match(pattern, email) else \"invalid\"",
    "parameters_schema": {
      "email": {
        "type": "string",
        "description": "Email to validate"
      }
    }
  }'
```

#### Option B: Via YAML Configuration
```yaml
tools:
  - name: "weather_checker"
    description: "Check weather for a location"
    function_code: |
      def check_weather(location: str) -> str:
          # Mock weather API
          return f"Weather in {location}: Sunny, 72°F"
    parameters_schema:
      location:
        type: "string"
        description: "Location to check weather for"
```

### Step 3: Create Agent with YAML

Create `my-agent.yaml`:
```yaml
name: "smart-assistant"
description: "AI assistant with custom capabilities"
llm_provider: "openai"
model: "gpt-3.5-turbo"
api_key_env: "OPENAI_API_KEY"

workflow_type: "conditional"

tools:
  - "calculator"
  - "web_search"
  - name: "text_analyzer"
    description: "Analyze text content"
    function_code: |
      def analyze_text(text: str) -> str:
          word_count = len(text.split())
          return f"Analysis: {word_count} words, {len(text)} characters"
    parameters_schema:
      text:
        type: "string"
        description: "Text to analyze"

nodes:
  - name: "classify"
    type: "llm"
    prompt: "Classify the request: analysis, calculation, search, or general"
    
  - name: "route"
    type: "conditional"
    condition: "state['output'].lower().strip()"
    branches:
      "analysis": "analyze_text"
      "calculation": "calculate"
      "search": "search_web"
      "default": "general_response"
      
  - name: "analyze_text"
    type: "tool"
    tool: "text_analyzer"
    
  - name: "calculate"
    type: "tool"
    tool: "calculator"
    
  - name: "search_web"
    type: "tool"
    tool: "web_search"
    
  - name: "general_response"
    type: "llm"
    prompt: "Provide a helpful general response"
    
  - name: "format_output"
    type: "llm"
    prompt: "Format the results into a user-friendly response"

edges:
  - source: "classify"
    target: "route"
  - source: "analyze_text"
    target: "format_output"
  - source: "calculate"
    target: "format_output"
  - source: "search_web"
    target: "format_output"
  - source: "general_response"
    target: "format_output"

entry_point: "classify"
```

Upload the configuration:
```bash
curl -X POST "http://localhost:8000/agents/from-yaml" \
  -F "file=@my-agent.yaml"
```

### Step 4: Use the Agent
```bash
curl -X POST "http://localhost:8000/agents/smart-assistant/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input": "Analyze this text: Hello world, this is a test message."
    }
  }'
```

## 📚 Complete API Reference

### Agent Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agents` | POST | Create agent from JSON |
| `/agents/from-yaml` | POST | Create agent from YAML file |
| `/agents` | GET | List all agents |
| `/agents/{name}` | GET | Get agent details |
| `/agents/{name}` | DELETE | Delete agent |
| `/agents/{name}/invoke` | POST | Execute agent |
| `/agents/{name}/stream` | POST | Stream agent execution |

### Custom Tools
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools/custom` | POST | Register custom tool |
| `/tools/custom/examples` | GET | Get tool examples |
| `/tools` | GET | List all tools |
| `/tools/custom/{name}` | DELETE | Remove custom tool |

### Configuration
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/config/validate` | POST | Validate JSON config |
| `/config/validate-yaml` | POST | Validate YAML config |

### Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/metrics` | GET | Prometheus metrics |

## 🛠️ Advanced Features

### 1. Custom State Schemas
Define custom state fields for your agents:
```yaml
state_schema:
  fields:
    user_context:
      type: "dict"
      required: true
    session_data:
      type: "dict"
      required: false
```

### 2. Retry Configuration
Add retry logic to nodes:
```yaml
nodes:
  - name: "api_call"
    type: "tool"
    tool: "external_api"
    retry_config:
      max_attempts: 3
      min_wait: 1
      max_wait: 10
```

### 3. Workflow Types
- **Sequential**: Linear execution
- **Parallel**: Concurrent node execution
- **Conditional**: Dynamic routing
- **Cyclic**: Loops with iteration limits
- **Custom**: Define your own edges

### 4. Observability
Built-in monitoring and logging:
```yaml
enable_logging: true
enable_metrics: true
enable_tracing: true
```

## 📁 Example Use Cases

### 1. Customer Support Bot
```yaml
name: "support-bot"
tools:
  - name: "ticket_system"
    function_code: |
      def create_ticket(issue: str, priority: str = "medium") -> str:
          return f"Ticket created: {issue} (Priority: {priority})"
```

### 2. Data Analysis Agent
```yaml
name: "data-analyst"
tools:
  - name: "csv_processor"
    function_code: |
      def process_csv(file_path: str) -> str:
          import pandas as pd
          df = pd.read_csv(file_path)
          return f"Processed {len(df)} rows, {len(df.columns)} columns"
```

### 3. Content Processor
```yaml
name: "content-processor"
tools:
  - name: "text_summarizer"
    function_code: |
      def summarize_text(text: str, max_sentences: int = 3) -> str:
          sentences = text.split('.')[:max_sentences]
          return '. '.join(sentences) + '.'
```

## 🔧 Development Tools

### Python SDK Usage
```python
from langgraph_agent_builder import (
    AgentBuilder, 
    AgentConfig, 
    CustomToolDefinition,
    NodeConfig,
    NodeType,
    LLMProvider
)

# Create custom tool
tool_def = CustomToolDefinition(
    name="my_tool",
    description="My custom tool",
    function_code="def my_func(x): return x * 2"
)

# Create agent config
config = AgentConfig(
    name="my-agent",
    llm_provider=LLMProvider.OPENAI,
    model="gpt-3.5-turbo",
    nodes=[
        NodeConfig(
            name="process",
            type=NodeType.LLM,
            prompt="Process the input"
        )
    ]
)

# Build agent
builder = AgentBuilder()
agent = builder.build(config)
result = await agent.ainvoke({"input": "Hello"})
```

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up -d

# This starts:
# - Agent Builder API (port 8000)
# - Redis for state persistence (port 6379)
# - Prometheus for metrics (port 9090)  
# - Grafana for dashboards (port 3000)
```

## 🚦 Best Practices

1. **Tool Development**
   - Keep tools focused and single-purpose
   - Include proper error handling
   - Validate inputs with parameter schemas
   - Test tools independently before integration

2. **Agent Design**
   - Use meaningful node names
   - Design clear workflows
   - Set appropriate timeouts
   - Monitor performance metrics

3. **Production Deployment**
   - Use environment variables for API keys
   - Enable logging and metrics
   - Set up proper monitoring
   - Implement health checks

4. **Security**
   - Validate custom tool code
   - Limit tool execution permissions
   - Use secure API authentication
   - Monitor for unusual activity

## 📖 Documentation

- **Full Documentation**: [docs/index.md](docs/index.md)
- **API Usage Guide**: [docs/api_usage_guide.md](docs/api_usage_guide.md)
- **Configuration Examples**: [examples/config_examples/](examples/config_examples/)
- **Python Examples**: [examples/](examples/)

## 🤝 Support

- **Issues**: GitHub Issues
- **Examples**: Check the `examples/` directory
- **API Reference**: Swagger UI at `http://localhost:8000/docs`

This enhanced LangGraph Agent Builder now provides a complete solution for building production-ready AI agents with custom tools and YAML configuration support! 
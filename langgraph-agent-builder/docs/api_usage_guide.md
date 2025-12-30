# LangGraph Agent Builder API Usage Guide

This guide provides step-by-step instructions for using the LangGraph Agent Builder API to create and manage AI agents.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Creating Agents](#creating-agents)
3. [Custom Tools](#custom-tools)
4. [Running Agents](#running-agents)
5. [Configuration Management](#configuration-management)
6. [Monitoring and Management](#monitoring-and-management)
7. [Examples](#examples)

## Getting Started

### Prerequisites
1. Start the API server:
```bash
python -m src.main --host 0.0.0.0 --port 8000
```

2. Set up environment variables (copy from `env.example`):
```bash
cp env.example .env
# Edit .env with your API keys
```

### Base URL
All API endpoints are relative to: `http://localhost:8000`

### Health Check
```bash
curl http://localhost:8000/health
```

## Creating Agents

### Method 1: JSON Configuration via API

**Endpoint:** `POST /agents`

**Example Request:**
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-assistant",
    "description": "A helpful AI assistant",
    "llm_provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key_env": "OPENAI_API_KEY",
    "workflow_type": "sequential",
    "nodes": [
      {
        "name": "understand",
        "type": "llm",
        "prompt": "Analyze the user question and understand what they need."
      },
      {
        "name": "respond",
        "type": "llm", 
        "prompt": "Provide a helpful response based on your analysis."
      }
    ],
    "tools": ["calculator", "web_search"]
  }'
```

**Response:**
```json
{
  "status": "success",
  "agent_name": "my-assistant",
  "message": "Agent 'my-assistant' created successfully"
}
```

### Method 2: YAML Configuration File

**Endpoint:** `POST /agents/from-yaml`

**Step 1:** Create a YAML configuration file (`my-agent.yaml`):
```yaml
name: "customer-support-bot"
description: "Customer support agent"
llm_provider: "openai"
model: "gpt-3.5-turbo"
api_key_env: "OPENAI_API_KEY"
workflow_type: "sequential"

nodes:
  - name: "classify"
    type: "llm"
    prompt: "Classify this customer query into: technical, billing, or general"
  - name: "respond"
    type: "llm"
    prompt: "Provide a helpful customer support response"

tools: ["web_search"]
enable_logging: true
enable_metrics: true
```

**Step 2:** Upload the file:
```bash
curl -X POST "http://localhost:8000/agents/from-yaml" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@my-agent.yaml"
```

## Custom Tools

### Step 1: Register Custom Tools

**Endpoint:** `POST /tools/custom`

**Example 1: Inline Function Code**
```bash
curl -X POST "http://localhost:8000/tools/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "email_validator",
    "description": "Validate email addresses",
    "function_code": "def validate_email(email: str) -> str:\n    import re\n    pattern = r\"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$\"\n    if re.match(pattern, email):\n        return f\"Email {email} is valid\"\n    else:\n        return f\"Email {email} is invalid\"",
    "parameters_schema": {
      "email": {
        "type": "string",
        "description": "The email address to validate"
      }
    }
  }'
```

**Example 2: External Module**
```bash
curl -X POST "http://localhost:8000/tools/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "file_processor",
    "description": "Process text files",
    "module_path": "./custom_tools/file_processor.py",
    "function_name": "process_file",
    "parameters_schema": {
      "file_path": {
        "type": "string",
        "description": "Path to the file to process"
      },
      "operation": {
        "type": "string",
        "description": "Operation: count_words, count_lines, or extract_emails"
      }
    }
  }'
```

### Step 2: View Available Tools

```bash
curl http://localhost:8000/tools
```

### Step 3: Get Tool Examples

```bash
curl http://localhost:8000/tools/custom/examples
```

### Step 4: Use Custom Tools in Agents

Include custom tools in your agent configuration:
```json
{
  "name": "email-processor",
  "tools": ["email_validator", "file_processor"],
  "nodes": [
    {
      "name": "validate_emails",
      "type": "tool",
      "tool": "email_validator",
      "tool_config": {
        "email": "$input"
      }
    }
  ]
}
```

## Running Agents

### Synchronous Execution

**Endpoint:** `POST /agents/{agent_name}/invoke`

```bash
curl -X POST "http://localhost:8000/agents/my-assistant/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input": "What is the capital of France?"
    },
    "thread_id": "conversation-123",
    "metadata": {
      "user_id": "user123",
      "session": "session456"
    }
  }'
```

**Response:**
```json
{
  "output": "The capital of France is Paris.",
  "messages": [...],
  "metadata": {...},
  "tools_output": {...}
}
```

### Streaming Execution

**Endpoint:** `POST /agents/{agent_name}/stream`

```bash
curl -X POST "http://localhost:8000/agents/my-assistant/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input": "Explain quantum computing"
    }
  }'
```

This returns Server-Sent Events (SSE) for real-time streaming.

### Python Client Example

```python
import httpx
import asyncio

async def stream_agent_response():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/agents/my-assistant/stream",
            json={"input": {"input": "Tell me about AI"}}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    print(f"Event: {line[6:]}")

asyncio.run(stream_agent_response())
```

## Configuration Management

### Validate Configuration Before Creating Agent

**Endpoint:** `POST /config/validate`

```bash
curl -X POST "http://localhost:8000/config/validate" \
  -H "Content-Type: application/json" \
  -d @my-agent-config.json
```

### Validate YAML Configuration

**Endpoint:** `POST /config/validate-yaml`

```bash
curl -X POST "http://localhost:8000/config/validate-yaml" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@my-agent.yaml"
```

## Monitoring and Management

### List All Agents

```bash
curl http://localhost:8000/agents
```

### Get Agent Information

```bash
curl http://localhost:8000/agents/my-assistant
```

### Delete Agent

```bash
curl -X DELETE http://localhost:8000/agents/my-assistant
```

### Remove Custom Tool

```bash
curl -X DELETE http://localhost:8000/tools/custom/email_validator
```

### Get Metrics

```bash
curl http://localhost:8000/metrics
```

## Examples

### Example 1: Customer Support Bot with YAML

**File: `customer-support.yaml`**
```yaml
name: "support-bot"
description: "Intelligent customer support agent"
llm_provider: "openai"
model: "gpt-4"
api_key_env: "OPENAI_API_KEY"
workflow_type: "conditional"

tools:
  - "web_search"
  - name: "ticket_system"
    description: "Create and manage support tickets"
    function_code: |
      def create_ticket(issue: str, priority: str = "medium") -> str:
          # Mock ticket creation
          import random
          ticket_id = f"TICK-{random.randint(1000, 9999)}"
          return f"Created ticket {ticket_id} for issue: {issue} (Priority: {priority})"
    parameters_schema:
      issue:
        type: "string"
        description: "Description of the issue"
      priority:
        type: "string"
        description: "Priority level: low, medium, high"
        default: "medium"

nodes:
  - name: "classify_issue"
    type: "llm"
    prompt: |
      Classify this customer issue into one of:
      - technical: Technical problems or bugs
      - billing: Payment or subscription issues  
      - account: Account access or settings
      - general: General inquiries
      Respond with only the category.
      
  - name: "route_issue"
    type: "conditional"
    condition: "state['output'].strip().lower()"
    branches:
      "technical": "handle_technical"
      "billing": "handle_billing"
      "account": "handle_account"
      "default": "handle_general"
      
  - name: "handle_technical"
    type: "tool"
    tool: "ticket_system"
    tool_config:
      issue: "$input"
      priority: "high"
      
  - name: "handle_billing"
    type: "llm"
    prompt: "Provide helpful billing support. Be empathetic and offer clear solutions."
    
  - name: "handle_account"
    type: "llm"
    prompt: "Help with account-related issues. Guide through troubleshooting steps."
    
  - name: "handle_general"
    type: "tool"
    tool: "web_search"
    
  - name: "final_response"
    type: "llm"
    prompt: |
      Provide a professional, helpful customer support response based on the previous analysis.
      Include:
      1. Acknowledgment of the issue
      2. Clear solution or next steps
      3. Ticket number if one was created
      4. Offer for additional help

edges:
  - source: "classify_issue"
    target: "route_issue"
  - source: "handle_technical"
    target: "final_response"
  - source: "handle_billing" 
    target: "final_response"
  - source: "handle_account"
    target: "final_response"
  - source: "handle_general"
    target: "final_response"

entry_point: "classify_issue"
```

**Usage:**
```bash
# 1. Create the agent
curl -X POST "http://localhost:8000/agents/from-yaml" \
  -F "file=@customer-support.yaml"

# 2. Test with different issue types
curl -X POST "http://localhost:8000/agents/support-bot/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input": "My payment failed and I cannot access my account"
    }
  }'
```

### Example 2: Data Analysis Agent

**Step 1:** Register custom data analysis tool
```bash
curl -X POST "http://localhost:8000/tools/custom" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "csv_analyzer",
    "description": "Analyze CSV data files",
    "function_code": "def analyze_csv(file_path: str, columns: str = \"all\") -> str:\n    import pandas as pd\n    try:\n        df = pd.read_csv(file_path)\n        if columns == \"all\":\n            analysis = f\"Dataset has {len(df)} rows and {len(df.columns)} columns.\\nColumns: {list(df.columns)}\\nSummary:\\n{df.describe()}\"\n        else:\n            col_list = [c.strip() for c in columns.split(\",\")]\n            analysis = f\"Analysis for columns {col_list}:\\n{df[col_list].describe()}\"\n        return analysis\n    except Exception as e:\n        return f\"Error analyzing CSV: {str(e)}\"",
    "parameters_schema": {
      "file_path": {
        "type": "string",
        "description": "Path to the CSV file"
      },
      "columns": {
        "type": "string", 
        "description": "Comma-separated column names, or \"all\" for all columns",
        "default": "all"
      }
    }
  }'
```

**Step 2:** Create agent
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data-analyst",
    "description": "Data analysis agent",
    "llm_provider": "openai",
    "model": "gpt-4",
    "api_key_env": "OPENAI_API_KEY",
    "workflow_type": "sequential",
    "tools": ["csv_analyzer"],
    "nodes": [
      {
        "name": "analyze_data",
        "type": "tool",
        "tool": "csv_analyzer",
        "tool_config": {
          "file_path": "$input",
          "columns": "all"
        }
      },
      {
        "name": "interpret_results",
        "type": "llm",
        "prompt": "Interpret the data analysis results and provide insights in plain English. Highlight key findings and trends."
      }
    ]
  }'
```

**Step 3:** Use the agent
```bash
curl -X POST "http://localhost:8000/agents/data-analyst/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "input": "/path/to/sales_data.csv"
    }
  }'
```

## Error Handling

### Common Error Responses

**400 Bad Request:** Invalid configuration or parameters
```json
{
  "detail": "Invalid configuration: missing required field 'llm_provider'"
}
```

**404 Not Found:** Agent or tool not found
```json
{
  "detail": "Agent 'non-existent-agent' not found"
}
```

**500 Internal Server Error:** Server-side error
```json
{
  "detail": "Internal server error"
}
```

### Best Practices

1. **Always validate configurations** before creating agents
2. **Use meaningful names** for agents and tools
3. **Test custom tools** before using them in production agents
4. **Monitor metrics** for performance insights
5. **Use streaming** for long-running operations
6. **Implement proper error handling** in custom tools
7. **Set appropriate timeouts** for agents with external dependencies

### Troubleshooting

1. **Agent creation fails:** Check API keys and configuration format
2. **Custom tool errors:** Verify function code syntax and dependencies
3. **Tool not found:** Ensure custom tools are registered before use
4. **Slow responses:** Check tool performance and set appropriate timeouts
5. **Memory issues:** Monitor agent state size and use checkpoints for long conversations

This guide covers the main functionality of the LangGraph Agent Builder API. For more advanced features and customization options, refer to the main documentation. 
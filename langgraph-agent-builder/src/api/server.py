"""FastAPI server for LangGraph Agent Builder."""

from typing import Dict, Any, Optional, List
import json
import asyncio
from contextlib import asynccontextmanager
from io import StringIO

# Import with fallbacks
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
    from fastapi.responses import JSONResponse, StreamingResponse
except ImportError:
    # Fallback FastAPI implementation for demonstration
    class FastAPI:
        def __init__(self, **kwargs):
            pass
        def get(self, path): return lambda func: func
        def post(self, path): return lambda func: func
        def delete(self, path): return lambda func: func
        def exception_handler(self, exc_type): return lambda func: func
    
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
    
    class JSONResponse:
        def __init__(self, **kwargs): pass
    
    class StreamingResponse:
        def __init__(self, *args, **kwargs): pass
    
    class BackgroundTasks:
        pass
    
    def File(**kwargs):
        return None
    
    class UploadFile:
        pass
    
    def Form(**kwargs):
        return None

try:
    import yaml
except ImportError:
    # Fallback YAML implementation
    class yaml:
        @staticmethod
        def safe_load(content):
            raise ImportError("PyYAML not available. Install with: pip install pyyaml")
        
        @staticmethod
        def dump(data, file, **kwargs):
            raise ImportError("PyYAML not available. Install with: pip install pyyaml")
        
        class YAMLError(Exception):
            pass

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    # Fallback prometheus implementation
    def generate_latest():
        return b"# Prometheus not available"
    
    CONTENT_TYPE_LATEST = "text/plain"

from ..config import AgentConfig, AgentRunConfig
from ..builders import AgentBuilder
from ..core import ToolRegistry
from ..core.custom_tools import CustomToolDefinition, EXAMPLE_TOOLS
from ..utils import MetricsCollector, setup_logging, get_logger


logger = get_logger(__name__)


class AgentManager:
    """Manages agent instances."""
    
    def __init__(self):
        """Initialize agent manager."""
        self.agents: Dict[str, Any] = {}
        self.tool_registry = ToolRegistry()
        self.builder = AgentBuilder(
            tool_registry=self.tool_registry,
            metrics_collector=MetricsCollector()
        )
    
    def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent."""
        agent = self.builder.build(config)
        self.agents[config.name] = agent
        return config.name
    
    def get_agent(self, name: str) -> Any:
        """Get an agent by name."""
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not found")
        return self.agents[name]
    
    def list_agents(self) -> List[str]:
        """List all agent names."""
        return list(self.agents.keys())
    
    def delete_agent(self, name: str) -> None:
        """Delete an agent."""
        if name in self.agents:
            del self.agents[name]


# Global agent manager
agent_manager = AgentManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging(format="console")
    logger.info("LangGraph Agent Builder API starting up")
    yield
    # Shutdown
    logger.info("LangGraph Agent Builder API shutting down")


# Create FastAPI app
app = FastAPI(
    title="LangGraph Agent Builder API",
    description="API for building and running LangGraph agents dynamically",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LangGraph Agent Builder API",
        "version": "0.1.0"
    }


@app.post("/agents")
async def create_agent(config: AgentConfig):
    """Create a new agent from configuration."""
    try:
        agent_name = agent_manager.create_agent(config)
        logger.info(f"Created agent: {agent_name}")
        return {
            "status": "success",
            "agent_name": agent_name,
            "message": f"Agent '{agent_name}' created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create agent: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/agents")
async def list_agents():
    """List all agents."""
    return {
        "agents": agent_manager.list_agents()
    }


@app.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """Get information about a specific agent."""
    try:
        agent = agent_manager.get_agent(agent_name)
        return {
            "name": agent.config.name,
            "description": agent.config.description,
            "version": agent.config.version,
            "workflow_type": agent.config.workflow_type,
            "nodes": [node.dict() for node in agent.config.nodes],
            "tools": agent.config.tools,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/agents/{agent_name}")
async def delete_agent(agent_name: str):
    """Delete an agent."""
    try:
        agent_manager.delete_agent(agent_name)
        return {
            "status": "success",
            "message": f"Agent '{agent_name}' deleted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/agents/{agent_name}/invoke")
async def invoke_agent(
    agent_name: str,
    run_config: AgentRunConfig,
    background_tasks: BackgroundTasks
):
    """Invoke an agent with the given input."""
    try:
        agent = agent_manager.get_agent(agent_name)
        result = await agent.ainvoke(
            input_data=run_config.input,
            config=run_config.config,
            thread_id=run_config.thread_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to invoke agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/{agent_name}/stream")
async def stream_agent(
    agent_name: str,
    run_config: AgentRunConfig
):
    """Stream agent execution."""
    try:
        agent = agent_manager.get_agent(agent_name)
        
        async def event_generator():
            """Generate SSE events."""
            async for event in agent.astream(
                input_data=run_config.input,
                config=run_config.config,
                thread_id=run_config.thread_id
            ):
                # Format as Server-Sent Event
                data = json.dumps(event)
                yield f"data: {data}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to stream agent {agent_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Get Prometheus metrics."""
    return StreamingResponse(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/agents/from-yaml")
async def create_agent_from_yaml(file: UploadFile = File(...)):
    """Create an agent from a YAML configuration file."""
    try:
        # Read and parse YAML file
        content = await file.read()
        config_dict = yaml.safe_load(content.decode('utf-8'))
        
        # Validate and create agent config
        config = AgentConfig(**config_dict)
        agent_name = agent_manager.create_agent(config)
        
        logger.info(f"Created agent from YAML: {agent_name}")
        return {
            "status": "success",
            "agent_name": agent_name,
            "message": f"Agent '{agent_name}' created successfully from YAML file"
        }
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to create agent from YAML: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tools/custom")
async def register_custom_tool(tool_definition: CustomToolDefinition):
    """Register a custom tool."""
    try:
        # Create a temporary tool manager to register the tool
        from ..core import ToolManager
        temp_tool_manager = ToolManager(agent_manager.tool_registry)
        tool_instance = temp_tool_manager.register_custom_tool_from_definition(tool_definition)
        
        # Also register in the global registry for future agents
        agent_manager.tool_registry.register_tool(tool_definition.name, tool_instance)
        
        logger.info(f"Registered custom tool: {tool_definition.name}")
        return {
            "status": "success",
            "tool_name": tool_definition.name,
            "message": f"Custom tool '{tool_definition.name}' registered successfully"
        }
    except Exception as e:
        logger.error(f"Failed to register custom tool: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tools/custom/examples")
async def get_custom_tool_examples():
    """Get examples of custom tool definitions."""
    return {
        "examples": EXAMPLE_TOOLS,
        "usage": {
            "description": "Use these examples as templates for creating your own custom tools",
            "endpoint": "POST /tools/custom",
            "note": "You can either provide function_code (inline Python code) or module_path + function_name (reference to a file)"
        }
    }


@app.get("/tools")
async def list_all_tools():
    """List all available tools (built-in and custom)."""
    try:
        # Get tool manager from any existing agent or create a new one
        if agent_manager.agents:
            # Use tool manager from first agent
            first_agent = next(iter(agent_manager.agents.values()))
            all_tools = first_agent.tool_manager.list_all_tools()
        else:
            # Create a temporary tool manager
            from ..core import ToolManager
            tool_manager = ToolManager()
            all_tools = tool_manager.list_all_tools()
        
        return {
            "tools": all_tools,
            "count": len(all_tools)
        }
    except Exception as e:
        logger.error(f"Failed to list tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tools/custom/{tool_name}")
async def remove_custom_tool(tool_name: str):
    """Remove a custom tool."""
    try:
        # Remove from all agent tool managers
        removed = False
        for agent in agent_manager.agents.values():
            if agent.tool_manager.custom_tool_manager.remove_tool(tool_name):
                removed = True
        
        if removed:
            return {
                "status": "success",
                "message": f"Custom tool '{tool_name}' removed successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Custom tool '{tool_name}' not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove custom tool: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/validate")
async def validate_agent_config(config: AgentConfig):
    """Validate an agent configuration without creating the agent."""
    try:
        # The Pydantic model validation happens automatically
        # Additional custom validation can be added here
        
        return {
            "status": "valid",
            "message": "Agent configuration is valid",
            "summary": {
                "name": config.name,
                "nodes_count": len(config.nodes),
                "tools_count": len(config.tools),
                "workflow_type": config.workflow_type
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")


@app.post("/config/validate-yaml")
async def validate_yaml_config(file: UploadFile = File(...)):
    """Validate a YAML agent configuration file."""
    try:
        # Read and parse YAML file
        content = await file.read()
        config_dict = yaml.safe_load(content.decode('utf-8'))
        
        # Validate configuration
        config = AgentConfig(**config_dict)
        
        return {
            "status": "valid",
            "message": "YAML configuration is valid",
            "summary": {
                "name": config.name,
                "nodes_count": len(config.nodes),
                "tools_count": len(config.tools),
                "workflow_type": config.workflow_type
            }
        }
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents_count": len(agent_manager.agents)
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    ) 
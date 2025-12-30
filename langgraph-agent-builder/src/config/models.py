"""Configuration models for the LangGraph Agent Builder."""

from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    BEDROCK = "bedrock"
    CUSTOM = "custom"


class NodeType(str, Enum):
    """Types of nodes in the agent workflow."""
    LLM = "llm"
    TOOL = "tool"
    CONDITIONAL = "conditional"
    HUMAN_INPUT = "human_input"
    CUSTOM = "custom"


class WorkflowType(str, Enum):
    """Types of agent workflows."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    CYCLIC = "cyclic"
    CUSTOM = "custom"


class ToolConfig(BaseModel):
    """Configuration for a tool."""
    name: str = Field(..., description="Name of the tool")
    type: str = Field(..., description="Type of the tool")
    description: Optional[str] = Field(None, description="Description of the tool")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    
    class Config:
        extra = "allow"


class NodeConfig(BaseModel):
    """Configuration for a workflow node."""
    name: str = Field(..., description="Unique name of the node")
    type: NodeType = Field(..., description="Type of the node")
    description: Optional[str] = Field(None, description="Description of the node")
    
    # LLM specific fields
    prompt: Optional[str] = Field(None, description="Prompt template for LLM nodes")
    model: Optional[str] = Field(None, description="Specific model to use for this node")
    temperature: Optional[float] = Field(None, description="Temperature for LLM sampling")
    
    # Tool specific fields
    tool: Optional[str] = Field(None, description="Tool name for tool nodes")
    tool_config: Optional[Dict[str, Any]] = Field(None, description="Tool-specific configuration")
    
    # Conditional specific fields
    condition: Optional[str] = Field(None, description="Condition expression for conditional nodes")
    branches: Optional[Dict[str, str]] = Field(None, description="Branch mappings for conditional nodes")
    
    # General fields
    retry_config: Optional[Dict[str, Any]] = Field(None, description="Retry configuration")
    timeout: Optional[int] = Field(None, description="Timeout in seconds")
    
    @validator('prompt')
    def prompt_required_for_llm(cls, v, values):
        if values.get('type') == NodeType.LLM and not v:
            raise ValueError("Prompt is required for LLM nodes")
        return v
    
    @validator('tool')
    def tool_required_for_tool_node(cls, v, values):
        if values.get('type') == NodeType.TOOL and not v:
            raise ValueError("Tool name is required for tool nodes")
        return v
    
    class Config:
        extra = "allow"


class EdgeConfig(BaseModel):
    """Configuration for edges between nodes."""
    source: str = Field(..., description="Source node name")
    target: str = Field(..., description="Target node name")
    condition: Optional[str] = Field(None, description="Condition for edge traversal")
    
    class Config:
        extra = "allow"


class StateSchema(BaseModel):
    """Schema definition for agent state."""
    fields: Dict[str, Dict[str, Any]] = Field(..., description="State field definitions")
    
    class Config:
        extra = "allow"


class AgentConfig(BaseModel):
    """Complete configuration for an agent."""
    # Basic information
    name: str = Field(..., description="Unique name of the agent")
    description: Optional[str] = Field(None, description="Description of the agent")
    version: str = Field("1.0.0", description="Version of the agent")
    
    # LLM configuration
    llm_provider: LLMProvider = Field(..., description="LLM provider to use")
    model: str = Field(..., description="Default model to use")
    api_key_env: Optional[str] = Field(None, description="Environment variable for API key")
    temperature: float = Field(0.7, description="Default temperature for LLM")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for responses")
    
    # Workflow configuration
    workflow_type: WorkflowType = Field(WorkflowType.SEQUENTIAL, description="Type of workflow")
    nodes: List[NodeConfig] = Field(..., description="List of nodes in the workflow")
    edges: Optional[List[EdgeConfig]] = Field(None, description="Custom edges between nodes")
    entry_point: Optional[str] = Field(None, description="Entry point node name")
    
    # Tools configuration
    tools: List[Union[str, ToolConfig]] = Field(default_factory=list, description="Tools available to the agent")
    
    # State configuration
    state_schema: Optional[StateSchema] = Field(None, description="Custom state schema")
    checkpointer: Optional[Dict[str, Any]] = Field(None, description="Checkpointer configuration")
    
    # Runtime configuration
    timeout: int = Field(300, description="Global timeout in seconds")
    max_iterations: int = Field(10, description="Maximum iterations for cyclic workflows")
    streaming: bool = Field(True, description="Enable streaming responses")
    
    # Observability configuration
    enable_logging: bool = Field(True, description="Enable structured logging")
    enable_metrics: bool = Field(True, description="Enable Prometheus metrics")
    enable_tracing: bool = Field(True, description="Enable distributed tracing")
    
    # Advanced configuration
    custom_handlers: Optional[List[str]] = Field(None, description="Custom handler class names")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('edges')
    def validate_edges(cls, v, values):
        if v and values.get('workflow_type') == WorkflowType.SEQUENTIAL:
            raise ValueError("Custom edges are not allowed for sequential workflows")
        return v
    
    @validator('entry_point')
    def validate_entry_point(cls, v, values):
        if v:
            node_names = [node.name for node in values.get('nodes', [])]
            if v not in node_names:
                raise ValueError(f"Entry point '{v}' not found in nodes")
        return v
    
    class Config:
        extra = "allow"


class AgentRunConfig(BaseModel):
    """Configuration for running an agent."""
    input: Dict[str, Any] = Field(..., description="Input data for the agent")
    config: Optional[Dict[str, Any]] = Field(None, description="Runtime configuration overrides")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata for this run")
    
    class Config:
        extra = "allow" 
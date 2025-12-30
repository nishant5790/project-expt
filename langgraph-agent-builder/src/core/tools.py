"""Tools registry and factory for LangGraph agents."""

from typing import Dict, List, Any, Callable, Optional, Union
from pydantic import BaseModel, Field
import importlib
import inspect
from .custom_tools import CustomToolManager, CustomToolDefinition

# Import LangChain components with fallbacks
try:
    from langchain_core.tools import BaseTool, StructuredTool
    from langchain.tools import tool
except ImportError:
    # Fallback tool implementations
    class BaseTool:
        def __init__(self, name=None, description=None):
            self.name = name
            self.description = description
            
        def invoke(self, input_data):
            return f"Tool {self.name} called with {input_data}"
    
    class StructuredTool(BaseTool):
        @classmethod
        def from_function(cls, func, name=None, description=None, args_schema=None):
            tool = cls(name=name or func.__name__, description=description or func.__doc__)
            tool.func = func
            tool.args_schema = args_schema
            return tool
            
        def invoke(self, input_data):
            if hasattr(self, 'func'):
                if isinstance(input_data, dict):
                    return self.func(**input_data)
                else:
                    return self.func(input_data)
            return super().invoke(input_data)
    
    def tool(name=None, description=None, args_schema=None):
        def decorator(func):
            func.name = name or func.__name__
            func.description = description or func.__doc__
            func.args_schema = args_schema
            return func
        return decorator

try:
    from langchain_community.tools import DuckDuckGoSearchRun
except ImportError:
    # Fallback search tool
    class DuckDuckGoSearchRun(BaseTool):
        def __init__(self):
            super().__init__(name="web_search", description="Search the web for information")
            
        def invoke(self, query):
            return f"Mock search results for: {query}"


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        """Initialize tool registry."""
        self._tools: Dict[str, Union[BaseTool, Callable]] = {}
        self._tool_configs: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default built-in tools."""
        # Web search tool
        self.register_tool(
            "web_search",
            DuckDuckGoSearchRun(),
            {
                "description": "Search the web for information",
                "category": "search"
            }
        )
        
        # Add more default tools as needed
        
    def register_tool(
        self,
        name: str,
        tool: Union[BaseTool, Callable],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a tool in the registry.
        
        Args:
            name: Unique name for the tool
            tool: The tool instance or function
            config: Additional configuration for the tool
        """
        self._tools[name] = tool
        self._tool_configs[name] = config or {}
        
    def get_tool(self, name: str) -> Union[BaseTool, Callable]:
        """Get a tool by name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        return self._tools[name]
    
    def get_tools(self, names: List[str]) -> List[Union[BaseTool, Callable]]:
        """Get multiple tools by names."""
        return [self.get_tool(name) for name in names]
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self._tools.keys())
    
    def get_tool_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a tool."""
        return self._tool_configs.get(name, {})


class ToolFactory:
    """Factory for creating tool instances."""
    
    @staticmethod
    def create_tool_from_function(
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        args_schema: Optional[BaseModel] = None
    ) -> StructuredTool:
        """
        Create a tool from a function.
        
        Args:
            func: The function to wrap as a tool
            name: Name for the tool
            description: Description of what the tool does
            args_schema: Pydantic model for argument validation
            
        Returns:
            A StructuredTool instance
        """
        if not name:
            name = func.__name__
            
        if not description:
            description = func.__doc__ or f"Tool: {name}"
            
        return StructuredTool.from_function(
            func=func,
            name=name,
            description=description,
            args_schema=args_schema
        )
    
    @staticmethod
    def create_tool_from_config(config: Dict[str, Any]) -> BaseTool:
        """
        Create a tool from configuration.
        
        Args:
            config: Tool configuration dictionary
            
        Returns:
            A tool instance
        """
        tool_type = config.get("type", "function")
        
        if tool_type == "function":
            # Create from function definition
            module_name = config.get("module")
            function_name = config.get("function")
            
            if not module_name or not function_name:
                raise ValueError("module and function required for function tools")
            
            # Import the function
            module = importlib.import_module(module_name)
            func = getattr(module, function_name)
            
            return ToolFactory.create_tool_from_function(
                func=func,
                name=config.get("name"),
                description=config.get("description")
            )
            
        elif tool_type == "class":
            # Create from class definition
            class_path = config.get("class")
            if not class_path:
                raise ValueError("class required for class tools")
            
            # Import the class
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)
            
            # Instantiate with parameters
            params = config.get("parameters", {})
            return tool_class(**params)
            
        else:
            raise ValueError(f"Unsupported tool type: {tool_type}")


# Example custom tools
class DatabaseQueryInput(BaseModel):
    """Input for database query tool."""
    query: str = Field(..., description="SQL query to execute")
    database: str = Field(default="default", description="Database to query")


@tool("database_query", args_schema=DatabaseQueryInput)
def database_query(query: str, database: str = "default") -> str:
    """
    Query a database and return results.
    
    This is a placeholder implementation. In production, this would
    connect to an actual database.
    """
    # Placeholder implementation
    return f"Executed query '{query}' on database '{database}'"


@tool("calculator")
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate
        
    Returns:
        The result of the calculation
    """
    try:
        # Safe evaluation of mathematical expressions
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


class ToolManager:
    """Manages tools for an agent."""
    
    def __init__(self, registry: Optional[ToolRegistry] = None, custom_tools_dir: Optional[str] = None):
        """Initialize tool manager."""
        self.registry = registry or ToolRegistry()
        self.custom_tool_manager = CustomToolManager(custom_tools_dir)
        
        # Load existing custom tools from directory
        self.custom_tool_manager.load_tools_from_directory()
        
    def load_tools(
        self,
        tool_configs: List[Union[str, Dict[str, Any]]]
    ) -> List[BaseTool]:
        """
        Load tools based on configurations.
        
        Args:
            tool_configs: List of tool names or configurations
            
        Returns:
            List of tool instances
        """
        tools = []
        
        for config in tool_configs:
            if isinstance(config, str):
                # Simple tool name - check custom tools first, then registry
                tool = self.custom_tool_manager.get_tool(config)
                if tool:
                    tools.append(tool)
                else:
                    tool = self.registry.get_tool(config)
                    tools.append(tool)
            elif isinstance(config, dict):
                # Check if it's a custom tool definition
                if "function_code" in config or ("module_path" in config and "function_name" in config):
                    # Create custom tool
                    tool_def = CustomToolDefinition(**config)
                    tool = self.custom_tool_manager.register_tool_from_definition(tool_def)
                    tools.append(tool)
                elif "name" in config and config["name"] in self.registry.list_tools():
                    # Get from registry with override config
                    tool = self.registry.get_tool(config["name"])
                    tools.append(tool)
                else:
                    # Create new tool from config using factory
                    tool = ToolFactory.create_tool_from_config(config)
                    tools.append(tool)
            else:
                raise ValueError(f"Invalid tool configuration: {config}")
                
        return tools
    
    def register_custom_tool(
        self,
        name: str,
        tool: Union[BaseTool, Callable, CustomToolDefinition],
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a custom tool."""
        if isinstance(tool, CustomToolDefinition):
            self.custom_tool_manager.register_tool_from_definition(tool)
        else:
            self.registry.register_tool(name, tool, config)
    
    def register_custom_tool_from_definition(self, tool_def: CustomToolDefinition) -> BaseTool:
        """Register a custom tool from definition."""
        return self.custom_tool_manager.register_tool_from_definition(tool_def)
    
    def list_all_tools(self) -> Dict[str, str]:
        """List all available tools (built-in and custom)."""
        all_tools = {}
        
        # Add built-in tools
        for name in self.registry.list_tools():
            config = self.registry.get_tool_config(name)
            all_tools[name] = config.get('description', 'Built-in tool')
        
        # Add custom tools
        all_tools.update(self.custom_tool_manager.list_tools())
        
        return all_tools
    
    def get_custom_tool_examples(self) -> Dict[str, Any]:
        """Get example custom tool definitions."""
        from .custom_tools import EXAMPLE_TOOLS
        return EXAMPLE_TOOLS 
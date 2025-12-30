"""Custom tools manager for dynamic tool loading."""

import importlib
import inspect
import os
import sys
from typing import Dict, Any, Callable, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field

# Import structlog with fallback
try:
    import structlog
except ImportError:
    import logging
    class structlog:
        @staticmethod
        def get_logger(*args, **kwargs):
            return logging.getLogger(__name__)

# Import LangChain components with fallbacks
try:
    from langchain_core.tools import BaseTool, StructuredTool
    from langchain.tools import tool
except ImportError:
    # Use the same fallback implementations from tools.py
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


logger = structlog.get_logger(__name__)


class CustomToolDefinition(BaseModel):
    """Definition for a custom tool."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    function_code: Optional[str] = Field(None, description="Python function code as string")
    module_path: Optional[str] = Field(None, description="Path to Python module containing the tool")
    function_name: Optional[str] = Field(None, description="Name of the function in the module")
    parameters_schema: Optional[Dict[str, Any]] = Field(None, description="Pydantic schema for parameters")
    requirements: Optional[list] = Field(default_factory=list, description="Required Python packages")
    
    class Config:
        extra = "allow"


class CustomToolManager:
    """Manages custom tools with dynamic loading capabilities."""
    
    def __init__(self, tools_directory: Optional[str] = None):
        """
        Initialize custom tool manager.
        
        Args:
            tools_directory: Directory containing custom tool modules
        """
        self.tools_directory = Path(tools_directory) if tools_directory else Path("custom_tools")
        self.loaded_tools: Dict[str, BaseTool] = {}
        self.tool_definitions: Dict[str, CustomToolDefinition] = {}
        
        # Ensure tools directory exists
        self.tools_directory.mkdir(exist_ok=True)
        
        # Add tools directory to Python path
        if str(self.tools_directory) not in sys.path:
            sys.path.insert(0, str(self.tools_directory))
    
    def register_tool_from_definition(self, tool_def: CustomToolDefinition) -> BaseTool:
        """
        Register a tool from a definition.
        
        Args:
            tool_def: Tool definition
            
        Returns:
            The created tool instance
        """
        logger.info(f"Registering custom tool: {tool_def.name}")
        
        try:
            if tool_def.function_code:
                # Create tool from inline code
                tool_instance = self._create_tool_from_code(tool_def)
            elif tool_def.module_path and tool_def.function_name:
                # Create tool from module
                tool_instance = self._create_tool_from_module(tool_def)
            else:
                raise ValueError("Tool definition must include either function_code or module_path+function_name")
            
            self.loaded_tools[tool_def.name] = tool_instance
            self.tool_definitions[tool_def.name] = tool_def
            
            logger.info(f"Successfully registered tool: {tool_def.name}")
            return tool_instance
            
        except Exception as e:
            logger.error(f"Failed to register tool {tool_def.name}: {str(e)}")
            raise
    
    def _create_tool_from_code(self, tool_def: CustomToolDefinition) -> BaseTool:
        """Create a tool from inline Python code."""
        # Create a safe namespace for execution
        namespace = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sorted': sorted,
                'sum': sum,
                'min': min,
                'max': max,
            },
            'requests': None,  # Will import if needed
            'json': None,
            'datetime': None,
            'os': None,
        }
        
        # Import commonly used modules
        try:
            import requests
            namespace['requests'] = requests
        except ImportError:
            pass
            
        try:
            import json
            namespace['json'] = json
        except ImportError:
            pass
            
        try:
            import datetime
            namespace['datetime'] = datetime
        except ImportError:
            pass
        
        # Execute the function code
        exec(tool_def.function_code, namespace)
        
        # Find the function in the namespace
        func = None
        for name, obj in namespace.items():
            if callable(obj) and not name.startswith('_') and hasattr(obj, '__name__'):
                func = obj
                break
        
        if not func:
            raise ValueError("No callable function found in the provided code")
        
        # Create parameter schema if provided
        args_schema = None
        if tool_def.parameters_schema:
            args_schema = self._create_pydantic_model(
                f"{tool_def.name}Input",
                tool_def.parameters_schema
            )
        
        # Create the tool
        return StructuredTool.from_function(
            func=func,
            name=tool_def.name,
            description=tool_def.description,
            args_schema=args_schema
        )
    
    def _create_tool_from_module(self, tool_def: CustomToolDefinition) -> BaseTool:
        """Create a tool from a module file."""
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location("custom_tool", tool_def.module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the function
            func = getattr(module, tool_def.function_name)
            
            # Create parameter schema if provided
            args_schema = None
            if tool_def.parameters_schema:
                args_schema = self._create_pydantic_model(
                    f"{tool_def.name}Input",
                    tool_def.parameters_schema
                )
            
            # Create the tool
            return StructuredTool.from_function(
                func=func,
                name=tool_def.name,
                description=tool_def.description,
                args_schema=args_schema
            )
            
        except Exception as e:
            logger.error(f"Failed to load tool from module {tool_def.module_path}: {str(e)}")
            raise
    
    def _create_pydantic_model(self, name: str, schema: Dict[str, Any]) -> type:
        """Create a Pydantic model from a schema definition."""
        fields = {}
        
        for field_name, field_def in schema.items():
            field_type = field_def.get('type', str)
            field_description = field_def.get('description', '')
            field_default = field_def.get('default', ...)
            
            # Map string types to Python types
            type_mapping = {
                'string': str,
                'str': str,
                'integer': int,
                'int': int,
                'number': float,
                'float': float,
                'boolean': bool,
                'bool': bool,
                'array': list,
                'list': list,
                'object': dict,
                'dict': dict,
            }
            
            if isinstance(field_type, str):
                field_type = type_mapping.get(field_type, str)
            
            if field_default == ...:
                fields[field_name] = (field_type, Field(description=field_description))
            else:
                fields[field_name] = (field_type, Field(default=field_default, description=field_description))
        
        return type(name, (BaseModel,), {'__annotations__': {k: v[0] for k, v in fields.items()}, 
                                         **{k: v[1] for k, v in fields.items()}})
    
    def save_tool_to_file(self, tool_def: CustomToolDefinition) -> str:
        """
        Save a tool definition to a Python file.
        
        Args:
            tool_def: Tool definition
            
        Returns:
            Path to the saved file
        """
        if not tool_def.function_code:
            raise ValueError("Tool definition must include function_code to save to file")
        
        filename = f"{tool_def.name}.py"
        filepath = self.tools_directory / filename
        
        # Create the tool file
        tool_content = f'''"""
Custom tool: {tool_def.name}
{tool_def.description}
"""

{tool_def.function_code}
'''
        
        with open(filepath, 'w') as f:
            f.write(tool_content)
        
        logger.info(f"Saved tool {tool_def.name} to {filepath}")
        return str(filepath)
    
    def load_tools_from_directory(self) -> Dict[str, BaseTool]:
        """Load all tools from the tools directory."""
        loaded = {}
        
        for file_path in self.tools_directory.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
                
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find tool functions (functions decorated with @tool or having specific attributes)
                for name, obj in inspect.getmembers(module):
                    if callable(obj) and hasattr(obj, 'name') and hasattr(obj, 'description'):
                        tool_name = getattr(obj, 'name', name)
                        loaded[tool_name] = obj
                        self.loaded_tools[tool_name] = obj
                        logger.info(f"Loaded tool from file: {tool_name}")
                        
            except Exception as e:
                logger.error(f"Failed to load tool from {file_path}: {str(e)}")
                continue
        
        return loaded
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.loaded_tools.get(name)
    
    def list_tools(self) -> Dict[str, str]:
        """List all loaded tools with descriptions."""
        return {
            name: getattr(tool, 'description', 'No description')
            for name, tool in self.loaded_tools.items()
        }
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool from the registry."""
        if name in self.loaded_tools:
            del self.loaded_tools[name]
            if name in self.tool_definitions:
                del self.tool_definitions[name]
            return True
        return False


# Example custom tools that users can use as templates
EXAMPLE_TOOLS = {
    "weather_api": {
        "name": "weather_api",
        "description": "Get current weather for a location",
        "function_code": '''
def get_weather(location: str) -> str:
    """Get weather information for a location."""
    import requests
    
    # This is a mock implementation
    # In real usage, you would call an actual weather API
    return f"The weather in {location} is sunny with 72°F"
''',
        "parameters_schema": {
            "location": {
                "type": "string",
                "description": "The location to get weather for"
            }
        }
    },
    
    "file_reader": {
        "name": "file_reader", 
        "description": "Read contents of a text file",
        "function_code": '''
def read_file(file_path: str) -> str:
    """Read the contents of a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
''',
        "parameters_schema": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to read"
            }
        }
    },
    
    "url_fetcher": {
        "name": "url_fetcher",
        "description": "Fetch content from a URL",
        "function_code": '''
def fetch_url(url: str) -> str:
    """Fetch content from a URL."""
    import requests
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text[:5000]  # Limit to first 5000 characters
    except Exception as e:
        return f"Error fetching URL: {str(e)}"
''',
        "parameters_schema": {
            "url": {
                "type": "string", 
                "description": "The URL to fetch content from"
            }
        }
    }
} 
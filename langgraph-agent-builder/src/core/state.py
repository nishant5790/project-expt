"""State management for LangGraph agents."""

from typing import TypedDict, Dict, Any, Optional, List, Annotated
from pydantic import BaseModel

# Import with fallback
try:
    from langgraph.graph import add_messages
except ImportError:
    # Fallback implementation for add_messages
    def add_messages(x: List[Dict[str, Any]], y: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback add_messages function."""
        return x + y


class BaseAgentState(TypedDict):
    """Base state for all agents."""
    messages: Annotated[List[Dict[str, Any]], add_messages]
    input: str
    output: Optional[str]
    current_node: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]
    context: Dict[str, Any]
    iterations: int


class ExtendedAgentState(BaseAgentState):
    """Extended state with additional fields."""
    tools_output: Dict[str, Any]
    intermediate_steps: List[Dict[str, Any]]
    user_feedback: Optional[str]
    memory: Dict[str, Any]
    
    
def create_state_class(state_schema: Optional[Dict[str, Dict[str, Any]]] = None) -> type:
    """
    Dynamically create a state class based on schema.
    
    Args:
        state_schema: Dictionary defining additional state fields
        
    Returns:
        A TypedDict class for the agent state
    """
    if not state_schema:
        return BaseAgentState
    
    # Start with base state fields
    fields = {
        'messages': Annotated[List[Dict[str, Any]], add_messages],
        'input': str,
        'output': Optional[str],
        'current_node': Optional[str],
        'error': Optional[str],
        'metadata': Dict[str, Any],
        'context': Dict[str, Any],
        'iterations': int,
    }
    
    # Add custom fields from schema
    for field_name, field_config in state_schema.items():
        field_type = field_config.get('type', Any)
        required = field_config.get('required', False)
        
        # Convert string types to Python types
        type_mapping = {
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': List[Any],
            'dict': Dict[str, Any],
        }
        
        if isinstance(field_type, str):
            field_type = type_mapping.get(field_type, Any)
        
        if not required:
            field_type = Optional[field_type]
            
        fields[field_name] = field_type
    
    # Create the TypedDict class dynamically
    return type('CustomAgentState', (TypedDict,), fields)


class StateManager:
    """Manages agent state throughout execution."""
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        """Initialize state manager."""
        self.state = initial_state or self._get_default_state()
        
    def _get_default_state(self) -> Dict[str, Any]:
        """Get default state."""
        return {
            'messages': [],
            'input': '',
            'output': None,
            'current_node': None,
            'error': None,
            'metadata': {},
            'context': {},
            'iterations': 0,
        }
    
    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update state with new values."""
        self.state.update(updates)
        return self.state
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from state."""
        return self.state.get(key, default)
    
    def increment_iterations(self) -> int:
        """Increment iteration counter."""
        self.state['iterations'] += 1
        return self.state['iterations']
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the state."""
        if 'messages' not in self.state:
            self.state['messages'] = []
        self.state['messages'].append(message)
    
    def set_error(self, error: str) -> None:
        """Set error in state."""
        self.state['error'] = error
    
    def clear_error(self) -> None:
        """Clear error from state."""
        self.state['error'] = None
    
    def snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of current state."""
        return dict(self.state) 
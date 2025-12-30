"""Node builders for LangGraph agents."""

from typing import Dict, Any, Callable, List, Optional
from ..config import NodeConfig, NodeType

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
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.runnables import RunnablePassthrough
except ImportError:
    # Fallback message implementations
    class BaseMessage:
        def __init__(self, content="", role=""):
            self.content = content
            self.role = role
    
    class HumanMessage(BaseMessage):
        def __init__(self, content=""):
            super().__init__(content, "human")
    
    class AIMessage(BaseMessage):
        def __init__(self, content=""):
            super().__init__(content, "ai")
    
    class SystemMessage(BaseMessage):
        def __init__(self, content=""):
            super().__init__(content, "system")
    
    class ChatPromptTemplate:
        @classmethod
        def from_messages(cls, messages):
            return cls()
    
    class MessagesPlaceholder:
        def __init__(self, name):
            self.name = name
    
    class RunnablePassthrough:
        pass

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
except ImportError:
    # Fallback retry implementation
    def retry(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def stop_after_attempt(attempts):
        return None
    
    def wait_exponential(min=1, max=10):
        return None


logger = structlog.get_logger()


class NodeBuilder:
    """Base class for building nodes."""
    
    def build(self, config: NodeConfig, context: Dict[str, Any]) -> Callable:
        """Build a node function from configuration."""
        raise NotImplementedError


class LLMNodeBuilder(NodeBuilder):
    """Builder for LLM nodes."""
    
    def build(self, config: NodeConfig, context: Dict[str, Any]) -> Callable:
        """Build an LLM node."""
        llm_manager = context.get("llm_manager")
        if not llm_manager:
            raise ValueError("LLM manager not provided in context")
        
        # Get node-specific LLM configuration
        llm_config = {
            "model": config.model,
            "temperature": config.temperature,
        }
        llm_config = {k: v for k, v in llm_config.items() if v is not None}
        
        # Get LLM instance
        llm = llm_manager.get_llm(
            node_config=llm_config,
            cache_key=config.name
        )
        
        # Build prompt template
        prompt = self._build_prompt(config.prompt)
        
        # Create the node function
        def llm_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute LLM node."""
            try:
                logger.info(f"Executing LLM node: {config.name}")
                
                # Update current node
                state["current_node"] = config.name
                
                # Prepare messages
                messages = state.get("messages", [])
                
                # Add system prompt if needed
                if config.prompt and not any(isinstance(m, SystemMessage) for m in messages):
                    messages = [SystemMessage(content=config.prompt)] + messages
                
                # Invoke LLM
                response = llm.invoke(messages)
                
                # Update state
                state["messages"] = messages + [response]
                state["output"] = response.content
                
                logger.info(f"LLM node {config.name} completed successfully")
                return state
                
            except Exception as e:
                logger.error(f"Error in LLM node {config.name}: {str(e)}")
                state["error"] = str(e)
                raise
        
        # Apply retry logic if configured
        if config.retry_config:
            llm_node = self._apply_retry(llm_node, config.retry_config)
            
        return llm_node
    
    def _build_prompt(self, prompt_template: str) -> ChatPromptTemplate:
        """Build prompt template."""
        return ChatPromptTemplate.from_messages([
            ("system", prompt_template),
            MessagesPlaceholder("messages")
        ])
    
    def _apply_retry(self, func: Callable, retry_config: Dict[str, Any]) -> Callable:
        """Apply retry logic to a function."""
        max_attempts = retry_config.get("max_attempts", 3)
        min_wait = retry_config.get("min_wait", 1)
        max_wait = retry_config.get("max_wait", 10)
        
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(min=min_wait, max=max_wait)
        )(func)


class ToolNodeBuilder(NodeBuilder):
    """Builder for tool nodes."""
    
    def build(self, config: NodeConfig, context: Dict[str, Any]) -> Callable:
        """Build a tool node."""
        tool_manager = context.get("tool_manager")
        if not tool_manager:
            raise ValueError("Tool manager not provided in context")
        
        # Get the tool
        tool = tool_manager.registry.get_tool(config.tool)
        
        # Create the node function
        def tool_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute tool node."""
            try:
                logger.info(f"Executing tool node: {config.name}")
                
                # Update current node
                state["current_node"] = config.name
                
                # Prepare tool input
                tool_input = self._prepare_tool_input(state, config.tool_config)
                
                # Invoke tool
                result = tool.invoke(tool_input)
                
                # Update state
                state["tools_output"] = state.get("tools_output", {})
                state["tools_output"][config.name] = result
                
                # Add result to messages
                messages = state.get("messages", [])
                messages.append(AIMessage(content=f"Tool {config.tool} result: {result}"))
                state["messages"] = messages
                
                logger.info(f"Tool node {config.name} completed successfully")
                return state
                
            except Exception as e:
                logger.error(f"Error in tool node {config.name}: {str(e)}")
                state["error"] = str(e)
                raise
        
        # Apply retry logic if configured
        if config.retry_config:
            tool_node = self._apply_retry(tool_node, config.retry_config)
            
        return tool_node
    
    def _prepare_tool_input(
        self,
        state: Dict[str, Any],
        tool_config: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Prepare input for tool invocation."""
        tool_input = {}
        
        if tool_config:
            # Map state values to tool input
            for key, value in tool_config.items():
                if isinstance(value, str) and value.startswith("$"):
                    # Reference to state value
                    state_key = value[1:]
                    tool_input[key] = state.get(state_key)
                else:
                    tool_input[key] = value
        else:
            # Default: pass the last message content
            messages = state.get("messages", [])
            if messages:
                tool_input["input"] = messages[-1].content
                
        return tool_input
    
    def _apply_retry(self, func: Callable, retry_config: Dict[str, Any]) -> Callable:
        """Apply retry logic to a function."""
        max_attempts = retry_config.get("max_attempts", 3)
        min_wait = retry_config.get("min_wait", 1)
        max_wait = retry_config.get("max_wait", 10)
        
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(min=min_wait, max=max_wait)
        )(func)


class ConditionalNodeBuilder(NodeBuilder):
    """Builder for conditional nodes."""
    
    def build(self, config: NodeConfig, context: Dict[str, Any]) -> Callable:
        """Build a conditional node."""
        # Parse condition
        condition_func = self._parse_condition(config.condition)
        branches = config.branches or {}
        
        # Create the node function
        def conditional_node(state: Dict[str, Any]) -> str:
            """Execute conditional node."""
            try:
                logger.info(f"Executing conditional node: {config.name}")
                
                # Update current node
                state["current_node"] = config.name
                
                # Evaluate condition
                result = condition_func(state)
                
                # Determine next node
                next_node = branches.get(str(result), branches.get("default", "END"))
                
                logger.info(f"Conditional node {config.name} directing to: {next_node}")
                return next_node
                
            except Exception as e:
                logger.error(f"Error in conditional node {config.name}: {str(e)}")
                state["error"] = str(e)
                raise
                
        return conditional_node
    
    def _parse_condition(self, condition: str) -> Callable:
        """Parse condition string into a callable."""
        # Simple implementation - in production, use a proper expression parser
        def condition_func(state: Dict[str, Any]) -> Any:
            # Evaluate condition in a safe context
            safe_globals = {"state": state}
            try:
                return eval(condition, {"__builtins__": {}}, safe_globals)
            except Exception as e:
                logger.error(f"Error evaluating condition: {condition}, error: {str(e)}")
                return False
                
        return condition_func


class HumanInputNodeBuilder(NodeBuilder):
    """Builder for human input nodes."""
    
    def build(self, config: NodeConfig, context: Dict[str, Any]) -> Callable:
        """Build a human input node."""
        # Create the node function
        def human_input_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute human input node."""
            try:
                logger.info(f"Executing human input node: {config.name}")
                
                # Update current node
                state["current_node"] = config.name
                
                # In production, this would integrate with a UI or API
                # For now, we'll use a placeholder
                prompt = config.description or "Please provide input:"
                
                # Mark that human input is needed
                state["needs_human_input"] = True
                state["human_input_prompt"] = prompt
                
                # If human input is already provided, use it
                if "human_input" in state:
                    messages = state.get("messages", [])
                    messages.append(HumanMessage(content=state["human_input"]))
                    state["messages"] = messages
                    state["needs_human_input"] = False
                    del state["human_input"]
                
                logger.info(f"Human input node {config.name} completed")
                return state
                
            except Exception as e:
                logger.error(f"Error in human input node {config.name}: {str(e)}")
                state["error"] = str(e)
                raise
                
        return human_input_node


class CustomNodeBuilder(NodeBuilder):
    """Builder for custom nodes."""
    
    def build(self, config: NodeConfig, context: Dict[str, Any]) -> Callable:
        """Build a custom node."""
        # Load custom node function
        custom_handlers = context.get("custom_handlers", {})
        
        if config.name not in custom_handlers:
            raise ValueError(f"Custom handler not found for node: {config.name}")
            
        custom_func = custom_handlers[config.name]
        
        # Wrap the custom function
        def custom_node(state: Dict[str, Any]) -> Dict[str, Any]:
            """Execute custom node."""
            try:
                logger.info(f"Executing custom node: {config.name}")
                
                # Update current node
                state["current_node"] = config.name
                
                # Execute custom function
                result = custom_func(state, config)
                
                logger.info(f"Custom node {config.name} completed successfully")
                return result
                
            except Exception as e:
                logger.error(f"Error in custom node {config.name}: {str(e)}")
                state["error"] = str(e)
                raise
                
        return custom_node


class NodeFactory:
    """Factory for creating nodes."""
    
    def __init__(self):
        """Initialize node factory."""
        self._builders = {
            NodeType.LLM: LLMNodeBuilder(),
            NodeType.TOOL: ToolNodeBuilder(),
            NodeType.CONDITIONAL: ConditionalNodeBuilder(),
            NodeType.HUMAN_INPUT: HumanInputNodeBuilder(),
            NodeType.CUSTOM: CustomNodeBuilder(),
        }
    
    def create_node(
        self,
        config: NodeConfig,
        context: Dict[str, Any]
    ) -> Callable:
        """
        Create a node from configuration.
        
        Args:
            config: Node configuration
            context: Build context with managers and handlers
            
        Returns:
            A callable node function
        """
        builder = self._builders.get(config.type)
        if not builder:
            raise ValueError(f"Unsupported node type: {config.type}")
            
        return builder.build(config, context) 
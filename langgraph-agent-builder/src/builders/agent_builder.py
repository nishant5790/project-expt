"""Main agent builder for creating LangGraph agents from configuration."""

from typing import Dict, Any, List, Optional, Union

# Import structlog with fallback
try:
    import structlog
except ImportError:
    # Fallback structlog implementation
    import logging
    class structlog:
        @staticmethod
        def get_logger(*args, **kwargs):
            return logging.getLogger(__name__)

# Import LangGraph components with fallbacks
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Fallback implementation if langgraph is not available
    class StateGraph:
        def __init__(self, state_type):
            self.state_type = state_type
            self.nodes = {}
            self.edges = []
            
        def add_node(self, name, func):
            self.nodes[name] = func
            
        def add_edge(self, source, target):
            self.edges.append((source, target))
            
        def add_conditional_edges(self, source, func):
            self.nodes[source] = func
            
        def set_entry_point(self, node):
            self.entry_point = node
            
        def compile(self, checkpointer=None):
            return MockLangGraphApp(self.nodes, self.edges)
    
    END = "__end__"

try:
    from langgraph.checkpoint import MemorySaver
except ImportError:
    # Fallback memory saver
    class MemorySaver:
        def __init__(self):
            self.memory = {}

try:
    from langgraph.checkpoint.redis import RedisSaver
except ImportError:
    # Fallback redis saver
    class RedisSaver:
        def __init__(self, client):
            self.client = client

try:
    import redis
except ImportError:
    # Mock redis if not available
    class redis:
        @staticmethod
        def Redis(**kwargs):
            return None

from ..config import (
    AgentConfig,
    WorkflowType,
    NodeType,
    EdgeConfig
)
from ..core.state import create_state_class, StateManager
from ..core.llm_factory import LLMManager
from ..core.tools import ToolManager, ToolRegistry
from ..core.nodes import NodeFactory
from ..utils.metrics import MetricsCollector
from ..utils.logging import setup_logging


logger = structlog.get_logger()


class MockLangGraphApp:
    """Mock LangGraph application for when LangGraph is not available."""
    
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges
        
    async def ainvoke(self, state, config=None):
        """Mock async invoke method."""
        # Simple sequential execution for demonstration
        current_state = dict(state)
        
        for node_name, node_func in self.nodes.items():
            try:
                result = node_func(current_state)
                if isinstance(result, dict):
                    current_state.update(result)
                else:
                    current_state['output'] = result
            except Exception as e:
                current_state['error'] = str(e)
                break
                
        return current_state
        
    def invoke(self, state, config=None):
        """Mock sync invoke method."""
        # Simple sequential execution for demonstration
        current_state = dict(state)
        
        for node_name, node_func in self.nodes.items():
            try:
                result = node_func(current_state)
                if isinstance(result, dict):
                    current_state.update(result)
                else:
                    current_state['output'] = result
            except Exception as e:
                current_state['error'] = str(e)
                break
                
        return current_state
        
    async def astream(self, state, config=None):
        """Mock async stream method."""
        current_state = dict(state)
        
        for node_name, node_func in self.nodes.items():
            try:
                result = node_func(current_state)
                if isinstance(result, dict):
                    current_state.update(result)
                else:
                    current_state['output'] = result
                    
                yield {node_name: current_state}
            except Exception as e:
                current_state['error'] = str(e)
                yield {node_name: current_state}
                break


class AgentBuilder:
    """Builder for creating LangGraph agents from configuration."""
    
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        custom_handlers: Optional[Dict[str, Any]] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        """
        Initialize agent builder.
        
        Args:
            tool_registry: Registry of available tools
            custom_handlers: Custom node handlers
            metrics_collector: Metrics collector for monitoring
        """
        self.tool_registry = tool_registry or ToolRegistry()
        self.custom_handlers = custom_handlers or {}
        self.metrics_collector = metrics_collector
        self.node_factory = NodeFactory()
        
        # Setup logging if enabled
        setup_logging()
    
    def build(self, config: AgentConfig) -> "LangGraphAgent":
        """
        Build a LangGraph agent from configuration.
        
        Args:
            config: Agent configuration
            
        Returns:
            A configured LangGraph agent
        """
        logger.info(f"Building agent: {config.name}")
        
        try:
            # Create state class
            state_class = self._create_state_class(config)
            
            # Create managers
            llm_manager = self._create_llm_manager(config)
            tool_manager = self._create_tool_manager(config)
            
            # Build context for node creation
            context = {
                "llm_manager": llm_manager,
                "tool_manager": tool_manager,
                "custom_handlers": self.custom_handlers,
                "config": config,
                "metrics_collector": self.metrics_collector
            }
            
            # Create the graph
            graph = self._build_graph(config, state_class, context)
            
            # Create checkpointer if configured
            checkpointer = self._create_checkpointer(config)
            
            # Compile the graph
            app = graph.compile(checkpointer=checkpointer)
            
            # Create and return agent
            agent = LangGraphAgent(
                app=app,
                config=config,
                state_manager=StateManager(),
                llm_manager=llm_manager,
                tool_manager=tool_manager,
                metrics_collector=self.metrics_collector
            )
            
            logger.info(f"Successfully built agent: {config.name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to build agent {config.name}: {str(e)}")
            raise
    
    def _create_state_class(self, config: AgentConfig) -> type:
        """Create state class from configuration."""
        if config.state_schema:
            return create_state_class(config.state_schema.fields)
        return create_state_class()
    
    def _create_llm_manager(self, config: AgentConfig) -> LLMManager:
        """Create LLM manager."""
        llm_config = {
            "provider": config.llm_provider,
            "model": config.model,
            "api_key_env": config.api_key_env,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        return LLMManager(llm_config)
    
    def _create_tool_manager(self, config: AgentConfig) -> ToolManager:
        """Create tool manager."""
        tool_manager = ToolManager(self.tool_registry)
        
        # Register custom tools from config
        for tool_config in config.tools:
            if isinstance(tool_config, dict) and tool_config.get("type") == "custom":
                # Custom tool registration would go here
                pass
                
        return tool_manager
    
    def _build_graph(
        self,
        config: AgentConfig,
        state_class: type,
        context: Dict[str, Any]
    ) -> StateGraph:
        """Build the LangGraph state graph."""
        # Create graph
        graph = StateGraph(state_class)
        
        # Create nodes
        nodes = {}
        for node_config in config.nodes:
            node_func = self.node_factory.create_node(node_config, context)
            nodes[node_config.name] = node_func
            
            # Add node to graph
            if node_config.type == NodeType.CONDITIONAL:
                graph.add_conditional_edges(node_config.name, node_func)
            else:
                graph.add_node(node_config.name, node_func)
        
        # Add edges based on workflow type
        if config.workflow_type == WorkflowType.SEQUENTIAL:
            self._add_sequential_edges(graph, config.nodes)
        elif config.workflow_type == WorkflowType.PARALLEL:
            self._add_parallel_edges(graph, config.nodes)
        elif config.workflow_type == WorkflowType.CONDITIONAL:
            self._add_conditional_edges(graph, config)
        elif config.workflow_type == WorkflowType.CYCLIC:
            self._add_cyclic_edges(graph, config)
        elif config.workflow_type == WorkflowType.CUSTOM:
            self._add_custom_edges(graph, config)
        
        # Set entry point
        entry_point = config.entry_point or config.nodes[0].name
        graph.set_entry_point(entry_point)
        
        return graph
    
    def _add_sequential_edges(self, graph: StateGraph, nodes: List[Any]) -> None:
        """Add edges for sequential workflow."""
        for i in range(len(nodes) - 1):
            if nodes[i].type != NodeType.CONDITIONAL:
                graph.add_edge(nodes[i].name, nodes[i + 1].name)
        
        # Add edge from last node to END
        if nodes and nodes[-1].type != NodeType.CONDITIONAL:
            graph.add_edge(nodes[-1].name, END)
    
    def _add_parallel_edges(self, graph: StateGraph, nodes: List[Any]) -> None:
        """Add edges for parallel workflow."""
        # In parallel workflow, all nodes execute independently
        # This is a simplified implementation
        for node in nodes:
            if node.type != NodeType.CONDITIONAL:
                graph.add_edge(node.name, END)
    
    def _add_conditional_edges(self, graph: StateGraph, config: AgentConfig) -> None:
        """Add edges for conditional workflow."""
        # Use custom edges if provided
        if config.edges:
            for edge in config.edges:
                graph.add_edge(edge.source, edge.target)
        else:
            # Default conditional workflow
            self._add_sequential_edges(graph, config.nodes)
    
    def _add_cyclic_edges(self, graph: StateGraph, config: AgentConfig) -> None:
        """Add edges for cyclic workflow."""
        # Add cycle detection and iteration limit
        # This is a simplified implementation
        if config.edges:
            for edge in config.edges:
                graph.add_edge(edge.source, edge.target)
        else:
            # Create a default cycle
            nodes = config.nodes
            for i in range(len(nodes)):
                next_idx = (i + 1) % len(nodes)
                if nodes[i].type != NodeType.CONDITIONAL:
                    graph.add_edge(nodes[i].name, nodes[next_idx].name)
    
    def _add_custom_edges(self, graph: StateGraph, config: AgentConfig) -> None:
        """Add custom edges from configuration."""
        if not config.edges:
            raise ValueError("Custom workflow requires edges to be specified")
            
        for edge in config.edges:
            if edge.condition:
                # Conditional edge
                graph.add_conditional_edges(
                    edge.source,
                    lambda state: edge.target if eval(edge.condition, {"state": state}) else END
                )
            else:
                # Direct edge
                graph.add_edge(edge.source, edge.target)
    
    def _create_checkpointer(self, config: AgentConfig) -> Optional[Any]:
        """Create checkpointer based on configuration."""
        if not config.checkpointer:
            return MemorySaver()
            
        checkpointer_type = config.checkpointer.get("type", "memory")
        
        if checkpointer_type == "memory":
            return MemorySaver()
        elif checkpointer_type == "redis":
            redis_config = config.checkpointer.get("config", {})
            client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password")
            )
            return RedisSaver(client)
        else:
            raise ValueError(f"Unsupported checkpointer type: {checkpointer_type}")


class LangGraphAgent:
    """Wrapper for a compiled LangGraph agent."""
    
    def __init__(
        self,
        app: Any,
        config: AgentConfig,
        state_manager: StateManager,
        llm_manager: LLMManager,
        tool_manager: ToolManager,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        """Initialize LangGraph agent."""
        self.app = app
        self.config = config
        self.state_manager = state_manager
        self.llm_manager = llm_manager
        self.tool_manager = tool_manager
        self.metrics_collector = metrics_collector
    
    async def ainvoke(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke the agent asynchronously.
        
        Args:
            input_data: Input data for the agent
            config: Runtime configuration overrides
            thread_id: Thread ID for conversation continuity
            
        Returns:
            Agent execution result
        """
        try:
            # Prepare initial state
            initial_state = self._prepare_initial_state(input_data)
            
            # Prepare config
            run_config = self._prepare_run_config(config, thread_id)
            
            # Record metrics
            if self.metrics_collector:
                self.metrics_collector.record_invocation(self.config.name)
            
            # Invoke the agent
            result = await self.app.ainvoke(initial_state, config=run_config)
            
            # Process result
            final_result = self._process_result(result)
            
            # Record success
            if self.metrics_collector:
                self.metrics_collector.record_success(self.config.name)
                
            return final_result
            
        except Exception as e:
            logger.error(f"Error invoking agent {self.config.name}: {str(e)}")
            
            # Record error
            if self.metrics_collector:
                self.metrics_collector.record_error(self.config.name, str(e))
                
            raise
    
    def invoke(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Invoke the agent synchronously.
        
        Args:
            input_data: Input data for the agent
            config: Runtime configuration overrides
            thread_id: Thread ID for conversation continuity
            
        Returns:
            Agent execution result
        """
        try:
            # Prepare initial state
            initial_state = self._prepare_initial_state(input_data)
            
            # Prepare config
            run_config = self._prepare_run_config(config, thread_id)
            
            # Record metrics
            if self.metrics_collector:
                self.metrics_collector.record_invocation(self.config.name)
            
            # Invoke the agent
            result = self.app.invoke(initial_state, config=run_config)
            
            # Process result
            final_result = self._process_result(result)
            
            # Record success
            if self.metrics_collector:
                self.metrics_collector.record_success(self.config.name)
                
            return final_result
            
        except Exception as e:
            logger.error(f"Error invoking agent {self.config.name}: {str(e)}")
            
            # Record error
            if self.metrics_collector:
                self.metrics_collector.record_error(self.config.name, str(e))
                
            raise
    
    async def astream(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None
    ):
        """Stream agent execution asynchronously."""
        initial_state = self._prepare_initial_state(input_data)
        run_config = self._prepare_run_config(config, thread_id)
        
        async for event in self.app.astream(initial_state, config=run_config):
            yield event
    
    def _prepare_initial_state(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare initial state for agent execution."""
        state = self.state_manager._get_default_state()
        
        # Handle different input formats
        if isinstance(input_data, str):
            state["input"] = input_data
            state["messages"] = [{"role": "user", "content": input_data}]
        elif isinstance(input_data, dict):
            state.update(input_data)
            if "input" in input_data and "messages" not in input_data:
                state["messages"] = [{"role": "user", "content": input_data["input"]}]
        
        return state
    
    def _prepare_run_config(
        self,
        config: Optional[Dict[str, Any]],
        thread_id: Optional[str]
    ) -> Dict[str, Any]:
        """Prepare runtime configuration."""
        run_config = {"configurable": {}}
        
        if thread_id:
            run_config["configurable"]["thread_id"] = thread_id
            
        if config:
            run_config.update(config)
            
        return run_config
    
    def _process_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Process agent execution result."""
        # Extract key information from result
        processed = {
            "output": result.get("output"),
            "messages": result.get("messages", []),
            "metadata": result.get("metadata", {}),
            "error": result.get("error"),
        }
        
        # Add additional context if available
        if "tools_output" in result:
            processed["tools_output"] = result["tools_output"]
            
        if "intermediate_steps" in result:
            processed["intermediate_steps"] = result["intermediate_steps"]
            
        return processed 
"""Metrics collection for LangGraph Agent Builder."""

import time
from typing import Dict, Any, Optional
from contextlib import contextmanager

# Import with fallback
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary
except ImportError:
    # Fallback prometheus implementations
    class Counter:
        def __init__(self, name, description, labels=None):
            self.name = name
            self._value = type('Value', (), {'sum': lambda: 0})()
            
        def labels(self, **kwargs):
            return self
            
        def inc(self, amount=1):
            pass
    
    class Histogram:
        def __init__(self, name, description, labels=None):
            self.name = name
            
        def labels(self, **kwargs):
            return self
            
        def observe(self, amount):
            pass
    
    class Gauge:
        def __init__(self, name, description, labels=None):
            self.name = name
            self._value = type('Value', (), {'sum': lambda: 0})()
            
        def labels(self, **kwargs):
            return self
            
        def inc(self, amount=1):
            pass
            
        def dec(self, amount=1):
            pass
    
    class Summary:
        def __init__(self, name, description, labels=None):
            self.name = name
            
        def labels(self, **kwargs):
            return self
            
        def observe(self, amount):
            pass


class MetricsCollector:
    """Collects metrics for agent execution."""
    
    def __init__(self, namespace: str = "langgraph_agent"):
        """Initialize metrics collector."""
        self.namespace = namespace
        
        # Define metrics
        self.invocation_counter = Counter(
            f"{namespace}_invocations_total",
            "Total number of agent invocations",
            ["agent_name"]
        )
        
        self.success_counter = Counter(
            f"{namespace}_successes_total",
            "Total number of successful agent executions",
            ["agent_name"]
        )
        
        self.error_counter = Counter(
            f"{namespace}_errors_total",
            "Total number of agent errors",
            ["agent_name", "error_type"]
        )
        
        self.execution_time = Histogram(
            f"{namespace}_execution_duration_seconds",
            "Agent execution duration in seconds",
            ["agent_name", "node_name"]
        )
        
        self.node_execution_time = Summary(
            f"{namespace}_node_execution_duration_seconds",
            "Individual node execution duration in seconds",
            ["agent_name", "node_name", "node_type"]
        )
        
        self.active_agents = Gauge(
            f"{namespace}_active_agents",
            "Number of currently active agents",
            ["agent_name"]
        )
        
        self.llm_tokens = Counter(
            f"{namespace}_llm_tokens_total",
            "Total number of LLM tokens used",
            ["agent_name", "model", "token_type"]
        )
        
        self.tool_calls = Counter(
            f"{namespace}_tool_calls_total",
            "Total number of tool calls",
            ["agent_name", "tool_name"]
        )
    
    def record_invocation(self, agent_name: str) -> None:
        """Record an agent invocation."""
        self.invocation_counter.labels(agent_name=agent_name).inc()
        self.active_agents.labels(agent_name=agent_name).inc()
    
    def record_success(self, agent_name: str) -> None:
        """Record a successful agent execution."""
        self.success_counter.labels(agent_name=agent_name).inc()
        self.active_agents.labels(agent_name=agent_name).dec()
    
    def record_error(self, agent_name: str, error: str) -> None:
        """Record an agent error."""
        error_type = type(error).__name__ if hasattr(error, "__class__") else "Unknown"
        self.error_counter.labels(agent_name=agent_name, error_type=error_type).inc()
        self.active_agents.labels(agent_name=agent_name).dec()
    
    @contextmanager
    def measure_execution_time(self, agent_name: str, node_name: str = "total"):
        """Context manager to measure execution time."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.execution_time.labels(
                agent_name=agent_name,
                node_name=node_name
            ).observe(duration)
    
    def record_node_execution(
        self,
        agent_name: str,
        node_name: str,
        node_type: str,
        duration: float
    ) -> None:
        """Record node execution metrics."""
        self.node_execution_time.labels(
            agent_name=agent_name,
            node_name=node_name,
            node_type=node_type
        ).observe(duration)
    
    def record_llm_tokens(
        self,
        agent_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None:
        """Record LLM token usage."""
        self.llm_tokens.labels(
            agent_name=agent_name,
            model=model,
            token_type="prompt"
        ).inc(prompt_tokens)
        
        self.llm_tokens.labels(
            agent_name=agent_name,
            model=model,
            token_type="completion"
        ).inc(completion_tokens)
    
    def record_tool_call(self, agent_name: str, tool_name: str) -> None:
        """Record a tool call."""
        self.tool_calls.labels(
            agent_name=agent_name,
            tool_name=tool_name
        ).inc()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics as a dictionary."""
        # This is a simplified version - in production, you'd want to
        # properly serialize Prometheus metrics
        return {
            "invocations": self.invocation_counter._value.sum(),
            "successes": self.success_counter._value.sum(),
            "errors": self.error_counter._value.sum(),
            "active_agents": self.active_agents._value.sum(),
        }


class NoOpMetricsCollector(MetricsCollector):
    """No-op metrics collector for when metrics are disabled."""
    
    def __init__(self, namespace: str = "langgraph_agent"):
        """Initialize no-op metrics collector."""
        self.namespace = namespace
    
    def record_invocation(self, agent_name: str) -> None:
        """No-op."""
        pass
    
    def record_success(self, agent_name: str) -> None:
        """No-op."""
        pass
    
    def record_error(self, agent_name: str, error: str) -> None:
        """No-op."""
        pass
    
    @contextmanager
    def measure_execution_time(self, agent_name: str, node_name: str = "total"):
        """No-op context manager."""
        yield
    
    def record_node_execution(
        self,
        agent_name: str,
        node_name: str,
        node_type: str,
        duration: float
    ) -> None:
        """No-op."""
        pass
    
    def record_llm_tokens(
        self,
        agent_name: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None:
        """No-op."""
        pass
    
    def record_tool_call(self, agent_name: str, tool_name: str) -> None:
        """No-op."""
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return empty metrics."""
        return {} 
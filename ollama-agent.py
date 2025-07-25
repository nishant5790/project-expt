from agno.agent import Agent
from agno.models.ollama import OllamaTools
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OllamaTools(id="gemma3"),
    show_tool_calls=True,
    markdown=True,
)
agent.print_response("What is the capital of France?")